# Isolated database and upload directory for every test run (set before app modules import settings).
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="codeproof-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["AUTH_RATE_LIMIT"] = "1000"
os.environ["CODEPROOF_ENV"] = "development"
