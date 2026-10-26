from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analyzers.registry import LANGUAGES
from app.api.deps import get_current_user, require_roles
from app.core.db import get_db
from app.core.files import delete_source
from app.models import Assignment, Role, User
from app.schemas.api import AssignmentIn, AssignmentPatch
from app.services import audit
from app.services.access import get_owned_assignment, not_found
from fastapi import HTTPException

router = APIRouter(prefix="/assignments", tags=["assignments"])
_KNOWN = {l["id"] for l in LANGUAGES}


def _check_languages(langs: list[str] | None) -> list[str] | None:
    if langs is None:
        return None
    clean = [l.lower() for l in langs]
    bad = [l for l in clean if l not in _KNOWN]
    if bad:
        raise HTTPException(422, f"Unknown language(s): {', '.join(sorted(set(bad)))}.")
    return sorted(set(clean))


def _out(a: Assignment, user: User) -> dict:
    d = {"id": a.id, "professor_id": a.professor_id, "title": a.title, "description": a.description,
         "instructions": a.instructions, "allowed_languages": a.allowed_languages or [],
         "due_date": a.due_date.isoformat() if a.due_date else None,
         "created_at": a.created_at.isoformat(), "updated_at": a.updated_at.isoformat(),
         "submission_count": None}
    if user.role == Role.professor and a.professor_id == user.id:
        d["submission_count"] = len(a.submissions)
    return d


@router.get("")
def list_assignments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Assignment).order_by(Assignment.created_at.desc())
    if user.role == Role.professor:
        stmt = stmt.where(Assignment.professor_id == user.id)
    # Students and admins see all assignments (no enrollment model yet).
    return {"items": [_out(a, user) for a in db.scalars(stmt)]}


@router.post("", status_code=201)
def create_assignment(body: AssignmentIn, user: User = Depends(require_roles(Role.professor)),
                      db: Session = Depends(get_db)):
    a = Assignment(professor_id=user.id, title=body.title.strip(), description=body.description,
                   instructions=body.instructions, allowed_languages=_check_languages(body.allowed_languages) or [],
                   due_date=body.due_date)
    db.add(a)
    db.flush()
    audit.record(db, user, "assignment_created", "assignment", a.id)
    db.commit()
    db.refresh(a)
    return _out(a, user)


@router.get("/{assignment_id}")
def get_assignment(assignment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(Assignment, assignment_id)
    if a is None:
        raise not_found("Assignment")
    if user.role == Role.professor and a.professor_id != user.id:
        raise not_found("Assignment")
    return _out(a, user)


@router.patch("/{assignment_id}")
def update_assignment(assignment_id: int, body: AssignmentPatch,
                      user: User = Depends(require_roles(Role.professor)), db: Session = Depends(get_db)):
    a = get_owned_assignment(db, user, assignment_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "allowed_languages":
            value = _check_languages(value)
        if field == "title" and value is None:
            continue
        setattr(a, field, value)
    audit.record(db, user, "assignment_updated", "assignment", a.id)
    db.commit()
    db.refresh(a)
    return _out(a, user)


@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: int, user: User = Depends(require_roles(Role.professor)),
                      db: Session = Depends(get_db)):
    a = get_owned_assignment(db, user, assignment_id)
    refs = [s.secure_storage_reference for s in a.submissions]
    audit.record(db, user, "assignment_deleted", "assignment", a.id, submissions_deleted=len(refs))
    db.delete(a)
    db.commit()
    for ref in refs:
        delete_source(ref)
    return Response(status_code=204)
