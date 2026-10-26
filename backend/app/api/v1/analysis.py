from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.db import get_db
from app.core.files import read_source
from app.models import Analysis, Role, User
from app.schemas.api import AnalysisRunIn, PreviewIn
from app.services import audit
from app.services.access import get_submission_for, not_found
from app.services.analysis_service import analyze_source, to_api
from app.services.analysis_store import analysis_to_dict, run_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/preview")
def preview(body: PreviewIn, user: User = Depends(require_roles(Role.student, Role.professor))):
    """Analyze pasted code without storing it. Returns the real analyzer output."""
    return to_api(analyze_source(body.source, body.language, body.filename))


def _rerun(db: Session, user: User, submission_id: int) -> dict:
    sub = get_submission_for(db, user, submission_id)
    source = read_source(sub.secure_storage_reference)
    if source is None:
        raise HTTPException(409, "The stored source file is no longer available.")
    row = run_analysis(db, sub, source)
    audit.record(db, user, "analysis_run", "analysis", row.id, submission_id=sub.id)
    db.commit()
    db.refresh(row)
    return analysis_to_dict(row)


@router.post("", status_code=201)
def run(body: AnalysisRunIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _rerun(db, user, body.submission_id)


def _get_analysis(db: Session, user: User, analysis_id: str) -> Analysis:
    a = db.get(Analysis, analysis_id)
    if a is None:
        raise not_found("Analysis")
    get_submission_for(db, user, a.submission_id)  # enforces data isolation (404 if out of scope)
    return a


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analysis_to_dict(_get_analysis(db, user, analysis_id))


@router.post("/{analysis_id}/retry", status_code=201)
def retry(analysis_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = _get_analysis(db, user, analysis_id)
    if a.analysis_status != "failed":
        raise HTTPException(409, "Only failed analyses can be retried. Use POST /analysis to run a new analysis.")
    return _rerun(db, user, a.submission_id)
