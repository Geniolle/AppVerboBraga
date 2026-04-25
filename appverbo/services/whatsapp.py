from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any

import httpx

from appverbo.core import *  # noqa: F403,F401

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

__all__ = [
    "has_whatsapp_verification_config",
    "normalize_whatsapp_recipient",
    "extract_whatsapp_api_error",
    "send_whatsapp_verification_template",
    "map_whatsapp_delivery_status",
]
