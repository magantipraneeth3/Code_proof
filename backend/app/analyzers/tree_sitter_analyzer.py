"""Parser-backed, non-executing structural analysis for non-Python languages."""
import ast

from tree_sitter_language_pack import get_parser

from app.analyzers.base import AnalyzerResult

PARSER_NAMES = {
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "javascript": "javascript",
    "typescript": "typescript",
    "tsx": "tsx",
}
MAX_AUTODETECT_BYTES = 128_000

_FUNCTIONS = {
    "function_declaration", "function_definition", "method_declaration", "method_definition",
    "constructor_declaration", "arrow_function", "function_expression", "lambda_expression",
}
_CLASSES = {"class_declaration", "class_specifier", "interface_declaration"}
_LOOPS = {"for_statement", "enhanced_for_statement", "for_in_statement", "for_of_statement",
          "while_statement", "do_statement", "while_expression"}
_CONDITIONALS = {"if_statement", "switch_statement", "switch_expression", "conditional_expression",
                 "ternary_expression"}
_ASSIGNMENTS = {"assignment_expression", "assignment_statement", "assignment", "variable_declarator",
                "init_declarator"}
_IMPORTS = {"import_declaration", "import_statement", "preproc_include"}
_COMMENTS = {"comment", "line_comment", "block_comment", "documentation_comment"}
_ERROR_HANDLERS = {"try_statement", "try_with_resources_statement", "try_expression",
                   "except_clause", "catch_clause", "finally_clause"}
_NESTING = _FUNCTIONS | _CLASSES | _LOOPS | _CONDITIONALS | _ERROR_HANDLERS
_RETURNS = {"return_statement", "return_expression"}


def parse_source(source: str, language: str):
    parser_name = PARSER_NAMES.get(language)
    if parser_name is None:
        raise ValueError(f"No parser is configured for {language}.")
    return get_parser(parser_name).parse(source.encode("utf-8"))


def detect_language(source: str) -> tuple[str | None, str, list[str]]:
    """Return a unique clean parser match; ambiguous snippets remain unknown."""
    if not source.strip():
        return None, "unknown", []
    if len(source.encode("utf-8")) > MAX_AUTODETECT_BYTES:
        return None, "not_run_size_limit", []
    matches = []
    errored = []
    try:
        ast.parse(source)
        matches.append("python")
    except SyntaxError:
        errored.append("python")
    for language in PARSER_NAMES:
        try:
            root = parse_source(source, language).root_node
        except (LookupError, ValueError):
            continue
        if not root.has_error and root.named_child_count:
            matches.append(language)
        elif root.has_error:
            errored.append(language)
    if len(matches) == 1:
        return matches[0], "unique_parser_match", matches
    return None, "unknown", matches or errored


class TreeSitterAnalyzer:
    def __init__(self, language: str):
        self.language = language

    def analyze(self, source: str) -> AnalyzerResult:
        return analyze_tree_sitter(source, self.language)


def _recursive_function_names(nodes) -> set[str]:
    recursive = set()
    for node in nodes:
        if node.type not in _FUNCTIONS:
            continue
        name_node = node.child_by_field_name("name")
        body = node.child_by_field_name("body")
        if name_node is None:
            declarator = node.child_by_field_name("declarator")
            if declarator is not None:
                stack = [declarator]
                while stack and name_node is None:
                    current = stack.pop()
                    if current.type in {"identifier", "field_identifier"}:
                        name_node = current
                    else:
                        stack.extend(reversed(current.children))
        if name_node is None and node.type == "arrow_function" and node.parent is not None:
            name_node = node.parent.child_by_field_name("name")
        if name_node is None or body is None:
            continue
        function_name = name_node.text.decode("utf-8", errors="replace")
        for child in _walk(body):
            if child.type not in {"call_expression", "method_invocation"}:
                continue
            callee = child.child_by_field_name("function") or child.child_by_field_name("name")
            if callee is not None and callee.text.decode("utf-8", errors="replace").split(".")[-1] == function_name:
                recursive.add(function_name)
                break
    return recursive


def _walk(root):
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(node.children))


def _parse_errors(root, source: str) -> tuple[str | None, list[dict]]:
    lines = source.splitlines()
    errors = []
    for node in _walk(root):
        if node.type != "ERROR" and not node.is_missing:
            continue
        row, column = node.start_point.row, node.start_point.column
        if node.is_missing:
            message = f"Expected {node.type}"
        else:
            excerpt = lines[row].strip() if row < len(lines) else ""
            message = f"Unexpected syntax near {excerpt[:80]!r}" if excerpt else "Unexpected syntax"
        errors.append({"line": row + 1, "column": column + 1, "message": message})
        if len(errors) == 10:
            break
    first = errors[0]["message"] if errors else None
    if first and errors:
        first = f"{first} (line {errors[0]['line']}, column {errors[0]['column']})"
    return first, errors


def analyze_tree_sitter(source: str, language: str) -> AnalyzerResult:
    tree = parse_source(source, language)
    root = tree.root_node
    nodes = list(_walk(root))
    counts = {kind: sum(node.type in types for node in nodes) for kind, types in {
        "function_count": _FUNCTIONS,
        "class_count": _CLASSES,
        "loop_count": _LOOPS,
        "conditional_count": _CONDITIONALS,
        "import_count": _IMPORTS,
        "assignment_count": _ASSIGNMENTS,
        "return_count": _RETURNS,
        "comment_count": _COMMENTS,
        "error_handling_count": _ERROR_HANDLERS,
    }.items()}
    max_depth = 0
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        next_depth = depth + int(node.type in _NESTING)
        max_depth = max(max_depth, next_depth)
        stack.extend((child, next_depth) for child in node.children)

    lines = source.splitlines()
    non_empty_lines = sum(bool(line.strip()) for line in lines)
    comment_nodes = [node for node in nodes if node.type in _COMMENTS]
    comment_lines = {row for node in comment_nodes
                     for row in range(node.start_point.row, node.end_point.row + 1)}
    code_lines = {node.start_point.row for node in nodes if node.child_count == 0 and
                  node.type not in _COMMENTS and node.type != "ERROR" and node.text.strip()}
    syntax_valid = not root.has_error
    syntax_error, errors = _parse_errors(root, source)
    counts.update({
        "total_lines": len(lines),
        "non_empty_lines": non_empty_lines,
        "blank_lines": len(lines) - non_empty_lines,
        "comment_lines": len(comment_lines),
        "code_lines": len(code_lines),
        "max_nesting_depth": max_depth,
        "cyclomatic_complexity": 1 + counts["loop_count"] + counts["conditional_count"],
        "recursion_detected": bool(_recursive_function_names(nodes)),
    })
    counts["program_style"] = "object-oriented" if counts["class_count"] else \
        "function-oriented" if counts["function_count"] else "script/procedural" if non_empty_lines else "not determined"

    findings = []
    for key, label in (("function_count", "function(s)"), ("class_count", "class/interface declaration(s)"),
                       ("loop_count", "loop(s)"), ("conditional_count", "conditional(s)")):
        if counts[key]:
            findings.append(f"{counts[key]} {label}")
    if not findings:
        findings.append("No function, class, loop, or conditional nodes were found.")
    summary = ", ".join(findings)
    limitations = ["Metrics are based on parser-recovered syntax trees and describe structure, not authorship.",
                   "Cyclomatic complexity is approximated from loop and conditional nodes.",
                   "Tree-sitter syntax parsing does not validate types or compiler semantics."]
    if not syntax_valid:
        limitations.append("Syntax errors were found; structural metrics may be partial.")

    return AnalyzerResult(
        language=language,
        syntax_valid=syntax_valid,
        syntax_error=syntax_error,
        metrics={**counts, "syntax_errors": errors},
        structural_findings=[summary],
        limitations=limitations,
    )