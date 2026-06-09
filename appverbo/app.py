from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from appverbo.config.settings import settings
from appverbo.routes.auth import router as auth_router
from appverbo.routes.entities import router as entity_router
from appverbo.routes.import_mt940 import router as import_mt940_router
from appverbo.routes.profile import router as profile_router
from appverbo.routes.users import router as user_router
from appverbo.routes.webhooks import router as webhook_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _stop_scheduler = None
    try:
        from appverbo.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        _stop_scheduler = stop_scheduler
    except ImportError as exc:
        logger.warning("Scheduler not started (missing dependency): %s", exc)
    try:
        yield
    finally:
        if _stop_scheduler is not None:
            _stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(title="AppVerboBraga User Admin", lifespan=_lifespan)
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.APP_SECRET_KEY,
        same_site="lax",
        https_only=False,
    )

    @app.middleware("http")
    async def log_create_user_request_v1(request, call_next):
        if request.method.upper() != "POST" or request.url.path != "/users/new":
            return await call_next(request)

        raw_body = await request.body()
        content_type = str(request.headers.get("content-type") or "")
        preview_text = ""
        if raw_body:
            try:
                preview_text = raw_body[:2000].decode("utf-8", errors="replace")
            except Exception:
                preview_text = "<decode-error>"

        logger.warning(
            "DEBUG /users/new request: query=%s content_type=%s content_length=%s referer=%s origin=%s body_preview=%r",
            str(request.url.query or ""),
            content_type,
            str(request.headers.get("content-length") or ""),
            str(request.headers.get("referer") or ""),
            str(request.headers.get("origin") or ""),
            preview_text,
        )

        async def receive():
            return {
                "type": "http.request",
                "body": raw_body,
                "more_body": False,
            }

        request._receive = receive
        response = await call_next(request)

        logger.warning(
            "DEBUG /users/new response: status=%s location=%s",
            getattr(response, "status_code", ""),
            str(response.headers.get("location") or ""),
        )
        return response

    # APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V2_START
    @app.middleware("http")
    async def appverbo_dynamic_no_store_middleware_v2(request, call_next):
        response = await call_next(request)
        request_path = str(request.url.path or "")

        if not request_path.startswith("/static"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["X-AppVerbo-Dynamic-Sync"] = "no-store-v2"

        return response

    # APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V2_END

    app.include_router(auth_router)
    app.include_router(profile_router)
    app.include_router(webhook_router)
    app.include_router(entity_router)
    app.include_router(user_router)
    app.include_router(import_mt940_router)
    return app
