import unittest

try:
    from fastapi.testclient import TestClient
    from app.main import app
    HAVE_FASTAPI = True
except ImportError:
    HAVE_FASTAPI = False


@unittest.skipUnless(HAVE_FASTAPI, "fastapi not installed in this environment")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        r = self.client.get("/api/v1/health")
        self.assertEqual(r.status_code, 200)
        self.assertIn("X-Request-ID", r.headers)

    def test_languages(self):
        r = self.client.get("/api/v1/languages")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["languages"][0]["id"], "python")


if __name__ == "__main__":
    unittest.main()
