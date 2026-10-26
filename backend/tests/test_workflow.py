"""End-to-end API tests (FastAPI TestClient + SQLite). Skipped when fastapi/sqlalchemy are missing."""
import os
import unittest
import uuid

try:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.deps import auth_limiter
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

PW = "a-long-test-password"
CODE = "def add(a, b):\n    return a + b\n"


def email():
    return f"{uuid.uuid4().hex[:10]}@example.com"


@unittest.skipUnless(HAVE_DEPS, "fastapi/sqlalchemy not installed in this environment")
class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = TestClient(app)
        cls.c.__enter__()  # runs startup (creates tables)

    @classmethod
    def tearDownClass(cls):
        cls.c.__exit__(None, None, None)

    def setUp(self):
        auth_limiter.reset()

    # helpers
    def register(self, role):
        r = self.c.post("/api/v1/auth/register", json={"email": email(), "password": PW, "role": role})
        self.assertEqual(r.status_code, 201, r.text)
        return {"Authorization": "Bearer " + r.json()["access_token"]}

    def assignment(self, prof, **extra):
        r = self.c.post("/api/v1/assignments", json={"title": "HW1", **extra}, headers=prof)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["id"]

    def submit(self, student, aid, filename="a.py", source=CODE):
        return self.c.post("/api/v1/submissions", headers=student,
                           json={"assignment_id": aid, "filename": filename, "source": source})

    # tests
    def test_full_workflow(self):
        prof, stu = self.register("professor"), self.register("student")
        aid = self.assignment(prof, allowed_languages=["python"])
        self.assertEqual(len(self.c.get("/api/v1/assignments", headers=stu).json()["items"]) >= 1, True)
        r = self.submit(stu, aid)
        self.assertEqual(r.status_code, 201, r.text)
        sid = r.json()["id"]
        d = self.c.get(f"/api/v1/submissions/{sid}", headers=prof).json()
        a = d["analyses"][0]
        self.assertEqual(a["analysis_status"], "completed")
        self.assertTrue(a["syntax_valid"])
        self.assertEqual(a["code_metrics"]["function_count"], 1)
        self.assertEqual(a["model_status"], "unavailable")
        self.assertEqual(a["authorship_assessment"], "inconclusive")
        self.assertIsNone(a["probability"])
        self.assertEqual(a["provenance_summary"], "No verified provenance evidence available.")
        rep = self.c.post("/api/v1/reports", json={"analysis_id": a["analysis_id"]}, headers=prof)
        self.assertEqual(rep.status_code, 201, rep.text)
        pdf = self.c.get(rep.json()["download_url"], headers=prof)
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertEqual(self.c.get(rep.json()["download_url"], headers=stu).status_code, 403)
        stats = self.c.get("/api/v1/dashboard/stats", headers=prof).json()
        self.assertEqual(stats["total_submissions"], 1)
        self.assertEqual(stats["completed_analyses"], 1)

    def test_authentication_rules(self):
        self.assertEqual(self.c.get("/api/v1/auth/me").status_code, 401)
        self.assertEqual(self.c.get("/api/v1/assignments", headers={"Authorization": "Bearer junk"}).status_code, 401)
        e = email()
        self.assertEqual(self.c.post("/api/v1/auth/register", json={"email": e, "password": PW}).status_code, 201)
        self.assertEqual(self.c.post("/api/v1/auth/register", json={"email": e, "password": PW}).status_code, 409)
        self.assertEqual(self.c.post("/api/v1/auth/register", json={"email": email(), "password": "short"}).status_code, 422)
        bad = self.c.post("/api/v1/auth/login", json={"email": e, "password": "wrong-password"})
        self.assertEqual(bad.status_code, 401)
        self.assertEqual(self.c.post("/api/v1/auth/login", json={"email": "no@one.com", "password": "x"}).json()["message"],
                         bad.json()["message"])  # no account enumeration
        self.assertEqual(self.c.post("/api/v1/auth/login", json={"email": e, "password": PW}).status_code, 200)

    def test_rate_limit_on_auth(self):
        from app.api import deps
        old = deps.auth_limiter.limit
        deps.auth_limiter.limit = 3
        try:
            codes = [self.c.post("/api/v1/auth/login", json={"email": "x@y.com", "password": "p"}).status_code
                     for _ in range(5)]
            self.assertIn(429, codes)
        finally:
            deps.auth_limiter.limit = old

    def test_roles_enforced_on_server(self):
        prof, stu = self.register("professor"), self.register("student")
        self.assertEqual(self.c.post("/api/v1/assignments", json={"title": "x"}, headers=stu).status_code, 403)
        aid = self.assignment(prof)
        self.assertEqual(self.submit(prof, aid).status_code, 403)  # only students submit
        self.assertEqual(self.c.post("/api/v1/reports", json={"analysis_id": "x"}, headers=stu).status_code, 403)

    def test_data_isolation(self):
        prof1, prof2 = self.register("professor"), self.register("professor")
        stu1, stu2 = self.register("student"), self.register("student")
        aid = self.assignment(prof1)
        sid = self.submit(stu1, aid).json()["id"]
        aid_analysis = self.c.get(f"/api/v1/submissions/{sid}", headers=prof1).json()["analyses"][0]["analysis_id"]
        for who in (prof2, stu2):
            self.assertEqual(self.c.get(f"/api/v1/submissions/{sid}", headers=who).status_code, 404)
            self.assertEqual(self.c.get(f"/api/v1/analysis/{aid_analysis}", headers=who).status_code, 404)
            self.assertEqual(self.c.post("/api/v1/analysis", json={"submission_id": sid}, headers=who).status_code, 404)
            self.assertEqual(self.c.delete(f"/api/v1/submissions/{sid}", headers=who).status_code, 404)
            self.assertEqual(self.c.get("/api/v1/submissions", headers=who).json()["total"], 0)
        self.assertEqual(self.c.post("/api/v1/reports", json={"analysis_id": aid_analysis}, headers=prof2).status_code, 404)
        self.assertEqual(self.c.patch(f"/api/v1/assignments/{aid}", json={"title": "hijack"}, headers=prof2).status_code, 404)
        self.assertEqual(self.c.delete(f"/api/v1/assignments/{aid}", headers=prof2).status_code, 404)
        self.assertEqual(self.c.get(f"/api/v1/assignments/{aid}", headers=prof2).status_code, 404)
        self.assertEqual(self.c.get("/api/v1/assignments", headers=prof2).json()["items"], [])

    def test_upload_validation(self):
        prof, stu = self.register("professor"), self.register("student")
        aid = self.assignment(prof)
        up = lambda name, data: self.c.post("/api/v1/submissions/upload", headers=stu, data={"assignment_id": aid},
                                            files={"file": (name, data)})
        ok = up("../../evil/x.py", CODE.encode())
        self.assertEqual(ok.status_code, 201, ok.text)
        self.assertEqual(ok.json()["original_filename"], "x.py")
        self.assertEqual(up("run.exe", b"MZ").status_code, 422)
        self.assertEqual(up("a.py", b"a\x00b").status_code, 422)
        self.assertEqual(up("a.py", b"").status_code, 422)
        self.assertEqual(up("big.py", b"x = 1\n" * 300_000).status_code, 422)
        stored = os.listdir(os.environ["UPLOAD_DIR"])
        self.assertTrue(all(len(n) == 36 and n.endswith(".src") for n in stored))  # randomized names

    def test_unsupported_language_and_syntax_error_are_honest(self):
        prof, stu = self.register("professor"), self.register("student")
        aid = self.assignment(prof)
        sid = self.submit(stu, aid, "A.java", "class A {}").json()["id"]
        a = self.c.get(f"/api/v1/submissions/{sid}", headers=stu).json()["analyses"][0]
        self.assertEqual(a["analysis_status"], "completed")
        self.assertTrue(a["syntax_valid"])
        self.assertEqual(a["code_metrics"]["class_count"], 1)
        sid2 = self.submit(stu, aid, "b.py", "def f(:\n").json()["id"]
        b = self.c.get(f"/api/v1/submissions/{sid2}", headers=stu).json()["analyses"][0]
        self.assertFalse(b["syntax_valid"])

    def test_disallowed_language_rejected(self):
        prof, stu = self.register("professor"), self.register("student")
        aid = self.assignment(prof, allowed_languages=["python"])
        self.assertEqual(self.submit(stu, aid, "A.java", "class A {}").status_code, 422)
        self.assertEqual(self.c.post("/api/v1/assignments", headers=prof,
                                     json={"title": "x", "allowed_languages": ["cobol"]}).status_code, 422)

    def test_preview_and_retry_rules(self):
        stu = self.register("student")
        self.assertEqual(self.c.post("/api/v1/analysis/preview", json={"source": "x=1", "language": "python"}).status_code, 401)
        r = self.c.post("/api/v1/analysis/preview", headers=stu, json={"source": "x = 1", "language": "python"}).json()
        self.assertEqual((r["analysis_status"], r["model_status"]), ("completed", "unavailable"))
        e = self.c.post("/api/v1/analysis/preview", headers=stu, json={"source": "  ", "language": "python"}).json()
        self.assertEqual(e["analysis_status"], "rejected_empty")
        prof = self.register("professor")
        sid = self.submit(stu, self.assignment(prof)).json()["id"]
        aid = self.c.get(f"/api/v1/submissions/{sid}", headers=stu).json()["analyses"][0]["analysis_id"]
        self.assertEqual(self.c.post(f"/api/v1/analysis/{aid}/retry", headers=stu).status_code, 409)  # not failed
        self.assertEqual(self.c.post("/api/v1/analysis", headers=stu, json={"submission_id": sid}).status_code, 201)

    def test_injection_and_markup_are_inert(self):
        prof, stu = self.register("professor"), self.register("student")
        aid = self.assignment(prof)
        self.submit(stu, aid)
        r = self.c.get("/api/v1/submissions", headers=prof, params={"q": "' OR 1=1 --"})
        self.assertEqual((r.status_code, r.json()["total"]), (200, 0))
        a = self.c.post("/api/v1/assignments", headers=prof, json={"title": "<script>alert(1)</script>"})
        self.assertEqual(a.status_code, 201)
        self.assertTrue(a.headers["content-type"].startswith("application/json"))

    def test_errors_are_consistent_and_safe(self):
        r = self.c.get("/api/v1/submissions/999999", headers=self.register("student"))
        self.assertEqual(r.status_code, 404)
        self.assertEqual(set(r.json()), {"error", "message", "request_id"})
        self.assertNotIn("Traceback", r.text)

    def test_delete_submission_removes_file(self):
        prof, stu = self.register("professor"), self.register("student")
        sid = self.submit(stu, self.assignment(prof)).json()["id"]
        before = set(os.listdir(os.environ["UPLOAD_DIR"]))
        self.assertEqual(self.c.delete(f"/api/v1/submissions/{sid}", headers=stu).status_code, 204)
        self.assertEqual(self.c.get(f"/api/v1/submissions/{sid}", headers=stu).status_code, 404)
        self.assertEqual(len(before) - len(set(os.listdir(os.environ["UPLOAD_DIR"]))), 1)

    def test_professor_review_notes_lifecycle_and_scope(self):
        prof, other_prof = self.register("professor"), self.register("professor")
        stu = self.register("student")
        sid = self.submit(stu, self.assignment(prof)).json()["id"]
        notes_url = f"/api/v1/submissions/{sid}/notes"

        self.assertEqual(self.c.get(notes_url, headers=stu).status_code, 403)
        self.assertEqual(self.c.post(notes_url, headers=stu, json={"body": "note"}).status_code, 403)
        self.assertEqual(self.c.get(notes_url, headers=other_prof).status_code, 404)
        self.assertEqual(self.c.post(notes_url, headers=prof, json={"body": "   "}).status_code, 422)

        created = self.c.post(notes_url, headers=prof, json={"body": "  Check edge cases.  "})
        self.assertEqual(created.status_code, 201, created.text)
        note = created.json()
        self.assertEqual(note["body"], "Check edge cases.")
        professor_email = self.c.get("/api/v1/auth/me", headers=prof).json()["email"]
        self.assertEqual(note["author_email"], professor_email)
        self.assertEqual(self.c.get(notes_url, headers=prof).json()["items"], [note])

        note_url = f"{notes_url}/{note['id']}"
        updated = self.c.patch(note_url, headers=prof, json={"body": "Review complete."})
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["body"], "Review complete.")
        self.assertEqual(self.c.patch(note_url, headers=other_prof, json={"body": "Changed"}).status_code, 404)
        self.assertEqual(self.c.delete(note_url, headers=other_prof).status_code, 404)
        self.assertEqual(self.c.delete(note_url, headers=prof).status_code, 204)
        self.assertEqual(self.c.get(notes_url, headers=prof).json()["items"], [])

    def test_review_queue_status_and_scope(self):
        prof, other_prof = self.register("professor"), self.register("professor")
        stu = self.register("student")
        sid = self.submit(stu, self.assignment(prof)).json()["id"]
        review_url = f"/api/v1/submissions/{sid}/review-status"
        self.assertEqual(self.c.get("/api/v1/submissions", headers=prof).json()["items"][0]["review_status"],
                         "needs_review")
        self.assertEqual(self.c.get("/api/v1/submissions", headers=prof,
                                    params={"review_status": "needs_review"}).json()["total"], 1)
        self.assertEqual(self.c.patch(review_url, headers=stu, json={"status": "reviewed"}).status_code, 403)
        self.assertEqual(self.c.patch(review_url, headers=other_prof,
                                      json={"status": "reviewed"}).status_code, 404)
        marked = self.c.patch(review_url, headers=prof, json={"status": "reviewed"})
        self.assertEqual(marked.status_code, 200, marked.text)
        self.assertEqual(marked.json()["review_status"], "reviewed")
        self.assertIsNotNone(marked.json()["reviewed_at"])
        self.assertEqual(self.c.get("/api/v1/submissions", headers=prof,
                                    params={"review_status": "reviewed"}).json()["total"], 1)
        self.assertEqual(self.c.patch(review_url, headers=prof,
                                      json={"status": "needs_review"}).json()["reviewed_at"], None)
        self.assertEqual(self.c.get("/api/v1/submissions", headers=stu,
                                    params={"review_status": "needs_review"}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
