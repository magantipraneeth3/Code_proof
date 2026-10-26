from datetime import datetime
from typing import Literal, Optional
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterIn(BaseModel):
    email: str = Field(max_length=320, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=10, max_length=128)
    role: Literal["student", "professor"] = "student"


class LoginIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AssignmentIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10_000)
    instructions: str = Field(default="", max_length=10_000)
    allowed_languages: list[str] = Field(default_factory=list, max_length=20)
    due_date: Optional[datetime] = None


class AssignmentPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=10_000)
    instructions: Optional[str] = Field(default=None, max_length=10_000)
    allowed_languages: Optional[list[str]] = Field(default=None, max_length=20)
    due_date: Optional[datetime] = None


class SubmissionIn(BaseModel):
    assignment_id: int
    filename: str = Field(min_length=1, max_length=255)
    language: Optional[str] = Field(default=None, max_length=32)
    source: str = Field(min_length=1, max_length=settings.max_source_bytes)


class PreviewIn(BaseModel):
    source: str = Field(max_length=settings.max_source_bytes)
    language: Optional[str] = Field(default=None, max_length=32)
    filename: Optional[str] = Field(default=None, max_length=255)


class AnalysisRunIn(BaseModel):
    submission_id: int


class ReportIn(BaseModel):
    analysis_id: str = Field(max_length=36)


class ReviewNoteIn(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)


class ReviewNotePatch(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)


class ReviewStatusIn(BaseModel):
    status: Literal["needs_review", "reviewed"]


class PublicAnalyzeIn(BaseModel):
    code: str = Field(max_length=settings.max_source_bytes)
    language: Optional[str] = Field(default=None, max_length=32)
    compare_samples: bool = True


class PublicCompareIn(BaseModel):
    code_a: str = Field(max_length=settings.max_source_bytes)
    language_a: str = Field(min_length=1, max_length=32)
    code_b: str = Field(max_length=settings.max_source_bytes)
    language_b: str = Field(min_length=1, max_length=32)
