"""
TrackShift FastAPI Server Entry Point
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router

app = FastAPI(
    title="TrackShift API",
    description="F1 Tyre Degradation Intelligence Engine with Widening Uncertainty Cones",
    version="1.0.0"
)

# CORS origins are configurable via env var for deployment (comma-separated),
# defaulting to "*" for local React development.
_cors_origins_env = os.getenv("CORS_ORIGINS", "*")
_cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
# Browsers reject `allow_credentials=True` combined with a wildcard origin,
# so only enable credentials when explicit origins are configured.
_allow_credentials = "*" not in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("UVICORN_RELOAD", "true").lower() == "true"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload_enabled)
