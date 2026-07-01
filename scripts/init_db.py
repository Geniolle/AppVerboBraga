from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from dotenv import load_dotenv


def get_database_url() -> str:
    # Use env var for production; fallback to local SQLite for quick start.
    return os.getenv("DATABASE_URL", "sqlite:///app.db")


def get_alembic_config_v1(database_url: str) -> Config:
    alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return alembic_cfg


def database_is_at_head_v1(database_url: str, alembic_cfg: Config) -> bool:
    script_directory = ScriptDirectory.from_config(alembic_cfg)
    expected_heads = set(script_directory.get_heads())

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            current_heads = set(MigrationContext.configure(connection).get_current_heads())
    finally:
        engine.dispose()

    return bool(expected_heads) and current_heads == expected_heads


def main() -> None:
    # ###################################################################################
    # (1) CARREGAR CONFIGURAÇÃO E PREPARAR O ALEMBIC
    # ###################################################################################
    load_dotenv()
    database_url = get_database_url()
    alembic_cfg = get_alembic_config_v1(database_url)
    safe_url = make_url(database_url).render_as_string(hide_password=True)

    # ###################################################################################
    # (2) EVITAR UPGRADE COMPLETO QUANDO A BASE JÁ ESTÁ EM HEAD
    # ###################################################################################
    if database_is_at_head_v1(database_url, alembic_cfg):
        print(f"Database already at head: {safe_url}")
        return

    command.upgrade(alembic_cfg, "head")
    print(f"Database migrated to head: {safe_url}")


if __name__ == "__main__":
    main()
