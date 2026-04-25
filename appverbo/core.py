from __future__ import annotations

from pathlib import Path

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI
from fastapi import File, Form, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, delete, func, inspect, select, text, update
from sqlalchemy.exc import IntegrityError, NoSuchTableError
from sqlalchemy.orm import Session, sessionmaker
from starlette.middleware.sessions import SessionMiddleware

from appverbo.config.settings import settings
from appverbo.db.bootstrap import (
    ensure_entities_optional_columns,
    ensure_members_optional_columns,
    ensure_required_global_profiles,
    ensure_sidebar_menu_settings_table,
    get_allowed_global_profiles_for_form,
    normalize_entities_internal_numbers,
    normalize_profile_name,
)
from appverbo.db.session import SessionLocal, engine
from appverbo.integrations.oauth import oauth
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)

BASE_DIR = settings.BASE_DIR
STATIC_DIR = settings.STATIC_DIR
ENTITY_LOGOS_DIR = settings.ENTITY_LOGOS_DIR

MAX_ENTITY_LOGO_SIZE_BYTES = settings.MAX_ENTITY_LOGO_SIZE_BYTES
ALLOWED_ENTITY_LOGO_EXTENSIONS = settings.ALLOWED_ENTITY_LOGO_EXTENSIONS
LOGO_CONTENT_TYPE_EXTENSION = settings.LOGO_CONTENT_TYPE_EXTENSION

DATABASE_URL = settings.DATABASE_URL
APP_SECRET_KEY = settings.APP_SECRET_KEY

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
MICROSOFT_CLIENT_ID = settings.MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET = settings.MICROSOFT_CLIENT_SECRET
GITHUB_CLIENT_ID = settings.GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET = settings.GITHUB_CLIENT_SECRET

ADMIN_LOGIN_EMAIL = settings.ADMIN_LOGIN_EMAIL
ADMIN_PROFILE_NAMES = settings.ADMIN_PROFILE_NAMES
ENTITY_SUPERUSER_PROFILE_NAME = settings.ENTITY_SUPERUSER_PROFILE_NAME

WHATSAPP_GRAPH_API_VERSION = settings.WHATSAPP_GRAPH_API_VERSION
WHATSAPP_ACCESS_TOKEN = settings.WHATSAPP_ACCESS_TOKEN
WHATSAPP_PHONE_NUMBER_ID = settings.WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_TEMPLATE_NAME = settings.WHATSAPP_TEMPLATE_NAME
WHATSAPP_TEMPLATE_LANGUAGE = settings.WHATSAPP_TEMPLATE_LANGUAGE
WHATSAPP_WEBHOOK_VERIFY_TOKEN = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
APP_PUBLIC_URL = settings.APP_PUBLIC_URL
USER_INVITE_TTL_HOURS = settings.USER_INVITE_TTL_HOURS

SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USERNAME = settings.SMTP_USERNAME
SMTP_PASSWORD = settings.SMTP_PASSWORD
SMTP_FROM_EMAIL = settings.SMTP_FROM_EMAIL
SMTP_FROM_NAME = settings.SMTP_FROM_NAME
SMTP_USE_TLS = settings.SMTP_USE_TLS

ALLOWED_ACCOUNT_STATUS = settings.ALLOWED_ACCOUNT_STATUS
ENTITY_PROFILE_SCOPE_OWNER = settings.ENTITY_PROFILE_SCOPE_OWNER
ENTITY_PROFILE_SCOPE_LEGADO = settings.ENTITY_PROFILE_SCOPE_LEGADO
ALLOWED_ENTITY_PROFILE_SCOPE = settings.ALLOWED_ENTITY_PROFILE_SCOPE
ENTITY_INTERNAL_NUMBER_MIN = settings.ENTITY_INTERNAL_NUMBER_MIN
ENTITY_INTERNAL_NUMBER_MAX = settings.ENTITY_INTERNAL_NUMBER_MAX
GLOBAL_PROFILE_CHOICES = settings.GLOBAL_PROFILE_CHOICES
ALLOWED_GLOBAL_PROFILE_NAMES = settings.ALLOWED_GLOBAL_PROFILE_NAMES
ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED = settings.ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED

templates = Jinja2Templates(directory=str(Path(BASE_DIR) / "templates"))
app = FastAPI(title="AppVerboBraga User Admin")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(
    SessionMiddleware,
    secret_key=APP_SECRET_KEY,
    same_site="lax",
    https_only=False,
)

__all__ = [
    "OAuth",
    "OAuthError",
    "Request",
    "UploadFile",
    "File",
    "Form",
    "Query",
    "status",
    "HTMLResponse",
    "JSONResponse",
    "PlainTextResponse",
    "RedirectResponse",
    "create_engine",
    "delete",
    "func",
    "inspect",
    "select",
    "text",
    "update",
    "IntegrityError",
    "NoSuchTableError",
    "Session",
    "sessionmaker",
    "BASE_DIR",
    "STATIC_DIR",
    "ENTITY_LOGOS_DIR",
    "MAX_ENTITY_LOGO_SIZE_BYTES",
    "ALLOWED_ENTITY_LOGO_EXTENSIONS",
    "LOGO_CONTENT_TYPE_EXTENSION",
    "DATABASE_URL",
    "APP_SECRET_KEY",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "MICROSOFT_CLIENT_ID",
    "MICROSOFT_CLIENT_SECRET",
    "GITHUB_CLIENT_ID",
    "GITHUB_CLIENT_SECRET",
    "ADMIN_LOGIN_EMAIL",
    "ADMIN_PROFILE_NAMES",
    "ENTITY_SUPERUSER_PROFILE_NAME",
    "WHATSAPP_GRAPH_API_VERSION",
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_TEMPLATE_NAME",
    "WHATSAPP_TEMPLATE_LANGUAGE",
    "WHATSAPP_WEBHOOK_VERIFY_TOKEN",
    "APP_PUBLIC_URL",
    "USER_INVITE_TTL_HOURS",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_FROM_EMAIL",
    "SMTP_FROM_NAME",
    "SMTP_USE_TLS",
    "ALLOWED_ACCOUNT_STATUS",
    "ENTITY_PROFILE_SCOPE_OWNER",
    "ENTITY_PROFILE_SCOPE_LEGADO",
    "ALLOWED_ENTITY_PROFILE_SCOPE",
    "ENTITY_INTERNAL_NUMBER_MIN",
    "ENTITY_INTERNAL_NUMBER_MAX",
    "GLOBAL_PROFILE_CHOICES",
    "ALLOWED_GLOBAL_PROFILE_NAMES",
    "ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED",
    "engine",
    "SessionLocal",
    "templates",
    "app",
    "oauth",
    "ensure_entities_optional_columns",
    "ensure_members_optional_columns",
    "ensure_required_global_profiles",
    "ensure_sidebar_menu_settings_table",
    "normalize_entities_internal_numbers",
    "normalize_profile_name",
    "get_allowed_global_profiles_for_form",
    "Entity",
    "Member",
    "MemberEntity",
    "MemberEntityStatus",
    "MemberStatus",
    "Profile",
    "User",
    "UserAccountStatus",
    "UserProfile",
]
