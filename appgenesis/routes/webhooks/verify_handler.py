from __future__ import annotations

from fastapi import Query, status
from fastapi.responses import PlainTextResponse

from appgenesis.domains.webhooks.use_cases import verify_whatsapp_subscription_challenge

from appgenesis.routes.webhooks.router import router

@router.get("/webhooks/whatsapp")
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
) -> PlainTextResponse:
    challenge = verify_whatsapp_subscription_challenge(hub_mode, hub_challenge, hub_verify_token)
    if challenge is not None:
        return PlainTextResponse(challenge, status_code=status.HTTP_200_OK)
    return PlainTextResponse("forbidden", status_code=status.HTTP_403_FORBIDDEN)
