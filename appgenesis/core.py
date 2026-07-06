from __future__ import annotations

# NOTA (Fase 2 - refactor/appgenesis-process-architecture): este modulo e um hub de
# compatibilidade temporario. Ate a Fase 2, dezenas de ficheiros consumiam este modulo
# via "from appgenesis.core import *"; essas ocorrencias ja foram substituidas por
# imports explicitos. Constantes derivadas de settings ainda residem aqui (migracao
# para a sua origem real fica para uma fase futura). Novos ficheiros criados a partir
# desta fase NAO devem importar de appgenesis.core — importar diretamente da origem
# real do simbolo (appgenesis.models, appgenesis.config.settings, appgenesis.services.*, etc.).
#
# NOTA (Issue #28, 2026-07-06): mapeados 21 consumidores reais deste modulo em
# appgenesis/, scripts/ e tests/ (todos com imports nomeados explicitos, nenhum
# wildcard) — nao ha "zero consumidores" para justificar remocao deste ficheiro.
# A instancia FastAPI morta que existia aqui (app = FastAPI(...), com mount/
# middleware duplicados) foi removida: a aplicacao real e criada em
# appgenesis/app.py::create_app(), usada por web_app.py; nada importava "app"
# a partir daqui. Detalhe completo em docs/refactoring/issue-28-legacy-hubs-report.md.

from pathlib import Path

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import File, Form, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, delete, func, inspect, select, text, update
from sqlalchemy.exc import IntegrityError, NoSuchTableError
from sqlalchemy.orm import Session, sessionmaker

from appgenesis.config.settings import settings
from appgenesis.db.bootstrap import (
    ensure_entities_optional_columns,
    ensure_members_optional_columns,
    ensure_sidebar_menu_settings_table,
    normalize_entities_entity_numbers,
)
from appgenesis.db.session import SessionLocal, engine
from appgenesis.integrations.oauth import oauth
from appgenesis.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
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

ADMIN_LOGIN_EMAIL = settings.ADMIN_LOGIN_EMAIL
ADMIN_LOGIN_PASSWORD = settings.ADMIN_LOGIN_PASSWORD
ALLOWED_ACCOUNT_STATUS = settings.ALLOWED_ACCOUNT_STATUS
ENTITY_PROFILE_SCOPE_OWNER = settings.ENTITY_PROFILE_SCOPE_OWNER
ENTITY_PROFILE_SCOPE_LEGADO = settings.ENTITY_PROFILE_SCOPE_LEGADO
ALLOWED_ENTITY_PROFILE_SCOPE = settings.ALLOWED_ENTITY_PROFILE_SCOPE
ENTITY_NUMBER_MIN = settings.ENTITY_NUMBER_MIN
ENTITY_NUMBER_MAX = settings.ENTITY_NUMBER_MAX

templates = Jinja2Templates(directory=str(Path(BASE_DIR) / "templates"))

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
    "ADMIN_LOGIN_EMAIL",
    "ADMIN_LOGIN_PASSWORD",
    "ALLOWED_ACCOUNT_STATUS",
    "ENTITY_PROFILE_SCOPE_OWNER",
    "ENTITY_PROFILE_SCOPE_LEGADO",
    "ALLOWED_ENTITY_PROFILE_SCOPE",
    "ENTITY_NUMBER_MIN",
    "ENTITY_NUMBER_MAX",
    "engine",
    "SessionLocal",
    "templates",
    "oauth",
    "ensure_entities_optional_columns",
    "ensure_members_optional_columns",
    "ensure_sidebar_menu_settings_table",
    "normalize_entities_entity_numbers",
    "Entity",
    "Member",
    "MemberEntity",
    "MemberEntityStatus",
    "MemberStatus",
    "User",
    "UserAccountStatus",
]
