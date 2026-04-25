from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from appverbo.config.settings import settings
from appverbo.routes.auth import router as auth_router
from appverbo.routes.entities import router as entity_router
from appverbo.routes.profile import router as profile_router
from appverbo.routes.users import router as user_router
from appverbo.routes.webhooks import router as webhook_router


def create_app() -> FastAPI:
    app = FastAPI(title="AppVerboBraga User Admin")
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.APP_SECRET_KEY,
        same_site="lax",
        https_only=False,
    )

    app.include_router(auth_router)
    app.include_router(profile_router)
    app.include_router(webhook_router)
    app.include_router(entity_router)
    app.include_router(user_router)
    return app
