#!/usr/bin/env python3
"""PAL auth broker.

GitLab Pages is a static site, so it cannot hold the Widen token. This service
holds that token and hands it to the browser after a gate check. The browser
then uploads the GeoTIFF straight to Widen. This process never sees the file.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PAL Auth", version="0.1.0")

_origins = [o.strip() for o in
            os.environ.get("PAL_UPLOADER_ALLOW_ORIGINS", "*").split(",")
            if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _expected_gate() -> str:
    return os.environ.get("PAL_GATE", "").strip()


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "token_configured": bool(os.environ.get("ACQUIA_API_TOKEN", "").strip()),
        "gate_configured": bool(_expected_gate()),
    }


@app.post("/api/token")
def token(x_pal_gate: str = Header(default="")) -> dict:
    expected = _expected_gate()
    # Refuse when the gate is unset so a bare URL never leaks the Widen token.
    if not expected or x_pal_gate.strip() != expected:
        raise HTTPException(401, "unauthorized")
    acquia = os.environ.get("ACQUIA_API_TOKEN", "").strip()
    if not acquia:
        raise HTTPException(503, "ACQUIA_API_TOKEN is not configured")
    body = {
        "token": acquia,
        "base": os.environ.get(
            "ACQUIA_API_BASE", "https://api.widencollective.com/v2").strip(),
    }
    mapbox = os.environ.get("MAPBOX_ACCESS_TOKEN", "").strip()
    if mapbox:
        body["mapbox_token"] = mapbox
    return body
