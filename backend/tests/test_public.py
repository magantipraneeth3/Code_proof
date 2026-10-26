"""Public analyzer tests: no account is needed and no private data is exposed."""
import unittest

try:
    from fastapi.testclient import TestClient
    from app.api.v1.public import _limiter
    from app.core.db import SessionLocal
    from app.main import app
    from app.models import Submission
    from sqlalchemy import func, select
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


@unittest.skipUnless(HAVE_DEPS, "FastAPI/SQLAlchemy dependencies are unavailable")
class PublicAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def setUp(self):
        _limiter.reset()

    def submission_count(self):
        with SessionLocal() as db:
            return db.scalar(select(func.count()).select_from(Submission)) or 0

    def test_public_health_and_samples_require_no_auth(self):
        health = self.client.get("/api/v1/public/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["authorship_model"], "unavailable")
        self.assertIn("tsx", health.json()["syntax_and_structure_languages"])
        self.assertIn("cpp", health.json()["similarity_languages"])
        self.assertEqual(health.json()["max_source_bytes"], 1_000_000)
        samples = self.client.get("/api/v1/public/samples")
        self.assertEqual(samples.status_code, 200)
        items = samples.json()["items"]
        self.assertGreaterEqual(len(items), 1)
        for sample in items:
            self.assertEqual(sample["authoring_process"], "Unknown")
            self.assertEqual(sample["authorship_label"], "unknown")
            self.assertFalse(sample["label_verified"])
            self.assertFalse(sample["origin_verified"])
            self.assertIn("unverified", sample["license"].lower() + " unverified")

    def test_analyze_is_real_non_persistent_and_never_predicts(self):
        source = "def total(values):\n    return sum(values)\n"
        before = self.submission_count()
        response = self.client.post("/api/v1/public/analyze", json={"code": source, "language": "python"})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["analysis_status"], "completed")
        self.assertTrue(result["syntax_valid"])
        self.assertEqual(result["metrics"]["function_count"], 1)
        self.assertEqual(result["samples_compared"], 3)
        self.assertEqual(result["authorship_assessment"]["result"], "inconclusive")
        self.assertEqual(result["authorship_assessment"]["model_status"], "unavailable")
        self.assertIsNone(result["authorship_assessment"]["ai_likelihood_percent"])
        self.assertFalse(result["authorship_assessment"]["probability_calibrated"])
        self.assertNotIn("code", result)
        self.assertEqual(self.submission_count(), before)

    def test_very_short_code_remains_inconclusive(self):
        response = self.client.post("/api/v1/public/analyze", json={
            "code": "x=1", "language": "python", "compare_samples": False})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertTrue(result["syntax_valid"])
        self.assertEqual(result["authorship_assessment"]["result"], "inconclusive")
        self.assertIsNone(result["authorship_assessment"]["ai_likelihood_percent"])

    def test_auto_detection_ambiguity_and_manual_language_validation(self):
        python = self.client.post("/api/v1/public/analyze", json={
            "code": "def add(left, right):\n    return left + right\n", "compare_samples": False})
        self.assertEqual(python.status_code, 200, python.text)
        self.assertEqual(python.json()["language_detection"]["detected_language"], "python")
        self.assertEqual(python.json()["language_detection"]["confidence"], "unique_parser_match")
        self.assertEqual(python.json()["syntax"]["status"], "valid")
        self.assertEqual(python.json()["structure"]["metrics"]["function_count"], 1)

        ambiguous = self.client.post("/api/v1/public/analyze", json={"code": "x=1"})
        self.assertEqual(ambiguous.json()["analysis_status"], "unknown_language")
        self.assertIsNone(ambiguous.json()["metrics"])
        self.assertEqual(ambiguous.json()["syntax"]["status"], "unable_to_validate")

        mismatch = self.client.post("/api/v1/public/analyze", json={
            "code": "public class Main { public static void main(String[] args) { System.out.println(\"Hi\"); } }",
            "language": "python", "compare_samples": False})
        self.assertEqual(mismatch.status_code, 200, mismatch.text)
        self.assertEqual(mismatch.json()["language_detection"]["selection_status"], "mismatch")
        self.assertEqual(mismatch.json()["language_detection"]["detected_language"], "java")

    def test_empty_unknown_unsupported_and_oversized_inputs(self):
        empty = self.client.post("/api/v1/public/analyze", json={"code": "  ", "language": "python"})
        self.assertEqual(empty.status_code, 422)
        self.assertIn("Paste source code", empty.json()["message"])

        unknown = self.client.post("/api/v1/public/analyze", json={"code": "x", "language": "brainfuck"})
        self.assertEqual(unknown.status_code, 422)

        analyzed_js = self.client.post("/api/v1/public/analyze", json={
            "code": "function add(a, b) { return a + b; }", "language": "javascript"})
        self.assertEqual(analyzed_js.status_code, 200)
        self.assertEqual(analyzed_js.json()["analysis_status"], "completed")
        self.assertTrue(analyzed_js.json()["syntax_valid"])
        self.assertEqual(analyzed_js.json()["metrics"]["function_count"], 1)
        self.assertIsNone(analyzed_js.json()["authorship_assessment"]["ai_likelihood_percent"])

        oversized = self.client.post("/api/v1/public/analyze", json={"code": "x" * 1_000_001, "language": "python"})
        self.assertEqual(oversized.status_code, 422)
        multibyte = self.client.post("/api/v1/public/compare", json={
            "code_a": "é" * 600_000, "language_a": "python", "code_b": "x = 1", "language_b": "python"})
        self.assertEqual(multibyte.status_code, 413)

    def test_compare_reports_similarity_not_authorship(self):
        a = "def add(left, right):\n    return left + right\n"
        b = "def add(first, second):\n    return first + second\n"
        response = self.client.post("/api/v1/public/compare", json={
            "code_a": a, "language_a": "python", "code_b": b, "language_b": "python"})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["comparison_status"], "completed")
        self.assertLess(result["similarity_percent"], 100.0)
        self.assertIsNotNone(result["ngram_similarity_percent"])
        self.assertIsNotNone(result["structural_similarity_percent"])
        self.assertTrue(result["matching_regions"])
        self.assertIn("def add", result["matching_regions"][0]["code_a_excerpt"])
        self.assertIn("def add", result["matching_regions"][0]["code_b_excerpt"])
        self.assertIn("does not establish copying", result["explanation"])
        self.assertNotIn("ai_likelihood_percent", result)

        mismatch = self.client.post("/api/v1/public/compare", json={
            "code_a": a, "language_a": "python", "code_b": "x", "language_b": "javascript"})
        self.assertEqual(mismatch.json()["comparison_status"], "language_mismatch")
        self.assertIsNone(mismatch.json()["similarity_percent"])

        same = self.client.post("/api/v1/public/compare", json={
            "code_a": a, "language_a": "python", "code_b": a, "language_b": "python"})
        self.assertEqual(same.json()["similarity_percent"], 100.0)

    def test_similarity_ignores_formatting_but_preserves_identifiers_and_algorithms(self):
        source = "def total(values):\n    return sum(values)\n"
        reformatted = "# descriptive comment\n\ndef total ( values ) : return sum ( values )\n"
        same_shape_different_names = "def count(items):\n    return len(items)\n"
        identical = self.client.post("/api/v1/public/compare", json={
            "code_a": source, "language_a": "python", "code_b": reformatted, "language_b": "python"}).json()
        different = self.client.post("/api/v1/public/compare", json={
            "code_a": source, "language_a": "python", "code_b": same_shape_different_names, "language_b": "python"}).json()
        self.assertEqual(identical["similarity_percent"], 100.0)
        self.assertLess(different["similarity_percent"], identical["similarity_percent"])

        other_algorithm = "def total(values):\n    result = 0\n    for value in values:\n        result += value\n    return result\n"
        algorithm_comparison = self.client.post("/api/v1/public/compare", json={
            "code_a": source, "language_a": "python", "code_b": other_algorithm, "language_b": "python"}).json()
        self.assertLess(algorithm_comparison["similarity_percent"], identical["similarity_percent"])

        invalid = self.client.post("/api/v1/public/compare", json={
            "code_a": "function broken( {", "language_a": "javascript",
            "code_b": "function alsoBroken( {", "language_b": "javascript"}).json()
        self.assertIsNone(invalid["structural_similarity_percent"])

    def test_each_language_compares_only_to_same_language_reference(self):
        sources = {
            "java": "public class Main { public static void main(String[] args) { System.out.println(\"Hi\"); } }",
            "c": "#include <stdio.h>\nint main(void) { printf(\"Hi\"); }",
            "cpp": "#include <iostream>\nint main() { std::cout << \"Hi\"; }",
            "javascript": "function sumValues(values) { let total = 0; for (const value of values) total += value; return total; }",
            "typescript": "function sumValues(values: number[]): number { let total = 0; for (const value of values) total += value; return total; }",
            "tsx": "type Props = { values: string[] }; function ValueList({ values }: Props) { return <ul>{values.map((value) => <li key={value}>{value}</li>)}</ul>; }",
        }
        for language, source in sources.items():
            with self.subTest(language=language):
                response = self.client.post("/api/v1/public/analyze", json={"code": source, "language": language})
                self.assertEqual(response.status_code, 200, response.text)
                result = response.json()
                self.assertTrue(result["syntax_valid"])
                self.assertEqual(result["similarity"]["status"], "available")
                self.assertEqual(result["samples_compared"], 1)
                self.assertEqual(result["similarity_results"][0]["reference_sample"]["language"], language)

    def test_public_endpoints_do_not_grant_private_submission_access(self):
        self.assertEqual(self.client.get("/api/v1/submissions").status_code, 401)

    def test_public_analysis_rate_limit(self):
        previous = _limiter.limit
        _limiter.limit = 1
        try:
            payload = {"code": "x = 1", "language": "python", "compare_samples": False}
            self.assertEqual(self.client.post("/api/v1/public/analyze", json=payload).status_code, 200)
            self.assertEqual(self.client.post("/api/v1/public/analyze", json=payload).status_code, 429)
        finally:
            _limiter.limit = previous


if __name__ == "__main__":
    unittest.main()