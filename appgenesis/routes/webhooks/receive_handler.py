from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse

from appgenesis.db.session import SessionLocal
from appgenesis.domains.webhooks.use_cases import record_whatsapp_delivery_statuses

from appgenesis.routes.webhooks.router import router

@router.post("/webhooks/whatsapp")
async def receive_whatsapp_webhook(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse({"status": "invalid-json"}, status_code=status.HTTP_400_BAD_REQUEST)

    with SessionLocal() as session:
        processed_statuses = record_whatsapp_delivery_statuses(session, payload)

    return JSONResponse({"status": "ok", "processed_statuses": processed_statuses})
