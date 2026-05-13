from __future__ import annotations

from typing import Any

from appverbo.services.user_status import user_account_status_label_pt_v1


def present_admin_user_row_v1(row: dict[str, Any]) -> dict[str, Any]:
    clean = dict(row or {})
    status = clean.get("status") or clean.get("account_status") or ""
    clean["status_label"] = user_account_status_label_pt_v1(status)
    return clean


def split_active_inactive_users_v1(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active: list[dict[str, Any]] = []
    inactive: list[dict[str, Any]] = []

    for row in rows or []:
        presented = present_admin_user_row_v1(row)
        if str(presented.get("status") or "").strip().lower() == "active":
            active.append(presented)
        else:
            inactive.append(presented)

    return active, inactive

