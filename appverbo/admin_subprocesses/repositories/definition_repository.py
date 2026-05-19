from __future__ import annotations

from datetime import datetime
import unicodedata
from typing import Any

from sqlalchemy import select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.models import AdminDefinition


DEFINITION_TYPE_VALUES_V1 = {
    "tamanho",
    "fonte",
    "cor",
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
        return "Inativo" if self._normalize_status(value) == DEFINITION_STATUS_INACTIVE_V1 else "Ativo"

    def _type_label(self, value: object) -> str:
        clean_type = self._normalize_definition_type(value)
        return {
            "tamanho": "Tamanho",
            "fonte": "Fonte",
            "cor": "Cor",
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

    def _to_row(self, model: AdminDefinition) -> dict[str, Any]:
        clean_status = self._normalize_status(model.status)
        clean_type = self._normalize_definition_type(model.parameter_type)

        return {
            "id": int(model.id),
            "key": str(model.id),
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
            return False, "Informe o nome do parâmetro."

        if not self._normalize_text(payload.get("initial_value")):
            return False, "Informe o valor inicial."

        if not self._normalize_text(payload.get("process_name")):
            return False, "Informe o processo."

        if not self._normalize_text(payload.get("subprocess_name")):
            return False, "Informe o subprocesso."

        return True, ""

    def list_rows(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        rows = session.execute(
            select(AdminDefinition).order_by(
                AdminDefinition.process_name.asc(),
                AdminDefinition.subprocess_name.asc(),
                AdminDefinition.parameter_name.asc(),
                AdminDefinition.id.asc(),
            )
        ).scalars().all()

        return [self._to_row(row) for row in rows]

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        parsed_id = self._coerce_int(edit_key)

        if parsed_id is None:
            return None

        record = session.get(AdminDefinition, parsed_id)

        if record is None:
            return None

        return self._to_row(record)

    def create_definition(
        self,
        *,
        session: Any,
        payload: dict[str, Any],
    ) -> tuple[bool, str, int]:
        valid, validation_error = self._validate_payload(payload)

        if not valid:
            return False, validation_error, 0

        record = AdminDefinition(
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
    ) -> tuple[bool, str]:
        parsed_id = self._coerce_int(definition_id)

        if parsed_id is None:
            return False, "Definição inválida para edição."

        valid, validation_error = self._validate_payload(payload)
        if not valid:
            return False, validation_error

        record = session.get(AdminDefinition, parsed_id)

        if record is None:
            return False, "Definição não encontrada para edição."

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
    ) -> tuple[bool, str]:
        parsed_id = self._coerce_int(definition_id)

        if parsed_id is None:
            return False, "Definição inválida para eliminar."

        record = session.get(AdminDefinition, parsed_id)

        if record is None:
            return False, "Definição não encontrada para eliminar."

        if self._normalize_status(record.status) == DEFINITION_STATUS_ACTIVE_V1:
            return False, "Só é permitido eliminar definições inativas."

        session.delete(record)
        return True, ""

    def create(
        self,
        session: Any,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _, _ = self.create_definition(session=session, payload=payload)
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
        )
        return ok
