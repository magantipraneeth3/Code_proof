import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Analysis, Submission
from app.services.analysis_service import analyze_source, failed_result, to_api

log = logging.getLogger("codeproof.analysis")


def run_analysis(db: Session, submission: Submission, source: str) -> Analysis:
    """Runs the real analyzer and stores the result. Source code is parsed, never executed."""
    lang = None if submission.language == "unknown" else submission.language
    try:
        result = analyze_source(source, lang, submission.original_filename)
    except Exception as exc:  # analyzer bug: record a failed analysis, never a fake success
        log.error("analysis failed submission_id=%s type=%s", submission.id, type(exc).__name__)
        result = failed_result(lang)
    row = Analysis(
        id=result["analysis_id"], submission_id=submission.id,
        analysis_status=result["analysis_status"], language=result.get("language"),
        syntax_result={"valid": result.get("syntax_valid"), "error": result.get("syntax_error")},
        code_metrics=result.get("code_metrics"),
        structural_findings=result.get("structural_findings", []),
        evidence_category=result["evidence_category"], model_version=result.get("model_version"),
        model_output={k: result.get(k) for k in ("model_status", "authorship_assessment", "probability", "reason")},
        provenance_summary=result["provenance_summary"], limitations=result["limitations"],
        message=result.get("message"), completed_at=datetime.now(timezone.utc),
    )
    db.add(row)
    return row


def analysis_to_dict(a: Analysis) -> dict:
    mo, sr = a.model_output or {}, a.syntax_result or {}
    return {
        "analysis_id": a.id, "submission_id": a.submission_id, "analysis_status": a.analysis_status,
        "language": a.language, "syntax_valid": sr.get("valid"), "syntax_error": sr.get("error"),
        "code_metrics": a.code_metrics, "structural_findings": a.structural_findings or [],
        "evidence_category": a.evidence_category, "model_status": mo.get("model_status", "unavailable"),
        "model_version": a.model_version,
        "authorship_assessment": mo.get("authorship_assessment", "inconclusive"),
        "probability": mo.get("probability"), "model_reason": mo.get("reason"),
        "provenance_summary": a.provenance_summary, "limitations": a.limitations or [],
        "message": a.message,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "completed_at": a.completed_at.isoformat() if a.completed_at else None,
    }
