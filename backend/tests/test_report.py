import unittest

from app.services.analysis_service import analyze_source, to_api
from app.services.report_service import build_report_pdf, report_sections

KW = dict(report_id="r-1", generated_at="2026-10-26T00:00:00Z", app_version="0.2.0",
          assignment_title="HW1", student_label="s@example.com", filename="a.py",
          submitted_at="2026-10-26T00:00:00Z")


def flat(sections):
    out = []
    for h, rows in sections:
        out.append(h)
        for r in rows:
            out.extend(r if isinstance(r, tuple) else [r])
    return "\n".join(map(str, out))


class ReportTests(unittest.TestCase):
    def test_content_is_honest(self):
        a = to_api(analyze_source("def f():\n    return 1\n", "python"), 1)
        text = flat(report_sections(analysis=a, **KW))
        self.assertIn("No verified provenance evidence available.", text)
        self.assertIn("does not imply that AI was not used", text)
        self.assertIn("unavailable", text)
        self.assertIn("INCONCLUSIVE", text)
        self.assertIn("Not performed", text)
        self.assertIn("function count", text)
        self.assertNotRegex(text, r"\d+(\.\d+)?\s*%\s*(AI|likely|probab)")

    def test_report_includes_real_review_status_and_notes(self):
        a = to_api(analyze_source("x = 1", "python"), 1)
        text = flat(report_sections(analysis=a, review_status="reviewed", review_notes=[{
            "author_email": "prof@example.com", "created_at": "2026-10-26T00:00:00+00:00",
            "body": "Discuss the loop invariant.",
        }], **KW))
        self.assertIn("Review status: reviewed", text)
        self.assertIn("prof@example.com", text)
        self.assertIn("Discuss the loop invariant.", text)

    def test_pdf_is_generated_for_all_statuses(self):
        for src, lang in (("x = 1", "python"), ("class A {}", "java"), ("", "python"), ("def f(:", "python")):
            pdf = build_report_pdf(analysis=to_api(analyze_source(src, lang), 1), **KW)
            self.assertTrue(pdf.startswith(b"%PDF"))
            self.assertIn(b"%%EOF", pdf[-32:])
            self.assertGreater(len(pdf), 1500)

    def test_markup_in_user_text_does_not_break_pdf(self):
        kw = {**KW, "assignment_title": "<b>HW & <i>1", "filename": "<script>.py"}
        a = to_api(analyze_source("x = 1", "python"), 1)
        self.assertTrue(build_report_pdf(analysis=a, **kw).startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
