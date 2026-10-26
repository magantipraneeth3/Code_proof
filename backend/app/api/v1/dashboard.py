from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.db import get_db
from app.models import Assignment, Role, User
from app.services.access import submission_scope

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(user: User = Depends(require_roles(Role.student, Role.professor)), db: Session = Depends(get_db)):
    """Real counts from the user's own data. Fields for unbuilt features are omitted, not faked."""
    subs = list(db.scalars(submission_scope(user).order_by(None)))
    if user.role == Role.professor:
        total_assignments = db.scalar(select(func.count()).select_from(Assignment)
                                      .where(Assignment.professor_id == user.id)) or 0
    else:
        total_assignments = db.scalar(select(func.count()).select_from(Assignment)) or 0
    latest = [s.analyses[-1] for s in subs if s.analyses]
    needs_review = sum(not s.review_record or s.review_record.status == "needs_review" for s in subs) \
        if user.role == Role.professor else 0
    recent = sorted(subs, key=lambda s: s.submitted_at, reverse=True)[:5]
    return {
        "total_assignments": total_assignments,
        "total_submissions": len(subs),
        "completed_analyses": sum(a.analysis_status == "completed" for a in latest),
        "recent_submissions": [{"id": s.id, "filename": s.original_filename, "language": s.language,
                                "submitted_at": s.submitted_at.isoformat()} for s in recent],
        **({"needs_review": needs_review} if user.role == Role.professor else {}),
    }
