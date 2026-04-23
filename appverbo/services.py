from __future__ import annotations

import base64
import hmac
import hashlib
import json
import re
import secrets
import smtplib
import time
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from authlib.integrations.starlette_client import OAuthError
from fastapi import Request, UploadFile, status
from fastapi.responses import HTMLResponse
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
from appverbo.core import *  # noqa: F403,F401
from appverbo.menu_settings import (
    MENU_DOCUMENTOS_FIELD_LABELS,
    MENU_DOCUMENTOS_FIELD_OPTIONS,
    MENU_DOCUMENTOS_FIELDS_DEFAULT,
    get_sidebar_menu_settings,
    get_visible_sidebar_menu_keys,
)


def parse_profile_custom_fields(raw_value: Any) -> dict[str, str]:
    if not isinstance(raw_value, str):
        return {}
    clean_value = raw_value.strip()
    if not clean_value:
        return {}
    try:
        parsed = json.loads(clean_value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}

    normalized: dict[str, str] = {}
    for raw_key, raw_field_value in parsed.items():
        clean_key = str(raw_key or "").strip().lower()
        if not clean_key.startswith("custom_"):
            continue
        if not clean_key:
            continue
        clean_field_value = str(raw_field_value or "").strip()
        if not clean_field_value:
            continue
        normalized[clean_key] = clean_field_value
    return normalized


def serialize_profile_custom_fields(values: dict[str, str]) -> str | None:
    normalized: dict[str, str] = {}
    for raw_key, raw_value in (values or {}).items():
        clean_key = str(raw_key or "").strip().lower()
        if not clean_key.startswith("custom_"):
            continue
        if not clean_key:
            continue
        clean_value = str(raw_value or "").strip()
        if not clean_value:
            continue
        normalized[clean_key] = clean_value
    if not normalized:
        return None
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True)


def hash_password(raw_password: str) -> str:
    iterations = 390000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    digest_b64 = base64.b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_b64}${digest_b64}"


def verify_password(raw_password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations_text, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        expected_digest = base64.b64decode(digest_b64.encode("utf-8"))
    except (ValueError, TypeError):
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256", raw_password.encode("utf-8"), salt, iterations
    )
    return secrets.compare_digest(candidate_digest, expected_digest)


def _urlsafe_b64encode(raw_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")


def _urlsafe_b64decode(raw_value: str) -> bytes:
    clean_value = (raw_value or "").strip()
    if not clean_value:
        raise ValueError("Valor base64 vazio.")
    padding = "=" * (-len(clean_value) % 4)
    return base64.urlsafe_b64decode(clean_value + padding)


def build_user_invite_token(user_id: int, login_email: str) -> str:
    issued_at = int(time.time())
    payload = {
        "uid": int(user_id),
        "email": (login_email or "").strip().lower(),
        "iat": issued_at,
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_encoded = _urlsafe_b64encode(payload_json)
    signature = hmac.new(
        APP_SECRET_KEY.encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    signature_encoded = _urlsafe_b64encode(signature)
    return f"{payload_encoded}.{signature_encoded}"


def parse_user_invite_token(token: str) -> dict[str, Any] | None:
    clean_token = (token or "").strip()
    if "." not in clean_token:
        return None
    payload_encoded, signature_encoded = clean_token.split(".", 1)
    if not payload_encoded or not signature_encoded:
        return None

    expected_signature = hmac.new(
        APP_SECRET_KEY.encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    try:
        received_signature = _urlsafe_b64decode(signature_encoded)
    except ValueError:
        return None
    if not hmac.compare_digest(expected_signature, received_signature):
        return None

    try:
        payload_raw = _urlsafe_b64decode(payload_encoded)
        payload = json.loads(payload_raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    user_id = payload.get("uid")
    login_email = str(payload.get("email") or "").strip().lower()
    issued_at = payload.get("iat")
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    if not login_email:
        return None
    if not isinstance(issued_at, int) or issued_at <= 0:
        return None

    max_token_age = max(int(USER_INVITE_TTL_HOURS), 1) * 3600
    if int(time.time()) - issued_at > max_token_age:
        return None

    return {
        "uid": user_id,
        "email": login_email,
        "iat": issued_at,
    }


def build_user_invite_link(request: Request, token: str) -> str:
    base_url = APP_PUBLIC_URL or str(request.base_url).rstrip("/")
    return f"{base_url}/users/invite/accept?token={quote(token, safe='')}"


def send_user_invite_email(
    recipient_email: str,
    recipient_name: str,
    entity_name: str,
    invite_link: str,
    invited_by_name: str,
) -> tuple[bool, str]:
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        return False, "Configuração de email incompleta. Defina SMTP_HOST e SMTP_FROM_EMAIL."

    recipient = (recipient_email or "").strip().lower()
    if not recipient:
        return False, "Email do destinatário inválido."

    display_name = (recipient_name or "").strip() or recipient
    entity_display_name = (entity_name or "").strip() or "-"
    inviter_display_name = (invited_by_name or "").strip() or "Administrador"
    subject = "Convite para ativar conta no AppVerboBraga"

    html_body = (
        "<p>Olá,</p>"
        f"<p>Foi convidado por <strong>{inviter_display_name}</strong> para aceder à entidade "
        f"<strong>{entity_display_name}</strong> no AppVerboBraga.</p>"
        "<p>Para concluir o registo e definir a sua palavra-passe, use o link abaixo:</p>"
        f"<p><a href=\"{invite_link}\">{invite_link}</a></p>"
        "<p>Se não reconhece este convite, ignore este email.</p>"
    )
    text_body = (
        f"Olá {display_name},\n\n"
        f"Foi convidado por {inviter_display_name} para aceder à entidade {entity_display_name} no AppVerboBraga.\n"
        "Para concluir o registo e definir a sua palavra-passe, use o link abaixo:\n"
        f"{invite_link}\n\n"
        "Se não reconhece este convite, ignore este email.\n"
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    message["To"] = recipient
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp_client:
            if SMTP_USE_TLS:
                smtp_client.starttls()
            if SMTP_USERNAME:
                smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp_client.send_message(message)
    except Exception as exc:
        return False, f"Falha ao enviar email de convite: {exc!s}"

    return True, ""

def owner_entity_exists(session: Session) -> bool:
    owner_id = session.scalar(
        select(Entity.id)
       .where(Entity.profile_scope == ENTITY_PROFILE_SCOPE_OWNER)
       .limit(1)
    )
    return owner_id is not None


def user_has_owner_entity_membership(session: Session, user_id: int) -> bool:
    owner_link_id = session.scalar(
        select(MemberEntity.id)
       .join(Entity, Entity.id == MemberEntity.entity_id)
       .join(User, User.member_id == MemberEntity.member_id)
       .where(
            User.id == user_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.profile_scope == ENTITY_PROFILE_SCOPE_OWNER,
            Entity.is_active.is_(True),
        )
       .limit(1)
    )
    return owner_link_id is not None


def _get_user_linked_entity_ids(
    session: Session,
    user_id: int,
    *,
    require_active_entity: bool = True,
) -> list[int]:
    stmt = (
        select(MemberEntity.entity_id)
       .join(User, User.member_id == MemberEntity.member_id)
       .join(Entity, Entity.id == MemberEntity.entity_id)
       .where(
            User.id == user_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
       .order_by(MemberEntity.id.asc())
    )
    if require_active_entity:
        stmt = stmt.where(Entity.is_active.is_(True))

    raw_ids = session.execute(stmt).scalars().all()
    ordered_unique_ids: list[int] = []
    seen_ids: set[int] = set()
    for raw_id in raw_ids:
        parsed_id = int(raw_id)
        if parsed_id in seen_ids:
            continue
        seen_ids.add(parsed_id)
        ordered_unique_ids.append(parsed_id)
    return ordered_unique_ids


def get_user_entity_permissions(
    session: Session,
    user_id: int,
    login_email: str,
    selected_entity_id: int | None = None,
) -> dict[str, Any]:
    is_admin = is_admin_user(session, user_id, login_email)
    has_owner_membership = user_has_owner_entity_membership(session, user_id)
    has_bootstrap_owner_gap = is_admin and not owner_entity_exists(session)
    can_manage_all_entities = is_admin and (has_owner_membership or has_bootstrap_owner_gap)

    linked_entity_ids = _get_user_linked_entity_ids(
        session,
        user_id,
        require_active_entity=True,
    )
    linked_entity_ids_set = set(linked_entity_ids)

    resolved_selected_entity_id: int | None = None
    if selected_entity_id is not None:
        selected_entity = session.get(Entity, selected_entity_id)
        if selected_entity is not None and selected_entity.is_active:
            if can_manage_all_entities or selected_entity_id in linked_entity_ids_set:
                resolved_selected_entity_id = int(selected_entity_id)
    if resolved_selected_entity_id is None and linked_entity_ids:
        resolved_selected_entity_id = linked_entity_ids[0]
    if resolved_selected_entity_id is None and can_manage_all_entities:
        first_active_entity_id = session.scalar(
            select(Entity.id)
           .where(Entity.is_active.is_(True))
           .order_by(Entity.name.asc())
           .limit(1)
        )
        if first_active_entity_id is not None:
            resolved_selected_entity_id = int(first_active_entity_id)

    if can_manage_all_entities:
        allowed_entity_ids = {
            int(raw_id) for raw_id in session.execute(select(Entity.id)).scalars().all()
        }
    elif resolved_selected_entity_id is not None:
        allowed_entity_ids = {resolved_selected_entity_id}
    else:
        allowed_entity_ids = set()

    return {
        "is_admin": bool(is_admin),
        "has_owner_membership": bool(has_owner_membership),
        "can_manage_all_entities": bool(can_manage_all_entities),
        "selected_entity_id": resolved_selected_entity_id,
        "allowed_entity_ids": allowed_entity_ids,
    }


def is_entity_within_permissions(entity_id: int, permissions: dict[str, Any]) -> bool:
    if permissions.get("can_manage_all_entities"):
        return True
    allowed_ids = permissions.get("allowed_entity_ids") or set()
    return int(entity_id) in allowed_ids


def get_page_data(
    session: Session,
    actor_user_id: int | None = None,
    actor_login_email: str = "",
    selected_entity_id: int | None = None,
) -> dict[str, Any]:
    entity_superuser_profile_name = ENTITY_SUPERUSER_PROFILE_NAME.strip() or "SUPER USER"
    permissions = {
        "is_admin": False,
        "has_owner_membership": False,
        "can_manage_all_entities": False,
        "selected_entity_id": selected_entity_id,
        "allowed_entity_ids": set(),
    }
    allowed_entity_ids: set[int] | None = None
    if actor_user_id is not None:
        permissions = get_user_entity_permissions(
            session,
            actor_user_id,
            actor_login_email,
            selected_entity_id,
        )
        allowed_entity_ids = set(permissions["allowed_entity_ids"])
        selected_entity_id = permissions["selected_entity_id"]
    current_user_is_admin = bool(permissions["is_admin"])

    sidebar_menu_settings = get_sidebar_menu_settings(session)
    visible_sidebar_menu_keys = get_visible_sidebar_menu_keys(
        sidebar_menu_settings,
        current_user_is_admin=current_user_is_admin,
    )
    profile_personal_visible_fields = list(MENU_DOCUMENTOS_FIELDS_DEFAULT)
    profile_personal_field_labels = dict(MENU_DOCUMENTOS_FIELD_LABELS)
    profile_personal_field_types: dict[str, str] = {}
    profile_personal_field_header_map: dict[str, str] = {}
    profile_personal_custom_field_meta: dict[str, dict[str, Any]] = {}
    for sidebar_item in sidebar_menu_settings:
        if str(sidebar_item.get("key") or "") != "documentos":
            continue
        options = sidebar_item.get("process_field_options") or []
        option_labels = {
            str(item.get("key") or "").strip().lower(): str(item.get("label") or "").strip()
            for item in options
            if str(item.get("key") or "").strip()
        }
        option_types = {
            str(item.get("key") or "").strip().lower(): str(item.get("field_type") or "").strip().lower()
            for item in options
            if str(item.get("key") or "").strip()
        }
        if option_labels:
            profile_personal_field_labels = option_labels
        if option_types:
            profile_personal_field_types = option_types
        raw_header_map = sidebar_item.get("process_visible_field_header_map")
        if isinstance(raw_header_map, dict):
            profile_personal_field_header_map = {
                str(raw_key or "").strip().lower(): str(raw_value or "").strip().lower()
                for raw_key, raw_value in raw_header_map.items()
                if str(raw_key or "").strip() and str(raw_value or "").strip()
            }
        for custom_field in sidebar_item.get("process_additional_fields") or []:
            clean_key = str(custom_field.get("key") or "").strip().lower()
            if not clean_key.startswith("custom_"):
                continue
            field_type = str(custom_field.get("field_type") or "text").strip().lower()
            if field_type not in {"text", "number", "email", "phone", "date", "flag", "header"}:
                field_type = "text"
            try:
                parsed_size = int(str(custom_field.get("size") or "").strip())
            except (TypeError, ValueError):
                parsed_size = 30
            if field_type in {"text", "number", "email", "phone"}:
                field_size: int | None = max(1, min(parsed_size, 255))
            else:
                field_size = None
            profile_personal_custom_field_meta[clean_key] = {
                "field_type": field_type,
                "size": field_size,
            }
        visible_raw = sidebar_item.get("process_visible_fields") or []
        visible_fields = [
            str(raw_key or "").strip().lower()
            for raw_key in visible_raw
            if str(raw_key or "").strip().lower() in profile_personal_field_labels
        ]
        if visible_fields:
            profile_personal_visible_fields = visible_fields
        elif profile_personal_field_labels:
            profile_personal_visible_fields = [
                field_key
                for field_key in MENU_DOCUMENTOS_FIELDS_DEFAULT
                if field_key in profile_personal_field_labels
            ]
            if not profile_personal_visible_fields:
                profile_personal_visible_fields = [next(iter(profile_personal_field_labels.keys()))]
        break

    profile_personal_sections: list[dict[str, str]] = [{"key": "geral", "label": "Geral"}]
    profile_personal_field_section_map: dict[str, str] = {}
    header_section_order: list[str] = []
    header_section_seen: set[str] = set()
    for field_key in profile_personal_visible_fields:
        clean_field_key = str(field_key or "").strip().lower()
        if not clean_field_key:
            continue
        field_type = str(profile_personal_field_types.get(clean_field_key) or "").strip().lower()
        if field_type == "header" and clean_field_key not in header_section_seen:
            header_section_order.append(clean_field_key)
            header_section_seen.add(clean_field_key)
    for header_key in profile_personal_field_header_map.values():
        clean_header_key = str(header_key or "").strip().lower()
        if not clean_header_key or clean_header_key in header_section_seen:
            continue
        if str(profile_personal_field_types.get(clean_header_key) or "").strip().lower() != "header":
            continue
        header_section_order.append(clean_header_key)
        header_section_seen.add(clean_header_key)

    if header_section_order:
        for section_key in header_section_order:
            section_label = profile_personal_field_labels.get(section_key, "Aba")
            profile_personal_sections.append({"key": section_key, "label": section_label})
        for field_key in profile_personal_visible_fields:
            clean_field_key = str(field_key or "").strip().lower()
            if not clean_field_key:
                continue
            field_type = str(profile_personal_field_types.get(clean_field_key) or "").strip().lower()
            if field_type == "header":
                continue
            header_key = str(profile_personal_field_header_map.get(clean_field_key) or "").strip().lower()
            if header_key in header_section_seen:
                profile_personal_field_section_map[clean_field_key] = header_key
            else:
                profile_personal_field_section_map[clean_field_key] = "geral"
        has_geral_fields = any(
            section_key == "geral" for section_key in profile_personal_field_section_map.values()
        )
        if not has_geral_fields:
            profile_personal_sections = [
                section for section in profile_personal_sections if section.get("key") != "geral"
            ]
    else:
        active_section_key = "geral"
        seen_section_keys = {"geral"}
        for field_key in profile_personal_visible_fields:
            clean_field_key = str(field_key or "").strip().lower()
            if not clean_field_key:
                continue
            field_type = str(profile_personal_field_types.get(clean_field_key) or "").strip().lower()
            if field_type == "header":
                section_key = clean_field_key
                section_label = profile_personal_field_labels.get(clean_field_key, "Aba")
                if section_key not in seen_section_keys:
                    profile_personal_sections.append({"key": section_key, "label": section_label})
                    seen_section_keys.add(section_key)
                active_section_key = section_key
                continue
            profile_personal_field_section_map[clean_field_key] = active_section_key
        if len(profile_personal_sections) > 1:
            has_geral_fields = any(
                section_key == "geral" for section_key in profile_personal_field_section_map.values()
            )
            if not has_geral_fields:
                profile_personal_sections = [
                    section for section in profile_personal_sections if section.get("key") != "geral"
                ]

    scoped_entity_ids = sorted(allowed_entity_ids) if allowed_entity_ids is not None else []
    apply_scope_filter = allowed_entity_ids is not None

    entities_stmt = (
        select(Entity.id, Entity.name, Entity.internal_number)
       .where(Entity.is_active.is_(True))
       .order_by(Entity.name)
    )
    if apply_scope_filter:
        if scoped_entity_ids:
            entities_stmt = entities_stmt.where(Entity.id.in_(scoped_entity_ids))
        else:
            entities_stmt = entities_stmt.where(Entity.id == -1)
    entities = session.execute(entities_stmt).all()

    profiles_for_form = get_allowed_global_profiles_for_form(session)

    entity_rows_stmt = (
        select(
            Entity.id,
            Entity.internal_number,
            Entity.name,
            Entity.acronym,
            Entity.tax_id,
            Entity.email,
            Entity.responsible_name,
            Entity.door_number,
            Entity.phone,
            Entity.address,
            Entity.freguesia,
            Entity.postal_code,
            Entity.country,
            Entity.description,
            Entity.profile_scope,
            Entity.logo_url,
            Entity.is_active,
            Entity.created_at,
        )
       .order_by(Entity.id.desc())
    )
    if apply_scope_filter:
        if scoped_entity_ids:
            entity_rows_stmt = entity_rows_stmt.where(Entity.id.in_(scoped_entity_ids))
        else:
            entity_rows_stmt = entity_rows_stmt.where(Entity.id == -1)

    recent_entities = session.execute(
        entity_rows_stmt.where(Entity.is_active.is_(True)).limit(10)
    ).all()
    inactive_entities_rows = session.execute(
        entity_rows_stmt.where(Entity.is_active.is_not(True))
    ).all()

    user_rows = session.execute(
        select(
            User.id,
            User.member_id,
            Member.full_name,
            Member.primary_phone,
            User.login_email,
            User.account_status,
            User.created_at,
        )
       .join(Member, Member.id == User.member_id)
       .order_by(User.id.desc())
    ).all()

    if apply_scope_filter:
        if scoped_entity_ids:
            scoped_member_ids = {
                int(raw_id)
                for raw_id in session.execute(
                    select(MemberEntity.member_id)
                   .where(
                        MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                        MemberEntity.entity_id.in_(scoped_entity_ids),
                    )
                   .distinct()
                ).scalars().all()
            }
            user_rows = [
                row for row in user_rows if int(row.member_id) in scoped_member_ids
            ]
        else:
            user_rows = []

    member_ids = [int(row.member_id) for row in user_rows]
    user_ids = [int(row.id) for row in user_rows]

    entity_name_by_member_id: dict[int, str] = {}
    if member_ids:
        entity_name_stmt = (
            select(MemberEntity.member_id, Entity.name)
           .join(Entity, Entity.id == MemberEntity.entity_id)
           .where(MemberEntity.member_id.in_(member_ids))
           .order_by(MemberEntity.member_id.asc(), MemberEntity.id.asc())
        )
        if apply_scope_filter and scoped_entity_ids:
            entity_name_stmt = entity_name_stmt.where(MemberEntity.entity_id.in_(scoped_entity_ids))
        elif apply_scope_filter:
            entity_name_stmt = entity_name_stmt.where(MemberEntity.entity_id == -1)

        for row in session.execute(entity_name_stmt).all():
            member_id_value = int(row.member_id)
            if member_id_value not in entity_name_by_member_id:
                entity_name_by_member_id[member_id_value] = row.name

    profile_name_by_user_id: dict[int, str] = {}
    superuser_user_ids: set[int] = set()
    if user_ids:
        profile_rows = session.execute(
            select(UserProfile.user_id, Profile.name)
           .join(Profile, Profile.id == UserProfile.profile_id)
           .where(UserProfile.user_id.in_(user_ids), UserProfile.is_active.is_(True))
           .order_by(UserProfile.user_id.asc(), UserProfile.id.asc())
        ).all()
        for row in profile_rows:
            user_id_value = int(row.user_id)
            if user_id_value not in profile_name_by_user_id:
                profile_name_by_user_id[user_id_value] = row.name

        superuser_rows = session.execute(
            select(UserProfile.user_id)
           .join(Profile, Profile.id == UserProfile.profile_id)
           .where(
                UserProfile.user_id.in_(user_ids),
                UserProfile.is_active.is_(True),
                Profile.is_active.is_(True),
                func.lower(Profile.name) == entity_superuser_profile_name.lower(),
            )
        ).all()
        superuser_user_ids = {int(row.user_id) for row in superuser_rows}

    all_users = [
        {
            "id": row.id,
            "member_id": row.member_id,
            "full_name": row.full_name,
            "primary_phone": row.primary_phone or "-",
            "login_email": row.login_email,
            "account_status": row.account_status,
            "entity_name": entity_name_by_member_id.get(int(row.member_id), "-"),
            "profile_name": profile_name_by_user_id.get(int(row.id), "-"),
            "is_entity_superuser": int(row.id) in superuser_user_ids,
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M") if row.created_at else "-",
        }
        for row in user_rows
    ]
    pending_users = [
        row for row in all_users if row["account_status"] == UserAccountStatus.PENDING.value
    ]
    created_users = [
        row for row in all_users if row["account_status"] != UserAccountStatus.PENDING.value
    ]
    superuser_users = [row for row in all_users if row["is_entity_superuser"]]
    recent_users = all_users[:10]

    account_status_map = {
        UserAccountStatus.ACTIVE.value: 0,
        UserAccountStatus.PENDING.value: 0,
        UserAccountStatus.INACTIVE.value: 0,
        UserAccountStatus.BLOCKED.value: 0,
    }
    for row in all_users:
        normalized_status = str(row.get("account_status") or "").strip().lower()
        if normalized_status not in account_status_map:
            account_status_map[normalized_status] = 0
        account_status_map[normalized_status] += 1
    account_status_summary = [
        {"status": UserAccountStatus.ACTIVE.value, "count": account_status_map.get(UserAccountStatus.ACTIVE.value, 0)},
        {"status": UserAccountStatus.PENDING.value, "count": account_status_map.get(UserAccountStatus.PENDING.value, 0)},
        {"status": UserAccountStatus.INACTIVE.value, "count": account_status_map.get(UserAccountStatus.INACTIVE.value, 0)},
        {"status": UserAccountStatus.BLOCKED.value, "count": account_status_map.get(UserAccountStatus.BLOCKED.value, 0)},
    ]

    def serialize_entity_row(row: Any) -> dict[str, Any]:
        return {
            "id": row.id,
            "internal_number": row.internal_number if row.internal_number is not None else "-",
            "name": row.name,
            "acronym": row.acronym or "",
            "tax_id": row.tax_id or "",
            "email": row.email or "",
            "responsible_name": row.responsible_name or "",
            "door_number": row.door_number or "",
            "phone": row.phone or "",
            "address": row.address or "",
            "freguesia": row.freguesia or "",
            "postal_code": row.postal_code or "",
            "country": row.country or "",
            "description": row.description or "",
            "profile_scope": (row.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO),
            "profile_scope_label": (
                "Owner"
                if (row.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO) == ENTITY_PROFILE_SCOPE_OWNER
                else "Legado"
            ),
            "logo_url": row.logo_url or "",
            "is_active": bool(row.is_active),
            "status_label": "Ativa" if row.is_active else "Inativa",
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M") if row.created_at else "-",
        }

    return {
        "entities": [
            {
                "id": row.id,
                "name": row.name,
                "internal_number": row.internal_number,
            }
            for row in entities
        ],
        "profiles": profiles_for_form,
        "account_status_summary": account_status_summary,
        "recent_entities": [serialize_entity_row(row) for row in recent_entities],
        "inactive_entities": [serialize_entity_row(row) for row in inactive_entities_rows],
        "recent_users": [
            {
                "id": row["id"],
                "full_name": row["full_name"],
                "login_email": row["login_email"],
                "account_status": row["account_status"],
                "created_at": row["created_at"],
            }
            for row in recent_users
        ],
        "all_users": all_users,
        "created_users": created_users,
        "pending_users": pending_users,
        "superuser_users": superuser_users,
        "entity_permissions": permissions,
        "current_user_can_manage_all_entities": bool(permissions["can_manage_all_entities"]),
        "sidebar_menu_settings": sidebar_menu_settings,
        "visible_sidebar_menu_keys": sorted(visible_sidebar_menu_keys),
        "profile_personal_visible_fields": profile_personal_visible_fields,
        "profile_personal_field_labels": profile_personal_field_labels,
        "profile_personal_field_section_map": profile_personal_field_section_map,
        "profile_personal_sections": profile_personal_sections,
        "profile_personal_custom_field_meta": profile_personal_custom_field_meta,
        "menu_documentos_field_options": [dict(item) for item in MENU_DOCUMENTOS_FIELD_OPTIONS],
        "menu_documentos_field_labels": dict(MENU_DOCUMENTOS_FIELD_LABELS),
        "dashboard_data": get_home_dashboard_data(
            session,
            allowed_entity_ids=allowed_entity_ids,
        ),
    }


def get_home_dashboard_data(
    session: Session,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, Any]:
    apply_scope_filter = allowed_entity_ids is not None
    scoped_entity_ids = sorted(allowed_entity_ids) if allowed_entity_ids is not None else []

    entity_counts_stmt = select(Entity.is_active, func.count(Entity.id)).group_by(Entity.is_active)
    if apply_scope_filter:
        if scoped_entity_ids:
            entity_counts_stmt = entity_counts_stmt.where(Entity.id.in_(scoped_entity_ids))
        else:
            entity_counts_stmt = entity_counts_stmt.where(Entity.id == -1)

    entity_counts = session.execute(entity_counts_stmt).all()
    active_entities = 0
    inactive_entities = 0
    for row in entity_counts:
        if bool(row.is_active):
            active_entities = int(row[1])
        else:
            inactive_entities = int(row[1])

    if apply_scope_filter:
        if scoped_entity_ids:
            scoped_user_ids = [
                int(raw_id)
                for raw_id in session.execute(
                    select(User.id)
                   .join(MemberEntity, MemberEntity.member_id == User.member_id)
                   .where(
                        MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                        MemberEntity.entity_id.in_(scoped_entity_ids),
                    )
                   .distinct()
                ).scalars().all()
            ]
        else:
            scoped_user_ids = []
    else:
        scoped_user_ids = []

    profile_count_map: dict[str, int] = {}
    if not apply_scope_filter or scoped_user_ids:
        user_profile_join_condition = (
            (UserProfile.profile_id == Profile.id)
            & (UserProfile.is_active.is_(True))
        )
        if apply_scope_filter:
            user_profile_join_condition = (
                user_profile_join_condition
                & (UserProfile.user_id.in_(scoped_user_ids))
            )

        profile_rows = session.execute(
            select(Profile.name, func.count(func.distinct(UserProfile.user_id)))
           .select_from(Profile)
           .outerjoin(UserProfile, user_profile_join_condition)
           .where(func.lower(Profile.name).in_(ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED))
           .group_by(Profile.id, Profile.name)
        ).all()
        for row in profile_rows:
            profile_count_map[normalize_profile_name(row.name)] = int(row[1])

    profile_labels = list(ALLOWED_GLOBAL_PROFILE_NAMES)
    profile_values = [
        profile_count_map.get(normalize_profile_name(label), 0) for label in profile_labels
    ]

    total_entities = active_entities + inactive_entities
    if apply_scope_filter:
        total_users = len(scoped_user_ids)
    else:
        total_users = session.scalar(select(func.count(User.id))) or 0

    return {
        "entity_status": {
            "labels": ["Ativas", "Inativas"],
            "values": [active_entities, inactive_entities],
        },
        "users_by_profile": {
            "labels": profile_labels,
            "values": profile_values,
        },
        "totals": {
            "entities": int(total_entities),
            "users": int(total_users),
            "active_entities": int(active_entities),
            "inactive_entities": int(inactive_entities),
        },
    }


def get_form_defaults() -> dict[str, str]:
    return {
        "full_name": "",
        "primary_phone": "",
        "email": "",
        "entity_id": "",
        "entity_name": "",
        "account_status": UserAccountStatus.ACTIVE.value,
        "profile_id": "",
    }


def get_entity_form_defaults() -> dict[str, str]:
    return {
        "name": "",
        "acronym": "",
        "tax_id": "",
        "email": "",
        "responsible_name": "",
        "door_number": "",
        "address": "",
        "freguesia": "",
        "postal_code": "",
        "country": "",
        "phone": "",
        "description": "",
        "profile_scope": ENTITY_PROFILE_SCOPE_LEGADO,
        "created_at": date.today().strftime("%d/%m/%Y"),
    }


def get_entity_edit_defaults() -> dict[str, str]:
    return {
        "id": "",
        "internal_number": "-",
        "name": "",
        "acronym": "",
        "tax_id": "",
        "email": "",
        "responsible_name": "",
        "door_number": "",
        "address": "",
        "freguesia": "",
        "postal_code": "",
        "country": "",
        "phone": "",
        "description": "",
        "profile_scope": ENTITY_PROFILE_SCOPE_LEGADO,
        "created_at": "",
        "logo_url": "",
        "status": "active",
    }


def get_entity_edit_data(
    session: Session,
    entity_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, str]:
    defaults = get_entity_edit_defaults()
    if entity_id is None:
        return defaults

    if allowed_entity_ids is not None and int(entity_id) not in allowed_entity_ids:
        return defaults

    entity = session.get(Entity, entity_id)
    if entity is None:
        return defaults

    return {
        "id": str(entity.id),
        "internal_number": str(entity.internal_number) if entity.internal_number is not None else "-",
        "name": entity.name or "",
        "acronym": entity.acronym or "",
        "tax_id": entity.tax_id or "",
        "email": entity.email or "",
        "responsible_name": entity.responsible_name or "",
        "door_number": entity.door_number or "",
        "address": entity.address or "",
        "freguesia": entity.freguesia or "",
        "postal_code": entity.postal_code or "",
        "country": entity.country or "",
        "phone": entity.phone or "",
        "description": entity.description or "",
        "profile_scope": entity.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO,
        "created_at": entity.created_at.strftime("%d/%m/%Y") if entity.created_at else "",
        "logo_url": entity.logo_url or "",
        "status": "active" if entity.is_active else "inactive",
    }


def get_user_edit_defaults() -> dict[str, str]:
    return {
        "id": "",
        "full_name": "",
        "primary_phone": "",
        "email": "",
        "entity_id": "",
        "entity_name": "",
        "account_status": UserAccountStatus.ACTIVE.value,
        "profile_id": "",
    }


def get_user_edit_data(
    session: Session,
    user_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, str]:
    defaults = get_user_edit_defaults()
    if user_id is None:
        return defaults

    row = session.execute(
        select(
            User.id,
            User.member_id,
            Member.full_name,
            Member.primary_phone,
            User.login_email,
            User.account_status,
        )
       .join(Member, Member.id == User.member_id)
       .where(User.id == user_id)
    ).one_or_none()
    if row is None:
        return defaults

    member_entity_stmt = (
        select(MemberEntity.entity_id)
       .where(MemberEntity.member_id == row.member_id)
       .order_by(MemberEntity.id.asc())
    )
    if allowed_entity_ids is not None:
        if allowed_entity_ids:
            member_entity_stmt = member_entity_stmt.where(
                MemberEntity.entity_id.in_(sorted(allowed_entity_ids))
            )
        else:
            return defaults

    member_entity_id = session.scalar(member_entity_stmt.limit(1))
    if allowed_entity_ids is not None and member_entity_id is None:
        return defaults

    profile_id = session.scalar(
        select(UserProfile.profile_id)
       .where(UserProfile.user_id == row.id, UserProfile.is_active.is_(True))
       .order_by(UserProfile.id.asc())
       .limit(1)
    )

    return {
        "id": str(row.id),
        "full_name": row.full_name or "",
        "primary_phone": row.primary_phone or "",
        "email": row.login_email or "",
        "entity_id": str(member_entity_id) if member_entity_id is not None else "",
        "entity_name": (
            session.execute(
                select(Entity.name).where(Entity.id == member_entity_id).limit(1)
            ).scalar_one_or_none()
            if member_entity_id is not None
            else ""
        )
        or "",
        "account_status": row.account_status or UserAccountStatus.ACTIVE.value,
        "profile_id": str(profile_id) if profile_id is not None else "",
    }


def get_next_entity_internal_number(session: Session) -> int:
    used_numbers = session.scalars(
        select(Entity.internal_number)
       .where(
            Entity.internal_number.is_not(None),
            Entity.internal_number >= ENTITY_INTERNAL_NUMBER_MIN,
            Entity.internal_number <= ENTITY_INTERNAL_NUMBER_MAX,
        )
       .order_by(Entity.internal_number.asc())
    ).all()
    used_set = {int(number) for number in used_numbers if isinstance(number, int)}
    for candidate in range(ENTITY_INTERNAL_NUMBER_MIN, ENTITY_INTERNAL_NUMBER_MAX + 1):
        if candidate not in used_set:
            return candidate
    return ENTITY_INTERNAL_NUMBER_MAX


def save_entity_logo_upload(entity_logo_file: UploadFile | None) -> tuple[str, str]:
    if entity_logo_file is None or not entity_logo_file.filename:
        return "", ""

    content_type = (entity_logo_file.content_type or "").strip().lower()
    file_ext = Path(entity_logo_file.filename).suffix.lower()
    if file_ext not in ALLOWED_ENTITY_LOGO_EXTENSIONS:
        mapped_ext = LOGO_CONTENT_TYPE_EXTENSION.get(content_type, "")
        file_ext = mapped_ext

    if file_ext not in ALLOWED_ENTITY_LOGO_EXTENSIONS:
        return "", "Formato de imagem inválido. Use PNG, JPG, WEBP, GIF ou SVG."

    stored_name = f"entity_logo_{secrets.token_hex(10)}{file_ext}"
    destination = ENTITY_LOGOS_DIR / stored_name
    total_size = 0

    try:
        with destination.open("wb") as file_handle:
            while True:
                chunk = entity_logo_file.file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_ENTITY_LOGO_SIZE_BYTES:
                    file_handle.close()
                    destination.unlink(missing_ok=True)
                    return "", "Imagem demasiado grande. Limite maximo: 5MB."
                file_handle.write(chunk)
    finally:
        entity_logo_file.file.close()

    return f"/static/entities/{stored_name}", ""


def build_users_new_url(**query_params: str) -> str:
    clean_query_params = {
        key: value
        for key, value in query_params.items()
        if isinstance(value, str) and value.strip()
    }
    if not clean_query_params:
        return "/users/new"
    return f"/users/new?{urlencode(clean_query_params)}"


def has_whatsapp_verification_config() -> bool:
    return bool(
        WHATSAPP_ACCESS_TOKEN
        and WHATSAPP_PHONE_NUMBER_ID
        and WHATSAPP_TEMPLATE_NAME
        and WHATSAPP_WEBHOOK_VERIFY_TOKEN
    )


def normalize_whatsapp_recipient(raw_phone: str) -> str:
    clean_phone = (raw_phone or "").strip()
    if not clean_phone:
        return ""

    if clean_phone.startswith("00"):
        clean_phone = "+" + clean_phone[2:]

    digits_only = re.sub(r"\D", "", clean_phone)
    if clean_phone.startswith("+"):
        if len(digits_only) < 8 or len(digits_only) > 15:
            return ""
        return digits_only

    if clean_phone.startswith("351") and len(digits_only) >= 11:
        return digits_only

    if len(digits_only) == 9:
        return f"351{digits_only}"

    if 8 <= len(digits_only) <= 15:
        return digits_only
    return ""


def format_whatsapp_status(status_value: str | None) -> str:
    status_lookup = {
        "unknown": "Não verificado",
        "pending": "Verificação pendente",
        "active": "Ativo no WhatsApp",
        "invalid": "Número sem WhatsApp",
        "failed": "Falha na verificação",
    }
    normalized = (status_value or "unknown").strip().lower()
    return status_lookup.get(normalized, "Não verificado")


def format_optional_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def format_optional_date_pt(value: date | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%d/%m/%Y")


def parse_optional_date_pt(raw_value: str) -> date | None:
    clean_value = (raw_value or "").strip()
    if not clean_value:
        return None
    return datetime.strptime(clean_value, "%d/%m/%Y").date()


def extract_whatsapp_api_error(payload: Any) -> str:
    if isinstance(payload, dict):
        error_block = payload.get("error")
        if isinstance(error_block, dict):
            message = str(error_block.get("message") or "").strip()
            details = str(
                error_block.get("error_user_msg")
                or error_block.get("error_data", {}).get("details")
                or ""
            ).strip()
            if message and details:
                return f"{message}: {details}"
            if message:
                return message
            if details:
                return details
    return "Falha na chamada da API do WhatsApp."


def send_whatsapp_verification_template(recipient_phone: str) -> tuple[bool, str, str]:
    if not has_whatsapp_verification_config():
        return (
            False,
            "",
            "Configuração WhatsApp incompleta. Defina token, número, template e verify token.",
        )

    url = (
        f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}"
        f"/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "template",
        "template": {
            "name": WHATSAPP_TEMPLATE_NAME,
            "language": {"code": WHATSAPP_TEMPLATE_LANGUAGE},
        },
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=20.0)
    except httpx.RequestError as exc:
        return False, "", f"Erro de rede ao contactar WhatsApp: {exc!s}"

    response_payload: Any
    try:
        response_payload = response.json()
    except ValueError:
        response_payload = {}

    if not response.is_success:
        return False, "", extract_whatsapp_api_error(response_payload)

    message_id = ""
    if isinstance(response_payload, dict):
        messages = response_payload.get("messages")
        if isinstance(messages, list) and messages:
            first_message = messages[0]
            if isinstance(first_message, dict):
                message_id = str(first_message.get("id") or "").strip()

    if not message_id:
        return False, "", "API do WhatsApp não devolveu id de mensagem."
    return True, message_id, ""


def map_whatsapp_delivery_status(status_value: str) -> str:
    normalized = (status_value or "").strip().lower()
    if normalized in {"read", "delivered"}:
        return "active"
    if normalized in {"failed", "undelivered"}:
        return "invalid"
    if normalized in {"sent"}:
        return "pending"
    return "pending"


def get_signup_defaults() -> dict[str, str]:
    return {
        "full_name": "",
        "primary_phone": "",
        "email": "",
        "entity_id": "",
    }


def get_login_defaults() -> dict[str, str]:
    return {
        "entity_id": "",
    }


def get_session_user_id(request: Request) -> int | None:
    raw_user_id = request.session.get("user_id")
    if isinstance(raw_user_id, int):
        return raw_user_id
    if isinstance(raw_user_id, str) and raw_user_id.isdigit():
        return int(raw_user_id)
    return None


def get_session_entity_id(request: Request) -> int | None:
    raw_entity_id = request.session.get("entity_id")
    if isinstance(raw_entity_id, int):
        return raw_entity_id
    if isinstance(raw_entity_id, str) and raw_entity_id.isdigit():
        return int(raw_entity_id)
    return None


def set_session_entity_context(request: Request, entity_context: dict[str, Any] | None) -> None:
    if entity_context is None:
        request.session.pop("entity_id", None)
        request.session.pop("entity_name", None)
        request.session.pop("entity_logo_url", None)
        return

    request.session["entity_id"] = int(entity_context["id"])
    request.session["entity_name"] = str(entity_context.get("name") or "")
    request.session["entity_logo_url"] = str(entity_context.get("logo_url") or "")


def get_entity_context_for_user(
    session: Session,
    user_id: int,
    login_email: str,
    entity_id: int | None = None,
) -> dict[str, Any] | None:
    permissions = get_user_entity_permissions(
        session,
        user_id,
        login_email,
        entity_id,
    )
    can_manage_all_entities = bool(permissions["can_manage_all_entities"])

    if entity_id is not None:
        selected_entity = session.get(Entity, entity_id)
        if selected_entity is None or not selected_entity.is_active:
            return None

        if can_manage_all_entities:
            return {
                "id": int(selected_entity.id),
                "name": selected_entity.name or "",
                "logo_url": selected_entity.logo_url or "",
            }

        has_membership = session.execute(
            select(MemberEntity.id)
           .join(User, User.member_id == MemberEntity.member_id)
           .where(
                User.id == user_id,
                MemberEntity.entity_id == entity_id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
           .limit(1)
        ).scalar_one_or_none()
        if has_membership is None:
            return None

        return {
            "id": int(selected_entity.id),
            "name": selected_entity.name or "",
            "logo_url": selected_entity.logo_url or "",
        }

    linked_entity = session.execute(
        select(Entity.id, Entity.name, Entity.logo_url)
       .join(MemberEntity, MemberEntity.entity_id == Entity.id)
       .join(User, User.member_id == MemberEntity.member_id)
       .where(
            User.id == user_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.is_active.is_(True),
        )
       .order_by(MemberEntity.id.asc())
       .limit(1)
    ).one_or_none()
    if linked_entity is not None:
        return {
            "id": int(linked_entity.id),
            "name": linked_entity.name or "",
            "logo_url": linked_entity.logo_url or "",
        }

    if can_manage_all_entities:
        first_active_entity = session.execute(
            select(Entity.id, Entity.name, Entity.logo_url)
           .where(Entity.is_active.is_(True))
           .order_by(Entity.name.asc())
           .limit(1)
        ).one_or_none()
        if first_active_entity is not None:
            return {
                "id": int(first_active_entity.id),
                "name": first_active_entity.name or "",
                "logo_url": first_active_entity.logo_url or "",
            }

    return None


def get_current_user(request: Request, session: Session) -> dict[str, Any] | None:
    user_id = get_session_user_id(request)
    if user_id is None:
        return None

    row = session.execute(
        select(User.id, User.login_email, User.account_status, Member.full_name)
       .join(Member, Member.id == User.member_id)
       .where(User.id == user_id)
    ).one_or_none()

    if row is None or row.account_status != UserAccountStatus.ACTIVE.value:
        request.session.clear()
        return None

    selected_entity_context = get_entity_context_for_user(
        session,
        row.id,
        row.login_email,
        get_session_entity_id(request),
    )
    if selected_entity_context is None:
        selected_entity_context = get_entity_context_for_user(
            session,
            row.id,
            row.login_email,
            None,
        )
    set_session_entity_context(request, selected_entity_context)

    return {
        "id": row.id,
        "full_name": row.full_name,
        "login_email": row.login_email,
    }


def get_user_personal_data(
    session: Session,
    user_id: int,
    selected_entity_id: int | None = None,
) -> dict[str, Any]:
    row = session.execute(
        select(
            Member.full_name,
            User.login_email,
            Member.primary_phone,
            Member.birth_date,
            Member.address,
            Member.city,
            Member.freguesia,
            Member.postal_code,
            Member.whatsapp_verification_status,
            Member.whatsapp_notice_opt_in,
            Member.whatsapp_last_check_at,
            Member.whatsapp_last_error,
            Member.training_discipulado_verbo_vida,
            Member.training_ebvv,
            Member.training_rhema,
            Member.training_escola_ministerial,
            Member.training_escola_missoes,
            Member.training_outros,
            Member.profile_custom_fields,
            Member.member_status,
            User.account_status,
            Member.is_collaborator,
        )
       .join(User, User.member_id == Member.id)
       .where(User.id == user_id)
    ).one_or_none()

    if row is None:
        return {
            "full_name": "-",
            "login_email": "-",
            "primary_phone": "-",
            "birth_date": "-",
            "address": "-",
            "city": "-",
            "freguesia": "-",
            "postal_code": "-",
            "whatsapp_verification_status": format_whatsapp_status("unknown"),
            "whatsapp_notice_opt_in": "Não autorizado",
            "whatsapp_notice_opt_in_raw": False,
            "whatsapp_last_check_at": "-",
            "whatsapp_last_error": "-",
            "training_discipulado_verbo_vida": False,
            "training_ebvv": False,
            "training_rhema": False,
            "training_escola_ministerial": False,
            "training_escola_missoes": False,
            "training_outros": "",
            "training_selected": [],
            "member_status": "-",
            "account_status": "-",
            "is_collaborator": "-",
            "custom_fields": {},
            "entities": "-",
            "primary_entity_name": "-",
            "primary_entity_address": "-",
            "primary_entity_phone": "-",
            "primary_entity_logo_url": "",
        }

    entity_rows = session.execute(
        select(Entity.id, Entity.name, Entity.address, Entity.phone, Entity.logo_url)
       .join(MemberEntity, MemberEntity.entity_id == Entity.id)
       .join(User, User.member_id == MemberEntity.member_id)
       .where(
            User.id == user_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.is_active.is_(True),
        )
       .order_by(MemberEntity.id.asc())
    ).all()
    entities = ", ".join(row_entity.name for row_entity in entity_rows) if entity_rows else "-"

    primary_entity_data: dict[str, str] | None = None
    if selected_entity_id is not None:
        for linked_entity in entity_rows:
            if int(linked_entity.id) == selected_entity_id:
                primary_entity_data = {
                    "name": linked_entity.name or "",
                    "address": linked_entity.address or "",
                    "phone": linked_entity.phone or "",
                    "logo_url": linked_entity.logo_url or "",
                }
                break

    if primary_entity_data is None and selected_entity_id is not None:
        selected_entity_row = session.execute(
            select(Entity.name, Entity.address, Entity.phone, Entity.logo_url)
           .where(Entity.id == selected_entity_id, Entity.is_active.is_(True))
           .limit(1)
        ).one_or_none()
        if selected_entity_row is not None:
            primary_entity_data = {
                "name": selected_entity_row.name or "",
                "address": selected_entity_row.address or "",
                "phone": selected_entity_row.phone or "",
                "logo_url": selected_entity_row.logo_url or "",
            }

    if primary_entity_data is None and entity_rows:
        first_linked_entity = entity_rows[0]
        primary_entity_data = {
            "name": first_linked_entity.name or "",
            "address": first_linked_entity.address or "",
            "phone": first_linked_entity.phone or "",
            "logo_url": first_linked_entity.logo_url or "",
        }

    if entities == "-" and primary_entity_data is not None:
        entities = primary_entity_data.get("name") or "-"
    training_selected: list[str] = []
    if row.training_discipulado_verbo_vida:
        training_selected.append("DISCIPULADO VERBO DA VIDA")
    if row.training_ebvv:
        training_selected.append("EBVV")
    if row.training_rhema:
        training_selected.append("RHEMA")
    if row.training_escola_ministerial:
        training_selected.append("ESCOLA MINISTERIAL")
    if row.training_escola_missoes:
        training_selected.append("ESCOLA DE MISSÕES")
    clean_training_outros = (row.training_outros or "").strip()
    if clean_training_outros:
        training_selected.append(f"OUTROS: {clean_training_outros}")
    custom_fields = parse_profile_custom_fields(row.profile_custom_fields)

    return {
        "full_name": row.full_name or "-",
        "login_email": row.login_email or "-",
        "primary_phone": row.primary_phone or "-",
        "birth_date": format_optional_date_pt(row.birth_date),
        "address": row.address or "-",
        "city": row.city or "-",
        "freguesia": row.freguesia or "-",
        "postal_code": row.postal_code or "-",
        "whatsapp_verification_status": format_whatsapp_status(row.whatsapp_verification_status),
        "whatsapp_notice_opt_in": "Autorizado" if row.whatsapp_notice_opt_in else "Não autorizado",
        "whatsapp_notice_opt_in_raw": bool(row.whatsapp_notice_opt_in),
        "whatsapp_last_check_at": format_optional_datetime(row.whatsapp_last_check_at),
        "whatsapp_last_error": row.whatsapp_last_error or "-",
        "training_discipulado_verbo_vida": bool(row.training_discipulado_verbo_vida),
        "training_ebvv": bool(row.training_ebvv),
        "training_rhema": bool(row.training_rhema),
        "training_escola_ministerial": bool(row.training_escola_ministerial),
        "training_escola_missoes": bool(row.training_escola_missoes),
        "training_outros": clean_training_outros,
        "training_selected": training_selected,
        "member_status": row.member_status or "-",
        "account_status": row.account_status or "-",
        "is_collaborator": "Sim" if row.is_collaborator else "Não",
        "custom_fields": custom_fields,
        "entities": entities,
        "primary_entity_name": (
            primary_entity_data["name"] if primary_entity_data and primary_entity_data.get("name") else "-"
        ),
        "primary_entity_address": (
            primary_entity_data["address"] if primary_entity_data and primary_entity_data.get("address") else "-"
        ),
        "primary_entity_phone": (
            primary_entity_data["phone"] if primary_entity_data and primary_entity_data.get("phone") else "-"
        ),
        "primary_entity_logo_url": (
            primary_entity_data["logo_url"] if primary_entity_data and primary_entity_data.get("logo_url") else ""
        ),
    }


def get_oauth_flags() -> dict[str, bool]:
    return {
        "oauth_google_enabled": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        "oauth_microsoft_enabled": bool(MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET),
        "oauth_github_enabled": bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET),
    }


def get_oauth_buttons() -> list[dict[str, Any]]:
    flags = get_oauth_flags()
    return [
        {
            "label": "Google (Gmail)",
            "url": "/oauth/login/google",
            "enabled": flags["oauth_google_enabled"],
        },
        {
            "label": "Microsoft (Hotmail/Outlook)",
            "url": "/oauth/login/microsoft",
            "enabled": flags["oauth_microsoft_enabled"],
        },
    ]


def get_entities_for_auth(session: Session) -> list[dict[str, Any]]:
    rows = session.execute(
        select(Entity.id, Entity.name, Entity.email)
       .where(Entity.is_active.is_(True))
       .order_by(Entity.name)
    ).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "email": (row.email or "").strip().lower(),
        }
        for row in rows
    ]


def resolve_active_entity_by_email(
    session: Session,
    raw_email: str,
) -> tuple[Entity | None, str]:
    clean_email = (raw_email or "").strip().lower()
    if not clean_email or "@" not in clean_email:
        return None, "Email inválido para determinar entidade."

    entities = list(
        session.execute(
            select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())
        ).scalars().all()
    )
    if not entities:
        return None, "Sem entidades ativas disponíveis."

    exact_matches = [
        entity for entity in entities if (entity.email or "").strip().lower() == clean_email
    ]
    if len(exact_matches) == 1:
        return exact_matches[0], ""
    if len(exact_matches) > 1:
        return None, "Existem múltiplas entidades com o mesmo email."

    _, domain = clean_email.split("@", 1)
    clean_domain = domain.strip()
    if clean_domain:
        domain_matches = []
        for entity in entities:
            entity_email = (entity.email or "").strip().lower()
            if "@" not in entity_email:
                continue
            _, entity_domain = entity_email.split("@", 1)
            if entity_domain.strip() == clean_domain:
                domain_matches.append(entity)
        if len(domain_matches) == 1:
            return domain_matches[0], ""
        if len(domain_matches) > 1:
            return None, "Existem múltiplas entidades com o mesmo domínio de email."

    if len(entities) == 1:
        return entities[0], ""

    return None, "Não foi possível determinar automaticamente a entidade pelo email."


def is_admin_user(session: Session, user_id: int, login_email: str) -> bool:
    email = (login_email or "").strip().lower()
    if ADMIN_LOGIN_EMAIL and email == ADMIN_LOGIN_EMAIL:
        return True

    if not ADMIN_PROFILE_NAMES:
        return False

    admin_profile_id = session.execute(
        select(Profile.id)
       .join(UserProfile, UserProfile.profile_id == Profile.id)
       .where(
            UserProfile.user_id == user_id,
            UserProfile.is_active.is_(True),
            Profile.is_active.is_(True),
            func.lower(Profile.name).in_(ADMIN_PROFILE_NAMES),
        )
       .limit(1)
    ).scalar_one_or_none()
    return admin_profile_id is not None


def is_allowed_global_profile(profile: Profile | None) -> bool:
    if profile is None:
        return False
    profile_name = normalize_profile_name(profile.name)
    if not profile_name:
        return False
    return profile_name in ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED


def get_or_create_entity_superuser_profile(session: Session) -> Profile:
    clean_name = ENTITY_SUPERUSER_PROFILE_NAME.strip() or "SUPER USER"
    profile = session.execute(
        select(Profile).where(func.lower(Profile.name) == clean_name.lower()).limit(1)
    ).scalar_one_or_none()
    if profile is not None:
        if not profile.is_active:
            profile.is_active = True
        return profile

    profile = Profile(
        name=clean_name,
        description="Perfil global SUPER USER.",
        is_active=True,
    )
    session.add(profile)
    session.flush()
    return profile


def get_admin_login_metrics(session: Session) -> dict[str, int]:
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    total_users = session.execute(select(func.count(User.id))).scalar_one() or 0
    active_users = (
        session.execute(
            select(func.count(User.id)).where(User.account_status == UserAccountStatus.ACTIVE.value)
        ).scalar_one()
        or 0
    )
    pending_users = (
        session.execute(
            select(func.count(User.id)).where(User.account_status == UserAccountStatus.PENDING.value)
        ).scalar_one()
        or 0
    )
    total_members = session.execute(select(func.count(Member.id))).scalar_one() or 0
    active_entities = (
        session.execute(select(func.count(Entity.id)).where(Entity.is_active.is_(True))).scalar_one()
        or 0
    )
    users_last_7_days = (
        session.execute(select(func.count(User.id)).where(User.created_at >= seven_days_ago)).scalar_one()
        or 0
    )

    return {
        "total_users": int(total_users),
        "active_users": int(active_users),
        "pending_users": int(pending_users),
        "total_members": int(total_members),
        "active_entities": int(active_entities),
        "users_last_7_days": int(users_last_7_days),
    }


def get_oauth_client(provider: str):
    if provider == "google" and GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        return oauth.create_client("google")
    if provider == "microsoft" and MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET:
        return oauth.create_client("microsoft")
    if provider == "github" and GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
        return oauth.create_client("github")
    return None


async def fetch_oauth_userinfo(
    request: Request,
    provider: str,
    client: Any,
    token: dict[str, Any],
) -> dict[str, Any]:
    userinfo: dict[str, Any] = token.get("userinfo") or {}

    if provider == "github":
        try:
            profile_response = await client.get("user", token=token)
            profile_response.raise_for_status()
            profile_payload = profile_response.json()
            if isinstance(profile_payload, dict):
                userinfo.update(profile_payload)
        except Exception:
            return {}

        if not userinfo.get("email"):
            try:
                email_response = await client.get("user/emails", token=token)
                email_response.raise_for_status()
                email_payload = email_response.json()
            except Exception:
                email_payload = []

            selected_email = ""
            if isinstance(email_payload, list):
                for item in email_payload:
                    if not isinstance(item, dict):
                        continue
                    candidate = str(item.get("email") or "").strip()
                    if not candidate:
                        continue
                    if item.get("primary") and item.get("verified"):
                        selected_email = candidate
                        break
                    if not selected_email and item.get("verified"):
                        selected_email = candidate
                    if not selected_email:
                        selected_email = candidate

            if selected_email:
                userinfo["email"] = selected_email

        if not userinfo.get("name"):
            userinfo["name"] = userinfo.get("login") or ""
        return userinfo

    if userinfo:
        return userinfo

    try:
        parsed = await client.parse_id_token(request, token)
        if parsed:
            return dict(parsed)
    except Exception:
        pass
    return {}


def upsert_user_by_email(
    session: Session,
    email: str,
    full_name: str,
    primary_phone: str,
    entity_id: int | None,
) -> User:
    clean_email = email.strip().lower()
    clean_name = full_name.strip() or clean_email.split("@")[0]
    clean_phone = primary_phone.strip() or "N/D"

    existing_user = session.execute(
        select(User).where(func.lower(User.login_email) == clean_email)
    ).scalar_one_or_none()
    if existing_user is not None:
        return existing_user

    member = session.execute(
        select(Member).where(func.lower(Member.email) == clean_email)
    ).scalar_one_or_none()
    if member is None:
        member = Member(
            full_name=clean_name,
            primary_phone=clean_phone,
            email=clean_email,
            member_status=MemberStatus.ACTIVE.value,
            is_collaborator=True,
        )
        session.add(member)
        session.flush()

    selected_entity: Entity | None = None
    if entity_id is not None:
        selected_entity = session.get(Entity, entity_id)
    if selected_entity is None:
        selected_entity = session.execute(
            select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.id).limit(1)
        ).scalars().first()
    if selected_entity is None:
        selected_entity = Entity(
            name="Entidade Principal",
            internal_number=get_next_entity_internal_number(session),
            is_active=True,
        )
        session.add(selected_entity)
        session.flush()

    active_link = session.execute(
        select(MemberEntity).where(
            MemberEntity.member_id == member.id,
            MemberEntity.entity_id == selected_entity.id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
    ).scalar_one_or_none()
    if active_link is None:
        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=selected_entity.id,
                status=MemberEntityStatus.ACTIVE.value,
                entry_date=date.today(),
            )
        )

    user = User(
        member_id=member.id,
        login_email=clean_email,
        password_hash=hash_password(secrets.token_urlsafe(24)),
        account_status=UserAccountStatus.ACTIVE.value,
    )
    session.add(user)
    session.flush()
    return user


def render_login(
    request: Request,
    error: str = "",
    success: str = "",
    email: str = "",
    mode: str = "login",
    login_data: dict[str, str] | None = None,
    signup_data: dict[str, str] | None = None,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    with SessionLocal() as session:
        entities = get_entities_for_auth(session)
        admin_metrics = get_admin_login_metrics(session) if mode == "admin" else {}

    if mode not in {"login", "signup", "admin"}:
        mode = "login"

    context = {
        "request": request,
        "error": error,
        "success": success,
        "email": email,
        "mode": mode,
        "login_data": login_data or get_login_defaults(),
        "signup_data": signup_data or get_signup_defaults(),
        "entities": entities,
        "admin_metrics": admin_metrics,
        "oauth_providers": get_oauth_buttons(),
        **get_oauth_flags(),
    }
    return templates.TemplateResponse(request, "login.html", context, status_code=status_code)
