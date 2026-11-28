"""Seed minimo para o job "browser" do CI (BD vazia).

Cria: admin owner, menu Definicoes (sessoes), config de Empresa e um processo de lista "calendario".
So estrutura (copiada da forma usada em producao), sem dados pessoais. Idempotente.
Uso: DATABASE_URL=... ADMIN_LOGIN_EMAIL=... python scripts/ci_seed_browser.py
"""

from __future__ import annotations

import json
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from appgenesis.services.process_settings.normalizers import (
    _resolve_sidebar_menu_settings_entity_id,
    ensure_sidebar_menu_settings_defaults,
)

VISIBILITY = {
    "requires_admin": True,
    "visibility_scopes": ["owner", "legado"],
    "visibility_scope_mode": "all",
    "visibility_scope_label": "Default",
}

# Menu de configuracao (Sessoes/Menu e editor de processos), igual a producao.
SESSOES_CONFIG = {"sidebar_section": "sistema", **VISIBILITY}

# Empresa: cabecalho "Dados da empresa" com os blocos fixos, igual a producao.
EMPRESA_CONFIG = {
    "sidebar_section": "sistema",
    "additional_fields": [
        {"key": "custom_dados_da_empresa", "label": "Dados da empresa", "field_type": "header", "is_required": False}
    ],
    "process_visible_fields": ["dados_gerais", "morada"],
    "process_visible_headers": [],
    "process_visible_field_rows": [
        {"field_key": "dados_gerais", "header_key": "custom_dados_da_empresa"},
        {"field_key": "morada", "header_key": "custom_dados_da_empresa"},
    ],
    "process_visible_field_header_map": {"dados_gerais": "custom_dados_da_empresa", "morada": "custom_dados_da_empresa"},
    "process_visible_fields_configured": True,
    "visible_fields": ["custom_dados_da_empresa", "dados_gerais", "morada"],
    "visible_field_headers": {"dados_gerais": "custom_dados_da_empresa", "morada": "custom_dados_da_empresa"},
    **VISIBILITY,
}

# Processo generico de formulario (campos com a forma do processo Ausencias de producao, sem layout de lista):
# abre no card dinamico (#dynamic-process-card) e tem editor de processo (campos, listas).
_FIELDS = [
    ("custom_data_inicio", "Data início", "date", True),
    ("custom_data_fim", "Data fim", "date", False),
    ("custom_titulo", "Título", "text", True),
    ("custom_descricao", "Descrição", "text", False),
]
CALENDARIO_CONFIG = {
    "sidebar_section": "igreja",
    "process_visible_fields_configured": True,
    "process_visible_headers": ["custom_evento"],
    "process_visible_fields": [key for key, *_ in _FIELDS] + ["custom_evento"],
    "visible_field_headers": {key: "custom_evento" for key, *_ in _FIELDS},
    "process_visible_field_header_map": {key: "custom_evento" for key, *_ in _FIELDS},
    "additional_fields": [{"key": "custom_evento", "label": "Evento", "field_type": "header", "is_required": False}]
    + [{"key": key, "label": label, "field_type": kind, "is_required": req} for key, label, kind, req in _FIELDS],
    "process_visible_field_rows": [
        {"field_key": key, "header_key": "custom_evento", "display_order": n} for n, (key, *_) in enumerate(_FIELDS, 1)
    ],
    **VISIBILITY,
}

MENUS = [
    ("sessoes", "Definições", SESSOES_CONFIG),
    ("empresa", "Empresa", EMPRESA_CONFIG),
    ("calendario", "Calendário", CALENDARIO_CONFIG),
]


def _upsert_menu(session: Session, entity_id: int | None, menu_key: str, label: str, config: dict) -> None:
    current = session.execute(
        text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = :key"), {"key": menu_key}
    ).first()
    payload = {"key": menu_key, "label": label, "config": json.dumps(config, ensure_ascii=False), "entity_id": entity_id}
    if current is None:
        session.execute(
            text(
                "INSERT INTO sidebar_menu_settings (entity_id, menu_key, menu_label, is_active, is_deleted, menu_config) "
                "VALUES (:entity_id, :key, :label, TRUE, FALSE, :config)"
            ),
            payload,
        )
    elif not (current.menu_config or "").strip():
        # Menus base criados pela app vem sem config; so preenche quando vazio.
        session.execute(
            text("UPDATE sidebar_menu_settings SET menu_config = :config WHERE menu_key = :key"), payload
        )


def main() -> None:
    engine = create_engine(os.environ["DATABASE_URL"])
    with Session(engine) as session:  # ensure_sidebar_menu_settings_defaults faz o seu proprio commit
        # Como em producao, o admin e owner: com o filtro por funcao ligado, nao-owner sem funcao leva 403.
        updated = session.execute(
            text("UPDATE users SET system_type = 'owner' WHERE login_email = :email"),
            {"email": os.environ["ADMIN_LOGIN_EMAIL"].strip().lower()},
        ).rowcount
        assert updated == 1, "admin do CI nao encontrado (correr bootstrap_admin.py antes)"
        # Entidade do admin = entidade owner 1000, como em producao (o editor mostra o Nº da entidade).
        session.execute(
            text(
                "UPDATE entities SET entity_number = 1000, profile_scope = 'owner' WHERE id = ("
                " SELECT me.entity_id FROM member_entities me JOIN users u ON u.member_id = me.member_id"
                " WHERE u.login_email = :email ORDER BY me.entity_id LIMIT 1)"
                " AND NOT EXISTS (SELECT 1 FROM entities WHERE entity_number = 1000)"
            ),
            {"email": os.environ["ADMIN_LOGIN_EMAIL"].strip().lower()},
        )

        ensure_sidebar_menu_settings_defaults(session)
        entity_id = _resolve_sidebar_menu_settings_entity_id(session)
        for menu_key, label, config in MENUS:
            _upsert_menu(session, entity_id, menu_key, label, config)
        session.commit()
        keys = session.execute(text("SELECT menu_key FROM sidebar_menu_settings ORDER BY menu_key")).scalars().all()
    print("menus:", ", ".join(keys))


if __name__ == "__main__":
    main()
