"""Seed minimo para o job "browser" do CI (BD vazia): admin owner e menu Definicoes (sessoes).

So estrutura, sem dados pessoais. Uso: DATABASE_URL=... ADMIN_LOGIN_EMAIL=... python scripts/ci_seed_browser.py
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

# Igual a producao: menu de configuracao (Sessoes/Menu), so para owner/legado com funcao.
SESSOES_MENU = {
    "menu_key": "sessoes",
    "menu_label": "Definições",
    "menu_config": {
        "sidebar_section": "sistema",
        "requires_admin": True,
        "visibility_scopes": ["owner", "legado"],
        "visibility_scope_mode": "all",
        "visibility_scope_label": "Default",
    },
}


def main() -> None:
    engine = create_engine(os.environ["DATABASE_URL"])
    with Session(engine) as session:  # ensure_sidebar_menu_settings_defaults faz o seu proprio commit
        # Como em producao, o admin e owner: com o filtro por funcao ligado, nao-owner sem funcao leva 403.
        updated = session.execute(
            text("UPDATE users SET system_type = 'owner' WHERE login_email = :email"),
            {"email": os.environ["ADMIN_LOGIN_EMAIL"].strip().lower()},
        ).rowcount
        assert updated == 1, "admin do CI nao encontrado (correr bootstrap_admin.py antes)"

        ensure_sidebar_menu_settings_defaults(session)
        exists = session.execute(
            text("SELECT 1 FROM sidebar_menu_settings WHERE menu_key = :key"), {"key": SESSOES_MENU["menu_key"]}
        ).first()
        if exists is None:
            session.execute(
                text(
                    "INSERT INTO sidebar_menu_settings (entity_id, menu_key, menu_label, is_active, is_deleted, menu_config) "
                    "VALUES (:entity_id, :menu_key, :menu_label, TRUE, FALSE, :menu_config)"
                ),
                {
                    "entity_id": _resolve_sidebar_menu_settings_entity_id(session),
                    "menu_key": SESSOES_MENU["menu_key"],
                    "menu_label": SESSOES_MENU["menu_label"],
                    "menu_config": json.dumps(SESSOES_MENU["menu_config"], ensure_ascii=False),
                },
            )
        session.commit()
        keys = session.execute(text("SELECT menu_key FROM sidebar_menu_settings ORDER BY menu_key")).scalars().all()
    print("menus:", ", ".join(keys))


if __name__ == "__main__":
    main()
