from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.core import *  # noqa: F403,F401
from appverbo.services import *  # noqa: F403,F401
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

from appverbo.routes.webhooks.router import router

@router.post("/webhooks/whatsapp")
async def receive_whatsapp_webhook(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse({"status": "invalid-json"}, status_code=status.HTTP_400_BAD_REQUEST)

    processed_statuses = 0
    with SessionLocal() as session:
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

                    member = session.execute(
                        select(Member).where(Member.whatsapp_last_message_id == message_id)
                    ).scalar_one_or_none()
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

    return JSONResponse({"status": "ok", "processed_statuses": processed_statuses})
