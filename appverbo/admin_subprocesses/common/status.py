from __future__ import annotations

from typing import Any, Iterable


# ###################################################################################
# (1) VALORES PADRAO DE STATUS
# ###################################################################################

INACTIVE_STATUS_VALUES = {
    "inativo",
    "inactive",
    "0",
    "false",
    "no",
    "nao",
    "n\u00e3o",
    "off",
}

ACTIVE_STATUS_VALUES = {
    "ativo",
    "active",
    "1",
    "true",
    "yes",
    "sim",
    "on",
}


STATUS_LABELS_PT = {
    "active": "Ativo",
    "inactive": "Inativo",
    "pending": "Pendente",
    "blocked": "Bloqueado",
    "ativo": "Ativo",
    "inativo": "Inativo",
}


# ###################################################################################
# (2) NORMALIZACAO DE STATUS
# ###################################################################################

def normalize_status_key_v1(value: object) -> str:
    return str(value or "").strip().lower()


def normalize_active_inactive_status_v1(
    value: object,
    *,
    active_value: str = "ativo",
    inactive_value: str = "inativo",
    raw_is_active: object = None,
) -> str:
    if raw_is_active is False:
        return inactive_value

    clean_value = normalize_status_key_v1(value)

    if clean_value in INACTIVE_STATUS_VALUES:
        return inactive_value

    if clean_value in ACTIVE_STATUS_VALUES:
        return active_value

    return active_value


def build_status_label_pt_v1(value: object) -> str:
    clean_value = normalize_status_key_v1(value)

    if clean_value in STATUS_LABELS_PT:
        return STATUS_LABELS_PT[clean_value]

    if clean_value in ACTIVE_STATUS_VALUES:
        return "Ativo"

    if clean_value in INACTIVE_STATUS_VALUES:
        return "Inativo"

    return str(value or "").strip() or "-"


# ###################################################################################
# (3) SEPARACAO DE LINHAS ATIVAS E INATIVAS
# ###################################################################################

def row_is_active_v1(
    row: dict[str, Any],
    *,
    status_field: str = "status",
    active_value: str = "ativo",
    inactive_value: str = "inativo",
) -> bool:
    normalized_status = normalize_active_inactive_status_v1(
        row.get(status_field),
        active_value=active_value,
        inactive_value=inactive_value,
        raw_is_active=row.get("is_active"),
    )

    return normalized_status == active_value


def split_rows_by_status_v1(
    rows: Iterable[dict[str, Any]],
    *,
    status_field: str = "status",
    active_value: str = "ativo",
    inactive_value: str = "inativo",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active_rows: list[dict[str, Any]] = []
    inactive_rows: list[dict[str, Any]] = []

    for raw_row in rows:
        row = dict(raw_row)

        if row_is_active_v1(
            row,
            status_field=status_field,
            active_value=active_value,
            inactive_value=inactive_value,
        ):
            active_rows.append(row)
        else:
            inactive_rows.append(row)

    return active_rows, inactive_rows