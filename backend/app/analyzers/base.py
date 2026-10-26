from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass
class AnalyzerResult:
    language: str
    syntax_valid: Optional[bool]
    syntax_error: Optional[str]
    metrics: dict
    structural_findings: list = field(default_factory=list)
    limitations: list = field(default_factory=list)


class LanguageAnalyzer(Protocol):
    language: str

    def analyze(self, source: str) -> AnalyzerResult: ...
