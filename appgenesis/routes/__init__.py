
from appgenesis.routes.auth import router as auth_router
from appgenesis.routes.entities import router as entity_router
from appgenesis.routes.profile import router as profile_router
from appgenesis.routes.users import router as user_router
from appgenesis.routes.webhooks import router as webhook_router

__all__ = [
    "auth_router",
    "entity_router",
    "profile_router",
    "user_router",
    "webhook_router",
]
