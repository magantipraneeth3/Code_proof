import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.models  # noqa: F401  (register tables)
from app.api.v1 import analysis, assignments, auth, dashboard, public, reports, review_notes, submissions, system
from app.core.config import settings
from app.core.db import Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("codeproof")

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def _rid(request: Request):
    return getattr(request.state, "request_id", None)


@app.middleware("http")
async def request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    msg = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(status_code=exc.status_code, headers=getattr(exc, "headers", None),
                        content={"error": f"http_{exc.status_code}", "message": msg, "request_id": _rid(request)})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    details = [{"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
               for e in exc.errors()]  # input values are deliberately not echoed
    return JSONResponse(status_code=422, content={"error": "validation_error",
                        "message": "The request was invalid.", "details": details, "request_id": _rid(request)})


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.error("Unhandled error request_id=%s type=%s", _rid(request), type(exc).__name__)
    return JSONResponse(status_code=500, content={"error": "internal_error",
                        "message": "An unexpected error occurred.", "request_id": _rid(request)})


@app.on_event("startup")
def init_db():
    # Dev convenience; Alembic migrations are not written yet.
    Base.metadata.create_all(bind=engine)


for r in (system.router, auth.router, assignments.router, submissions.router,
          review_notes.router, analysis.router, public.router, reports.router, dashboard.router):
    app.include_router(r, prefix="/api/v1")
