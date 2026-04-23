from __future__ import annotations

import base64
import hashlib
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, delete, func, inspect, select, text, update
from sqlalchemy.exc import IntegrityError, NoSuchTableError
from sqlalchemy.orm import Session, sessionmaker
from starlette.middleware.sessions import SessionMiddleware

from membrisia import (
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


def _env_bool(name: str, default: bool) -> bool:
    raw_value = (os.getenv(name, "") or "").strip().lower()
    if not raw_value:
        return default
    return raw_value in {"1", "true", "yes", "on", "sim"}


def _env_int(name: str, default: int) -> int:
    raw_value = (os.getenv(name, "") or "").strip()
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
STATIC_DIR = BASE_DIR / "static"
ENTITY_LOGOS_DIR = STATIC_DIR / "entities"
ENTITY_LOGOS_DIR.mkdir(parents=True, exist_ok=True)

MAX_ENTITY_LOGO_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_ENTITY_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
LOGO_CONTENT_TYPE_EXTENSION = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY") or secrets.token_urlsafe(32)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
ADMIN_LOGIN_EMAIL = (os.getenv("ADMIN_LOGIN_EMAIL", "admin@appverbo.local") or "").strip().lower()
ADMIN_PROFILE_NAMES = tuple(
    name.strip().lower()
    for name in (os.getenv("ADMIN_PROFILE_NAMES", "admin,administrador") or "").split(",")
    if name.strip()
)
ENTITY_SUPERUSER_PROFILE_NAME = (
    os.getenv("ENTITY_SUPERUSER_PROFILE_NAME", "SUPER USER") or "SUPER USER"
).strip()
WHATSAPP_GRAPH_API_VERSION = (os.getenv("WHATSAPP_GRAPH_API_VERSION", "v22.0") or "v22.0").strip()
WHATSAPP_ACCESS_TOKEN = (os.getenv("WHATSAPP_ACCESS_TOKEN", "") or "").strip()
WHATSAPP_PHONE_NUMBER_ID = (os.getenv("WHATSAPP_PHONE_NUMBER_ID", "") or "").strip()
WHATSAPP_TEMPLATE_NAME = (os.getenv("WHATSAPP_TEMPLATE_NAME", "") or "").strip()
WHATSAPP_TEMPLATE_LANGUAGE = (os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", "pt_PT") or "pt_PT").strip()
WHATSAPP_WEBHOOK_VERIFY_TOKEN = (os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "") or "").strip()
APP_PUBLIC_URL = (os.getenv("APP_PUBLIC_URL", "") or "").strip().rstrip("/")
USER_INVITE_TTL_HOURS = _env_int("USER_INVITE_TTL_HOURS", 72)
SMTP_HOST = (os.getenv("SMTP_HOST", "") or "").strip()
SMTP_PORT = _env_int("SMTP_PORT", 587)
SMTP_USERNAME = (os.getenv("SMTP_USERNAME", "") or "").strip()
SMTP_PASSWORD = (os.getenv("SMTP_PASSWORD", "") or "").strip()
SMTP_FROM_EMAIL = (os.getenv("SMTP_FROM_EMAIL", "") or "").strip()
SMTP_FROM_NAME = (os.getenv("SMTP_FROM_NAME", "AppVerboBraga") or "AppVerboBraga").strip()
SMTP_USE_TLS = _env_bool("SMTP_USE_TLS", True)

ALLOWED_ACCOUNT_STATUS = {
    UserAccountStatus.ACTIVE.value,
    UserAccountStatus.PENDING.value,
    UserAccountStatus.INACTIVE.value,
    UserAccountStatus.BLOCKED.value,
}
ENTITY_PROFILE_SCOPE_OWNER = "owner"
ENTITY_PROFILE_SCOPE_LEGADO = "legado"
ALLOWED_ENTITY_PROFILE_SCOPE = {
    ENTITY_PROFILE_SCOPE_OWNER,
    ENTITY_PROFILE_SCOPE_LEGADO,
}
ENTITY_INTERNAL_NUMBER_MIN = 1000
ENTITY_INTERNAL_NUMBER_MAX = 9999
GLOBAL_PROFILE_CHOICES = (
    {"name": "ADMIN", "description": "Perfil administrativo global."},
    {"name": "SUPER USER", "description": "Perfil com permissoes elevadas."},
    {"name": "USER", "description": "Perfil base de utilizador."},
)
ALLOWED_GLOBAL_PROFILE_NAMES = tuple(choice["name"] for choice in GLOBAL_PROFILE_CHOICES)
ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED = tuple(
    choice["name"].strip().lower() for choice in GLOBAL_PROFILE_CHOICES
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def ensure_entities_optional_columns() -> None:
    inspector = inspect(engine)
    try:
        existing_columns = {column["name"] for column in inspector.get_columns("entities")}
    except NoSuchTableError:
        return

    with engine.begin() as connection:
        if "internal_number" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN internal_number INTEGER"))
        if "tax_id" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN tax_id VARCHAR(40)"))
        if "email" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN email VARCHAR(150)"))
        if "responsible_name" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN responsible_name VARCHAR(200)"))
        if "door_number" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN door_number VARCHAR(30)"))
        if "address" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN address VARCHAR(255)"))
        if "freguesia" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN freguesia VARCHAR(120)"))
        if "postal_code" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN postal_code VARCHAR(30)"))
        if "country" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN country VARCHAR(120)"))
        if "phone" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN phone VARCHAR(30)"))
        if "logo_url" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN logo_url TEXT"))
        if "profile_scope" not in existing_columns:
            connection.execute(
                text("ALTER TABLE entities ADD COLUMN profile_scope VARCHAR(20) NOT NULL DEFAULT 'legado'")
            )

        if engine.dialect.name == "postgresql":
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_entities_internal_number "
                    "ON entities (internal_number) WHERE internal_number IS NOT NULL"
                )
            )
        else:
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_entities_internal_number "
                    "ON entities (internal_number)"
                )
            )
        try:
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_entities_single_owner_scope "
                    "ON entities (profile_scope) WHERE profile_scope = 'owner'"
                )
            )
        except Exception:
            # Fallback: aplicação já valida unicidade de owner em create/update.
            pass


def ensure_members_optional_columns() -> None:
    inspector = inspect(engine)
    try:
        existing_columns = {column["name"] for column in inspector.get_columns("members")}
    except NoSuchTableError:
        return
    missing_column_ddl = {
        "freguesia": "ALTER TABLE members ADD COLUMN freguesia VARCHAR(120)",
        "whatsapp_verification_status": "ALTER TABLE members ADD COLUMN whatsapp_verification_status VARCHAR(20) NOT NULL DEFAULT 'unknown'",
        "whatsapp_notice_opt_in": "ALTER TABLE members ADD COLUMN whatsapp_notice_opt_in BOOLEAN NOT NULL DEFAULT FALSE",
        "whatsapp_last_check_at": "ALTER TABLE members ADD COLUMN whatsapp_last_check_at TIMESTAMP",
        "whatsapp_last_error": "ALTER TABLE members ADD COLUMN whatsapp_last_error TEXT",
        "whatsapp_last_wa_id": "ALTER TABLE members ADD COLUMN whatsapp_last_wa_id VARCHAR(64)",
        "whatsapp_last_message_id": "ALTER TABLE members ADD COLUMN whatsapp_last_message_id VARCHAR(128)",
        "training_discipulado_verbo_vida": "ALTER TABLE members ADD COLUMN training_discipulado_verbo_vida BOOLEAN NOT NULL DEFAULT FALSE",
        "training_ebvv": "ALTER TABLE members ADD COLUMN training_ebvv BOOLEAN NOT NULL DEFAULT FALSE",
        "training_rhema": "ALTER TABLE members ADD COLUMN training_rhema BOOLEAN NOT NULL DEFAULT FALSE",
        "training_escola_ministerial": "ALTER TABLE members ADD COLUMN training_escola_ministerial BOOLEAN NOT NULL DEFAULT FALSE",
        "training_escola_missoes": "ALTER TABLE members ADD COLUMN training_escola_missoes BOOLEAN NOT NULL DEFAULT FALSE",
        "training_outros": "ALTER TABLE members ADD COLUMN training_outros VARCHAR(255)",
        "profile_custom_fields": "ALTER TABLE members ADD COLUMN profile_custom_fields TEXT",
    }

    with engine.begin() as connection:
        for column_name, ddl in missing_column_ddl.items():
            if column_name in existing_columns:
                continue
            connection.execute(text(ddl))


def ensure_sidebar_menu_settings_table() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sidebar_menu_settings (
                    menu_key VARCHAR(50) PRIMARY KEY,
                    menu_label VARCHAR(120) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                    menu_config TEXT
                )
                """
            )
        )

    inspector = inspect(engine)
    try:
        existing_columns = {column["name"] for column in inspector.get_columns("sidebar_menu_settings")}
    except NoSuchTableError:
        return

    if "menu_config" in existing_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE sidebar_menu_settings ADD COLUMN menu_config TEXT"))


def normalize_profile_name(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).lower()


def ensure_required_global_profiles() -> None:
    inspector = inspect(engine)
    try:
        table_names = set(inspector.get_table_names())
    except NoSuchTableError:
        return
    if "profiles" not in table_names:
        return

    with SessionLocal() as session:
        existing_profiles = session.execute(
            select(Profile).where(func.lower(Profile.name).in_(ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED))
        ).scalars().all()
        existing_by_normalized_name = {
            normalize_profile_name(profile.name): profile for profile in existing_profiles
        }

        changed = False
        for choice in GLOBAL_PROFILE_CHOICES:
            normalized_name = normalize_profile_name(choice["name"])
            profile = existing_by_normalized_name.get(normalized_name)
            if profile is None:
                session.add(
                    Profile(
                        name=choice["name"],
                        description=choice["description"],
                        is_active=True,
                    )
                )
                changed = True
                continue

            if not profile.is_active:
                profile.is_active = True
                changed = True
            if not (profile.description or "").strip():
                profile.description = choice["description"]
                changed = True

        if changed:
            session.commit()


def normalize_entities_internal_numbers() -> None:
    inspector = inspect(engine)
    try:
        table_names = set(inspector.get_table_names())
    except NoSuchTableError:
        return
    if "entities" not in table_names:
        return

    with engine.begin() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    id,
                    profile_scope,
                    internal_number,
                    created_at
                FROM entities
                ORDER BY
                    CASE
                        WHEN lower(coalesce(profile_scope, '')) = 'owner' THEN 0
                        ELSE 1
                    END,
                    CASE
                        WHEN created_at IS NULL THEN 1
                        ELSE 0
                    END,
                    created_at ASC,
                    id ASC
                """
            )
        ).all()

        if not rows:
            return

        max_capacity = ENTITY_INTERNAL_NUMBER_MAX - ENTITY_INTERNAL_NUMBER_MIN + 1
        if len(rows) > max_capacity:
            return

        has_invalid_number = False
        seen_numbers: set[int] = set()
        has_duplicate_number = False
        owner_number_is_minimum = True
        owner_row = next(
            (
                row
                for row in rows
                if (str(getattr(row, "profile_scope", "") or "").strip().lower()
                    == ENTITY_PROFILE_SCOPE_OWNER)
            ),
            None,
        )

        for row in rows:
            row_number = getattr(row, "internal_number", None)
            if not isinstance(row_number, int):
                has_invalid_number = True
                break
            if row_number < ENTITY_INTERNAL_NUMBER_MIN or row_number > ENTITY_INTERNAL_NUMBER_MAX:
                has_invalid_number = True
                break
            if row_number in seen_numbers:
                has_duplicate_number = True
                break
            seen_numbers.add(row_number)

        if owner_row is not None:
            owner_number = getattr(owner_row, "internal_number", None)
            owner_number_is_minimum = owner_number == ENTITY_INTERNAL_NUMBER_MIN

        if not has_invalid_number and not has_duplicate_number and owner_number_is_minimum:
            return

        connection.execute(text("UPDATE entities SET internal_number = NULL"))

        next_number = ENTITY_INTERNAL_NUMBER_MIN
        for row in rows:
            connection.execute(
                text("UPDATE entities SET internal_number = :number WHERE id = :entity_id"),
                {"number": next_number, "entity_id": int(row.id)},
            )
            next_number += 1


def get_allowed_global_profiles_for_form(session: Session) -> list[dict[str, Any]]:
    profile_rows = session.execute(
        select(Profile.id, Profile.name)
       .where(
            Profile.is_active.is_(True),
            func.lower(Profile.name).in_(ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED),
        )
       .order_by(Profile.id.asc())
    ).all()

    row_by_normalized_name: dict[str, Any] = {}
    for row in profile_rows:
        normalized_name = normalize_profile_name(row.name)
        if normalized_name not in row_by_normalized_name:
            row_by_normalized_name[normalized_name] = row

    profiles_for_form: list[dict[str, Any]] = []
    for choice in GLOBAL_PROFILE_CHOICES:
        row = row_by_normalized_name.get(normalize_profile_name(choice["name"]))
        if row is None:
            continue
        profiles_for_form.append({"id": row.id, "name": choice["name"]})
    return profiles_for_form


ensure_entities_optional_columns()
ensure_members_optional_columns()
ensure_sidebar_menu_settings_table()
ensure_required_global_profiles()
normalize_entities_internal_numbers()

app = FastAPI(title="AppVerboBraga User Admin")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(
    SessionMiddleware,
    secret_key=APP_SECRET_KEY,
    same_site="lax",
    https_only=False,
)

oauth = OAuth()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        client_kwargs={"scope": "openid email profile"},
    )
if MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET:
    oauth.register(
        name="microsoft",
        server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
        client_id=MICROSOFT_CLIENT_ID,
        client_secret=MICROSOFT_CLIENT_SECRET,
        client_kwargs={"scope": "openid email profile"},
    )
if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    oauth.register(
        name="github",
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        client_kwargs={"scope": "read:user user:email"},
    )
