from __future__ import annotations

from datetime import datetime
import unicodedata
from typing import Any

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.models import AdminDefinition
from appverbo.services.admin_definition_scope import list_admin_definitions_in_scope_v1
from appverbo.services.entity_scope import (
    ENTITY_SCOPE_DEFAULT_LABEL_V1,
    build_entity_scope_display_v1,
    build_entity_scope_name_map_v1,
    build_entity_scope_internal_number_map_v1,
    coerce_entity_scope_id_v1,
    is_record_visible_for_selected_entity_v1,
    resolve_selected_entity_scope_id_v1,
)


DEFINITION_TYPE_VALUES_V1 = {
    "tamanho",
    "fonte",
    "cor",
    "icone",
}

DEFINITION_STATUS_ACTIVE_V1 = "active"
DEFINITION_STATUS_INACTIVE_V1 = "inactive"


####################################################################################
# (1) REPOSITORY DO SUBPROCESSO DEFINICOES
####################################################################################


class DefinitionAdminRepository(BaseAdminSubprocessRepository):
    def _normalize_text(self, value: object) -> str:
        return " ".join(str(value or "").strip().split())

    def _normalize_lower(self, value: object) -> str:
        return self._normalize_text(value).lower()

    def _normalize_ascii(self, value: object) -> str:
        normalized = unicodedata.normalize("NFD", self._normalize_lower(value))
        return "".join(
            character
            for character in normalized
            if unicodedata.category(character) != "Mn"
        )

    def _normalize_definition_type(self, value: object) -> str:
        clean_value = self._normalize_ascii(value)

        aliases = {
            "tamanho": "tamanho",
            "size": "tamanho",
            "fonte": "fonte",
            "font": "fonte",
            "cor": "cor",
            "color": "cor",
            "icone": "icone",
            "icon": "icone",
        }

        mapped_value = aliases.get(clean_value, clean_value)

        if mapped_value not in DEFINITION_TYPE_VALUES_V1:
            return "tamanho"

        return mapped_value

    def _normalize_status(self, value: object) -> str:
        clean_value = self._normalize_ascii(value)

        if clean_value in {"inactive", "inativo", "0", "false", "no", "nao", "off"}:
            return DEFINITION_STATUS_INACTIVE_V1

        return DEFINITION_STATUS_ACTIVE_V1

    def _status_label(self, value: object) -> str:
        if self._normalize_status(value) == DEFINITION_STATUS_INACTIVE_V1:
            return "Inativo"

        return "Ativo"

    def _type_label(self, value: object) -> str:
        clean_type = self._normalize_definition_type(value)
        return {
            "tamanho": "Tamanho",
            "fonte": "Fonte",
            "cor": "Cor",
            "icone": "Icone",
        }.get(clean_type, "Tamanho")

    def _coerce_int(self, value: object) -> int | None:
        clean_value = self._normalize_text(value)

        if not clean_value.isdigit():
            return None

        return int(clean_value)

    def _format_datetime_label(self, value: object) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")

        return self._normalize_text(value)

    def _resolve_entity_scope_label(
        self,
        *,
        entity_id: object,
        entity_name_by_id: dict[int, str],
    ) -> str:
        parsed_entity_id = coerce_entity_scope_id_v1(entity_id)

        if parsed_entity_id is None:
            return ENTITY_SCOPE_DEFAULT_LABEL_V1

        return entity_name_by_id.get(parsed_entity_id, f"Entidade {parsed_entity_id}")

    def _to_row(
        self,
        model: AdminDefinition,
        *,
        entity_name_by_id: dict[int, str],
        entity_internal_number_by_id: dict[int, str],
    ) -> dict[str, Any]:
        clean_status = self._normalize_status(model.status)
        clean_type = self._normalize_definition_type(model.parameter_type)
        parsed_entity_id = coerce_entity_scope_id_v1(model.entity_id)
        if parsed_entity_id is None:
            entity_internal_number = "Default"
        else:
            entity_internal_number = entity_internal_number_by_id.get(parsed_entity_id, str(parsed_entity_id))

        return {
            "id": int(model.id),
            "key": str(model.id),
            "entity_id": parsed_entity_id,
            "entity_scope_label": self._resolve_entity_scope_label(
                entity_id=parsed_entity_id,
                entity_name_by_id=entity_name_by_id,
            ),
            "entity_internal_number": entity_internal_number,
            "is_global_scope": parsed_entity_id is None,
            "parameter_name": self._normalize_text(model.parameter_name),
            "parameter_type": clean_type,
            "parameter_type_label": self._type_label(clean_type),
            "initial_value": self._normalize_text(model.initial_value),
            "process_name": self._normalize_text(model.process_name),
            "subprocess_name": self._normalize_text(model.subprocess_name),
            "status": clean_status,
            "status_label": self._status_label(clean_status),
            "is_active": clean_status == DEFINITION_STATUS_ACTIVE_V1,
            "can_delete": clean_status != DEFINITION_STATUS_ACTIVE_V1,
            "created_at": self._format_datetime_label(model.created_at),
            "updated_at": self._format_datetime_label(model.updated_at),
        }

    def _validate_payload(self, payload: dict[str, Any]) -> tuple[bool, str]:
        if not self._normalize_text(payload.get("parameter_name")):
            return False, "Informe o nome do parametro."

        if not self._normalize_text(payload.get("initial_value")):
            return False, "Informe o valor inicial."

        if not self._normalize_text(payload.get("process_name")):
            return False, "Informe o processo."

        if not self._normalize_text(payload.get("subprocess_name")):
            return False, "Informe o subprocesso."

        return True, ""

    def _get_scoped_record(
        self,
        *,
        session: Any,
        definition_id: str,
        selected_entity_id: object,
    ) -> AdminDefinition | None:
        parsed_id = self._coerce_int(definition_id)

        if parsed_id is None:
            return None

        record = session.get(AdminDefinition, parsed_id)

        if record is None:
            return None

        if not is_record_visible_for_selected_entity_v1(
            record_entity_id=record.entity_id,
            selected_entity_id=selected_entity_id,
        ):
            return None

        return record

    def list_rows(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        selected_entity_id = resolve_selected_entity_scope_id_v1(context)
        rows = list_admin_definitions_in_scope_v1(
            session,
            selected_entity_id=selected_entity_id,
        )
        entity_ids = {
            int(row.entity_id)
            for row in rows
            if coerce_entity_scope_id_v1(row.entity_id) is not None
        }
        entity_name_by_id = build_entity_scope_name_map_v1(session, entity_ids)
        entity_internal_number_by_id = build_entity_scope_internal_number_map_v1(session, entity_ids)

        normalized_rows = [
            self._to_row(row, entity_name_by_id=entity_name_by_id, entity_internal_number_by_id=entity_internal_number_by_id)
            for row in rows
        ]
        normalized_rows.sort(
            key=lambda row: (
                bool(row.get("is_global_scope")),
                self._normalize_ascii(row.get("parameter_name")),
                self._normalize_ascii(row.get("process_name")),
                self._normalize_ascii(row.get("subprocess_name")),
                self._coerce_int(row.get("id")) or 0,
            )
        )

        return normalized_rows

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        record = self._get_scoped_record(
            session=session,
            definition_id=edit_key,
            selected_entity_id=resolve_selected_entity_scope_id_v1(context),
        )

        if record is None:
            return None

        entity_ids = [record.entity_id] if coerce_entity_scope_id_v1(record.entity_id) is not None else []
        entity_name_by_id = build_entity_scope_name_map_v1(session, entity_ids)
        entity_internal_number_by_id = build_entity_scope_internal_number_map_v1(session, entity_ids)
        return self._to_row(record, entity_name_by_id=entity_name_by_id, entity_internal_number_by_id=entity_internal_number_by_id)

    def create_definition(
        self,
        *,
        session: Any,
        payload: dict[str, Any],
        selected_entity_id: object = None,
    ) -> tuple[bool, str, int]:
        valid, validation_error = self._validate_payload(payload)

        if not valid:
            return False, validation_error, 0

        record = AdminDefinition(
            entity_id=coerce_entity_scope_id_v1(selected_entity_id),
            parameter_name=self._normalize_text(payload.get("parameter_name")),
            parameter_type=self._normalize_definition_type(payload.get("parameter_type")),
            initial_value=self._normalize_text(payload.get("initial_value")),
            process_name=self._normalize_text(payload.get("process_name")),
            subprocess_name=self._normalize_text(payload.get("subprocess_name")),
            status=self._normalize_status(payload.get("status")),
        )
        session.add(record)
        session.flush()

        return True, "", int(record.id)

    def update_definition(
        self,
        *,
        session: Any,
        definition_id: str,
        payload: dict[str, Any],
        selected_entity_id: object = None,
    ) -> tuple[bool, str]:
        if self._coerce_int(definition_id) is None:
            return False, "Definicao invalida para edicao."

        valid, validation_error = self._validate_payload(payload)
        if not valid:
            return False, validation_error

        record = self._get_scoped_record(
            session=session,
            definition_id=definition_id,
            selected_entity_id=selected_entity_id,
        )

        if record is None:
            return False, "Definicao nao encontrada para edicao."

        record.parameter_name = self._normalize_text(payload.get("parameter_name"))
        record.parameter_type = self._normalize_definition_type(payload.get("parameter_type"))
        record.initial_value = self._normalize_text(payload.get("initial_value"))
        record.process_name = self._normalize_text(payload.get("process_name"))
        record.subprocess_name = self._normalize_text(payload.get("subprocess_name"))
        record.status = self._normalize_status(payload.get("status"))

        session.add(record)
        return True, ""

    def delete_definition(
        self,
        *,
        session: Any,
        definition_id: str,
        selected_entity_id: object = None,
    ) -> tuple[bool, str]:
        if self._coerce_int(definition_id) is None:
            return False, "Definicao invalida para eliminar."

        record = self._get_scoped_record(
            session=session,
            definition_id=definition_id,
            selected_entity_id=selected_entity_id,
        )

        if record is None:
            return False, "Definicao nao encontrada para eliminar."

        if self._normalize_status(record.status) == DEFINITION_STATUS_ACTIVE_V1:
            return False, "So e permitido eliminar definicoes inativas."

        session.delete(record)
        return True, ""

    def create(
        self,
        session: Any,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _, _ = self.create_definition(
            session=session,
            payload=payload,
            selected_entity_id=resolve_selected_entity_scope_id_v1(context),
        )
        return ok

    def update(
        self,
        session: Any,
        edit_key: str,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _ = self.update_definition(
            session=session,
            definition_id=edit_key,
            payload=payload,
            selected_entity_id=resolve_selected_entity_scope_id_v1(context),
        )
        return ok

    def move(
        self,
        session: Any,
        edit_key: str,
        direction: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        return False

    def delete(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _ = self.delete_definition(
            session=session,
            definition_id=edit_key,
            selected_entity_id=resolve_selected_entity_scope_id_v1(context),
        )
        return ok
