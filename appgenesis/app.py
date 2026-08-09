
from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from appgenesis.config.settings import settings

logger = logging.getLogger(__name__)
from appgenesis.routes.auth import router as auth_router
from appgenesis.routes.empresa import router as empresa_router
from appgenesis.routes.entities import router as entity_router
from appgenesis.routes.landing import router as landing_router
from appgenesis.routes.profile import router as profile_router
from appgenesis.routes.users import router as user_router
from appgenesis.routes.webhooks import router as webhook_router


def create_app() -> FastAPI:
    app = FastAPI(title="AppGenesis User Admin")
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
    is_production = os.getenv("PRODUCTION", "").lower() in ("true", "1", "yes")

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.APP_SECRET_KEY,
        same_site="lax",
        https_only=is_production,
    )

    @app.get("/health")
    async def health_check():
        try:
            from appgenesis.db.session import SessionLocal
            session = SessionLocal()
            try:
                session.execute(text("SELECT 1"))
                return JSONResponse(
                    {"status": "healthy", "version": "1.0"},
                    status_code=200
                )
            finally:
                session.close()
        except Exception as exc:
            logger.error("Health check failed: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Service unavailable"
            )

    app.include_router(landing_router)
    app.include_router(auth_router)
    app.include_router(profile_router)
    app.include_router(webhook_router)
    app.include_router(entity_router)
    app.include_router(empresa_router)
    app.include_router(user_router)
    return app
