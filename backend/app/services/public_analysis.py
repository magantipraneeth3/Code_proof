"""Non-persistent public analysis and source-similarity helpers."""
import difflib
import io
import tokenize
import uuid
import ast
from datetime import datetime, timezone

from app.analyzers.registry import LANGUAGES
from app.core.config import settings
from app.analyzers.tree_sitter_analyzer import PARSER_NAMES, parse_source, detect_language as detect_parsed_language
from app.services.analysis_service import analyze_source

_KNOWN = {item["id"] for item in LANGUAGES}
_SIMILARITY_LANGUAGES = {"python", "java", "c", "cpp", "javascript", "typescript", "tsx"}
_IGNORED_TOKENS = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                   tokenize.DEDENT, tokenize.ENDMARKER}
_MAX_COMPARISON_TOKENS = 5_000
_NGRAM_SIZE = 3

REFERENCE_SAMPLES = [
    {
        "sample_id": "py-aggregate-loop-01",
        "name": "Aggregate values with a loop",
        "language": "python",
        "category": "sequence aggregation",
        "source": "CodeProof original demonstration sample",
        "license": "Original demo code; no third-party source included",
        "authoring_process": "Unknown",
        "authorship_label": "unknown",
        "label_verified": False,
        "origin_verified": False,
        "collection_date": None,
        "code": "def sum_values(values):\n    total = 0\n    for value in values:\n        total += value\n    return total\n",
    },
    {
        "sample_id": "py-aggregate-builtin-02",
        "name": "Aggregate values with a built-in",
        "language": "python",
        "category": "sequence aggregation",
        "source": "CodeProof original demonstration sample",
        "license": "Original demo code; no third-party source included",
        "authoring_process": "Unknown",
        "authorship_label": "unknown",
        "label_verified": False,
        "origin_verified": False,
        "collection_date": None,
        "code": "def sum_values(numbers):\n    return sum(numbers)\n",
    },
    {
        "sample_id": "py-mean-03",
        "name": "Calculate an arithmetic mean",
        "language": "python",
        "category": "sequence statistics",
        "source": "CodeProof original demonstration sample",
        "license": "Original demo code; no third-party source included",
        "authoring_process": "Unknown",
        "authorship_label": "unknown",
        "label_verified": False,
        "origin_verified": False,
        "collection_date": None,
        "code": "def average(items):\n    if not items:\n        return None\n    return sum(items) / len(items)\n",
    },
    {
        "sample_id": "java-sum-01", "name": "Aggregate values with a loop", "language": "java",
        "category": "sequence aggregation", "source": "CodeProof original demonstration sample",
        "license": "Original CodeProof code; no third-party source included", "authoring_process": "Unknown",
        "authorship_label": "unknown", "label_verified": False, "origin_verified": False, "collection_date": None,
        "code": "import java.util.List;\nclass SumExample {\n    static int sumValues(List<Integer> values) {\n        int total = 0;\n        for (int value : values) total += value;\n        return total;\n    }\n}\n",
    },
    {
        "sample_id": "c-sum-01", "name": "Aggregate values with a loop", "language": "c",
        "category": "sequence aggregation", "source": "CodeProof original demonstration sample",
        "license": "Original CodeProof code; no third-party source included", "authoring_process": "Unknown",
        "authorship_label": "unknown", "label_verified": False, "origin_verified": False, "collection_date": None,
        "code": "int sum_values(const int *values, int length) {\n    int total = 0;\n    for (int i = 0; i < length; i++) total += values[i];\n    return total;\n}\n",
    },
    {
        "sample_id": "cpp-sum-01", "name": "Aggregate values with a loop", "language": "cpp",
        "category": "sequence aggregation", "source": "CodeProof original demonstration sample",
        "license": "Original CodeProof code; no third-party source included", "authoring_process": "Unknown",
        "authorship_label": "unknown", "label_verified": False, "origin_verified": False, "collection_date": None,
        "code": "#include <vector>\nint sum_values(const std::vector<int>& values) {\n    int total = 0;\n    for (int value : values) total += value;\n    return total;\n}\n",
    },
    {
        "sample_id": "js-sum-01", "name": "Aggregate values with a loop", "language": "javascript",
        "category": "sequence aggregation", "source": "CodeProof original demonstration sample",
        "license": "Original CodeProof code; no third-party source included", "authoring_process": "Unknown",
        "authorship_label": "unknown", "label_verified": False, "origin_verified": False, "collection_date": None,
        "code": "function sumValues(values) {\n  let total = 0;\n  for (const value of values) total += value;\n  return total;\n}\n",
    },
    {
        "sample_id": "ts-sum-01", "name": "Aggregate values with a loop", "language": "typescript",
        "category": "sequence aggregation", "source": "CodeProof original demonstration sample",
        "license": "Original CodeProof code; no third-party source included", "authoring_process": "Unknown",
        "authorship_label": "unknown", "label_verified": False, "origin_verified": False, "collection_date": None,
        "code": "function sumValues(values: number[]): number {\n  let total = 0;\n  for (const value of values) total += value;\n  return total;\n}\n",
    },
    {
        "sample_id": "tsx-list-01", "name": "Render a list of values", "language": "tsx",
        "category": "UI rendering", "source": "CodeProof original demonstration sample",
        "license": "Original CodeProof code; no third-party source included", "authoring_process": "Unknown",
        "authorship_label": "unknown", "label_verified": False, "origin_verified": False, "collection_date": None,
        "code": "type Props = { values: string[] };\nfunction ValueList({ values }: Props) {\n  return <ul>{values.map((value) => <li key={value}>{value}</li>)}</ul>;\n}\n",
    },
]


def known_language(language: str) -> str:
    normalized = language.strip().lower()
    if normalized not in _KNOWN:
        raise ValueError(f"Unknown language '{language}'. Choose one of: {', '.join(sorted(_KNOWN))}.")
    return normalized


def _authorship_assessment() -> dict:
    return {
        "result": "inconclusive",
        "ai_likelihood_percent": None,
        "probability_calibrated": False,
        "model_status": "unavailable",
        "model_version": None,
        "explanation": "The current analysis examines code characteristics but cannot reliably estimate whether this code was generated by AI.",
    }


def _syntax_result(result: dict, language: str | None) -> dict:
    valid = result.get("syntax_valid")
    errors = (result.get("code_metrics") or {}).get("syntax_errors", [])
    if language == "python" and valid is False:
        try:
            ast.parse(result.get("source", ""))
        except SyntaxError as exc:
            errors = [{"line": exc.lineno, "column": exc.offset, "message": exc.msg}]
    status = "valid" if valid is True else "invalid" if valid is False else "unable_to_validate"
    validation = "complete" if valid is True else "partial" if valid is False else "unavailable"
    return {"status": status, "message": result.get("syntax_error"), "errors": errors,
            "validation": validation}


def _check_size(source: str) -> None:
    if len(source.encode("utf-8")) > settings.max_source_bytes:
        raise ValueError(f"Source exceeds the {settings.max_source_bytes}-byte limit.")


def _normalized_tokens(source: str) -> list[tuple[str, int, int]]:
    result = []
    for item in tokenize.generate_tokens(io.StringIO(source).readline):
        if item.type in _IGNORED_TOKENS:
            continue
        result.append((item.string, item.start[0], item.end[0]))
    return result


def _tree_sitter_tokens(source: str, language: str) -> list[tuple[str, int, int]]:
    tree = parse_source(source, language)
    tokens = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in {"comment", "line_comment", "block_comment", "documentation_comment"}:
            continue
        if node.child_count == 0:
            text = node.text.decode("utf-8", errors="replace")
            if text.strip():
                tokens.append((text, node.start_point.row + 1, node.end_point.row + 1))
        else:
            stack.extend(reversed(node.children))
    return tokens


def _ngram_similarity(values_a: list[str], values_b: list[str]) -> float | None:
    if min(len(values_a), len(values_b)) < _NGRAM_SIZE:
        return None
    grams_a = {tuple(values_a[i:i + _NGRAM_SIZE]) for i in range(len(values_a) - _NGRAM_SIZE + 1)}
    grams_b = {tuple(values_b[i:i + _NGRAM_SIZE]) for i in range(len(values_b) - _NGRAM_SIZE + 1)}
    union = grams_a | grams_b
    return round(100 * len(grams_a & grams_b) / len(union), 1) if union else 0.0


def _structure_similarity(metrics_a: dict, metrics_b: dict) -> float:
    keys = ("function_count", "class_count", "import_count", "cyclomatic_complexity", "max_nesting_depth")
    similarities = []
    for key in keys:
        left, right = metrics_a.get(key), metrics_b.get(key)
        if left is None or right is None:
            continue
        similarities.append(1.0 if left == right == 0 else 1 - abs(left - right) / max(left, right, 1))
    return round(100 * sum(similarities) / len(similarities), 1) if similarities else 0.0


def compare_sources(code_a: str, code_b: str, language: str, *, reference: dict | None = None) -> dict:
    """Compare source tokens without discarding identifiers or literal values."""
    _check_size(code_a)
    _check_size(code_b)
    try:
        if language == "python":
            tokens_a, tokens_b = _normalized_tokens(code_a), _normalized_tokens(code_b)
        else:
            tokens_a, tokens_b = _tree_sitter_tokens(code_a, language), _tree_sitter_tokens(code_b, language)
    except (tokenize.TokenError, IndentationError, LookupError, ValueError) as exc:
        return {"comparison_status": "tokenization_failed", "similarity_percent": None,
                "ngram_similarity_percent": None, "method": f"{language} token sequence comparison", "matching_regions": [],
                "explanation": f"Tokenization did not complete ({type(exc).__name__}); no similarity was calculated."}

    if max(len(tokens_a), len(tokens_b)) > _MAX_COMPARISON_TOKENS:
        return {"comparison_status": "skipped_complexity_limit", "similarity_percent": None,
            "ngram_similarity_percent": None, "method": f"{language} token sequence comparison", "matching_regions": [],
                "explanation": f"Comparison was skipped because a sample exceeds {_MAX_COMPARISON_TOKENS} tokens."}

    values_a = [item[0] for item in tokens_a]
    values_b = [item[0] for item in tokens_b]
    matcher = difflib.SequenceMatcher(None, values_a, values_b, autojunk=True)
    structural = None
    try:
        result_a = analyze_source(code_a, language)
        result_b = analyze_source(code_b, language)
        metrics_a = result_a.get("code_metrics") or {}
        metrics_b = result_b.get("code_metrics") or {}
        if result_a.get("syntax_valid") is True and result_b.get("syntax_valid") is True and metrics_a and metrics_b:
            structural = _structure_similarity(metrics_a, metrics_b)
    except (LookupError, ValueError):
        structural = None
    similarity = round(100 * matcher.ratio(), 1)
    shared = sorted(set(values_a) & set(values_b))[:24]
    lines_a, lines_b = code_a.splitlines(), code_b.splitlines()
    matching = []
    for block in matcher.get_matching_blocks():
        if block.size < 3:
            continue
        start_a, end_a = tokens_a[block.a][1], tokens_a[block.a + block.size - 1][2]
        start_b, end_b = tokens_b[block.b][1], tokens_b[block.b + block.size - 1][2]
        matching.append({"code_a_lines": [start_a, end_a], "code_b_lines": [start_b, end_b],
                         "matching_tokens": block.size,
                         "code_a_excerpt": "\n".join(lines_a[start_a - 1:end_a]),
                         "code_b_excerpt": "\n".join(lines_b[start_b - 1:end_b])})
    return {
        "comparison_status": "completed",
        "similarity_percent": similarity,
        "ngram_similarity_percent": _ngram_similarity(values_a, values_b),
        "method": f"{language} token-sequence similarity; whitespace and comments excluded; identifiers and literals retained",
        "structural_similarity_percent": structural,
        "shared_tokens": shared,
        "matching_regions": matching,
        "reference_sample": ({"sample_id": reference["sample_id"], "name": reference["name"],
                              "language": reference["language"], "category": reference["category"],
                              "source": reference["source"], "license": reference["license"],
                              "authoring_process": reference["authoring_process"],
                              "authorship_label": reference["authorship_label"],
                              "label_verified": reference["label_verified"],
                              "collection_date": reference["collection_date"],
                              "provenance_status": "unverified"} if reference else None),
        "provenance_status_a": "unknown",
        "provenance_status_b": "unverified" if reference else "unknown",
        "explanation": ("Similarity measures resemblance between normalized token sequences. It does not establish copying, "
                        "human authorship, AI involvement, or common provenance. Common exercises and starter code can "
                        "produce similar implementations independently."),
    }


def compare_python(code_a: str, code_b: str, *, reference: dict | None = None) -> dict:
    return compare_sources(code_a, code_b, "python", reference=reference)


def public_analyze(code: str, language: str | None = None, compare_samples: bool = True) -> dict:
    _check_size(code)
    if not code.strip():
        raise ValueError("Paste source code before running analysis.")

    detected, confidence, candidates = detect_parsed_language(code)
    manual_language = language is not None and language.strip().lower() not in {"", "auto"}
    selected = known_language(language) if manual_language else detected
    if selected is None:
        now = datetime.now(timezone.utc).isoformat()
        reason = "Automatic language detection is limited to 128 KB; select a language manually." \
            if confidence == "not_run_size_limit" else \
            "The source matched more than one language grammar; select a language manually." if candidates else \
            "No supported language could be identified reliably; select a language manually."
        return {
            "analysis_id": str(uuid.uuid4()), "language": None, "analysis_status": "unknown_language",
            "created_at": now, "syntax_valid": None, "syntax_error": None, "metrics": None,
            "structural_findings": [], "similarity_results": [], "samples_compared": 0,
            "language_detection": {"detected_language": None, "confidence": "unknown", "candidates": candidates,
                                   "selection_status": "ambiguous" if candidates else confidence},
            "syntax": {"status": "unable_to_validate", "message": reason, "errors": [], "validation": "unavailable"},
            "structure": {"status": "unavailable", "summary": "Not available until a language is selected.", "metrics": None},
            "similarity": {"status": "unavailable", "score": None, "reference_id": None,
                           "reference_title": None, "method": None, "matched_fragments": []},
            "provenance": {"status": "unavailable", "evidence": [], "explanation": "No verified authorship provenance was supplied."},
            "authorship_assessment": _authorship_assessment(), "explanation": reason,
            "limitations": ["Language detection is ambiguous or unsupported.",
                            "No validated authorship classifier is configured; no AI-likelihood percentage is available."],
            "message": reason,
        }
    language = selected

    result = analyze_source(code, language)
    result["source"] = code
    comparisons = []
    if compare_samples and language in _SIMILARITY_LANGUAGES:
        for sample in REFERENCE_SAMPLES:
            if sample["language"] != language:
                continue
            comparison = compare_sources(code, sample["code"], language, reference=sample)
            comparisons.append(comparison)
        comparisons.sort(key=lambda item: item["similarity_percent"] or 0, reverse=True)

    if result["analysis_status"] == "unsupported_language":
        explanation = f"No structural analyzer is available for {language}. No code metrics or authorship prediction were produced."
    elif result.get("syntax_valid") is False:
        explanation = f"The {language} parser found a syntax issue. Structural metrics may be partial."
    else:
        explanation = (f"{language} syntax and structural characteristics were analyzed. Similarity results, where available, "
                       "measure source resemblance only and do not identify an author or AI tool.")

    limitations = list(result.get("limitations", []))
    limitations.extend([
        "No validated authorship classifier is configured; no AI-likelihood percentage is available.",
        "Similarity is a measure of source resemblance, not an AI-authorship probability or proof of copying.",
        "Bundled reference examples have unknown, unverified authorship provenance and are demonstration material only.",
        "Public analysis is processed in memory and is not saved as a submission.",
    ])
    comparable = [item for item in comparisons if item["comparison_status"] == "completed"
                  and item["similarity_percent"] is not None]
    best_similarity = max(comparable, key=lambda item: item["similarity_percent"], default=None)
    selection_status = "manual"
    if manual_language:
        selection_status = "matches" if detected == language else "mismatch" if detected else "unconfirmed"
    else:
        selection_status = "detected"
    syntax = _syntax_result(result, language)
    if language == "python" and result.get("syntax_valid") is False:
        try:
            ast.parse(code)
        except SyntaxError as exc:
            syntax["errors"] = [{"line": exc.lineno, "column": exc.offset, "message": exc.msg}]
    structure_summary = ", ".join(result.get("structural_findings", [])) or "No structural summary available."
    similarity_report = {
        "status": "available" if best_similarity else "unavailable",
        "score": best_similarity["similarity_percent"] if best_similarity else None,
        "ngram_similarity_percent": best_similarity.get("ngram_similarity_percent") if best_similarity else None,
        "reference_id": best_similarity.get("reference_sample", {}).get("sample_id") if best_similarity else None,
        "reference_title": best_similarity.get("reference_sample", {}).get("name") if best_similarity else None,
        "method": best_similarity.get("method") if best_similarity else None,
        "matched_fragments": best_similarity.get("matching_regions", []) if best_similarity else [],
    }
    return {
        "analysis_id": result["analysis_id"],
        "language": result.get("language"),
        "analysis_status": result["analysis_status"],
        "created_at": result["created_at"],
        "syntax_valid": result.get("syntax_valid"),
        "syntax_error": result.get("syntax_error"),
        "metrics": result.get("code_metrics"),
        "structural_findings": result.get("structural_findings", []),
        "similarity_results": comparisons,
        "samples_compared": len(comparable),
        "provenance": {"status": "unavailable", "evidence": [],
                       "explanation": "No verified authorship provenance was supplied."},
        "authorship_assessment": {
            "result": "inconclusive",
            "ai_likelihood_percent": None,
            "probability_calibrated": False,
            "model_status": "unavailable",
            "model_version": None,
            "explanation": ("The current analysis examines code characteristics but cannot reliably estimate whether this code "
                            "was generated by AI."),
        },
        "explanation": explanation,
        "limitations": limitations,
        "message": result.get("message"),
        "language_detection": {"detected_language": detected, "confidence": confidence,
                               "candidates": candidates, "selection_status": selection_status},
        "syntax": syntax,
        "structure": {"status": "available" if result.get("code_metrics") else "unavailable",
                      "summary": structure_summary, "metrics": result.get("code_metrics")},
        "similarity": similarity_report,
    }


def public_samples() -> list[dict]:
    return [dict(sample) for sample in REFERENCE_SAMPLES]