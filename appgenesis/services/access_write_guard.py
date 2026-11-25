"""Guarda de escrita por acao do menu (exibir/editar/criar/eliminar).

Mapeia caminhos de escrita ao menu e as acoes que permitem a escrita.
O processo de dados dinamicos (/users/profile/process-data) valida a acao no
proprio handler (criar, editar ou eliminar, conforme a operacao).
Ativo apenas com APPGENESIS_ACCESS_FILTER_V1=1.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse

from appgenesis.services.access_actions import ACTION_CRIAR, ACTION_EDITAR, ACTION_ELIMINAR
from appgenesis.services.access_filter import access_filter_enabled, resolve_menu_actions_v1

# (prefixo, menu, acoes que permitem a escrita). Prefixos mais especificos primeiro.
WRITE_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("/users/functions/delete", "administrativo", (ACTION_ELIMINAR,)),
    ("/users/departments/delete", "administrativo", (ACTION_ELIMINAR,)),
    ("/users/profile/auth-profile-delete", "administrativo", (ACTION_ELIMINAR,)),
    ("/users/delete", "administrativo", (ACTION_ELIMINAR,)),
    ("/entities/delete", "administrativo", (ACTION_ELIMINAR,)),
    ("/settings/menu/sidebar-section-delete", "sessoes", (ACTION_ELIMINAR,)),
    ("/settings/menu/menu-delete", "sessoes", (ACTION_ELIMINAR,)),
    ("/settings/menu/delete", "sessoes", (ACTION_ELIMINAR,)),
    ("/users/profile/personal", "meu_perfil", (ACTION_EDITAR,)),
    ("/users/profile/whatsapp/", "meu_perfil", (ACTION_EDITAR,)),
    ("/users/profile/auth-profile-", "administrativo", (ACTION_CRIAR, ACTION_EDITAR)),
    ("/users/functions/", "administrativo", (ACTION_CRIAR, ACTION_EDITAR)),
    ("/users/departments/", "administrativo", (ACTION_CRIAR, ACTION_EDITAR)),
    ("/users/new", "administrativo", (ACTION_CRIAR,)),
    ("/users/update", "administrativo", (ACTION_EDITAR,)),
    ("/users/generate-invite", "administrativo", (ACTION_CRIAR,)),
    ("/users/resend-invite", "administrativo", (ACTION_EDITAR,)),
    ("/entities/", "administrativo", (ACTION_CRIAR, ACTION_EDITAR)),
    ("/empresa/update", "empresa", (ACTION_EDITAR,)),
    ("/settings/menu/", "sessoes", (ACTION_CRIAR, ACTION_EDITAR)),
)


def write_rule_for_path(path: str) -> tuple[str, tuple[str, ...]] | None:
    clean_path = str(path or "")
    for prefix, menu_key, required_any in WRITE_RULES:
        if clean_path == prefix or clean_path.startswith(prefix):
            return menu_key, required_any
    return None


def write_denied_for_path(request: Request, menu_key: str, required_any: tuple[str, ...]) -> bool:
    """True quando o utilizador autenticado nao tem nenhuma das acoes exigidas no menu."""
    from appgenesis.db.session import SessionLocal
    from appgenesis.models import User
    from appgenesis.services.session import get_current_user, get_session_entity_id

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return False  # sem sessao: a propria rota trata a autenticacao
        user = session.get(User, current_user["id"])
        actions = resolve_menu_actions_v1(
            session,
            entity_id=get_session_entity_id(request),
            user_system_type=getattr(user, "system_type", ""),
            menu_key=menu_key,
        )
        return not any(action in actions for action in required_any)


async def access_write_guard_middleware(request: Request, call_next: Any):
    if request.method == "POST" and access_filter_enabled():
        rule = write_rule_for_path(request.url.path)
        if rule and write_denied_for_path(request, rule[0], rule[1]):
            return HTMLResponse(
                "<!doctype html><meta charset='utf-8'><title>Sem permissão</title>"
                "<p>Sem permissão para esta ação.</p>",
                status_code=403,
            )
    return await call_next(request)
