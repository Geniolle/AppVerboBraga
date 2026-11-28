from __future__ import annotations

import json

from fastapi import Request, status
from fastapi.responses import JSONResponse

from appgenesis.db.session import SessionLocal
from appgenesis.domains.webhooks.use_cases import (
    is_valid_whatsapp_signature,
    record_whatsapp_delivery_statuses,
)

from appgenesis.routes.webhooks.router import router

@router.post("/webhooks/whatsapp")
async def receive_whatsapp_webhook(request: Request) -> JSONResponse:
    raw_body = await request.body()
    if not is_valid_whatsapp_signature(raw_body, request.headers.get("X-Hub-Signature-256")):
        return JSONResponse({"status": "invalid-signature"}, status_code=status.HTTP_403_FORBIDDEN)
    try:
        payload = json.loads(raw_body)
    except ValueError:
        return JSONResponse({"status": "invalid-json"}, status_code=status.HTTP_400_BAD_REQUEST)

    with SessionLocal() as session:
        processed_statuses = record_whatsapp_delivery_statuses(session, payload)

    return JSONResponse({"status": "ok", "processed_statuses": processed_statuses})
