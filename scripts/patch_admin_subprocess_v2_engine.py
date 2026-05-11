from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

FILES_TO_BACKUP = [
    PROJECT_ROOT / "appverbo" / "routes" / "profile" / "router.py",
]

FILES_TO_WRITE = {
    PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_models.py": None,
    PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_repository.py": None,
    PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_entity_repository.py": None,
    PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_registry.py": None,
    PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_service.py": None,
    PROJECT_ROOT / "appverbo" / "routes" / "profile" / "admin_subprocess_handlers_v2.py": None,
    PROJECT_ROOT / "templates" / "macros" / "admin_subprocess_v2.html": None,
    PROJECT_ROOT / "templates" / "admin_subprocess_v2_standalone.html": None,
    PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v2.css": None,
    PROJECT_ROOT / "static" / "js" / "modules" / "admin_subprocesses_v2.js": None,
}

ROUTER_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "router.py"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path | None:
    if not path.exists():
        return None

    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatório não encontrado: {path}")


####################################################################################
# (3) CONTEUDO DOS FICHEIROS V2
####################################################################################

V2_MODELS = r'''from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


# ###################################################################################
# (1) TIPOS
# ###################################################################################

AdminFieldTypeV2 = Literal[
    "text",
    "email",
    "tel",
    "number",
    "date",
    "textarea",
    "select",
    "checkbox",
    "hidden",
    "readonly",
    "file",
    "image",
]

AdminActionKindV2 = Literal[
    "view",
    "edit",
    "delete",
    "move_up",
    "move_down",
    "custom",
]


# ###################################################################################
# (2) CONFIGURACOES
# ###################################################################################

@dataclass(frozen=True)
class AdminFieldOptionV2:
    value: str
    label: str


@dataclass(frozen=True)
class AdminFieldConfigV2:
    key: str
    label: str
    field_type: AdminFieldTypeV2 = "text"
    input_name: str = ""
    source: str = ""
    required: bool = False
    max_length: int | None = None
    placeholder: str = ""
    default_value: str = ""
    help_text: str = ""
    css_class: str = ""
    grid_span: int = 1
    full_width: bool = False
    visible_on_create: bool = True
    visible_on_edit: bool = True
    readonly_on_create: bool = False
    readonly_on_edit: bool = False
    options: tuple[AdminFieldOptionV2, ...] = field(default_factory=tuple)

    @property
    def resolved_input_name(self) -> str:
        return self.input_name or self.key

    @property
    def resolved_source(self) -> str:
        return self.source or self.key


@dataclass(frozen=True)
class AdminColumnConfigV2:
    key: str
    label: str
    source: str = ""
    css_class: str = ""
    column_type: str = "text"

    @property
    def resolved_source(self) -> str:
        return self.source or self.key


@dataclass(frozen=True)
class AdminActionConfigV2:
    key: str
    label: str
    icon: str
    action_kind: AdminActionKindV2
    endpoint_name: str = ""
    css_class: str = ""
    confirm_message: str = ""
    allowed_statuses: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AdminSubprocessConfigV2:
    key: str
    label: str
    singular_label: str
    create_title: str
    edit_title: str
    active_title: str
    inactive_title: str
    repository_class_path: str
    identity_field: str = "id"
    label_field: str = "name"
    status_field: str = "status"
    active_value: str = "active"
    inactive_value: str = "inactive"
    create_endpoint: str = ""
    update_endpoint: str = ""
    delete_endpoint: str = ""
    move_endpoint: str = ""
    default_target: str = ""
    edit_target: str = ""
    edit_param: str = "edit_key"
    return_url_field: str = "return_url"
    create_mode_value: str = "create"
    edit_mode_value: str = "edit"
    mode_field: str = "mode"
    edit_key_field: str = "edit_key"
    fields: tuple[AdminFieldConfigV2, ...] = field(default_factory=tuple)
    columns: tuple[AdminColumnConfigV2, ...] = field(default_factory=tuple)
    actions: tuple[AdminActionConfigV2, ...] = field(default_factory=tuple)
    grid_columns: int = 4
    migration_status: str = "native_v2"

    @property
    def resolved_create_endpoint(self) -> str:
        return self.create_endpoint or f"/admin/subprocess-v2/{self.key}/create"

    @property
    def resolved_update_endpoint(self) -> str:
        return self.update_endpoint or f"/admin/subprocess-v2/{self.key}/update"

    @property
    def resolved_delete_endpoint(self) -> str:
        return self.delete_endpoint or f"/admin/subprocess-v2/{self.key}/delete"

    @property
    def resolved_move_endpoint(self) -> str:
        return self.move_endpoint or f"/admin/subprocess-v2/{self.key}/move"

    @property
    def resolved_default_target(self) -> str:
        return self.default_target or f"admin-subprocess-v2-{self.key}"

    @property
    def resolved_edit_target(self) -> str:
        return self.edit_target or f"admin-subprocess-v2-{self.key}-edit"


# ###################################################################################
# (3) ESTADO DE TELA
# ###################################################################################

@dataclass
class AdminSubprocessStateV2:
    config: AdminSubprocessConfigV2
    mode: str = "create"
    edit_key: str = ""
    edit_data: dict[str, Any] | None = None
    active_rows: list[dict[str, Any]] = field(default_factory=list)
    inactive_rows: list[dict[str, Any]] = field(default_factory=list)
    success: str = ""
    error: str = ""
    return_url: str = ""
    can_create: bool = True
    can_edit: bool = True
    can_delete: bool = True

    @property
    def is_editing(self) -> bool:
        return bool(self.edit_data)


@dataclass
class AdminSubprocessResultV2:
    ok: bool
    message: str = ""
    redirect_url: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
'''

V2_REPOSITORY = r'''from __future__ import annotations

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
'''

V2_ENTITY_REPOSITORY = r'''from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

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


# ###################################################################################
# (2) REPOSITORY ENTIDADE V2
# ###################################################################################

class EntityAdminSubprocessRepositoryV2(BaseAdminSubprocessRepositoryV2):
    def list_rows(self) -> list[dict[str, Any]]:
        entities = self.session.scalars(
            select(Entity).order_by(Entity.is_active.desc(), Entity.name.asc())
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
        current_max = self.session.scalar(select(func.max(Entity.internal_number))) or 0
        return int(current_max) + 1

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
            "message": f"Entidade criada com sucesso. Nº Cliente: {entity.internal_number}.",
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
'''

V2_REGISTRY = r'''from __future__ import annotations

from .v2_models import (
    AdminActionConfigV2,
    AdminColumnConfigV2,
    AdminFieldConfigV2,
    AdminFieldOptionV2,
    AdminSubprocessConfigV2,
)


# ###################################################################################
# (1) ENTIDADE 100% DECLARATIVA
# ###################################################################################

ENTIDADE_CONFIG_V2 = AdminSubprocessConfigV2(
    key="entidade",
    label="Entidade",
    singular_label="Entidade",
    create_title="Criar entidade",
    edit_title="Editar entidade",
    active_title="Entidades ativas",
    inactive_title="Entidades inativas",
    repository_class_path="appverbo.admin_subprocesses.v2_entity_repository.EntityAdminSubprocessRepositoryV2",
    identity_field="id",
    label_field="name",
    status_field="status",
    active_value="active",
    inactive_value="inactive",
    default_target="admin-subprocess-v2-entidade",
    edit_target="admin-subprocess-v2-entidade-edit",
    edit_param="entity_id",
    grid_columns=4,
    fields=(
        AdminFieldConfigV2(
            key="internal_number",
            label="Nº cliente",
            field_type="readonly",
            visible_on_create=False,
            readonly_on_edit=True,
        ),
        AdminFieldConfigV2(
            key="name",
            label="Nome da entidade",
            required=True,
            max_length=150,
            placeholder="Nome completo da entidade",
        ),
        AdminFieldConfigV2(
            key="acronym",
            label="Acrónimo",
            max_length=30,
            placeholder="Ex.: VB",
        ),
        AdminFieldConfigV2(
            key="tax_id",
            label="Nº Identificação Fiscal",
            required=True,
            max_length=40,
        ),
        AdminFieldConfigV2(
            key="profile_scope",
            label="Perfil da entidade",
            field_type="select",
            input_name="entity_profile_scope",
            required=True,
            options=(
                AdminFieldOptionV2("legado", "Legado"),
                AdminFieldOptionV2("owner", "Owner"),
            ),
        ),
        AdminFieldConfigV2(
            key="status",
            label="Estado",
            field_type="select",
            default_value="active",
            options=(
                AdminFieldOptionV2("active", "Ativo"),
                AdminFieldOptionV2("inactive", "Inativo"),
            ),
        ),
        AdminFieldConfigV2(
            key="email",
            label="Email",
            field_type="email",
            required=True,
            max_length=150,
        ),
        AdminFieldConfigV2(
            key="phone",
            label="Telefone",
            field_type="tel",
            required=True,
            max_length=30,
        ),
        AdminFieldConfigV2(
            key="responsible_name",
            label="Nome do responsável",
            required=True,
            max_length=200,
        ),
        AdminFieldConfigV2(
            key="address",
            label="Morada",
            required=True,
            max_length=255,
            grid_span=2,
        ),
        AdminFieldConfigV2(
            key="door_number",
            label="Nº da porta",
            required=True,
            max_length=30,
        ),
        AdminFieldConfigV2(
            key="freguesia",
            label="Freguesia",
            required=True,
            max_length=120,
        ),
        AdminFieldConfigV2(
            key="postal_code",
            label="Código postal",
            required=True,
            max_length=30,
        ),
        AdminFieldConfigV2(
            key="city",
            label="Cidade",
            required=True,
            max_length=120,
        ),
        AdminFieldConfigV2(
            key="country",
            label="País",
            required=True,
            max_length=120,
        ),
        AdminFieldConfigV2(
            key="logo_url",
            label="Imagem/ícone da entidade",
            field_type="file",
            input_name="entity_logo_file",
            full_width=True,
            help_text="PNG, JPG, WEBP, GIF ou SVG até 5MB.",
        ),
        AdminFieldConfigV2(
            key="description",
            label="Descrição",
            field_type="textarea",
            full_width=True,
            grid_span=4,
        ),
    ),
    columns=(
        AdminColumnConfigV2("internal_number", "Nº cliente"),
        AdminColumnConfigV2("name", "Nome"),
        AdminColumnConfigV2("profile_scope_label", "Perfil"),
        AdminColumnConfigV2("status_label", "Estado", column_type="badge"),
    ),
    actions=(
        AdminActionConfigV2("view", "Visualizar", "👁", "view"),
        AdminActionConfigV2("edit", "Editar", "✎", "edit"),
        AdminActionConfigV2(
            "delete",
            "Eliminar",
            "🗑",
            "delete",
            allowed_statuses=("inactive",),
            confirm_message="Confirmar eliminação desta entidade inativa?",
        ),
    ),
    migration_status="native_v2",
)


# ###################################################################################
# (2) REGISTRY
# ###################################################################################

ADMIN_SUBPROCESS_REGISTRY_V2 = {
    ENTIDADE_CONFIG_V2.key: ENTIDADE_CONFIG_V2,
}


def get_admin_subprocess_config_v2(key: str) -> AdminSubprocessConfigV2 | None:
    return ADMIN_SUBPROCESS_REGISTRY_V2.get(str(key or "").strip().lower())


def list_admin_subprocess_configs_v2() -> list[AdminSubprocessConfigV2]:
    return list(ADMIN_SUBPROCESS_REGISTRY_V2.values())
'''

V2_SERVICE = r'''from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .v2_models import AdminSubprocessConfigV2, AdminSubprocessStateV2
from .v2_registry import get_admin_subprocess_config_v2
from .v2_repository import (
    load_repository_class_v2,
    normalize_admin_subprocess_text_v2,
    split_admin_subprocess_rows_v2,
)


# ###################################################################################
# (1) URLS SEGURAS
# ###################################################################################

def sanitize_admin_subprocess_return_url_v2(raw_url: object, fallback_url: str) -> str:
    clean_url = normalize_admin_subprocess_text_v2(raw_url)

    if not clean_url:
        return fallback_url

    try:
        parsed_url = urlsplit(clean_url)
    except Exception:
        return fallback_url

    if parsed_url.scheme or parsed_url.netloc:
        return fallback_url

    path = parsed_url.path or "/users/new"

    if path not in {"/users/new", "/admin/subprocess-v2/entidade"} and not path.startswith("/admin/subprocess-v2/"):
        return fallback_url

    return urlunsplit(("", "", path, parsed_url.query, parsed_url.fragment))


def add_admin_subprocess_message_v2(
    url: str,
    *,
    config: AdminSubprocessConfigV2,
    success: str = "",
    error: str = "",
) -> str:
    parsed_url = urlsplit(url)
    params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))

    params.setdefault("menu", "administrativo")
    params.setdefault("admin_tab", config.key)
    params["appverbo_after_save"] = "1"

    if success:
        params[f"{config.key}_success"] = success

    if error:
        params[f"{config.key}_error"] = error

    return urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path or "/users/new",
            urlencode(params),
            parsed_url.fragment,
        )
    )


def default_admin_subprocess_return_url_v2(config: AdminSubprocessConfigV2) -> str:
    return (
        f"/users/new?menu=administrativo&admin_tab={config.key}"
        f"&target=%23{config.resolved_default_target}"
        f"#${config.resolved_default_target}"
    ).replace("#$", "#")


# ###################################################################################
# (2) REPOSITORY
# ###################################################################################

def create_admin_subprocess_repository_v2(
    *,
    config: AdminSubprocessConfigV2,
    session: Any,
    request: Any,
    current_user: dict[str, Any] | None,
) -> Any:
    repository_class = load_repository_class_v2(config.repository_class_path)
    return repository_class(
        session=session,
        request=request,
        current_user=current_user,
        config=config,
    )


# ###################################################################################
# (3) ESTADO DE TELA
# ###################################################################################

def build_admin_subprocess_state_v2(
    *,
    key: str,
    session: Any,
    request: Any,
    current_user: dict[str, Any] | None,
    edit_key: str = "",
    success: str = "",
    error: str = "",
    return_url: str = "",
) -> AdminSubprocessStateV2 | None:
    config = get_admin_subprocess_config_v2(key)

    if config is None:
        return None

    repository = create_admin_subprocess_repository_v2(
        config=config,
        session=session,
        request=request,
        current_user=current_user,
    )

    rows = repository.list_rows()
    active_rows, inactive_rows = split_admin_subprocess_rows_v2(rows, config)

    edit_data = repository.get_for_edit(edit_key) if edit_key else None

    return AdminSubprocessStateV2(
        config=config,
        mode="edit" if edit_data else "create",
        edit_key=edit_key,
        edit_data=edit_data,
        active_rows=active_rows,
        inactive_rows=inactive_rows,
        success=success,
        error=error,
        return_url=return_url or default_admin_subprocess_return_url_v2(config),
    )
'''

V2_HANDLERS = r'''from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError

from appverbo.core import *  # noqa: F403,F401
from appverbo.routes.profile.router import router
from appverbo.admin_subprocesses.v2_registry import get_admin_subprocess_config_v2
from appverbo.admin_subprocesses.v2_service import (
    add_admin_subprocess_message_v2,
    build_admin_subprocess_state_v2,
    create_admin_subprocess_repository_v2,
    default_admin_subprocess_return_url_v2,
    sanitize_admin_subprocess_return_url_v2,
)


# ###################################################################################
# (1) HELPERS
# ###################################################################################

def get_current_admin_user_or_redirect_v2(request: Request, session: Any) -> tuple[dict[str, Any] | None, RedirectResponse | None]:
    current_user = get_current_user(request, session)

    if current_user is None:
        return None, RedirectResponse(
            url="/login?error=Efetue login para continuar.",
            status_code=status.HTTP_302_FOUND,
        )

    current_user_is_admin = is_admin_user(
        session,
        current_user["id"],
        current_user["login_email"],
    )

    if not current_user_is_admin:
        return None, RedirectResponse(
            url="/users/new?menu=home&error=Apenas administradores podem aceder a este subprocesso.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return current_user, None


def build_redirect_after_admin_subprocess_action_v2(
    *,
    config: Any,
    raw_return_url: Any,
    success: str = "",
    error: str = "",
) -> RedirectResponse:
    fallback_url = default_admin_subprocess_return_url_v2(config)
    safe_return_url = sanitize_admin_subprocess_return_url_v2(raw_return_url, fallback_url)
    redirect_url = add_admin_subprocess_message_v2(
        safe_return_url,
        config=config,
        success=success,
        error=error,
    )

    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ###################################################################################
# (2) PAGINA STANDALONE GENERICA
# ###################################################################################

@router.get("/admin/subprocess-v2/{subprocess_key}", response_class=HTMLResponse)
def admin_subprocess_standalone_page_v2(
    subprocess_key: str,
    request: Request,
    edit_key: str = "",
) -> HTMLResponse:
    config = get_admin_subprocess_config_v2(subprocess_key)

    if config is None:
        return HTMLResponse("Subprocesso não encontrado.", status_code=404)

    with SessionLocal() as session:
        current_user, redirect_response = get_current_admin_user_or_redirect_v2(request, session)

        if redirect_response is not None:
            return redirect_response

        state = build_admin_subprocess_state_v2(
            key=config.key,
            session=session,
            request=request,
            current_user=current_user,
            edit_key=edit_key,
            success=str(request.query_params.get(f"{config.key}_success") or ""),
            error=str(request.query_params.get(f"{config.key}_error") or ""),
            return_url=f"/admin/subprocess-v2/{config.key}",
        )

        return templates.TemplateResponse(
            request,
            "admin_subprocess_v2_standalone.html",
            {
                "request": request,
                "state": state,
                "current_user": current_user,
            },
        )


# ###################################################################################
# (3) ACOES GENERICAS
# ###################################################################################

@router.post("/admin/subprocess-v2/{subprocess_key}/create")
async def create_admin_subprocess_record_v2(
    subprocess_key: str,
    request: Request,
) -> RedirectResponse:
    config = get_admin_subprocess_config_v2(subprocess_key)

    if config is None:
        return RedirectResponse(
            url="/users/new?menu=administrativo&error=Subprocesso não encontrado.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    submitted_form = await request.form()
    raw_return_url = submitted_form.get(config.return_url_field)

    with SessionLocal() as session:
        current_user, redirect_response = get_current_admin_user_or_redirect_v2(request, session)

        if redirect_response is not None:
            return redirect_response

        repository = create_admin_subprocess_repository_v2(
            config=config,
            session=session,
            request=request,
            current_user=current_user,
        )

        data = repository.clean_form(submitted_form)
        errors = repository.validate_create(data)

        if errors:
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error=" ".join(errors),
            )

        try:
            result = repository.create(data)

            if not result.get("ok", False):
                session.rollback()
                return build_redirect_after_admin_subprocess_action_v2(
                    config=config,
                    raw_return_url=raw_return_url,
                    error=str(result.get("message") or "Não foi possível criar o registo."),
                )

            session.commit()

            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                success=str(result.get("message") or "Registo criado com sucesso."),
            )
        except IntegrityError:
            session.rollback()
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error="Não foi possível criar o registo por conflito de dados.",
            )


@router.post("/admin/subprocess-v2/{subprocess_key}/update")
async def update_admin_subprocess_record_v2(
    subprocess_key: str,
    request: Request,
) -> RedirectResponse:
    config = get_admin_subprocess_config_v2(subprocess_key)

    if config is None:
        return RedirectResponse(
            url="/users/new?menu=administrativo&error=Subprocesso não encontrado.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    submitted_form = await request.form()
    raw_return_url = submitted_form.get(config.return_url_field)
    edit_key = str(submitted_form.get(config.edit_key_field) or "").strip()

    with SessionLocal() as session:
        current_user, redirect_response = get_current_admin_user_or_redirect_v2(request, session)

        if redirect_response is not None:
            return redirect_response

        repository = create_admin_subprocess_repository_v2(
            config=config,
            session=session,
            request=request,
            current_user=current_user,
        )

        data = repository.clean_form(submitted_form)
        errors = repository.validate_update(edit_key, data)

        if errors:
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error=" ".join(errors),
            )

        try:
            result = repository.update(edit_key, data)

            if not result.get("ok", False):
                session.rollback()
                return build_redirect_after_admin_subprocess_action_v2(
                    config=config,
                    raw_return_url=raw_return_url,
                    error=str(result.get("message") or "Não foi possível atualizar o registo."),
                )

            session.commit()

            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                success=str(result.get("message") or "Registo atualizado com sucesso."),
            )
        except IntegrityError:
            session.rollback()
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error="Não foi possível atualizar o registo por conflito de dados.",
            )


@router.post("/admin/subprocess-v2/{subprocess_key}/delete")
async def delete_admin_subprocess_record_v2(
    subprocess_key: str,
    request: Request,
) -> RedirectResponse:
    config = get_admin_subprocess_config_v2(subprocess_key)

    if config is None:
        return RedirectResponse(
            url="/users/new?menu=administrativo&error=Subprocesso não encontrado.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    submitted_form = await request.form()
    raw_return_url = submitted_form.get(config.return_url_field)
    edit_key = str(submitted_form.get(config.edit_key_field) or "").strip()

    with SessionLocal() as session:
        current_user, redirect_response = get_current_admin_user_or_redirect_v2(request, session)

        if redirect_response is not None:
            return redirect_response

        repository = create_admin_subprocess_repository_v2(
            config=config,
            session=session,
            request=request,
            current_user=current_user,
        )

        try:
            result = repository.delete(edit_key)

            if not result.get("ok", False):
                session.rollback()
                return build_redirect_after_admin_subprocess_action_v2(
                    config=config,
                    raw_return_url=raw_return_url,
                    error=str(result.get("message") or "Não foi possível eliminar o registo."),
                )

            session.commit()

            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                success=str(result.get("message") or "Registo eliminado com sucesso."),
            )
        except IntegrityError:
            session.rollback()
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error="Não foi possível eliminar o registo porque existem dados relacionados.",
            )
'''

V2_MACRO = r'''{% macro admin_subprocess_v2_get_value(row, field, default="") %}
  {{ row.get(field.resolved_source, default) if row else default }}
{% endmacro %}


{% macro render_admin_subprocess_v2_field(field, value="", mode="create") %}
  {% set is_visible = field.visible_on_edit if mode == "edit" else field.visible_on_create %}
  {% if is_visible %}
    {% set is_readonly = field.readonly_on_edit if mode == "edit" else field.readonly_on_create %}
    <div
      class="admin-subprocess-field-v2 {{ field.css_class }} {% if field.full_width %}admin-subprocess-field-full-v2{% endif %}"
      style="--admin-field-span: {{ field.grid_span if field.grid_span else 1 }};"
    >
      {% if field.field_type != "hidden" %}
        <label for="admin_subprocess_v2_{{ field.key }}">
          {{ field.label }}{% if field.required %} *{% endif %}
        </label>
      {% endif %}

      {% if field.field_type == "hidden" %}
        <input type="hidden" name="{{ field.resolved_input_name }}" value="{{ value or field.default_value }}">
      {% elif field.field_type == "readonly" or is_readonly %}
        <input
          id="admin_subprocess_v2_{{ field.key }}"
          name="{{ field.resolved_input_name }}"
          type="text"
          value="{{ value or field.default_value }}"
          readonly
        >
      {% elif field.field_type == "textarea" %}
        <textarea
          id="admin_subprocess_v2_{{ field.key }}"
          name="{{ field.resolved_input_name }}"
          {% if field.required %}required{% endif %}
          {% if field.placeholder %}placeholder="{{ field.placeholder }}"{% endif %}
        >{{ value or field.default_value }}</textarea>
      {% elif field.field_type == "select" %}
        <select
          id="admin_subprocess_v2_{{ field.key }}"
          name="{{ field.resolved_input_name }}"
          {% if field.required %}required{% endif %}
        >
          {% for option in field.options %}
            <option value="{{ option.value }}" {% if (value or field.default_value) == option.value %}selected{% endif %}>
              {{ option.label }}
            </option>
          {% endfor %}
        </select>
      {% elif field.field_type == "file" or field.field_type == "image" %}
        {% if value %}
          <div class="admin-subprocess-current-file-v2">
            Atual: {{ value }}
          </div>
        {% endif %}
        <input
          id="admin_subprocess_v2_{{ field.key }}"
          name="{{ field.resolved_input_name }}"
          type="file"
          {% if field.field_type == "image" %}accept="image/*"{% endif %}
        >
      {% elif field.field_type == "checkbox" %}
        <label class="admin-subprocess-checkbox-v2">
          <input
            id="admin_subprocess_v2_{{ field.key }}"
            name="{{ field.resolved_input_name }}"
            type="checkbox"
            value="1"
            {% if value in ["1", "true", "True", true] %}checked{% endif %}
          >
          <span>{{ field.help_text or field.label }}</span>
        </label>
      {% else %}
        <input
          id="admin_subprocess_v2_{{ field.key }}"
          name="{{ field.resolved_input_name }}"
          type="{{ field.field_type }}"
          value="{{ value or field.default_value }}"
          {% if field.required %}required{% endif %}
          {% if field.max_length %}maxlength="{{ field.max_length }}"{% endif %}
          {% if field.placeholder %}placeholder="{{ field.placeholder }}"{% endif %}
        >
      {% endif %}

      {% if field.help_text and field.field_type != "checkbox" %}
        <small>{{ field.help_text }}</small>
      {% endif %}
    </div>
  {% endif %}
{% endmacro %}


{% macro render_admin_subprocess_v2_form(state) %}
  <section
    id="{{ state.config.resolved_edit_target if state.is_editing else state.config.resolved_default_target }}"
    class="card admin-subprocess-card-v2 admin-subprocess-form-card-v2"
    data-admin-subprocess-v2="{{ state.config.key }}"
  >
    {% if state.success %}
      <div class="alert ok">{{ state.success }}</div>
    {% endif %}

    {% if state.error %}
      <div class="alert error">{{ state.error }}</div>
    {% endif %}

    {% if state.is_editing %}
      <h2>{{ state.config.edit_title }}</h2>

      <form method="post" enctype="multipart/form-data" action="{{ state.config.resolved_update_endpoint }}" class="admin-subprocess-form-v2">
        <input type="hidden" name="{{ state.config.mode_field }}" value="{{ state.config.edit_mode_value }}">
        <input type="hidden" name="{{ state.config.edit_key_field }}" value="{{ state.edit_key }}">
        <input type="hidden" name="{{ state.config.return_url_field }}" value="{{ state.return_url }}">

        <div class="admin-subprocess-grid-v2 admin-subprocess-grid-{{ state.config.grid_columns }}-v2">
          {% for field in state.config.fields %}
            {% set value = state.edit_data.get(field.resolved_source, "") if state.edit_data else "" %}
            {{ render_admin_subprocess_v2_field(field, value, "edit") }}
          {% endfor %}
        </div>

        <div class="form-action-row admin-subprocess-actions-v2">
          <button type="submit" class="action-btn">Guardar</button>
          <a class="action-btn-cancel" href="{{ state.return_url }}">Cancelar</a>
        </div>
      </form>
    {% else %}
      <details class="admin-subprocess-create-collapse-v2">
        <summary>
          <span>{{ state.config.create_title }}</span>
        </summary>

        <div class="admin-subprocess-create-body-v2">
          <form method="post" enctype="multipart/form-data" action="{{ state.config.resolved_create_endpoint }}" class="admin-subprocess-form-v2">
            <input type="hidden" name="{{ state.config.mode_field }}" value="{{ state.config.create_mode_value }}">
            <input type="hidden" name="{{ state.config.edit_key_field }}" value="">
            <input type="hidden" name="{{ state.config.return_url_field }}" value="{{ state.return_url }}">

            <div class="admin-subprocess-grid-v2 admin-subprocess-grid-{{ state.config.grid_columns }}-v2">
              {% for field in state.config.fields %}
                {{ render_admin_subprocess_v2_field(field, "", "create") }}
              {% endfor %}
            </div>

            <div class="form-action-row admin-subprocess-actions-v2">
              <button type="submit" class="action-btn">Guardar</button>
              <button type="button" class="action-btn-cancel" data-admin-subprocess-v2-cancel-create>Cancelar</button>
            </div>
          </form>
        </div>
      </details>
    {% endif %}
  </section>
{% endmacro %}


{% macro render_admin_subprocess_v2_row_actions(state, row, status_value) %}
  {% set row_key = row.get(state.config.identity_field, row.get("id", "")) %}
  {% set row_label = row.get(state.config.label_field, row.get("name", "")) %}

  <div class="admin-subprocess-row-actions-v2">
    {% for action in state.config.actions %}
      {% set allowed = not action.allowed_statuses or status_value in action.allowed_statuses %}
      {% if allowed and action.action_kind == "view" %}
        <button
          type="button"
          class="admin-subprocess-action-btn-v2"
          title="{{ action.label }}"
          aria-label="{{ action.label }}"
          data-admin-subprocess-v2-view
          data-view-title="{{ state.config.singular_label }}"
          data-view-details="{% for column in state.config.columns %}{{ column.label }}: {{ row.get(column.resolved_source, '') }}&#10;{% endfor %}"
        >{{ action.icon }}</button>
      {% elif allowed and action.action_kind == "edit" %}
        <a
          class="admin-subprocess-action-btn-v2 admin-subprocess-action-link-v2"
          title="{{ action.label }}"
          aria-label="{{ action.label }}"
          href="/admin/subprocess-v2/{{ state.config.key }}?edit_key={{ row_key }}"
        >{{ action.icon }}</a>
      {% elif allowed and action.action_kind == "delete" %}
        <form method="post" action="{{ state.config.resolved_delete_endpoint }}" class="admin-subprocess-inline-form-v2">
          <input type="hidden" name="{{ state.config.edit_key_field }}" value="{{ row_key }}">
          <input type="hidden" name="{{ state.config.return_url_field }}" value="{{ state.return_url }}">
          <button
            type="submit"
            class="admin-subprocess-action-btn-v2"
            title="{{ action.label }}"
            aria-label="{{ action.label }}"
            {% if action.confirm_message %}data-confirm-message="{{ action.confirm_message }}"{% endif %}
          >{{ action.icon }}</button>
        </form>
      {% endif %}
    {% endfor %}
  </div>
{% endmacro %}


{% macro render_admin_subprocess_v2_table(state, rows, title, status_value) %}
  <section
    class="card admin-subprocess-card-v2 admin-subprocess-table-card-v2"
    data-admin-subprocess-v2="{{ state.config.key }}"
    data-admin-subprocess-v2-status="{{ status_value }}"
  >
    <h2>{{ title }}</h2>

    {% if rows %}
      <div class="admin-subprocess-table-wrap-v2">
        <table class="admin-subprocess-table-v2" data-admin-subprocess-v2-table>
          <thead>
            <tr>
              {% for column in state.config.columns %}
                <th class="{{ column.css_class }}">{{ column.label }}</th>
              {% endfor %}
              <th>AÇÕES</th>
            </tr>
          </thead>
          <tbody>
            {% for row in rows %}
              <tr>
                {% for column in state.config.columns %}
                  {% set cell_value = row.get(column.resolved_source, "") %}
                  <td class="{{ column.css_class }}">
                    {% if column.column_type == "badge" %}
                      <span class="admin-subprocess-badge-v2 {% if status_value == state.config.active_value %}admin-subprocess-badge-active-v2{% else %}admin-subprocess-badge-inactive-v2{% endif %}">
                        {{ cell_value }}
                      </span>
                    {% else %}
                      {{ cell_value }}
                    {% endif %}
                  </td>
                {% endfor %}
                <td>
                  {{ render_admin_subprocess_v2_row_actions(state, row, status_value) }}
                </td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% else %}
      <p class="empty">Sem registos.</p>
    {% endif %}
  </section>
{% endmacro %}


{% macro render_admin_subprocess_v2_state(state) %}
  {{ render_admin_subprocess_v2_form(state) }}
  {{ render_admin_subprocess_v2_table(state, state.active_rows, state.config.active_title, state.config.active_value) }}
  {{ render_admin_subprocess_v2_table(state, state.inactive_rows, state.config.inactive_title, state.config.inactive_value) }}
{% endmacro %}
'''

V2_STANDALONE = r'''<!doctype html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <title>{{ state.config.label if state else "Subprocesso" }} - Admin V2</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/modules/admin_subprocesses_v2.css?v=20260506-admin-subprocess-v2">
</head>
<body>
  {% from "macros/admin_subprocess_v2.html" import render_admin_subprocess_v2_state %}

  <main class="admin-subprocess-standalone-v2">
    <div class="admin-subprocess-standalone-header-v2">
      <a href="/users/new?menu=administrativo">← Voltar ao Administrativo</a>
      <h1>{{ state.config.label if state else "Subprocesso" }}</h1>
    </div>

    {% if state %}
      {{ render_admin_subprocess_v2_state(state) }}
    {% else %}
      <section class="card">
        <p class="empty">Subprocesso não encontrado.</p>
      </section>
    {% endif %}
  </main>

  <script src="/static/js/modules/admin_subprocesses_v2.js?v=20260506-admin-subprocess-v2"></script>
</body>
</html>
'''

V2_CSS = r'''/* APPVERBO_ADMIN_SUBPROCESSES_V2_START */

.admin-subprocess-standalone-v2 {
  width: min(1280px, calc(100% - 32px));
  margin: 24px auto;
}

.admin-subprocess-standalone-header-v2 {
  margin-bottom: 16px;
}

.admin-subprocess-standalone-header-v2 a {
  color: #174ea6;
  font-weight: 800;
  text-decoration: none;
}

.admin-subprocess-standalone-header-v2 h1 {
  margin: 10px 0 0;
  color: #12213a;
  font-size: 26px;
  font-weight: 900;
}

.admin-subprocess-card-v2 {
  display: block;
  visibility: visible;
  width: 100%;
  box-sizing: border-box;
}

.admin-subprocess-form-card-v2 {
  background: #f3f6fb;
  border: 1px solid #d5dceb;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.admin-subprocess-table-card-v2 {
  background: #ffffff;
  border: 1px solid #d5dceb;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.admin-subprocess-card-v2 h2 {
  margin: 0 0 12px;
  color: #12213a;
  font-size: 22px;
  font-weight: 800;
}

.admin-subprocess-form-v2 {
  width: 100%;
}

.admin-subprocess-create-collapse-v2 > summary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 132px;
  min-height: 38px;
  padding: 0 16px;
  border-radius: 7px;
  background: #0f56c5;
  color: #ffffff;
  font-weight: 800;
  cursor: pointer;
  list-style: none;
}

.admin-subprocess-create-collapse-v2 > summary::-webkit-details-marker {
  display: none;
}

.admin-subprocess-create-collapse-v2[open] > summary {
  margin-bottom: 14px;
}

.admin-subprocess-grid-v2 {
  display: grid;
  gap: 12px;
  align-items: end;
  width: 100%;
}

.admin-subprocess-grid-1-v2 {
  grid-template-columns: 1fr;
}

.admin-subprocess-grid-2-v2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.admin-subprocess-grid-3-v2 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.admin-subprocess-grid-4-v2 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.admin-subprocess-field-v2 {
  min-width: 0;
  grid-column: span min(var(--admin-field-span, 1), 4);
}

.admin-subprocess-field-full-v2 {
  grid-column: 1 / -1;
}

.admin-subprocess-field-v2 label {
  display: block;
  margin-bottom: 6px;
  color: #12213a;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.admin-subprocess-field-v2 input,
.admin-subprocess-field-v2 select,
.admin-subprocess-field-v2 textarea {
  width: 100%;
  min-height: 38px;
  border: 1px solid #c6d0e2;
  border-radius: 7px;
  background: #ffffff;
  color: #12213a;
  padding: 8px 10px;
  box-sizing: border-box;
  font-size: 13px;
}

.admin-subprocess-field-v2 textarea {
  min-height: 92px;
  resize: vertical;
}

.admin-subprocess-field-v2 small {
  display: block;
  margin-top: 5px;
  color: #5d6b82;
  font-size: 12px;
}

.admin-subprocess-current-file-v2 {
  margin-bottom: 6px;
  color: #475569;
  font-size: 12px;
}

.admin-subprocess-checkbox-v2 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
}

.admin-subprocess-checkbox-v2 input {
  width: auto;
  min-height: auto;
}

.admin-subprocess-actions-v2 {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}

.admin-subprocess-actions-v2 .action-btn,
.admin-subprocess-actions-v2 .action-btn-cancel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 112px;
  width: 112px;
  height: 38px;
  min-height: 38px;
  box-sizing: border-box;
  text-decoration: none;
}

.admin-subprocess-table-wrap-v2,
.admin-subprocess-table-v2 {
  width: 100%;
}

.admin-subprocess-table-v2 {
  border-collapse: collapse;
}

.admin-subprocess-table-v2 th,
.admin-subprocess-table-v2 td {
  padding: 10px 12px;
  border-bottom: 1px solid #e3e8f2;
  text-align: left;
  vertical-align: middle;
}

.admin-subprocess-table-v2 th {
  color: #12213a;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.admin-subprocess-table-v2 th:last-child,
.admin-subprocess-table-v2 td:last-child {
  text-align: right;
}

.admin-subprocess-row-actions-v2 {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.admin-subprocess-inline-form-v2 {
  display: inline-flex;
  margin: 0;
  padding: 0;
}

.admin-subprocess-action-btn-v2 {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  min-width: 30px;
  height: 30px;
  min-height: 30px;
  padding: 0;
  border: 1px solid #b9cdf5;
  border-radius: 7px;
  background: #eef5ff;
  color: #174ea6;
  font-size: 15px;
  font-weight: 800;
  line-height: 1;
  text-align: center;
  text-decoration: none;
  cursor: pointer;
}

.admin-subprocess-action-btn-v2:hover {
  background: #dfeaff;
  border-color: #7fa8f2;
}

.admin-subprocess-badge-v2 {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 3px 9px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.admin-subprocess-badge-active-v2 {
  border-color: #badbcc;
  background: #e9f7ef;
  color: #0f5132;
}

.admin-subprocess-badge-inactive-v2 {
  border-color: #f0c36d;
  background: #fff7e0;
  color: #8a5a00;
}

@media (max-width: 1100px) {
  .admin-subprocess-grid-2-v2,
  .admin-subprocess-grid-3-v2,
  .admin-subprocess-grid-4-v2 {
    grid-template-columns: 1fr;
  }

  .admin-subprocess-field-v2,
  .admin-subprocess-field-full-v2 {
    grid-column: 1 / -1;
  }
}

/* APPVERBO_ADMIN_SUBPROCESSES_V2_END */
'''

V2_JS = r'''// APPVERBO_ADMIN_SUBPROCESSES_V2_START
(function () {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeTextV2(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  //###################################################################################
  // (2) VISUALIZAR DETALHES
  //###################################################################################

  function setupViewActionsV2() {
    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-v2-view]");

      if (!button) {
        return;
      }

      event.preventDefault();

      const title = button.getAttribute("data-view-title") || "Detalhes";
      const details = button.getAttribute("data-view-details") || "";

      alert(title + (details ? "\n" + details : ""));
    });
  }

  //###################################################################################
  // (3) CANCELAR CRIACAO
  //###################################################################################

  function setupCancelCreateV2() {
    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-v2-cancel-create]");

      if (!button) {
        return;
      }

      event.preventDefault();

      const form = button.closest("form");
      const details = button.closest("details");

      if (form) {
        form.reset();
      }

      if (details) {
        details.open = false;
      }
    });
  }

  //###################################################################################
  // (4) CONFIRMACAO
  //###################################################################################

  function setupConfirmActionsV2() {
    document.addEventListener("submit", function (event) {
      const submitter = event.submitter || document.activeElement;
      const message = submitter && submitter.getAttribute
        ? safeTextV2(submitter.getAttribute("data-confirm-message"))
        : "";

      if (message && !window.confirm(message)) {
        event.preventDefault();
      }
    }, true);
  }

  //###################################################################################
  // (5) INICIAR
  //###################################################################################

  function setupAdminSubprocessesV2() {
    if (window.__appverboAdminSubprocessesV2 === true) {
      return;
    }

    window.__appverboAdminSubprocessesV2 = true;

    setupViewActionsV2();
    setupCancelCreateV2();
    setupConfirmActionsV2();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAdminSubprocessesV2);
  } else {
    setupAdminSubprocessesV2();
  }
})();
// APPVERBO_ADMIN_SUBPROCESSES_V2_END
'''


####################################################################################
# (4) ESCREVER FICHEIROS
####################################################################################

FILES_TO_WRITE[PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_models.py"] = V2_MODELS
FILES_TO_WRITE[PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_repository.py"] = V2_REPOSITORY
FILES_TO_WRITE[PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_entity_repository.py"] = V2_ENTITY_REPOSITORY
FILES_TO_WRITE[PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_registry.py"] = V2_REGISTRY
FILES_TO_WRITE[PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_service.py"] = V2_SERVICE
FILES_TO_WRITE[PROJECT_ROOT / "appverbo" / "routes" / "profile" / "admin_subprocess_handlers_v2.py"] = V2_HANDLERS
FILES_TO_WRITE[PROJECT_ROOT / "templates" / "macros" / "admin_subprocess_v2.html"] = V2_MACRO
FILES_TO_WRITE[PROJECT_ROOT / "templates" / "admin_subprocess_v2_standalone.html"] = V2_STANDALONE
FILES_TO_WRITE[PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v2.css"] = V2_CSS
FILES_TO_WRITE[PROJECT_ROOT / "static" / "js" / "modules" / "admin_subprocesses_v2.js"] = V2_JS


def write_v2_files() -> None:
    for path in FILES_TO_BACKUP:
        require_file_v1(path)
        backup_path = backup_file_v1(path, "admin_subprocess_v2_engine")
        print(f"OK: backup criado: {backup_path}")

    for path in FILES_TO_WRITE:
        if path.exists():
            backup_path = backup_file_v1(path, "admin_subprocess_v2_engine")
            print(f"OK: backup criado: {backup_path}")

    for path, content in FILES_TO_WRITE.items():
        write_text_v1(path, content or "")
        print(f"OK: ficheiro escrito: {path}")


####################################################################################
# (5) PATCH ROUTER
####################################################################################

def patch_profile_router_v1() -> None:
    content = read_text_v1(ROUTER_PATH)

    import_line = "from appverbo.routes.profile import admin_subprocess_handlers_v2  # noqa: F401,E402"

    if import_line not in content:
        anchor = "from appverbo.routes.profile import profile_handlers  # noqa: F401,E402"

        if anchor not in content:
            raise RuntimeError("Não encontrei ponto para importar admin_subprocess_handlers_v2 no router.py.")

        content = content.replace(anchor, anchor + "\n" + import_line, 1)

    write_text_v1(ROUTER_PATH, content)
    print("OK: router.py atualizado com admin_subprocess_handlers_v2.")


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

def validate_content_v1() -> None:
    required_files = list(FILES_TO_WRITE.keys()) + [ROUTER_PATH]

    for path in required_files:
        require_file_v1(path)

    router_content = read_text_v1(ROUTER_PATH)
    registry_content = read_text_v1(PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_registry.py")
    macro_content = read_text_v1(PROJECT_ROOT / "templates" / "macros" / "admin_subprocess_v2.html")
    css_content = read_text_v1(PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v2.css")
    js_content = read_text_v1(PROJECT_ROOT / "static" / "js" / "modules" / "admin_subprocesses_v2.js")

    checks = [
        ("router import", "admin_subprocess_handlers_v2" in router_content),
        ("entidade config", "ENTIDADE_CONFIG_V2" in registry_content),
        ("entity repository", "EntityAdminSubprocessRepositoryV2" in registry_content),
        ("macro state", "render_admin_subprocess_v2_state" in macro_content),
        ("css marker", "APPVERBO_ADMIN_SUBPROCESSES_V2_START" in css_content),
        ("js marker", "APPVERBO_ADMIN_SUBPROCESSES_V2_START" in js_content),
    ]

    failed = [label for label, ok in checks if not ok]

    if failed:
        raise RuntimeError("Validações falharam: " + ", ".join(failed))

    print("OK: validação de conteúdo do motor V2 concluída.")


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    write_v2_files()
    patch_profile_router_v1()
    validate_content_v1()
    print("OK: motor Admin Subprocess V2 criado.")


if __name__ == "__main__":
    main()
