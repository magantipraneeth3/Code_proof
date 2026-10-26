from sqlalchemy.orm import Session

from app.models import AuditEvent, User


def record(db: Session, actor: User | None, event_type: str, resource_type: str,
           resource_id, **safe_metadata) -> None:
    """Adds an audit row (caller commits). Never pass source code, passwords or tokens."""
    db.add(AuditEvent(actor_id=actor.id if actor else None, event_type=event_type,
                      resource_type=resource_type, resource_id=str(resource_id),
                      safe_metadata=safe_metadata))
