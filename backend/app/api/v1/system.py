from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analyzers.registry import LANGUAGES
from app.core.config import settings
from app.core.db import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "version": settings.app_version,
            "database": "ok" if db_ok else "unavailable"}


@router.get("/languages")
def languages():
    return {"languages": LANGUAGES}
