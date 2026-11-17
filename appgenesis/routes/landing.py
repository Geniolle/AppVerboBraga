from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from appgenesis.core import templates

router = APIRouter()

_VAZIO = {"atualizado_em": None, "eventos": []}
_cache: dict = {"mtime": None, "dados": _VAZIO}


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Public landing page for Verbo da Vida Braga."""
    return templates.TemplateResponse(request, "landing.html", {"request": request})


@router.get("/api/eventos-agenda")
async def eventos_agenda():
    """Eventos do mês gerados por scripts/agenda; cache por mtime, sem tocar na Google."""
    caminho = Path(os.environ.get("AGENDA_OUTPUT_FILE", "eventos.json"))
    try:
        mtime = caminho.stat().st_mtime
    except OSError:
        return JSONResponse(_VAZIO, headers={"Cache-Control": "public, max-age=300"})
    if _cache["mtime"] != mtime:
        try:
            _cache["dados"] = json.loads(caminho.read_text(encoding="utf-8"))
            _cache["mtime"] = mtime
        except (OSError, ValueError):
            return JSONResponse(_VAZIO, headers={"Cache-Control": "no-store"})
    return JSONResponse(_cache["dados"], headers={"Cache-Control": "public, max-age=300"})
