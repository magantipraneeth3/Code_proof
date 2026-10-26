"""Python analyzer built on the standard-library ast and tokenize modules.
Source is parsed, never executed."""
import ast
import io
import tokenize

from app.analyzers.base import AnalyzerResult

_NESTING = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith,
            ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_DECISIONS = (ast.If, ast.For, ast.While, ast.AsyncFor, ast.ExceptHandler, ast.IfExp,
              ast.comprehension)


def _depth(node: ast.AST, current: int = 0) -> int:
    best = current
    stack = [(node, current)]
    while stack:
        parent, depth = stack.pop()
        for child in ast.iter_child_nodes(parent):
            child_depth = depth + 1 if isinstance(child, _NESTING) else depth
            best = max(best, child_depth)
            stack.append((child, child_depth))
    return best


def _line_counts(source: str) -> dict:
    lines = source.splitlines()
    blank = sum(1 for l in lines if not l.strip())
    comment_lines = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                comment_lines.add(tok.start[0])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        comment_lines = {i + 1 for i, l in enumerate(lines) if l.strip().startswith("#")}
    return {
        "total_lines": len(lines),
        "blank_lines": blank,
        "comment_lines": len(comment_lines),
        "code_lines": max(len(lines) - blank - len(comment_lines), 0),
    }


class PythonAnalyzer:
    language = "python"

    def analyze(self, source: str) -> AnalyzerResult:
        metrics = _line_counts(source)
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return AnalyzerResult(
                language=self.language, syntax_valid=False,
                syntax_error=f"{exc.msg} (line {exc.lineno})", metrics=metrics,
                structural_findings=["Source could not be parsed; structural metrics unavailable."],
                limitations=["Syntax errors prevent AST-based analysis."],
            )
        except (ValueError, RecursionError, MemoryError) as exc:
            return AnalyzerResult(self.language, None, f"Parser could not process input ({type(exc).__name__}).",
                                  metrics, limitations=["Input too complex to parse safely."])

        nodes = list(ast.walk(tree))
        names = [n.id for n in nodes if isinstance(n, ast.Name)]
        funcs = [n for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n for n in nodes if isinstance(n, ast.ClassDef)]
        arg_names = [a.arg for f in funcs for a in f.args.args]
        idents = names + [f.name for f in funcs] + [c.name for c in classes] + arg_names
        bool_ops = sum(len(n.values) - 1 for n in nodes if isinstance(n, ast.BoolOp))
        loops = sum(isinstance(n, (ast.For, ast.AsyncFor, ast.While)) for n in nodes)
        conditionals = sum(isinstance(n, (ast.If, ast.IfExp, ast.Match)) for n in nodes)
        assignments = sum(isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)) for n in nodes)
        recursive = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == function.name
                        for function in funcs for node in ast.walk(function))
        module_statements = [node for node in tree.body if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom))]
        if classes:
            program_style = "object-oriented"
        elif funcs and not module_statements:
            program_style = "function-oriented"
        elif module_statements:
            program_style = "script/procedural"
        else:
            program_style = "not determined"
        metrics.update({
            "function_count": len(funcs),
            "class_count": len(classes),
            "import_count": sum(isinstance(n, (ast.Import, ast.ImportFrom)) for n in nodes),
            "max_nesting_depth": _depth(tree),
            "cyclomatic_complexity": 1 + sum(isinstance(n, _DECISIONS) for n in nodes) + bool_ops,
            "try_except_count": sum(isinstance(n, ast.Try) for n in nodes),
            "loop_count": loops,
            "conditional_count": conditionals,
            "assignment_count": assignments,
            "return_count": sum(isinstance(n, ast.Return) for n in nodes),
            "comment_count": metrics["comment_lines"],
            "non_empty_lines": len(source.splitlines()) - metrics["blank_lines"],
            "recursion_detected": recursive,
            "program_style": program_style,
            "identifier_count": len(idents),
            "unique_identifiers": len(set(idents)),
            "avg_identifier_length": round(sum(map(len, idents)) / len(idents), 2) if idents else 0,
            "docstring_count": sum(
                ast.get_docstring(n) is not None for n in nodes
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module))),
        })
        findings = []
        if funcs:
            findings.append(f"Defines {len(funcs)} function(s) and {len(classes)} class(es).")
        if metrics["max_nesting_depth"] >= 5:
            findings.append("Deep nesting (>= 5 levels) observed.")
        if metrics["cyclomatic_complexity"] >= 20:
            findings.append("High aggregate cyclomatic complexity observed.")
        if not findings:
            findings.append("No notable structural patterns observed.")
        return AnalyzerResult(
            language=self.language, syntax_valid=True, syntax_error=None, metrics=metrics,
            structural_findings=findings,
            limitations=["Metrics describe code structure only; none of them indicate authorship."],
        )
