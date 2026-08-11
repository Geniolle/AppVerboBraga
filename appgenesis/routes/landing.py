from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from appgenesis.core import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Public landing page for Verbo da Vida Braga."""
    return templates.TemplateResponse(request, "landing.html", {"request": request})
