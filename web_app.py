from __future__ import annotations

from appverbo.core import app
from appverbo.routes.auth_routes import router as auth_router
from appverbo.routes.profile_routes import router as profile_router
from appverbo.routes.webhook_routes import router as webhook_router
from appverbo.routes.entity_routes import router as entity_router
from appverbo.routes.user_routes import router as user_router

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(webhook_router)
app.include_router(entity_router)
app.include_router(user_router)

