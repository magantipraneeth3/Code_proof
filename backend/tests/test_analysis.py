import unittest

from app.services.analysis_service import analyze_source, NO_PROVENANCE
from app.analyzers.tree_sitter_analyzer import detect_language

GOOD = '''
import os
# a comment
def f(x):
    """doc"""
    if x > 1 and x < 10:
        for i in range(x):
            try:
                pass
            except Exception:
                pass
    return x

class A:
    pass
'''


class AnalysisTests(unittest.TestCase):
    def test_valid_python(self):
        r = analyze_source(GOOD, "python")
        self.assertEqual(r["analysis_status"], "completed")
        self.assertTrue(r["syntax_valid"])
        self.assertEqual(r["code_metrics"]["function_count"], 1)
        self.assertEqual(r["code_metrics"]["class_count"], 1)
        self.assertEqual(r["code_metrics"]["comment_lines"], 1)
        self.assertGreaterEqual(r["code_metrics"]["cyclomatic_complexity"], 4)

    def test_malformed_python(self):
        r = analyze_source("def f(:\n  pass", "python")
        self.assertEqual(r["analysis_status"], "completed")
        self.assertFalse(r["syntax_valid"])
        self.assertIn("syntax_error", r)

    def test_empty(self):
        self.assertEqual(analyze_source("  \n", "python")["analysis_status"], "rejected_empty")

    def test_unsupported_language(self):
        self.assertEqual(analyze_source("program", "cobol")["analysis_status"], "unsupported_language")

    def test_tree_sitter_languages_have_real_syntax_and_structure(self):
        examples = {
            "java": "class Main { void run() { for (int i = 0; i < 3; i++) { if (i > 0) run(); } } }",
            "c": "int main(void) { int x = 0; for (int i = 0; i < 3; i++) { if (i) x++; } return x; }",
            "cpp": "class Main { public: int run(int x) { try { for (int i = 0; i < x; i++) {} } catch (...) {} return x; } };",
            "javascript": "function run(x) { for (let i = 0; i < x; i++) { if (i) return i; } }",
            "typescript": "function run(x: number): number { for (let i = 0; i < x; i++) { if (i) return i; } return 0; }",
            "tsx": "const App = () => <div>{items.map((item) => <span>{item}</span>)}</div>;",
        }
        for language, source in examples.items():
            with self.subTest(language=language):
                result = analyze_source(source, language)
                self.assertEqual(result["analysis_status"], "completed")
                self.assertTrue(result["syntax_valid"])
                self.assertIsInstance(result["code_metrics"]["loop_count"], int)
                self.assertIsInstance(result["code_metrics"]["function_count"], int)

    def test_tree_sitter_reports_invalid_syntax_with_location(self):
        result = analyze_source("function run( {\n  return 1;\n}", "javascript")
        self.assertEqual(result["analysis_status"], "completed")
        self.assertFalse(result["syntax_valid"])
        self.assertIsNotNone(result["syntax_error"])
        self.assertTrue(result["code_metrics"]["syntax_errors"])
        self.assertIn("line", result["code_metrics"]["syntax_errors"][0])

    def test_python_structure_counts_and_recursion(self):
        result = analyze_source("""# recursive factorial
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
""", "python")
        metrics = result["code_metrics"]
        self.assertEqual(metrics["loop_count"], 0)
        self.assertEqual(metrics["conditional_count"], 1)
        self.assertEqual(metrics["return_count"], 2)
        self.assertTrue(metrics["recursion_detected"])
        self.assertEqual(metrics["comment_count"], 1)

    def test_deep_python_nesting_does_not_recurse_in_metrics_walk(self):
        source = "if True:\n" * 300 + "    pass\n"
        result = analyze_source(source, "python")
        self.assertEqual(result["analysis_status"], "completed")

    def test_tree_sitter_structural_counts_and_recursion(self):
        result = analyze_source("function factorial(n) { if (n <= 1) return 1; return n * factorial(n - 1); }", "javascript")
        metrics = result["code_metrics"]
        self.assertEqual(metrics["function_count"], 1)
        self.assertEqual(metrics["conditional_count"], 1)
        self.assertEqual(metrics["return_count"], 2)
        self.assertTrue(metrics["recursion_detected"])

    def test_tree_sitter_does_not_call_other_function_recursion(self):
        result = analyze_source("function first() { return second(); } function second() { return 1; }", "javascript")
        self.assertFalse(result["code_metrics"]["recursion_detected"])

    def test_automatic_language_detection_requires_unique_parser_match(self):
        language, confidence, candidates = detect_language("def add(a, b):\n    return a + b\n")
        self.assertEqual((language, confidence, candidates), ("python", "unique_parser_match", ["python"]))
        language, confidence, candidates = detect_language("x = 1")
        self.assertIsNone(language)
        self.assertEqual(confidence, "unknown")
        self.assertGreater(len(candidates), 1)

    def test_unknown_language(self):
        self.assertEqual(analyze_source("x", None)["analysis_status"], "unsupported_language")

    def test_language_from_filename(self):
        self.assertEqual(analyze_source("x = 1", None, "a.py")["analysis_status"], "completed")

    def test_too_large(self):
        self.assertEqual(analyze_source("x = 1\n" * 400_000, "python")["analysis_status"], "rejected_too_large")

    def test_model_unavailable_and_inconclusive(self):
        r = analyze_source("x = 1", "python")
        self.assertEqual(r["model_status"], "unavailable")
        self.assertEqual(r["authorship_assessment"], "inconclusive")
        self.assertIsNone(r["probability"])
        self.assertEqual(r["evidence_category"], "E")

    def test_no_provenance_message(self):
        self.assertEqual(analyze_source("x = 1", "python")["provenance_summary"], NO_PROVENANCE)


if __name__ == "__main__":
    unittest.main()
