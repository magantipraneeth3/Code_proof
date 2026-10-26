from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.analyzers.registry import LANGUAGES, detect_language
from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.core.db import get_db
from app.core.files import UploadError, delete_source, read_source, store_source, validate_source_upload
from app.models import Assignment, Role, Submission, User
from app.models import Assignment, Role, Submission, SubmissionReview, User
from app.schemas.api import SubmissionIn
from app.services import audit
from app.services.access import get_submission_for, not_found, submission_scope
from app.services.analysis_store import analysis_to_dict, run_analysis

router = APIRouter(prefix="/submissions", tags=["submissions"])
_KNOWN = {l["id"] for l in LANGUAGES}


def _summary(s: Submission, viewer: User) -> dict:
    latest = s.analyses[-1] if s.analyses else None
    return {
        "id": s.id, "assignment_id": s.assignment_id, "assignment_title": s.assignment.title,
        "student_id": s.student_id,
        "student_email": s.student.email if viewer.role == Role.professor else None,
        "original_filename": s.original_filename, "language": s.language,
        "submission_status": s.submission_status, "submitted_at": s.submitted_at.isoformat(),
        "latest_analysis_id": latest.id if latest else None,
        "latest_analysis_status": latest.analysis_status if latest else None,
        "review_status": (s.review_record.status if s.review_record else "needs_review")
                 if viewer.role == Role.professor else None,
        "reviewed_at": (s.review_record.reviewed_at.isoformat() if s.review_record and s.review_record.reviewed_at else None)
                   if viewer.role == Role.professor else None,
    }


def _create(db: Session, student: User, assignment_id: int, filename: str, declared: str | None,
            data: bytes) -> dict:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise not_found("Assignment")
    try:
        name, text = validate_source_upload(filename, data, settings.max_source_bytes)
    except UploadError as exc:
        raise HTTPException(422, str(exc))
    if declared and declared.lower() not in _KNOWN:
        raise HTTPException(422, f"Unknown language '{declared}'.")
    lang = detect_language(name, declared) or "unknown"
    if assignment.allowed_languages and lang not in assignment.allowed_languages:
        raise HTTPException(422, "This language is not allowed for the assignment "
                                 f"(allowed: {', '.join(assignment.allowed_languages)}).")
    ref = store_source(text)
    try:
        sub = Submission(assignment_id=assignment.id, student_id=student.id, original_filename=name,
                         language=lang, secure_storage_reference=ref)
        db.add(sub)
        db.flush()
        run_analysis(db, sub, text)
        audit.record(db, student, "submission_created", "submission", sub.id,
                     assignment_id=assignment.id, language=lang, size_bytes=len(data))
        db.commit()
    except Exception:
        db.rollback()
        delete_source(ref)
        raise
    db.refresh(sub)
    return _summary(sub, student)


@router.post("", status_code=201)
def create_submission(body: SubmissionIn, student: User = Depends(require_roles(Role.student)),
                      db: Session = Depends(get_db)):
    return _create(db, student, body.assignment_id, body.filename, body.language, body.source.encode("utf-8"))


@router.post("/upload", status_code=201)
async def upload_submission(assignment_id: int = Form(...), language: str | None = Form(None),
                            file: UploadFile = File(...),
                            student: User = Depends(require_roles(Role.student)),
                            db: Session = Depends(get_db)):
    data = await file.read(settings.max_source_bytes + 1)  # bounded read
    return _create(db, student, assignment_id, file.filename or "", language, data)


@router.get("")
def list_submissions(user: User = Depends(get_current_user), db: Session = Depends(get_db),
                     assignment_id: int | None = None, language: str | None = None,
                     review_status: Literal["needs_review", "reviewed"] | None = None,
                     q: str | None = Query(None, max_length=100),
                     page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    stmt = submission_scope(user)
    if assignment_id is not None:
        stmt = stmt.where(Submission.assignment_id == assignment_id)
    if language:
        stmt = stmt.where(Submission.language == language.lower())
    if review_status:
        if user.role != Role.professor:
            raise HTTPException(403, "Review status filters are only available to professors.")
        stmt = stmt.outerjoin(SubmissionReview)
        if review_status == "needs_review":
            stmt = stmt.where(or_(SubmissionReview.submission_id.is_(None),
                                  SubmissionReview.status == "needs_review"))
        else:
            stmt = stmt.where(SubmissionReview.status == "reviewed")
    if q:
        stmt = stmt.where(Submission.original_filename.ilike(f"%{q}%"))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.order_by(Submission.submitted_at.desc()).limit(page_size).offset((page - 1) * page_size))
    return {"items": [_summary(s, user) for s in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/{submission_id}")
def get_submission(submission_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = get_submission_for(db, user, submission_id)
    return {**_summary(s, user), "source": read_source(s.secure_storage_reference),
            "analyses": [analysis_to_dict(a) for a in s.analyses]}


@router.delete("/{submission_id}", status_code=204)
def delete_submission(submission_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = get_submission_for(db, user, submission_id)
    ref = s.secure_storage_reference
    audit.record(db, user, "submission_deleted", "submission", s.id)
    db.delete(s)
    db.commit()
    delete_source(ref)
    return Response(status_code=204)
