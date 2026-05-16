from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from appverbo.routes.profile.router import router


TRACE_LOGGER_NAME = "APPVERBO_ADMIN_SUBPROCESS_CLICK_TRACE_V1"
TRACE_LOG_PATH = Path("appverbo_runtime_logs") / "admin_subprocess_click_trace.jsonl"

logger = logging.getLogger(TRACE_LOGGER_NAME)


def _clean_trace_value_v1(value: Any, depth: int = 0) -> Any:
    if depth > 5:
        return "[MAX_DEPTH]"

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        clean_value = value.strip()
        if len(clean_value) > 900:
            return clean_value[:900] + "...[TRUNCATED]"
        return clean_value

    if isinstance(value, list):
        return [_clean_trace_value_v1(item, depth + 1) for item in value[:60]]

    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for index, key in enumerate(value.keys()):
            if index >= 100:
                output["_truncated_keys"] = True
                break

            clean_key = str(key).strip()
            lowered_key = clean_key.lower()

            if lowered_key in {
                "password",
                "senha",
                "token",
                "secret",
                "cookie",
                "authorization",
                "csrf",
                "csrf_token",
            }:
                output[clean_key] = "[REDACTED]"
                continue

            output[clean_key] = _clean_trace_value_v1(value.get(key), depth + 1)

        return output

    return str(value)


def _write_jsonl_trace_v1(record: dict[str, Any]) -> None:
    TRACE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with TRACE_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        log_file.write("\n")


@router.post("/debug/admin-subprocess-click-trace", response_class=JSONResponse)
async def admin_subprocess_click_trace_v1(request: Request) -> JSONResponse:
    try:
        raw_payload = await request.json()
    except Exception as exc:
        raw_payload = {
            "payload_error": f"invalid_json: {exc.__class__.__name__}",
        }

    payload = _clean_trace_value_v1(raw_payload)

    record = {
        "logger": TRACE_LOGGER_NAME,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "request": {
            "client": request.client.host if request.client else "",
            "method": request.method,
            "path": request.url.path,
            "url": str(request.url),
        },
        "payload": payload,
    }

    logger.info(
        "APPVERBO_ADMIN_SUBPROCESS_CLICK_TRACE %s",
        json.dumps(record, ensure_ascii=False, sort_keys=True),
    )

    try:
        _write_jsonl_trace_v1(record)
    except Exception as exc:
        logger.warning(
            "APPVERBO_ADMIN_SUBPROCESS_CLICK_TRACE_FILE_WRITE_FAILED %s",
            exc,
        )

    return JSONResponse({"ok": True})
