from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from fastapi import Request
from fastapi.responses import Response

# ###################################################################################
# (1) CONSTANTS
# ###################################################################################

DEFAULT_LANGUAGE = "pt"
LANGUAGE_COOKIE_NAME = "appverbo_lang"
LANGUAGE_SESSION_KEY = "appverbo_lang"
SUPPORTED_LANGUAGES = ("pt", "en", "es", "fr")
TRANSLATIONS_DIR = Path(__file__).resolve().parents[1] / "i18n"
LANGUAGE_OPTIONS = (
    {"code": "pt", "label": "Português"},
    {"code": "en", "label": "English"},
    {"code": "es", "label": "Español"},
    {"code": "fr", "label": "Français"},
)

AUTH_MESSAGE_KEY_MAP = {
    "Informe email e palavra-passe.": "auth.messages.missing_email_password",
    "Selecione a entidade para entrar como administrador.": "auth.messages.select_admin_entity",
    "Entidade selecionada inválida.": "auth.messages.invalid_selected_entity",
    "Credenciais inválidas.": "auth.messages.invalid_credentials",
    "Acesso administrativo disponível apenas para utilizadores administradores.": (
        "auth.messages.admin_only_access"
    ),
    "Utilizador sem entidade ativa associada.": "auth.messages.user_without_active_entity",
    "Não é permitido entrar com uma entidade diferente da associada ao seu utilizador.": (
        "auth.messages.forbidden_other_entity"
    ),
    "Não tem permissão para entrar na entidade selecionada.": (
        "auth.messages.no_permission_selected_entity"
    ),
    "Já existe conta com este email. Use o login.": "auth.messages.account_exists_use_login",
    "Falha ao criar conta. Tente novamente.": "auth.messages.signup_failed",
    "Sessão encerrada com sucesso.": "auth.messages.logout_success",
    "Provedor não configurado.": "auth.messages.provider_not_configured",
    "Falha na autenticacao externa.": "auth.messages.external_auth_failed",
    "O provedor não devolveu email.": "auth.messages.provider_missing_email",
    "Falha ao concluir login externo.": "auth.messages.external_login_failed",
    "Palavra-passe redefinida com sucesso. Entre com a nova palavra-passe.": (
        "auth.messages.password_reset_success"
    ),
}
ACCOUNT_STATUS_MESSAGE_PATTERN = re.compile(
    r"^Conta com estado '([^']+)'\. Contacte o administrador\.$"
)


# ###################################################################################
# (2) LANGUAGE RESOLUTION
# ###################################################################################

def normalize_language(language: str | None) -> str:
    clean_language = str(language or "").strip().lower()
    if clean_language in SUPPORTED_LANGUAGES:
        return clean_language
    return DEFAULT_LANGUAGE


def resolve_request_language(request: Request) -> str:
    query_language = request.query_params.get("lang")
    if query_language:
        resolved_language = normalize_language(query_language)
        request.session[LANGUAGE_SESSION_KEY] = resolved_language
        return resolved_language

    session_language = request.session.get(LANGUAGE_SESSION_KEY)
    if session_language in SUPPORTED_LANGUAGES:
        return str(session_language)

    cookie_language = request.cookies.get(LANGUAGE_COOKIE_NAME)
    if cookie_language in SUPPORTED_LANGUAGES:
        resolved_language = str(cookie_language)
        request.session[LANGUAGE_SESSION_KEY] = resolved_language
        return resolved_language

    request.session[LANGUAGE_SESSION_KEY] = DEFAULT_LANGUAGE
    return DEFAULT_LANGUAGE


def persist_request_language(response: Response, request: Request, language: str) -> None:
    resolved_language = normalize_language(language)
    request.session[LANGUAGE_SESSION_KEY] = resolved_language
    response.set_cookie(
        LANGUAGE_COOKIE_NAME,
        resolved_language,
        max_age=60 * 60 * 24 * 365,
        samesite="lax",
    )


# ###################################################################################
# (3) TRANSLATION LOADING
# ###################################################################################

@lru_cache(maxsize=len(SUPPORTED_LANGUAGES))
def load_translations(language: str) -> dict[str, Any]:
    resolved_language = normalize_language(language)
    file_path = TRANSLATIONS_DIR / f"{resolved_language}.json"
    with file_path.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Translation file must contain an object: {file_path}")
    return payload


def _resolve_translation_value(payload: dict[str, Any], key: str) -> str | None:
    current_value: Any = payload
    for part in key.split("."):
        if not isinstance(current_value, dict):
            return None
        current_value = current_value.get(part)
    if isinstance(current_value, str):
        return current_value
    return None


def build_translator(language: str) -> Callable[..., str]:
    translations = load_translations(language)

    def translate(key: str, fallback: str = "", **kwargs: Any) -> str:
        template = _resolve_translation_value(translations, key)
        if template is None:
            template = fallback or key
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    return translate


# ###################################################################################
# (4) TEMPLATE CONTEXT AND AUTH MESSAGES
# ###################################################################################

def get_template_language_context(request: Request) -> dict[str, Any]:
    current_language = resolve_request_language(request)
    return {
        "current_lang": current_language,
        "available_languages": [dict(option) for option in LANGUAGE_OPTIONS],
        "t": build_translator(current_language),
    }


def translate_auth_runtime_message(message: str, translator: Callable[..., str]) -> str:
    clean_message = str(message or "").strip()
    if not clean_message:
        return ""

    status_match = ACCOUNT_STATUS_MESSAGE_PATTERN.match(clean_message)
    if status_match is not None:
        status_value = status_match.group(1).strip().lower()
        return translator(
            "auth.messages.account_status",
            status=translator(f"auth.account_status.{status_value}", fallback=status_value),
        )

    translation_key = AUTH_MESSAGE_KEY_MAP.get(clean_message)
    if translation_key:
        return translator(translation_key)

    return clean_message


__all__ = [
    "DEFAULT_LANGUAGE",
    "LANGUAGE_COOKIE_NAME",
    "LANGUAGE_SESSION_KEY",
    "SUPPORTED_LANGUAGES",
    "normalize_language",
    "resolve_request_language",
    "persist_request_language",
    "load_translations",
    "build_translator",
    "get_template_language_context",
    "translate_auth_runtime_message",
]
