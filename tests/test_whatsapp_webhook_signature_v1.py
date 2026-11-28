"""POST do webhook WhatsApp so e aceite com X-Hub-Signature-256 valido (falha fechada)."""

import hashlib
import hmac
import json
from dataclasses import replace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import appgenesis.domains.webhooks.use_cases as use_cases
import appgenesis.routes.webhooks.receive_handler as receive_module
from appgenesis.routes.webhooks.router import router

BODY = json.dumps({"entry": []}).encode()


def _client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


class _Session:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_webhook_closed_without_app_secret():
    with patch.object(use_cases, "settings", replace(use_cases.settings, WHATSAPP_APP_SECRET="")):
        response = _client().post("/webhooks/whatsapp", content=BODY, headers={"X-Hub-Signature-256": _sign("x", BODY)})
    assert response.status_code == 403


def test_webhook_rejects_bad_signature_and_accepts_valid_one():
    with patch.object(use_cases, "settings", replace(use_cases.settings, WHATSAPP_APP_SECRET="s3gredo")), patch.object(
        receive_module, "SessionLocal", _Session
    ), patch.object(receive_module, "record_whatsapp_delivery_statuses", return_value=0) as record_mock:
        client = _client()
        bad = client.post("/webhooks/whatsapp", content=BODY, headers={"X-Hub-Signature-256": _sign("outro", BODY)})
        missing = client.post("/webhooks/whatsapp", content=BODY)
        good = client.post("/webhooks/whatsapp", content=BODY, headers={"X-Hub-Signature-256": _sign("s3gredo", BODY)})
    assert bad.status_code == 403 and missing.status_code == 403
    assert good.status_code == 200 and record_mock.call_count == 1
