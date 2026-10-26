"""Upload validation and randomized on-disk storage. Uploaded code is never executed."""
import os
import re
import uuid

from app.core.config import settings

ALLOWED_EXTENSIONS = {".py", ".java", ".js", ".jsx", ".ts", ".tsx", ".c", ".h", ".cpp", ".cc", ".hpp"}
_REF_RE = re.compile(r"^[0-9a-f]{32}\.src$")


class UploadError(ValueError):
    """Message is safe to show to users."""


def safe_filename(name: str) -> str:
    base = os.path.basename((name or "").replace("\\", "/"))
    base = "".join(ch for ch in base if ch.isprintable() and ch not in '<>:"|?*').strip(" .")
    if not base or base in {".", ".."}:
        raise UploadError("A valid file name is required.")
    return base[:255]


def validate_source_upload(filename: str, data: bytes, max_bytes: int | None = None) -> tuple[str, str]:
    """Returns (safe_filename, decoded_text) or raises UploadError."""
    limit = max_bytes or settings.max_source_bytes
    name = safe_filename(filename)
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadError(f"File type '{ext or 'none'}' is not allowed.")
    if len(data) > limit:
        raise UploadError(f"File exceeds the {limit}-byte limit.")
    if not data.strip():
        raise UploadError("The file is empty.")
    if b"\x00" in data:
        raise UploadError("Binary content is not accepted.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise UploadError("File must be UTF-8 text.")
    return name, text


def _path(ref: str) -> str:
    if not _REF_RE.match(ref or ""):
        raise UploadError("Invalid storage reference.")
    return os.path.join(settings.upload_dir, ref)


def store_source(text: str) -> str:
    os.makedirs(settings.upload_dir, mode=0o700, exist_ok=True)
    ref = uuid.uuid4().hex + ".src"
    fd = os.open(_path(ref), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return ref


def read_source(ref: str) -> str | None:
    try:
        with open(_path(ref), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UploadError):
        return None


def delete_source(ref: str) -> None:
    try:
        os.remove(_path(ref))
    except (OSError, UploadError):
        pass
