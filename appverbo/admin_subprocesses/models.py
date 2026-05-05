
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


AdminSubprocessMode = Literal["create", "edit"]
AdminSubprocessStatus = Literal["ativo", "inativo"]


@dataclass(frozen=True)
class AdminFieldConfig:
    key: str
    label: str
    input_name: str
    field_type: str = "text"
    required: bool = False
    options: tuple[tuple[str, str], ...] = ()
    placeholder: str = ""
    max_length: int | None = None
    readonly_on_create: bool = False
    readonly_on_edit: bool = False
    css_class: str = ""


@dataclass(frozen=True)
class AdminColumnConfig:
    key: str
    label: str
    source: str
    align: str = "left"
    css_class: str = ""


@dataclass(frozen=True)
class AdminActionConfig:
    key: str
    label: str
    icon: str
    action_type: str = "link"
    route_name: str = ""
    visible_when: tuple[str, ...] = ("ativo", "inativo")
    requires_confirmation: bool = False
    confirmation_message: str = ""


@dataclass(frozen=True)
class AdminSubprocessConfig:
    key: str
    label: str
    singular_label: str
    plural_label: str
    edit_param: str
    default_target: str
    edit_target: str
    create_title: str
    edit_title: str
    active_title: str
    inactive_title: str
    save_endpoint: str
    create_endpoint: str = ""
    update_endpoint: str = ""
    move_endpoint: str = ""
    delete_endpoint: str = ""
    repository_name: str = ""
    repository_class: str = ""
    status_field: str = "status"
    active_value: str = "ativo"
    inactive_value: str = "inativo"
    identity_field: str = "key"
    label_field: str = "label"
    mode_field: str = "subprocess_mode"
    edit_key_field: str = "subprocess_edit_key"
    return_url_field: str = "subprocess_return_url"
    create_mode_value: str = "create"
    edit_mode_value: str = "edit"
    enabled: bool = True
    migration_status: str = "native"
    fields: tuple[AdminFieldConfig, ...] = ()
    columns: tuple[AdminColumnConfig, ...] = ()
    actions: tuple[AdminActionConfig, ...] = ()


@dataclass
class AdminSubprocessState:
    config: AdminSubprocessConfig
    mode: AdminSubprocessMode = "create"
    edit_key: str = ""
    edit_data: dict[str, Any] | None = None
    active_rows: list[dict[str, Any]] = field(default_factory=list)
    inactive_rows: list[dict[str, Any]] = field(default_factory=list)
    success: str = ""
    error: str = ""
    return_url: str = ""

    @property
    def is_editing(self) -> bool:
        return self.mode == "edit" and bool(self.edit_data)

    @property
    def target_card_id(self) -> str:
        if self.is_editing:
            return self.config.edit_target
        return self.config.default_target
