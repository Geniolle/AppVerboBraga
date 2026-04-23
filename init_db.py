from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from dotenv import load_dotenv


def get_database_url() -> str:
    # Use env var for production; fallback to local SQLite for quick start.
    return os.getenv("DATABASE_URL", "sqlite:///app.db")


def main() -> None:
    load_dotenv()
    database_url = get_database_url()
    alembic_cfg = Config(str(Path(__file__).with_name("alembic.ini")))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(alembic_cfg, "head")
    safe_url = make_url(database_url).render_as_string(hide_password=True)
    print(f"Database migrated to head: {safe_url}")


if __name__ == "__main__":
    main()
