from __future__ import annotations

from importlib import import_module
from typing import Any

from starlette.datastructures import FormData

from .v2_models import AdminSubprocessConfigV2


# ###################################################################################
# (1) HELPERS GENERICOS
# ###################################################################################

INACTIVE_STATUS_VALUES_V2 = {
    "inativo",
    "inactive",
    "0",
    "false",
    "no",
    "nao",
    "não",
    "off",
}


def normalize_admin_subprocess_text_v2(value: object) -> str:
    return str(value or "").strip()


def normalize_admin_subprocess_key_v2(value: object) -> str:
    return normalize_admin_subprocess_text_v2(value).lower()


def normalize_admin_subprocess_status_v2(
    row: dict[str, Any],
    config: AdminSubprocessConfigV2,
) -> str:
    raw_status = normalize_admin_subprocess_key_v2(row.get(config.status_field))
    raw_is_active = row.get("is_active")

    if raw_is_active is False:
        return config.inactive_value

    if raw_status in INACTIVE_STATUS_VALUES_V2:
        return config.inactive_value

    return config.active_value


def is_admin_subprocess_row_active_v2(
    row: dict[str, Any],
    config: AdminSubprocessConfigV2,
) -> bool:
    return normalize_admin_subprocess_status_v2(row, config) == config.active_value


def split_admin_subprocess_rows_v2(
    rows: list[dict[str, Any]],
    config: AdminSubprocessConfigV2,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active_rows: list[dict[str, Any]] = []
    inactive_rows: list[dict[str, Any]] = []

    for raw_row in rows:
        row = dict(raw_row)
        row[config.status_field] = normalize_admin_subprocess_status_v2(row, config)

        if is_admin_subprocess_row_active_v2(row, config):
            active_rows.append(row)
        else:
            inactive_rows.append(row)

    return active_rows, inactive_rows


def load_repository_class_v2(repository_class_path: str) -> type:
    module_name, class_name = repository_class_path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, class_name)


# ###################################################################################
# (2) BASE REPOSITORY
# ###################################################################################

class BaseAdminSubprocessRepositoryV2:
    def __init__(
        self,
        *,
        session: Any,
        request: Any,
        current_user: dict[str, Any] | None,
        config: AdminSubprocessConfigV2,
    ) -> None:
        self.session = session
        self.request = request
        self.current_user = current_user
        self.config = config

    def list_rows(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_for_edit(self, edit_key: str) -> dict[str, Any] | None:
        clean_edit_key = normalize_admin_subprocess_text_v2(edit_key)

        if not clean_edit_key:
            return None

        for row in self.list_rows():
            if normalize_admin_subprocess_text_v2(row.get(self.config.identity_field)) == clean_edit_key:
                return dict(row)

        return None

    def clean_form(self, form: FormData) -> dict[str, Any]:
        data: dict[str, Any] = {}

        for field in self.config.fields:
            if field.field_type == "file" or field.field_type == "image":
                data[field.key] = form.get(field.resolved_input_name)
                continue

            if field.field_type == "checkbox":
                data[field.key] = "1" if form.get(field.resolved_input_name) else "0"
                continue

            data[field.key] = normalize_admin_subprocess_text_v2(
                form.get(field.resolved_input_name, field.default_value)
            )

        return data

    def validate_required_fields(self, data: dict[str, Any]) -> list[str]:
        missing_labels: list[str] = []

        for field in self.config.fields:
            if not field.required:
                continue

            if field.field_type in {"file", "image"}:
                continue

            if not normalize_admin_subprocess_text_v2(data.get(field.key)):
                missing_labels.append(field.label)

        return missing_labels

    def validate_create(self, data: dict[str, Any]) -> list[str]:
        return self.validate_required_fields(data)

    def validate_update(self, edit_key: str, data: dict[str, Any]) -> list[str]:
        return self.validate_required_fields(data)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def update(self, edit_key: str, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def delete(self, edit_key: str) -> dict[str, Any]:
        raise NotImplementedError

    def move(self, edit_key: str, direction: str) -> dict[str, Any]:
        return {"ok": False, "message": "Ordenação não implementada para este subprocesso."}
