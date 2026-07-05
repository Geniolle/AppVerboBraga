from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from appgenesis.core import WHATSAPP_WEBHOOK_VERIFY_TOKEN
from appgenesis.domains.webhooks.repositories import find_member_by_whatsapp_message_id
from appgenesis.services.whatsapp import map_whatsapp_delivery_status


def verify_whatsapp_subscription_challenge(
    hub_mode: str | None,
    hub_challenge: str | None,
    hub_verify_token: str | None,
) -> str | None:
    if (
        hub_mode == "subscribe"
        and hub_challenge is not None
        and WHATSAPP_WEBHOOK_VERIFY_TOKEN
        and hub_verify_token == WHATSAPP_WEBHOOK_VERIFY_TOKEN
    ):
        return hub_challenge
    return None


def record_whatsapp_delivery_statuses(session: Session, payload: dict[str, Any]) -> int:
    processed_statuses = 0
    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes", []):
            if not isinstance(change, dict):
                continue
            value = change.get("value")
            if not isinstance(value, dict):
                continue
            statuses = value.get("statuses") or []
            if not isinstance(statuses, list):
                continue

            for status_item in statuses:
                if not isinstance(status_item, dict):
                    continue
                message_id = str(status_item.get("id") or "").strip()
                if not message_id:
                    continue

                member = find_member_by_whatsapp_message_id(session, message_id)
                if member is None:
                    continue

                processed_statuses += 1
                delivery_status = str(status_item.get("status") or "").strip().lower()
                member.whatsapp_verification_status = map_whatsapp_delivery_status(delivery_status)
                member.whatsapp_last_check_at = datetime.now(timezone.utc)

                recipient_id = str(status_item.get("recipient_id") or "").strip()
                if recipient_id:
                    member.whatsapp_last_wa_id = recipient_id

                error_message = ""
                errors = status_item.get("errors") or []
                if isinstance(errors, list) and errors:
                    first_error = errors[0]
                    if isinstance(first_error, dict):
                        error_message = str(
                            first_error.get("title")
                            or first_error.get("message")
                            or ""
                        ).strip()
                if not error_message and delivery_status in {"failed", "undelivered"}:
                    error_message = f"Entrega não concluída ({delivery_status})."
                member.whatsapp_last_error = error_message or None

    session.commit()
    return processed_statuses
