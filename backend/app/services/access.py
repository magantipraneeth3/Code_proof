"""Single source of truth for data isolation. Resources outside a user's scope are
reported as 404 (not 403) so their existence is not revealed."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Assignment, Role, Submission, User


def not_found(what: str = "Resource") -> HTTPException:
    return HTTPException(status_code=404, detail=f"{what} not found.")


def submission_scope(user: User):
    """SELECT of the submissions this user may see. Admins get no access to student code."""
    stmt = select(Submission).join(Assignment, Submission.assignment_id == Assignment.id)
    if user.role == Role.student:
        return stmt.where(Submission.student_id == user.id)
    if user.role == Role.professor:
        return stmt.where(Assignment.professor_id == user.id)
    raise HTTPException(status_code=403, detail="Your role cannot access submissions.")


def get_submission_for(db: Session, user: User, submission_id: int) -> Submission:
    sub = db.scalar(submission_scope(user).where(Submission.id == submission_id))
    if sub is None:
        raise not_found("Submission")
    return sub


def get_owned_assignment(db: Session, user: User, assignment_id: int) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if a is None or a.professor_id != user.id:
        raise not_found("Assignment")
    return a
