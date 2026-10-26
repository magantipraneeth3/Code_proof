from app.analyzers.python_analyzer import PythonAnalyzer
from app.analyzers.tree_sitter_analyzer import PARSER_NAMES, TreeSitterAnalyzer

# Capability table: entries are supported only when backed by a real parser.
LANGUAGES = [
    {"id": "python", "name": "Python", "extensions": [".py"], "status": "supported",
     "analysis": "AST + tokenize"},
    {"id": "java", "name": "Java", "extensions": [".java"], "status": "supported", "analysis": "Tree-sitter syntax and structure"},
    {"id": "javascript", "name": "JavaScript", "extensions": [".js", ".jsx", ".mjs"], "status": "supported", "analysis": "Tree-sitter syntax and structure"},
    {"id": "typescript", "name": "TypeScript", "extensions": [".ts"], "status": "supported", "analysis": "Tree-sitter syntax and structure"},
    {"id": "tsx", "name": "TypeScript JSX", "extensions": [".tsx"], "status": "supported", "analysis": "Tree-sitter syntax and structure"},
    {"id": "c", "name": "C", "extensions": [".c", ".h"], "status": "supported", "analysis": "Tree-sitter syntax and structure"},
    {"id": "cpp", "name": "C++", "extensions": [".cpp", ".cc", ".hpp"], "status": "supported", "analysis": "Tree-sitter syntax and structure"},
]
_PYTHON_ANALYZER = PythonAnalyzer()
_ANALYZERS = {"python": _PYTHON_ANALYZER, **{language: TreeSitterAnalyzer(language) for language in PARSER_NAMES}}


def get_analyzer(language: str):
    selected = (language or "").lower()
    return _ANALYZERS.get(selected)


def detect_language(filename: str | None, declared: str | None) -> str | None:
    if declared:
        return declared.lower()
    if filename:
        lower = filename.lower()
        for lang in LANGUAGES:
            if any(lower.endswith(ext) for ext in lang["extensions"]):
                return lang["id"]
    return None
