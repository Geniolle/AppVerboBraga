from __future__ import annotations

from typing import Any

from sqlalchemy import case, select

from appverbo.core import *  # noqa: F403,F401
from appverbo.models import Entity
from appverbo.services.entities import (
    apply_entity_form_data_v1,
    clean_entity_form_data_v1,
    get_duplicate_entity_name_id_v1,
    get_existing_owner_entity_id_v1,
    save_entity_logo_upload,
    validate_entity_required_fields_v1,
)

from .v2_repository import (
    BaseAdminSubprocessRepositoryV2,
    normalize_admin_subprocess_text_v2,
)


# ###################################################################################
# (1) LABELS
# ###################################################################################

def entity_scope_label_v2(value: object) -> str:
    clean_value = str(value or "").strip().lower()

    if clean_value == "owner":
        return "Owner"

    return "Legado"


def entity_status_label_v2(is_active: object) -> str:
    return "Ativo" if bool(is_active) else "Inativo"


def format_entity_created_at_v2(value: object) -> str:
    if value is None:
        return ""

    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")

    return str(value or "").strip()


# ###################################################################################
# (2) REPOSITORY ENTIDADE V2
# ###################################################################################

class EntityAdminSubprocessRepositoryV2(BaseAdminSubprocessRepositoryV2):
    def list_rows(self) -> list[dict[str, Any]]:
        entities = self.session.scalars(
            select(Entity).order_by(
                Entity.is_active.desc(),
                case((Entity.internal_number.is_(None), 1), else_=0),
                Entity.internal_number.asc(),
                Entity.id.asc(),
            )
        ).all()

        rows: list[dict[str, Any]] = []

        for entity in entities:
            rows.append(self.entity_to_row_v2(entity))

        return rows

    def entity_to_row_v2(self, entity: Entity) -> dict[str, Any]:
        return {
            "id": str(entity.id),
            "internal_number": "" if entity.internal_number is None else str(entity.internal_number),
            "name": entity.name or "",
            "label": entity.name or "",
            "acronym": entity.acronym or "",
            "tax_id": entity.tax_id or "",
            "email": entity.email or "",
            "responsible_name": entity.responsible_name or "",
            "door_number": entity.door_number or "",
            "address": entity.address or "",
            "city": entity.city or "",
            "freguesia": entity.freguesia or "",
            "postal_code": entity.postal_code or "",
            "country": entity.country or "",
            "phone": entity.phone or "",
            "logo_url": entity.logo_url or "",
            "description": entity.description or "",
            "profile_scope": entity.profile_scope or "legado",
            "profile_scope_label": entity_scope_label_v2(entity.profile_scope),
            "created_at": entity.created_at,
            "created_at_display": format_entity_created_at_v2(entity.created_at),
            "is_active": bool(entity.is_active),
            "status": self.config.active_value if entity.is_active else self.config.inactive_value,
            "status_label": entity_status_label_v2(entity.is_active),
        }

    def get_entity_v2(self, edit_key: str) -> Entity | None:
        try:
            entity_id = int(str(edit_key or "").strip())
        except ValueError:
            return None

        return self.session.get(Entity, entity_id)

    def get_for_edit(self, edit_key: str) -> dict[str, Any] | None:
        entity = self.get_entity_v2(edit_key)

        if entity is None:
            return None

        return self.entity_to_row_v2(entity)

    def clean_form(self, form: Any) -> dict[str, Any]:
        form_data, invalid_profile_scope = clean_entity_form_data_v1(
            name=form.get("name", ""),
            acronym=form.get("acronym", ""),
            tax_id=form.get("tax_id", ""),
            email=form.get("email", ""),
            responsible_name=form.get("responsible_name", ""),
            door_number=form.get("door_number", ""),
            address=form.get("address", ""),
            city=form.get("city", ""),
            freguesia=form.get("freguesia", ""),
            postal_code=form.get("postal_code", ""),
            country=form.get("country", ""),
            phone=form.get("phone", ""),
            entity_profile_scope=form.get("entity_profile_scope", form.get("profile_scope", "legado")),
            description=form.get("description", ""),
            created_at_text="",
        )

        form_data["status"] = normalize_admin_subprocess_text_v2(form.get("status", "active")) or "active"
        form_data["logo_file"] = form.get("entity_logo_file")
        form_data["invalid_profile_scope"] = invalid_profile_scope

        return form_data

    def validate_entity_v2(
        self,
        data: dict[str, Any],
        *,
        ignore_entity_id: int | None = None,
    ) -> list[str]:
        errors: list[str] = []

        missing_labels = validate_entity_required_fields_v1(data)

        if data.get("invalid_profile_scope"):
            missing_labels.append("Perfil da entidade")

        if missing_labels:
            errors.append("Preencha os campos obrigatórios: " + ", ".join(missing_labels) + ".")

        clean_name = normalize_admin_subprocess_text_v2(data.get("name"))

        if clean_name and get_duplicate_entity_name_id_v1(
            self.session,
            clean_name,
            ignore_entity_id=ignore_entity_id,
        ) is not None:
            errors.append("Já existe uma entidade com este nome.")

        if normalize_admin_subprocess_text_v2(data.get("profile_scope")).lower() == "owner":
            existing_owner_id = get_existing_owner_entity_id_v1(
                self.session,
                ignore_entity_id=ignore_entity_id,
            )

            if existing_owner_id is not None:
                errors.append("Já existe uma entidade com perfil Owner. Apenas uma é permitida.")

        return errors

    def validate_create(self, data: dict[str, Any]) -> list[str]:
        return self.validate_entity_v2(data)

    def validate_update(self, edit_key: str, data: dict[str, Any]) -> list[str]:
        entity = self.get_entity_v2(edit_key)

        if entity is None:
            return ["Entidade não encontrada."]

        return self.validate_entity_v2(data, ignore_entity_id=entity.id)

    def get_next_internal_number_v2(self) -> int:
        used_numbers = self.session.scalars(
            select(Entity.internal_number)
            .where(
                Entity.internal_number.is_not(None),
                Entity.internal_number >= ENTITY_INTERNAL_NUMBER_MIN,
                Entity.internal_number <= ENTITY_INTERNAL_NUMBER_MAX,
            )
            .order_by(Entity.internal_number.asc())
        ).all()

        used_set = {
            int(number)
            for number in used_numbers
            if isinstance(number, int)
        }

        for candidate in range(ENTITY_INTERNAL_NUMBER_MIN, ENTITY_INTERNAL_NUMBER_MAX + 1):
            if candidate not in used_set:
                return candidate

        return ENTITY_INTERNAL_NUMBER_MAX

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        stored_logo_url = ""
        logo_error = ""

        logo_file = data.get("logo_file")

        if logo_file is not None:
            stored_logo_url, logo_error = save_entity_logo_upload(logo_file)

        if logo_error:
            return {"ok": False, "message": logo_error}

        entity = Entity(
            internal_number=self.get_next_internal_number_v2(),
            logo_url=stored_logo_url or None,
            is_active=str(data.get("status") or "active").lower() != "inactive",
        )
        apply_entity_form_data_v1(entity, data)

        self.session.add(entity)
        self.session.flush()

        return {
            "ok": True,
            "message": f"Entidade criada com sucesso. Nº Entidade: {entity.internal_number}.",
            "row": self.entity_to_row_v2(entity),
        }

    def update(self, edit_key: str, data: dict[str, Any]) -> dict[str, Any]:
        entity = self.get_entity_v2(edit_key)

        if entity is None:
            return {"ok": False, "message": "Entidade não encontrada."}

        logo_file = data.get("logo_file")

        if logo_file is not None and getattr(logo_file, "filename", ""):
            stored_logo_url, logo_error = save_entity_logo_upload(logo_file)

            if logo_error:
                return {"ok": False, "message": logo_error}

            if stored_logo_url:
                entity.logo_url = stored_logo_url

        apply_entity_form_data_v1(entity, data)
        entity.is_active = str(data.get("status") or "active").lower() != "inactive"

        self.session.flush()

        return {
            "ok": True,
            "message": "Entidade atualizada com sucesso.",
            "row": self.entity_to_row_v2(entity),
        }

    def delete(self, edit_key: str) -> dict[str, Any]:
        entity = self.get_entity_v2(edit_key)

        if entity is None:
            return {"ok": False, "message": "Entidade não encontrada."}

        if entity.is_active:
            return {"ok": False, "message": "Apenas entidades inativas podem ser eliminadas."}

        self.session.delete(entity)
        self.session.flush()

        return {"ok": True, "message": "Entidade eliminada com sucesso."}
