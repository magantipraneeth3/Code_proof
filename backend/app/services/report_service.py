"""PDF report generation. Content is built by report_sections() (pure, testable) and
rendered by build_report_pdf(). Nothing here invents evidence: features that are not
implemented are reported as 'not performed'."""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FOLLOW_UP = [
    "Treat this report as decision-support evidence for human review, not as proof of authorship or misconduct.",
    "If questions remain, consider asking the student to explain or walk through their code.",
    "Do not base an allegation of academic misconduct on this report alone.",
    "Consider that permitted AI assistance or common textbook solutions can produce similar code.",
]


def report_sections(*, report_id: str, generated_at: str, app_version: str, assignment_title: str,
                    student_label: str, filename: str, submitted_at: str, analysis: dict,
                    review_status: str = "needs_review", review_notes: list[dict] | None = None
                    ) -> list[tuple[str, list]]:
    """Returns [(heading, rows)] where rows are strings or (label, value) pairs."""
    a = analysis
    sections: list[tuple[str, list]] = [
        ("Report details", [("Report ID", report_id), ("Generated (UTC)", generated_at),
                            ("Application version", app_version), ("Analysis ID", a["analysis_id"]),
                            ("Analysis date", a.get("created_at") or "n/a")]),
        ("Submission", [("Assignment", assignment_title), ("Student", student_label),
                        ("File", filename), ("Submitted", submitted_at),
                        ("Detected language", a.get("language") or "unknown")]),
        ("Analysis status", [("Status", a["analysis_status"]),
                             ("Syntax valid", {True: "yes", False: "no", None: "not determined"}[a.get("syntax_valid")])]
                            + ([("Syntax error", a["syntax_error"])] if a.get("syntax_error") else [])
                            + ([("Message", a["message"])] if a.get("message") else [])),
    ]
    metrics = a.get("code_metrics")
    sections.append(("Code metrics (descriptive only; not evidence of authorship)",
                     [(k.replace("_", " "), str(v)) for k, v in metrics.items()] if metrics
                     else ["No code metrics available for this analysis."]))
    sections.append(("Structural observations", a.get("structural_findings") or ["None recorded."]))
    sections.append(("Evidence assessment (UNVERIFIED unless stated)", [
        ("A. Verified provenance evidence", a["provenance_summary"]
         + " This does not imply that AI was not used."),
        ("B. Model-based indication", f"Model status: {a['model_status']}. " + (a.get("model_reason") or "")),
        ("C. Code similarity", "Not performed (similarity comparison is not implemented in this version)."),
        ("D. Development history", "Not analyzed (Git history analysis is not implemented in this version)."),
        ("E. Overall authorship assessment", a["authorship_assessment"].upper()),
    ]))
    note_rows = [f"{note['author_email']} · {note['created_at']}: {note['body']}"
                 for note in (review_notes or [])]
    sections.append(("Human review", [f"Review status: {review_status.replace('_', ' ')}"] +
                     (note_rows or ["No reviewer notes recorded."])))
    sections.append(("Recommended follow-up", FOLLOW_UP))
    return sections


def build_report_pdf(**kwargs) -> bytes:
    sections = report_sections(**kwargs)
    report_id = kwargs["report_id"]
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=colors.HexColor("#1a2440"), spaceBefore=10)
    banner = ParagraphStyle("banner", parent=body, backColor=colors.HexColor("#fff4d6"), borderPadding=6)
    P = lambda t, s=body: Paragraph(escape(str(t)), s)

    story = [Paragraph("CodeProof Analysis Report", styles["Title"]),
             Paragraph("UNVERIFIED ASSESSMENT — decision support for human review only. "
                       "This report does not prove authorship or misconduct.", banner), Spacer(1, 6)]
    for heading, rows in sections:
        story.append(Paragraph(escape(heading), h2))
        pairs = [r for r in rows if isinstance(r, tuple)]
        plain = [r for r in rows if not isinstance(r, tuple)]
        if pairs:
            t = Table([[P(k), P(v)] for k, v in pairs], colWidths=[55 * mm, 115 * mm])
            t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f4fa"))]))
            story.append(t)
        for line in plain:
            story.append(P("• " + str(line)))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(18 * mm, 10 * mm, f"CodeProof report {report_id}")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    buf = BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=16 * mm, bottomMargin=18 * mm,
                      title=f"CodeProof report {report_id}").build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
