"""Guarda de escrita por nivel do menu (exibir bloqueia POST; editar permite).

Mapeia caminhos de escrita ao menu de origem. O processo de dados dinamicos
(/users/profile/process-data) valida o menu no proprio handler, pelo menu_key.
Ativo apenas com APPGENESIS_ACCESS_FILTER_V1=1.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse

from appgenesis.services.access_filter import (
    NIVEL_EDITAR,
    access_filter_enabled,
    resolve_menu_access_level_v1,
)

# Ordem importa: prefixos mais especificos primeiro.
WRITE_PATH_MENU_MAP: tuple[tuple[str, str], ...] = (
    ("/users/profile/personal", "meu_perfil"),
    ("/users/profile/whatsapp/", "meu_perfil"),
    ("/users/profile/auth-profile-", "administrativo"),
    ("/users/functions/", "administrativo"),
    ("/users/departments/", "administrativo"),
    ("/users/new", "administrativo"),
    ("/users/update", "administrativo"),
    ("/users/delete", "administrativo"),
    ("/users/generate-invite", "administrativo"),
    ("/users/resend-invite", "administrativo"),
    ("/entities/", "administrativo"),
    ("/empresa/update", "empresa"),
    ("/settings/menu/", "sessoes"),
)


def menu_for_write_path(path: str) -> str | None:
    clean_path = str(path or "")
    for prefix, menu_key in WRITE_PATH_MENU_MAP:
        if clean_path == prefix or clean_path.startswith(prefix):
            return menu_key
    return None


def write_denied_for_menu(request: Request, menu_key: str) -> bool:
    """True quando o utilizador autenticado nao tem nivel editar no menu."""
    from appgenesis.db.session import SessionLocal
    from appgenesis.models import User
    from appgenesis.services.session import get_current_user, get_session_entity_id

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return False  # sem sessao: a propria rota trata a autenticacao
        user = session.get(User, current_user["id"])
        level = resolve_menu_access_level_v1(
            session,
            entity_id=get_session_entity_id(request),
            user_system_type=getattr(user, "system_type", ""),
            menu_key=menu_key,
        )
        return level != NIVEL_EDITAR


async def access_write_guard_middleware(request: Request, call_next: Any):
    if request.method == "POST" and access_filter_enabled():
        menu_key = menu_for_write_path(request.url.path)
        if menu_key and write_denied_for_menu(request, menu_key):
            return HTMLResponse(
                "<!doctype html><meta charset='utf-8'><title>Sem permissão</title>"
                "<p>Sem permissão para editar este processo (nível exibir).</p>",
                status_code=403,
            )
    return await call_next(request)
