# CodeProof — AI Code Authorship Analysis Platform (Stage 2: core workflow)

Decision-support tooling for reviewing programming submissions. It never claims to prove authorship.
"Inconclusive" is a normal result, and the ML model reports `unavailable` until a validated one exists.

## Working workflow
Professor registers → creates an assignment → student registers → submits code (paste or file upload) →
the server analyzes it (Python AST/tokenize; code is parsed, never executed) → results appear in the UI →
professor generates and downloads a PDF report. Roles are enforced on the server; users only see their own data.

## Implemented
- Auth (scrypt password hashing, JWT bearer tokens, auth rate limiting), roles: student / professor
- Assignments CRUD (professor-owned), submissions (JSON + multipart upload), upload validation, randomized storage names
- Analysis: Python AST/tokenize plus Tree-sitter syntax and structural analysis for Java, C, C++, JavaScript, TypeScript, and TSX
- Stateless analysis preview endpoint for the "Analyze code" page
- Public no-account analyzer at `/analyze`; parser-based language detection, syntax/structure analysis, and within-language token/3-gram comparison
- Authorship classifier remains unavailable; public results contain no AI-likelihood percentage
- PDF reports (professor only), audit events for key actions, request IDs, consistent safe error responses
- Professor-only review notes on owned submissions (create, edit, and delete)
- Professor review queue with persisted review status and side-by-side source inspection
- Frontend: landing, login/register, dashboard (real counts), assignments, submissions (search/filter/pagination),
    submission detail + results and review notes, public analysis workspace
## Not implemented yet (shown as "soon" in the UI where relevant)
Admin role features, Alembic migrations (tables are created at startup), PostgreSQL driver/config, ZIP/project uploads,
bulk upload/analysis, AST-equivalence or cross-language similarity comparison, Git history, verified provenance records,
settings/privacy page, password reset, Monaco editor in the authenticated workspace (public analyzer uses Monaco), shadcn/ui, React Hook Form + Zod,
Recharts, Playwright/Vitest component tests, authorship ML pipeline and labeled training dataset,
server-side token revocation, analysis timeouts/sandboxing, deployment configs.

## Run
    # backend (Python 3.11+)
    cd backend && python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000
    # frontend
    cd frontend && npm install && npm run dev        # http://localhost:5173

## Test
    cd backend && python -m pytest                   # or: python -m unittest discover -s tests -t .
    cd frontend && npm test                          # Node test runner (API client + helpers)

## API (all under /api/v1)
| Area | Endpoints |
|---|---|
| System | GET /health, GET /languages |
| Public analyzer | GET /public/health, GET /public/samples; POST /public/analyze, POST /public/compare (no auth; rate-limited) |
| Auth | POST /auth/register, /auth/login, /auth/logout; GET /auth/me |
| Assignments | GET/POST /assignments; GET/PATCH/DELETE /assignments/{id} |
| Submissions | GET/POST /submissions; POST /submissions/upload; GET/DELETE /submissions/{id} |
| Reviews | GET/POST /submissions/{id}/notes; PATCH/DELETE /submissions/{id}/notes/{note_id}; PATCH /submissions/{id}/review-status (owning professor only) |
| Analysis | POST /analysis/preview; POST /analysis; GET /analysis/{id}; POST /analysis/{id}/retry (failed only) |
| Reports | POST /reports; GET /reports/{id}/download (professor only) |
| Dashboard | GET /dashboard/stats |

Design decisions: students can see all assignments (no enrollment model yet) and their own submissions and analyses;
professors see only submissions to their own assignments; resources outside a user's scope return 404.
Admins have no access to student code. Auth tokens live in sessionStorage.
Public analysis does not save user code or access private submissions. The per-process, in-memory abuse limiter uses request IPs.
Tree-sitter supplies parser-backed syntax/structure for Java, C/C++, JavaScript, TypeScript, and TSX, but does not execute code
or validate type/semantic errors. Automatic detection is bounded to 128 KB and accepts only a unique clean parser match; ambiguous
code needs manual language selection. Similarity uses within-language parser tokens, sequence matching, and n-gram overlap, not
authorship probability. Bundled examples are original and have unknown, unverified authorship provenance; they are not training data.
The public rate limiter is in-memory and per process. Model training/evaluation commands are not provided: no labeled authorship
dataset or validated model pipeline exists, so predictions remain disabled.

Tree-sitter parser dependency is installed with `pip install -r backend/requirements.txt`. Do not run submitted programs or
treat parser metrics, similarity, or a missing provenance record as evidence that AI did or did not author code.
