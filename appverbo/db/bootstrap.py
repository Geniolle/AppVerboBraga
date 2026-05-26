from __future__ import annotations

import re
import unicodedata
from typing import Any

from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.orm import Session

from appverbo.config.settings import settings
from appverbo.db.session import SessionLocal, engine
from appverbo.models import AdminDefinition, Profile


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
        if "city" not in existing_columns:
            connection.execute(text("ALTER TABLE entities ADD COLUMN city VARCHAR(120)"))
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
            select(Profile).where(func.lower(Profile.name).in_(settings.ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED))
        ).scalars().all()
        existing_by_normalized_name = {
            normalize_profile_name(profile.name): profile for profile in existing_profiles
        }

        changed = False
        for choice in settings.GLOBAL_PROFILE_CHOICES:
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


# ###################################################################################
# (B1) DEFINICOES DEFAULT - TITULO DO PROCESSO ADMINISTRATIVO
# ###################################################################################

ADMIN_PROCESS_TITLE_DEFINITION_DEFAULTS_V1: tuple[dict[str, str | tuple[str, ...]], ...] = (
    {
        "parameter_name": "TITULO PROCESSO TAMANHO",
        "parameter_type": "tamanho",
        "initial_value": "20",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "titulo processo tamanho",
            "titulo do processo tamanho",
            "titulo tamanho",
        ),
    },
    {
        "parameter_name": "TITULO PROCESSO FONTE",
        "parameter_type": "fonte",
        "initial_value": "Segoe UI",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "titulo processo fonte",
            "titulo do processo fonte",
            "titulo fonte",
        ),
    },
    {
        "parameter_name": "TITULO PROCESSO COR",
        "parameter_type": "cor",
        "initial_value": "#0F172A",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "titulo processo cor",
            "titulo do processo cor",
            "titulo cor",
        ),
    },
    {
        "parameter_name": "CARD ITEM TEXTO TAMANHO",
        "parameter_type": "tamanho",
        "initial_value": "12",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "card item texto tamanho",
            "item card texto tamanho",
            "item texto tamanho",
        ),
    },
    {
        "parameter_name": "CARD ITEM TEXTO FONTE",
        "parameter_type": "fonte",
        "initial_value": "Inter, \"Segoe UI\", sans-serif",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "card item texto fonte",
            "item card texto fonte",
            "item texto fonte",
        ),
    },
    {
        "parameter_name": "CARD ITEM TEXTO COR",
        "parameter_type": "cor",
        "initial_value": "#0F1F3A",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "card item texto cor",
            "item card texto cor",
            "item texto cor",
        ),
    },
    {
        "parameter_name": "CARD ITEM TEXTO PESO",
        "parameter_type": "tamanho",
        "initial_value": "500",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "card item texto peso",
            "item card texto peso",
            "item texto peso",
        ),
    },
    {
        "parameter_name": "CARD CABECALHO TEXTO COR",
        "parameter_type": "cor",
        "initial_value": "#000000",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "card cabecalho texto cor",
            "cabecalho texto cor",
            "header texto cor",
        ),
    },
    {
        "parameter_name": "BARRA CABECALHO COR",
        "parameter_type": "cor",
        "initial_value": "#334A62",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "barra cabecalho cor",
            "barra do cabecalho cor",
            "topbar cor",
            "header bar color",
        ),
    },
    {
        "parameter_name": "BARRA LATERAL FUNDO COR",
        "parameter_type": "cor",
        "initial_value": "#F3F3F4",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "barra lateral fundo cor",
            "sidebar fundo cor",
            "sidebar background color",
        ),
    },
    {
        "parameter_name": "BARRA LATERAL ITEM ATIVO FUNDO COR",
        "parameter_type": "cor",
        "initial_value": "#E4E6EA",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "barra lateral item ativo fundo cor",
            "sidebar item ativo fundo cor",
            "sidebar active background color",
        ),
    },
    {
        "parameter_name": "BARRA LATERAL TEXTO COR",
        "parameter_type": "cor",
        "initial_value": "#5C6572",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "barra lateral texto cor",
            "sidebar texto cor",
            "sidebar text color",
        ),
    },
    {
        "parameter_name": "BARRA LATERAL TEXTO TAMANHO",
        "parameter_type": "tamanho",
        "initial_value": "14",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "barra lateral texto tamanho",
            "sidebar texto tamanho",
            "sidebar text size",
        ),
    },
    {
        "parameter_name": "BARRA LATERAL TEXTO FONTE",
        "parameter_type": "fonte",
        "initial_value": "\"Segoe UI\", Tahoma, Arial, sans-serif",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "barra lateral texto fonte",
            "barra lateral tipo de letra",
            "sidebar texto fonte",
            "sidebar font family",
        ),
    },
    {
        "parameter_name": "BARRA LATERAL TEXTO PESO",
        "parameter_type": "tamanho",
        "initial_value": "500",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "barra lateral texto peso",
            "sidebar texto peso",
            "sidebar font weight",
        ),
    },
    {
        "parameter_name": "BARRA LATERAL ICONE COR",
        "parameter_type": "cor",
        "initial_value": "#5F6B7D",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "barra lateral icone cor",
            "sidebar icone cor",
            "sidebar icon color",
        ),
    },
    {
        "parameter_name": "BARRA LATERAL SECAO TEXTO COR",
        "parameter_type": "cor",
        "initial_value": "#808792",
        "process_name": "Geral",
        "subprocess_name": "Geral",
        "status": "active",
        "aliases": (
            "barra lateral secao texto cor",
            "sidebar secao texto cor",
            "sidebar section text color",
        ),
    },
)


def _normalize_definition_lookup_text_v1(value: object) -> str:
    clean_value = " ".join(str(value or "").strip().split()).lower()
    normalized = unicodedata.normalize("NFD", clean_value)
    return "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )


def ensure_admin_process_title_default_definitions_v1() -> None:
    inspector = inspect(engine)
    try:
        table_names = set(inspector.get_table_names())
    except NoSuchTableError:
        return
    if "admin_definitions" not in table_names:
        return

    with SessionLocal() as session:
        rows = session.execute(select(AdminDefinition)).scalars().all()
        changed = False

        for default_row in ADMIN_PROCESS_TITLE_DEFINITION_DEFAULTS_V1:
            parameter_type = _normalize_definition_lookup_text_v1(default_row.get("parameter_type"))
            process_name = _normalize_definition_lookup_text_v1(default_row.get("process_name"))
            subprocess_name = _normalize_definition_lookup_text_v1(default_row.get("subprocess_name"))
            aliases = tuple(
                str(alias)
                for alias in default_row.get("aliases", ())
                if str(alias or "").strip()
            )
            normalized_aliases = {
                _normalize_definition_lookup_text_v1(alias)
                for alias in aliases
            }
            normalized_aliases.add(
                _normalize_definition_lookup_text_v1(default_row.get("parameter_name"))
            )

            has_match = any(
                _normalize_definition_lookup_text_v1(row.parameter_type) == parameter_type
                and _normalize_definition_lookup_text_v1(row.process_name) == process_name
                and _normalize_definition_lookup_text_v1(row.subprocess_name) == subprocess_name
                and _normalize_definition_lookup_text_v1(row.parameter_name) in normalized_aliases
                for row in rows
            )
            if has_match:
                continue

            record = AdminDefinition(
                parameter_name=str(default_row.get("parameter_name") or "").strip(),
                parameter_type=str(default_row.get("parameter_type") or "").strip(),
                initial_value=str(default_row.get("initial_value") or "").strip(),
                process_name=str(default_row.get("process_name") or "").strip(),
                subprocess_name=str(default_row.get("subprocess_name") or "").strip(),
                status=str(default_row.get("status") or "active").strip() or "active",
            )
            session.add(record)
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

        max_capacity = settings.ENTITY_INTERNAL_NUMBER_MAX - settings.ENTITY_INTERNAL_NUMBER_MIN + 1
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
                    == settings.ENTITY_PROFILE_SCOPE_OWNER)
            ),
            None,
        )

        for row in rows:
            row_number = getattr(row, "internal_number", None)
            if not isinstance(row_number, int):
                has_invalid_number = True
                break
            if row_number < settings.ENTITY_INTERNAL_NUMBER_MIN or row_number > settings.ENTITY_INTERNAL_NUMBER_MAX:
                has_invalid_number = True
                break
            if row_number in seen_numbers:
                has_duplicate_number = True
                break
            seen_numbers.add(row_number)

        if owner_row is not None:
            owner_number = getattr(owner_row, "internal_number", None)
            owner_number_is_minimum = owner_number == settings.ENTITY_INTERNAL_NUMBER_MIN

        if not has_invalid_number and not has_duplicate_number and owner_number_is_minimum:
            return

        connection.execute(text("UPDATE entities SET internal_number = NULL"))

        next_number = settings.ENTITY_INTERNAL_NUMBER_MIN
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
            func.lower(Profile.name).in_(settings.ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED),
        )
       .order_by(Profile.id.asc())
    ).all()

    row_by_normalized_name: dict[str, Any] = {}
    for row in profile_rows:
        normalized_name = normalize_profile_name(row.name)
        if normalized_name not in row_by_normalized_name:
            row_by_normalized_name[normalized_name] = row

    profiles_for_form: list[dict[str, Any]] = []
    for choice in settings.GLOBAL_PROFILE_CHOICES:
        row = row_by_normalized_name.get(normalize_profile_name(choice["name"]))
        if row is None:
            continue
        profiles_for_form.append({"id": row.id, "name": choice["name"]})
    return profiles_for_form
