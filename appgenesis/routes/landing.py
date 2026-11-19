from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from appgenesis.core import templates

router = APIRouter()

_VAZIO = {"atualizado_em": None, "eventos": []}
_cache: dict = {"mtime": None, "dados": _VAZIO}

# Departamentos da landing. Páginas fixas no código: alterar aqui e fazer deploy.
# "imagem" (ficheiro em static/img) tem prioridade sobre "svg" (caminho d de um ícone).
DEPARTAMENTOS = [
    {
        "slug": "centro-de-cura",
        "nome": "Centro de Cura",
        "imagem": "/static/img/icon-centro-de-cura.png",
        "resumo": "Ensinar · Orar · Acreditar · Curar.",
        "descricao": [
            "Primeiro Centro de Cura na Europa, da Verbo da Vida Braga.",
            "Próxima edição em breve. Faz a tua inscrição e fica a par das novidades.",
        ],
        "acoes": [
            {"texto": "Inscrição", "url": "https://forms.gle/qVLuDgFuJf8znRfg7", "principal": True},
            {"texto": "WhatsApp", "url": "https://api.whatsapp.com/send/?phone=351913489133&text=Ola.+Quero+participar+da+proxima+edi%C3%A7%C3%A3o+do+centro+de+cura.+Como+devo+fazer%3F&type=phone_number&app_absent=0", "principal": False},
            {"texto": "Ver trailer", "url": "https://www.youtube.com/watch?v=dfpbPAMCMzU", "principal": False},
        ],
        "fotos": [],
    },
    {
        "slug": "jovens",
        "nome": "Jovens",
        "svg": "M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8-4.3-4.1 5.9-.9z",
        "resumo": "Um espaço de comunhão, crescimento e serviço para os jovens.",
        "descricao": ["Em breve, mais informações sobre este departamento."],
        "acoes": [],
        "fotos": [],
    },
    {
        "slug": "departamento-infantil",
        "nome": "Departamento Infantil",
        "imagem": "/static/img/icon-criancas.png",
        "resumo": "Um espaço de comunhão, crescimento e serviço para as crianças.",
        "descricao": ["Em breve, mais informações sobre este departamento."],
        "acoes": [],
        "fotos": [],
    },
    {
        "slug": "a-livraria",
        "nome": "A livraria",
        "imagem": "/static/img/icon-verboshop.png",
        "resumo": "Um espaço de comunhão, crescimento e serviço para a família.",
        "descricao": ["Em breve, mais informações sobre este departamento."],
        "acoes": [],
        "fotos": [],
    },
    {
        "slug": "verbo-cafe",
        "nome": "Verbo café",
        "imagem": "/static/img/icon-verbo-cafe.png",
        "resumo": "Um espaço de comunhão, crescimento e serviço para a família.",
        "descricao": ["Em breve, mais informações sobre este departamento."],
        "acoes": [],
        "fotos": [],
    },
]


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Public landing page for Verbo da Vida Braga."""
    return templates.TemplateResponse(
        request, "landing.html", {"request": request, "departamentos": DEPARTAMENTOS}
    )


@router.get("/departamentos/{slug}", response_class=HTMLResponse)
async def departamento_page(request: Request, slug: str):
    """Página de um departamento (dados fixos em DEPARTAMENTOS)."""
    departamento = next((d for d in DEPARTAMENTOS if d["slug"] == slug), None)
    if departamento is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "departamento.html", {"request": request, "d": departamento}
    )


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
