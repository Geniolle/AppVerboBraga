from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


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


@dataclass(frozen=True)
class Settings:
    BASE_DIR: Path
    STATIC_DIR: Path
    ENTITY_LOGOS_DIR: Path

    MAX_ENTITY_LOGO_SIZE_BYTES: int
    ALLOWED_ENTITY_LOGO_EXTENSIONS: set[str]
    LOGO_CONTENT_TYPE_EXTENSION: dict[str, str]

    DATABASE_URL: str
    APP_SECRET_KEY: str

    GOOGLE_CLIENT_ID: str | None
    GOOGLE_CLIENT_SECRET: str | None
    MICROSOFT_CLIENT_ID: str | None
    MICROSOFT_CLIENT_SECRET: str | None
    GITHUB_CLIENT_ID: str | None
    GITHUB_CLIENT_SECRET: str | None

    ADMIN_LOGIN_EMAIL: str
    ADMIN_PROFILE_NAMES: tuple[str, ...]
    ENTITY_SUPERUSER_PROFILE_NAME: str

    WHATSAPP_GRAPH_API_VERSION: str
    WHATSAPP_ACCESS_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_TEMPLATE_NAME: str
    WHATSAPP_TEMPLATE_LANGUAGE: str
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str

    APP_PUBLIC_URL: str
    USER_INVITE_TTL_HOURS: int

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str
    SMTP_USE_TLS: bool

    ALLOWED_ACCOUNT_STATUS: set[str]
    ENTITY_PROFILE_SCOPE_OWNER: str
    ENTITY_PROFILE_SCOPE_LEGADO: str
    ALLOWED_ENTITY_PROFILE_SCOPE: set[str]
    ENTITY_INTERNAL_NUMBER_MIN: int
    ENTITY_INTERNAL_NUMBER_MAX: int
    GLOBAL_PROFILE_CHOICES: tuple[dict[str, str], ...]
    ALLOWED_GLOBAL_PROFILE_NAMES: tuple[str, ...]
    ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED: tuple[str, ...]


def _build_settings() -> Settings:
    base_dir = Path(__file__).resolve().parents[2]
    load_dotenv(base_dir / ".env")
    static_dir = base_dir / "static"
    entity_logos_dir = static_dir / "entities"
    entity_logos_dir.mkdir(parents=True, exist_ok=True)

    global_profile_choices = (
        {"name": "ADMIN", "description": "Perfil administrativo global."},
        {"name": "SUPER USER", "description": "Perfil com permissoes elevadas."},
        {"name": "USER", "description": "Perfil base de utilizador."},
    )
    allowed_global_profile_names = tuple(choice["name"] for choice in global_profile_choices)

    return Settings(
        BASE_DIR=base_dir,
        STATIC_DIR=static_dir,
        ENTITY_LOGOS_DIR=entity_logos_dir,
        MAX_ENTITY_LOGO_SIZE_BYTES=5 * 1024 * 1024,
        ALLOWED_ENTITY_LOGO_EXTENSIONS={".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"},
        LOGO_CONTENT_TYPE_EXTENSION={
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/svg+xml": ".svg",
        },
        DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///app.db"),
        APP_SECRET_KEY=os.getenv("APP_SECRET_KEY") or secrets.token_urlsafe(32),
        GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID"),
        GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET"),
        MICROSOFT_CLIENT_ID=os.getenv("MICROSOFT_CLIENT_ID"),
        MICROSOFT_CLIENT_SECRET=os.getenv("MICROSOFT_CLIENT_SECRET"),
        GITHUB_CLIENT_ID=os.getenv("GITHUB_CLIENT_ID"),
        GITHUB_CLIENT_SECRET=os.getenv("GITHUB_CLIENT_SECRET"),
        ADMIN_LOGIN_EMAIL=(os.getenv("ADMIN_LOGIN_EMAIL", "admin@appverbo.local") or "").strip().lower(),
        ADMIN_PROFILE_NAMES=tuple(
            name.strip().lower()
            for name in (os.getenv("ADMIN_PROFILE_NAMES", "admin,administrador") or "").split(",")
            if name.strip()
        ),
        ENTITY_SUPERUSER_PROFILE_NAME=(
            os.getenv("ENTITY_SUPERUSER_PROFILE_NAME", "SUPER USER") or "SUPER USER"
        ).strip(),
        WHATSAPP_GRAPH_API_VERSION=(os.getenv("WHATSAPP_GRAPH_API_VERSION", "v22.0") or "v22.0").strip(),
        WHATSAPP_ACCESS_TOKEN=(os.getenv("WHATSAPP_ACCESS_TOKEN", "") or "").strip(),
        WHATSAPP_PHONE_NUMBER_ID=(os.getenv("WHATSAPP_PHONE_NUMBER_ID", "") or "").strip(),
        WHATSAPP_TEMPLATE_NAME=(os.getenv("WHATSAPP_TEMPLATE_NAME", "") or "").strip(),
        WHATSAPP_TEMPLATE_LANGUAGE=(os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", "pt_PT") or "pt_PT").strip(),
        WHATSAPP_WEBHOOK_VERIFY_TOKEN=(os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "") or "").strip(),
        APP_PUBLIC_URL=(os.getenv("APP_PUBLIC_URL", "") or "").strip().rstrip("/"),
        USER_INVITE_TTL_HOURS=_env_int("USER_INVITE_TTL_HOURS", 72),
        SMTP_HOST=(os.getenv("SMTP_HOST", "") or "").strip(),
        SMTP_PORT=_env_int("SMTP_PORT", 587),
        SMTP_USERNAME=(os.getenv("SMTP_USERNAME", "") or "").strip(),
        SMTP_PASSWORD=(os.getenv("SMTP_PASSWORD", "") or "").strip(),
        SMTP_FROM_EMAIL=(os.getenv("SMTP_FROM_EMAIL", "") or "").strip(),
        SMTP_FROM_NAME=(os.getenv("SMTP_FROM_NAME", "AppVerboBraga") or "AppVerboBraga").strip(),
        SMTP_USE_TLS=_env_bool("SMTP_USE_TLS", True),
        ALLOWED_ACCOUNT_STATUS={"active", "pending", "inactive", "blocked"},
        ENTITY_PROFILE_SCOPE_OWNER="owner",
        ENTITY_PROFILE_SCOPE_LEGADO="legado",
        ALLOWED_ENTITY_PROFILE_SCOPE={"owner", "legado"},
        ENTITY_INTERNAL_NUMBER_MIN=1000,
        ENTITY_INTERNAL_NUMBER_MAX=9999,
        GLOBAL_PROFILE_CHOICES=global_profile_choices,
        ALLOWED_GLOBAL_PROFILE_NAMES=allowed_global_profile_names,
        ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED=tuple(
            choice["name"].strip().lower() for choice in global_profile_choices
        ),
    )


settings = _build_settings()

