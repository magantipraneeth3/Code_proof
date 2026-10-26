from fastapi import APIRouter, HTTPException, Request

from app.analyzers.registry import LANGUAGES
from app.core.config import settings
from app.core.ratelimit import SlidingWindowLimiter
from app.schemas.api import PublicAnalyzeIn, PublicCompareIn
from app.services.public_analysis import _SIMILARITY_LANGUAGES, compare_sources, public_analyze, public_samples

router = APIRouter(prefix="/public", tags=["public analyzer"])
_limiter = SlidingWindowLimiter(settings.public_analysis_rate_limit)
_SUPPORTED = {item["id"] for item in LANGUAGES if item["status"] == "supported"}


def _rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    if not _limiter.allow(client_host):
        raise HTTPException(429, "Public analysis limit reached. Please wait a minute before trying again.")


def _source_bytes(*sources: str) -> None:
    if any(len(source.encode("utf-8")) > settings.max_source_bytes for source in sources):
        raise HTTPException(413, f"Each code sample is limited to {settings.max_source_bytes} bytes.")


@router.get("/health")
def public_health():
    return {"status": "ok", "syntax_structure_analysis": "available", "authorship_model": "unavailable",
            "syntax_and_structure_languages": [item["id"] for item in LANGUAGES if item["status"] == "supported"],
            "similarity_languages": ["python", "java", "c", "cpp", "javascript", "typescript", "tsx"],
            "max_source_bytes": settings.max_source_bytes}


@router.get("/samples")
def list_public_samples():
    return {"items": public_samples()}


@router.post("/analyze")
def analyze_public(body: PublicAnalyzeIn, request: Request):
    _rate_limit(request)
    _source_bytes(body.code)
    try:
        return public_analyze(body.code, body.language, body.compare_samples)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/compare")
def compare_public(body: PublicCompareIn, request: Request):
    _rate_limit(request)
    _source_bytes(body.code_a, body.code_b)
    if not body.code_a.strip() or not body.code_b.strip():
        raise HTTPException(422, "Enter code in both samples before comparing.")
    try:
        language_a = body.language_a.strip().lower()
        language_b = body.language_b.strip().lower()
        known = {item["id"] for item in LANGUAGES}
        if language_a not in known or language_b not in known:
            raise ValueError(f"Choose a supported language option: {', '.join(sorted(known))}.")
        if language_a != language_b:
            return {"comparison_status": "language_mismatch", "similarity_percent": None,
                    "structural_similarity_percent": None, "matching_regions": [],
                    "explanation": "Choose the same language for both samples. Cross-language comparison is not implemented."}
        if language_a not in _SUPPORTED:
            return {"comparison_status": "unsupported_language", "language": language_a,
                    "similarity_percent": None, "structural_similarity_percent": None,
                    "matching_regions": [],
                    "explanation": f"No language-aware comparison method is available for {language_a}."}
        if language_a not in _SIMILARITY_LANGUAGES:
            return {"comparison_status": "comparison_unavailable", "language": language_a,
                "similarity_percent": None, "structural_similarity_percent": None,
                "matching_regions": [],
                "explanation": f"No language-aware similarity method is available for {language_a}."}
        return {"language": language_a, **compare_sources(body.code_a, body.code_b, language_a)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc