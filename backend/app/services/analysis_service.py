import uuid
from datetime import datetime, timezone

from app.analyzers.registry import detect_language, get_analyzer
from app.core.config import settings
from app.ml.inference import model_assessment

NO_PROVENANCE = "No verified provenance evidence available."
GENERAL_LIMITATIONS = [
    "Authorship cannot be reliably determined from final source code alone.",
    "No verified provenance evidence does not imply AI was not used.",
    "Findings are decision-support evidence for human review, not proof of misconduct.",
]


def analyze_source(source: str, language: str | None = None, filename: str | None = None) -> dict:
    base = {
        "analysis_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_category": "E",
        "provenance_summary": NO_PROVENANCE,
        "limitations": list(GENERAL_LIMITATIONS),
        **model_assessment(),
    }
    lang = detect_language(filename, language)
    base["language"] = lang

    if not source or not source.strip():
        return {**base, "analysis_status": "rejected_empty", "message": "No source code provided."}
    if len(source.encode("utf-8", errors="ignore")) > settings.max_source_bytes:
        return {**base, "analysis_status": "rejected_too_large",
                "message": f"Source exceeds the {settings.max_source_bytes}-byte limit."}
    analyzer = get_analyzer(lang) if lang else None
    if analyzer is None:
        return {**base, "analysis_status": "unsupported_language",
                "message": f"Language '{lang or 'unknown'}' is not supported yet; no analysis was performed."}

    result = analyzer.analyze(source)
    return {
        **base,
        "analysis_status": "completed",
        "syntax_valid": result.syntax_valid,
        "syntax_error": result.syntax_error,
        "code_metrics": result.metrics,
        "structural_findings": result.structural_findings,
        "limitations": result.limitations + base["limitations"],
    }


def failed_result(language: str | None = None) -> dict:
    return {
        "analysis_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_category": "E",
        "provenance_summary": NO_PROVENANCE,
        "limitations": list(GENERAL_LIMITATIONS),
        **model_assessment(),
        "language": language,
        "analysis_status": "failed",
        "message": "Analysis failed due to an internal error. It can be retried.",
    }


def to_api(result: dict, submission_id: int | None = None) -> dict:
    """Normalize analyze_source() output to the shape the API returns."""
    return {
        "analysis_id": result["analysis_id"],
        "submission_id": submission_id,
        "analysis_status": result["analysis_status"],
        "language": result.get("language"),
        "syntax_valid": result.get("syntax_valid"),
        "syntax_error": result.get("syntax_error"),
        "code_metrics": result.get("code_metrics"),
        "structural_findings": result.get("structural_findings", []),
        "evidence_category": result["evidence_category"],
        "model_status": result["model_status"],
        "model_version": result.get("model_version"),
        "authorship_assessment": result["authorship_assessment"],
        "probability": result.get("probability"),
        "model_reason": result.get("reason"),
        "provenance_summary": result["provenance_summary"],
        "limitations": result["limitations"],
        "message": result.get("message"),
        "created_at": result["created_at"],
        "completed_at": result["created_at"],
    }
