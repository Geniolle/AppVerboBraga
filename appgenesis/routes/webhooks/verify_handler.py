from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appgenesis.core import WHATSAPP_WEBHOOK_VERIFY_TOKEN
from appgenesis.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
)

from appgenesis.routes.webhooks.router import router

@router.get("/webhooks/whatsapp")
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
) -> PlainTextResponse:
    if (
        hub_mode == "subscribe"
        and hub_challenge is not None
        and WHATSAPP_WEBHOOK_VERIFY_TOKEN
        and hub_verify_token == WHATSAPP_WEBHOOK_VERIFY_TOKEN
    ):
        return PlainTextResponse(hub_challenge, status_code=status.HTTP_200_OK)
    return PlainTextResponse("forbidden", status_code=status.HTTP_403_FORBIDDEN)
