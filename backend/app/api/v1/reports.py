from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import settings
from app.core.db import get_db
from app.models import Analysis, Report, Role, User
from app.schemas.api import ReportIn
from app.services import audit
from app.services.access import get_submission_for, not_found
from app.services.analysis_store import analysis_to_dict
from app.services.report_service import build_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])
_professor = require_roles(Role.professor)  # restricted: students cannot generate or download reports


@router.post("", status_code=201)
def create_report(body: ReportIn, user: User = Depends(_professor), db: Session = Depends(get_db)):
    analysis = db.get(Analysis, body.analysis_id)
    if analysis is None:
        raise not_found("Analysis")
    sub = get_submission_for(db, user, analysis.submission_id)
    report = Report(submission_id=sub.id, analysis_id=analysis.id, created_by=user.id)
    db.add(report)
    db.flush()
    audit.record(db, user, "report_generated", "report", report.id, submission_id=sub.id)
    db.commit()
    return {"report_id": report.id, "download_url": f"/api/v1/reports/{report.id}/download"}


@router.get("/{report_id}/download")
def download_report(report_id: str, user: User = Depends(_professor), db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if report is None:
        raise not_found("Report")
    sub = get_submission_for(db, user, report.submission_id)
    analysis = db.get(Analysis, report.analysis_id)
    pdf = build_report_pdf(
        report_id=report.id, generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        app_version=settings.app_version, assignment_title=sub.assignment.title,
        student_label=sub.student.email, filename=sub.original_filename,
        submitted_at=sub.submitted_at.isoformat(), analysis=analysis_to_dict(analysis),
        review_status=sub.review_record.status if sub.review_record else "needs_review",
        review_notes=[{"author_email": note.author.email, "created_at": note.created_at.isoformat(),
                   "body": note.body} for note in sub.review_notes])
    audit.record(db, user, "report_downloaded", "report", report.id)
    db.commit()
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="codeproof-report-{report.id}.pdf"'})
