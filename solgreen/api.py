"""Minimal HTTP API for Coolify health checks."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Solgreen", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, Any] | JSONResponse:
    """Health check endpoint for Coolify."""
    db_url = os.environ.get("SOLGREEN_DATABASE_URL")
    if not db_url:
        return JSONResponse(
            status_code=503, content={"status": "error", "detail": "SOLGREEN_DATABASE_URL not set"}
        )
    try:
        from solgreen.db.connection import get_connection

        with get_connection(db_url) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "solgreen", "version": "0.1.0"}
