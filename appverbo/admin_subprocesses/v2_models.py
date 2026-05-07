from __future__ import annotations

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
