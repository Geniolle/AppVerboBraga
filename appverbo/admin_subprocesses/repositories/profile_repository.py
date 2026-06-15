from __future__ import annotations

from typing import Any

from sqlalchemy import select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.models.profile import Profile
from appverbo.services.entity_scope import (
    coerce_entity_scope_id_v1,
    resolve_selected_entity_scope_id_v1,
)


PROFILE_STATUS_ACTIVE_V1 = "ativo"
PROFILE_STATUS_INACTIVE_V1 = "inativo"

PROFILE_VISIBILITY_ENTITY_V1 = "entity"
PROFILE_VISIBILITY_ALL_V1 = "all"


# ###################################################################################
# (1) REPOSITORY DO SUBPROCESSO PERFIL
# ###################################################################################


class ProfileAdminRepository(BaseAdminSubprocessRepository):

    def _normalize_text(self, value: object) -> str:
        return " ".join(str(value or "").strip().split())

    def _normalize_lower(self, value: object) -> str:
        return self._normalize_text(value).lower()

    def _normalize_status(self, value: object) -> str:
        clean = self._normalize_lower(value)
        if clean in {"inativo", "inactive", "0", "false", "no", "off"}:
            return PROFILE_STATUS_INACTIVE_V1
        return PROFILE_STATUS_ACTIVE_V1

    def _status_label(self, value: object) -> str:
        if self._normalize_status(value) == PROFILE_STATUS_INACTIVE_V1:
            return "Inativo"
        return "Ativo"

    def _normalize_visibility(self, value: object) -> str:
        clean = self._normalize_lower(value)
        if clean in {"all", "todos os sistemas", "todos sistemas"}:
            return PROFILE_VISIBILITY_ALL_V1
        return PROFILE_VISIBILITY_ENTITY_V1

    def _visibility_label(self, value: object) -> str:
        if self._normalize_visibility(value) == PROFILE_VISIBILITY_ALL_V1:
            return "Todos os sistemas"
        return "Esta entidade"

    def _coerce_int(self, value: object) -> int | None:
        clean = self._normalize_text(value)
        if clean.isdigit():
            return int(clean)
        return None

    def _to_row(self, model: Profile) -> dict[str, Any]:
        clean_status = self._normalize_status(
            PROFILE_STATUS_ACTIVE_V1 if model.is_active else PROFILE_STATUS_INACTIVE_V1
        )
        clean_visibility = self._normalize_visibility(model.visibility_scope_mode or "entity")

        return {
            "id": int(model.id),
            "key": str(model.id),
            "name": self._normalize_text(model.name),
            "description": self._normalize_text(model.description or ""),
            "visibility_scope_mode": clean_visibility,
            "visibility_scope_label": self._visibility_label(clean_visibility),
            "entity_id": coerce_entity_scope_id_v1(model.entity_id),
            "status": clean_status,
            "status_label": self._status_label(clean_status),
            "is_active": clean_status == PROFILE_STATUS_ACTIVE_V1,
            "can_delete": clean_status != PROFILE_STATUS_ACTIVE_V1,
        }

    def _validate_payload(self, payload: dict[str, Any]) -> tuple[bool, str]:
        if not self._normalize_text(payload.get("name")):
            return False, "Informe o nome do perfil."
        return True, ""

    def _get_scoped_record(
        self,
        *,
        session: Any,
        profile_id: str,
        selected_entity_id: object,
    ) -> Profile | None:
        parsed_id = self._coerce_int(profile_id)
        if parsed_id is None:
            return None

        record = session.get(Profile, parsed_id)
        if record is None:
            return None

        parsed_selected = coerce_entity_scope_id_v1(selected_entity_id)
        parsed_record_entity = coerce_entity_scope_id_v1(record.entity_id)

        if parsed_record_entity is not None and parsed_selected is not None:
            if parsed_record_entity != parsed_selected:
                return None

        return record

    def list_rows(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        selected_entity_id = resolve_selected_entity_scope_id_v1(context)
        parsed_selected = coerce_entity_scope_id_v1(selected_entity_id)

        stmt = select(Profile).order_by(Profile.name)

        records = session.execute(stmt).scalars().all()

        rows = []
        for record in records:
            parsed_record_entity = coerce_entity_scope_id_v1(record.entity_id)
            clean_visibility = self._normalize_visibility(record.visibility_scope_mode or "entity")

            is_own = parsed_selected is not None and parsed_record_entity == parsed_selected
            is_global = parsed_record_entity is None
            is_all_visibility = clean_visibility == PROFILE_VISIBILITY_ALL_V1

            if is_own or is_global or is_all_visibility:
                rows.append(self._to_row(record))

        return rows

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        record = self._get_scoped_record(
            session=session,
            profile_id=edit_key,
            selected_entity_id=resolve_selected_entity_scope_id_v1(context),
        )
        if record is None:
            return None
        return self._to_row(record)

    def create_profile(
        self,
        *,
        session: Any,
        payload: dict[str, Any],
        selected_entity_id: object = None,
    ) -> tuple[bool, str, int]:
        valid, error_msg = self._validate_payload(payload)
        if not valid:
            return False, error_msg, 0

        clean_name = self._normalize_text(payload.get("name"))
        clean_description = self._normalize_text(payload.get("description") or "")
        clean_visibility = self._normalize_visibility(payload.get("visibility_scope_mode") or "entity")
        clean_status = self._normalize_status(payload.get("status") or PROFILE_STATUS_ACTIVE_V1)
        parsed_entity_id = coerce_entity_scope_id_v1(selected_entity_id)

        existing = session.execute(
            select(Profile).where(Profile.name == clean_name)
        ).scalar_one_or_none()
        if existing is not None:
            return False, f"Já existe um perfil com o nome '{clean_name}'.", 0

        record = Profile(
            name=clean_name,
            description=clean_description or None,
            is_active=(clean_status == PROFILE_STATUS_ACTIVE_V1),
            entity_id=parsed_entity_id,
            visibility_scope_mode=clean_visibility,
        )
        session.add(record)
        session.flush()
        return True, "", int(record.id)

    def update_profile(
        self,
        *,
        session: Any,
        profile_id: str,
        payload: dict[str, Any],
        selected_entity_id: object = None,
    ) -> tuple[bool, str]:
        valid, error_msg = self._validate_payload(payload)
        if not valid:
            return False, error_msg

        record = self._get_scoped_record(
            session=session,
            profile_id=profile_id,
            selected_entity_id=selected_entity_id,
        )
        if record is None:
            return False, "Perfil não encontrado para edição."

        clean_name = self._normalize_text(payload.get("name"))
        existing = session.execute(
            select(Profile).where(Profile.name == clean_name, Profile.id != record.id)
        ).scalar_one_or_none()
        if existing is not None:
            return False, f"Já existe um perfil com o nome '{clean_name}'."

        record.name = clean_name
        record.description = self._normalize_text(payload.get("description") or "") or None
        record.visibility_scope_mode = self._normalize_visibility(
            payload.get("visibility_scope_mode") or "entity"
        )
        clean_status = self._normalize_status(payload.get("status") or PROFILE_STATUS_ACTIVE_V1)
        record.is_active = clean_status == PROFILE_STATUS_ACTIVE_V1
        session.add(record)
        return True, ""

    def delete_profile(
        self,
        *,
        session: Any,
        profile_id: str,
        selected_entity_id: object = None,
    ) -> tuple[bool, str]:
        record = self._get_scoped_record(
            session=session,
            profile_id=profile_id,
            selected_entity_id=selected_entity_id,
        )
        if record is None:
            return False, "Perfil não encontrado para eliminar."

        if record.is_active:
            return False, "Só é permitido eliminar perfis inativos."

        session.delete(record)
        return True, ""

    def create(
        self,
        session: Any,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _, _ = self.create_profile(
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
        ok, _ = self.update_profile(
            session=session,
            profile_id=edit_key,
            payload=payload,
            selected_entity_id=resolve_selected_entity_scope_id_v1(context),
        )
        return ok

    def delete(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _ = self.delete_profile(
            session=session,
            profile_id=edit_key,
            selected_entity_id=resolve_selected_entity_scope_id_v1(context),
        )
        return ok
