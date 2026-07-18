"""JobPilot FastAPI application entry point."""

import os

os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.db import init_db
from backend.app.observability import setup_observability
from backend.app.routes import (
    auth,
    auth_github,
    auth_google,
    github,
    jobs,
    profile,
    runs,
    search,
    worker,
)

app = FastAPI(title="JobPilot API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(auth_google.router)
app.include_router(auth_github.router)
app.include_router(github.router)
app.include_router(search.router)
app.include_router(runs.router)
app.include_router(jobs.router)
app.include_router(worker.router)
setup_observability(app)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
