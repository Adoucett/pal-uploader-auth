#!/usr/bin/env python3
"""PAL auth broker.

GitLab Pages is a static site, so it cannot hold Widen tokens. This service
holds one token per superuser and hands the chosen person's token to the
browser after a gate check. The browser then uploads the GeoTIFF straight to
Widen. This process never sees the file.

Operators are config, not code. Adding a person is two Render env vars and a
restart, once Molly issues their key:

    PAL_OPERATORS=aaron|Aaron Doucett,seve|Seve Name
    PAL_TOKEN_AARON=planet/...
    PAL_TOKEN_SEVE=planet/...

Until PAL_OPERATORS is set, a single operator "aaron" is served from
ACQUIA_API_TOKEN so the current one-key setup keeps working.
"""
from __future__ import annotations

import os
import re

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="PAL Auth", version="0.2.0")

_origins = [o.strip() for o in
            os.environ.get("PAL_UPLOADER_ALLOW_ORIGINS", "*").split(",")
            if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

_ID = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


def _expected_gate() -> str:
    return os.environ.get("PAL_GATE", "").strip()


def _require_gate(presented: str) -> None:
    expected = _expected_gate()
    # Refuse when the gate is unset so a bare URL never leaks a Widen token.
    if not expected or presented.strip() != expected:
        raise HTTPException(401, "unauthorized")


def _token_for(operator_id: str) -> str:
    specific = os.environ.get(f"PAL_TOKEN_{operator_id.upper()}", "").strip()
    if specific:
        return specific
    # The original single-key env still drives Aaron until a dedicated
    # PAL_TOKEN_AARON is set.
    if operator_id == "aaron":
        return os.environ.get("ACQUIA_API_TOKEN", "").strip()
    return ""


def _operators() -> list[dict]:
    """Configured superusers that actually have a key. Names only, no tokens."""
    raw = os.environ.get("PAL_OPERATORS", "").strip()
    if not raw:
        raw = "aaron|Aaron Doucett"
    found: list[dict] = []
    seen: set[str] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "|" in part:
            oid, name = part.split("|", 1)
        else:
            oid, name = part, part
        oid = oid.strip().lower()
        name = name.strip()
        if not _ID.match(oid) or not name or oid in seen:
            continue
        if not _token_for(oid):
            continue
        seen.add(oid)
        found.append({"id": oid, "name": name})
    return found


def _widen_base() -> str:
    return os.environ.get(
        "ACQUIA_API_BASE", "https://api.widencollective.com/v2").strip()


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "gate_configured": bool(_expected_gate()),
        "operators": len(_operators()),
    }


@app.get("/api/operators")
def operators(x_pal_gate: str = Header(default="")) -> dict:
    _require_gate(x_pal_gate)
    return {"operators": _operators()}


class TokenBody(BaseModel):
    operator: str


@app.post("/api/token")
def token(body: TokenBody, x_pal_gate: str = Header(default="")) -> dict:
    _require_gate(x_pal_gate)
    oid = body.operator.strip().lower()
    match = next((op for op in _operators() if op["id"] == oid), None)
    if match is None:
        raise HTTPException(404, "unknown operator")
    acquia = _token_for(oid)
    if not acquia:
        raise HTTPException(503, "operator has no key configured")
    out = {
        "operator": match["id"],
        "name": match["name"],
        "token": acquia,
        "base": _widen_base(),
    }
    mapbox = os.environ.get("MAPBOX_ACCESS_TOKEN", "").strip()
    if mapbox:
        out["mapbox_token"] = mapbox
    return out
