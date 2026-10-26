from fastapi import APIRouter, Depends, HTTPException, Response
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.db import get_db
from app.models import ReviewNote, Role, User
from app.models import ReviewNote, Role, SubmissionReview, User
from app.schemas.api import ReviewNoteIn, ReviewNotePatch, ReviewStatusIn
from app.services import audit
from app.services.access import get_submission_for, not_found

router = APIRouter(prefix="/submissions", tags=["review notes"])
_professor = require_roles(Role.professor)


def _out(note: ReviewNote) -> dict:
    return {
        "id": note.id,
        "submission_id": note.submission_id,
        "author_email": note.author.email,
        "body": note.body,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


@router.patch("/{submission_id}/review-status")
def set_review_status(submission_id: int, body: ReviewStatusIn,
                      user: User = Depends(_professor), db: Session = Depends(get_db)):
    submission = get_submission_for(db, user, submission_id)
    review = db.get(SubmissionReview, submission_id)
    if review is None:
        review = SubmissionReview(submission_id=submission.id)
        db.add(review)
    review.status = body.status
    review.reviewed_by_id = user.id if body.status == "reviewed" else None
    review.reviewed_at = datetime.now(timezone.utc) if body.status == "reviewed" else None
    audit.record(db, user, "submission_review_status_changed", "submission", submission.id,
                 status=body.status)
    db.commit()
    db.refresh(review)
    return {"submission_id": submission.id, "review_status": review.status,
            "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None}


@router.get("/{submission_id}/notes")
def list_notes(submission_id: int, user: User = Depends(_professor), db: Session = Depends(get_db)):
    submission = get_submission_for(db, user, submission_id)
    return {"items": [_out(note) for note in submission.review_notes]}


@router.post("/{submission_id}/notes", status_code=201)
def create_note(submission_id: int, body: ReviewNoteIn,
                user: User = Depends(_professor), db: Session = Depends(get_db)):
    submission = get_submission_for(db, user, submission_id)
    text = body.body.strip()
    if not text:
        raise HTTPException(422, "A review note cannot be empty.")
    note = ReviewNote(submission_id=submission.id, author_id=user.id, body=text)
    db.add(note)
    db.flush()
    audit.record(db, user, "review_note_created", "review_note", note.id,
                 submission_id=submission.id)
    db.commit()
    db.refresh(note)
    return _out(note)


@router.patch("/{submission_id}/notes/{note_id}")
def update_note(submission_id: int, note_id: int, body: ReviewNotePatch,
                user: User = Depends(_professor), db: Session = Depends(get_db)):
    get_submission_for(db, user, submission_id)
    note = db.get(ReviewNote, note_id)
    if note is None or note.submission_id != submission_id:
        raise not_found("Review note")
    text = body.body.strip()
    if not text:
        raise HTTPException(422, "A review note cannot be empty.")
    note.body = text
    audit.record(db, user, "review_note_updated", "review_note", note.id,
                 submission_id=submission_id)
    db.commit()
    db.refresh(note)
    return _out(note)


@router.delete("/{submission_id}/notes/{note_id}", status_code=204)
def delete_note(submission_id: int, note_id: int,
                user: User = Depends(_professor), db: Session = Depends(get_db)):
    get_submission_for(db, user, submission_id)
    note = db.get(ReviewNote, note_id)
    if note is None or note.submission_id != submission_id:
        raise not_found("Review note")
    audit.record(db, user, "review_note_deleted", "review_note", note.id,
                 submission_id=submission_id)
    db.delete(note)
    db.commit()
    return Response(status_code=204)