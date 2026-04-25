from __future__ import annotations

import base64
import hmac
import hashlib
import json
import secrets
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any
from urllib.parse import quote

from appverbo.core import *  # noqa: F403,F401

SIGNUP_COUNTRY_PHONE_OPTIONS: tuple[dict[str, str], ...] = (
    {
        "value": "PT",
        "label": "Portugal",
        "calling_code": "+351",
        "placeholder": "+351 910 000 000",
    },
    {
        "value": "BR",
        "label": "Brasil",
        "calling_code": "+55",
        "placeholder": "+55 11 99999-9999",
    },
)


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

def build_user_invite_token(
    user_id: int,
    login_email: str,
    entity_id: int | None = None,
) -> str:
    issued_at = int(time.time())
    payload = {
        "uid": int(user_id),
        "email": (login_email or "").strip().lower(),
        "iat": issued_at,
    }
    if isinstance(entity_id, int) and entity_id > 0:
        payload["eid"] = int(entity_id)
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
    entity_id_raw = payload.get("eid")
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    if not login_email:
        return None
    if not isinstance(issued_at, int) or issued_at <= 0:
        return None
    entity_id: int | None = None
    if entity_id_raw is not None:
        if not isinstance(entity_id_raw, int) or entity_id_raw <= 0:
            return None
        entity_id = int(entity_id_raw)

    max_token_age = max(int(USER_INVITE_TTL_HOURS), 1) * 3600
    if int(time.time()) - issued_at > max_token_age:
        return None

    return {
        "uid": user_id,
        "email": login_email,
        "iat": issued_at,
        "entity_id": entity_id,
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

def get_signup_defaults() -> dict[str, str]:
    return {
        "full_name": "",
        "country": "",
        "primary_phone": "",
        "email": "",
        "entity_id": "",
        "entity_name": "",
        "entity_locked": "",
    }

def get_login_defaults() -> dict[str, str]:
    return {
        "entity_id": "",
    }


def get_signup_country_options() -> list[dict[str, str]]:
    return [dict(option) for option in SIGNUP_COUNTRY_PHONE_OPTIONS]


def validate_signup_phone_country(country: str, primary_phone: str) -> str:
    clean_country = (country or "").strip().upper()
    clean_phone = (primary_phone or "").strip()
    if not clean_country:
        return "País é obrigatório."
    if not clean_phone:
        return "Telefone principal é obrigatório."

    selected_option = next(
        (option for option in SIGNUP_COUNTRY_PHONE_OPTIONS if option["value"] == clean_country),
        None,
    )
    if selected_option is None:
        return "País inválido."

    expected_code = selected_option["calling_code"]
    if not clean_phone.startswith(expected_code):
        return (
            f"Telefone inválido para {selected_option['label']}. "
            f"Use o código {expected_code}."
        )
    return ""

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
    from appverbo.services.page import get_next_entity_internal_number

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
        "signup_country_options": get_signup_country_options(),
        "entities": entities,
        "admin_metrics": admin_metrics,
        "oauth_providers": get_oauth_buttons(),
        **get_oauth_flags(),
    }
    return templates.TemplateResponse(request, "login.html", context, status_code=status_code)

__all__ = [
    "hash_password",
    "verify_password",
    "_urlsafe_b64encode",
    "_urlsafe_b64decode",
    "build_user_invite_token",
    "parse_user_invite_token",
    "build_user_invite_link",
    "send_user_invite_email",
    "get_signup_defaults",
    "get_signup_country_options",
    "get_login_defaults",
    "validate_signup_phone_country",
    "get_oauth_flags",
    "get_oauth_buttons",
    "get_entities_for_auth",
    "resolve_active_entity_by_email",
    "is_admin_user",
    "is_allowed_global_profile",
    "get_or_create_entity_superuser_profile",
    "get_admin_login_metrics",
    "get_oauth_client",
    "fetch_oauth_userinfo",
    "upsert_user_by_email",
    "render_login",
]
