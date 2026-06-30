from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from appverbo.config.settings import settings

# ###################################################################################
# (1) CONFIGURAÇÃO DO ENGINE SQLALCHEMY
# ###################################################################################
_database_url = make_url(settings.DATABASE_URL)
_engine_kwargs = {
    "future": True,
}

if _database_url.get_backend_name() != "sqlite":
    _engine_kwargs.update(
        {
            "pool_size": max(1, int(settings.DB_POOL_SIZE)),
            "max_overflow": max(0, int(settings.DB_MAX_OVERFLOW)),
            "pool_timeout": max(1, int(settings.DB_POOL_TIMEOUT_SECONDS)),
            "pool_recycle": max(1, int(settings.DB_POOL_RECYCLE_SECONDS)),
            "pool_pre_ping": bool(settings.DB_POOL_PRE_PING),
        }
    )

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
