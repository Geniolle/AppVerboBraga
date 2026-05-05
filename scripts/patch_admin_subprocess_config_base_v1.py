from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"

PACKAGE_DIR = ROOT / "appverbo" / "admin_subprocesses"
REPOSITORIES_DIR = PACKAGE_DIR / "repositories"
MACROS_DIR = ROOT / "templates" / "macros"
CSS_DIR = ROOT / "static" / "css" / "modules"
JS_DIR = ROOT / "static" / "js" / "modules"

AGENTS_MARKER_START = "<!-- APPVERBO_ADMIN_SUBPROCESS_CONFIG_BASE_V1_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_ADMIN_SUBPROCESS_CONFIG_BASE_V1_END -->"


def fail_v1(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def write_text_v1(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"OK: escrito {path}")


def resolve_agents_path_v1() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (1) CRIAR ESTRUTURA DE PASTAS
####################################################################################

PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)
MACROS_DIR.mkdir(parents=True, exist_ok=True)
CSS_DIR.mkdir(parents=True, exist_ok=True)
JS_DIR.mkdir(parents=True, exist_ok=True)


####################################################################################
# (2) CRIAR MODELOS DE CONFIGURACAO
####################################################################################

models_content = r'''
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
'''

write_text_v1(PACKAGE_DIR / "models.py", models_content)


####################################################################################
# (3) CRIAR SERVICO GENERICO
####################################################################################

service_content = r'''
from __future__ import annotations

from typing import Any, Iterable

from .models import AdminSubprocessConfig, AdminSubprocessState


INACTIVE_STATUS_VALUES = {
    "inativo",
    "inactive",
    "0",
    "false",
    "no",
    "nao",
    "não",
    "off",
}


def normalize_admin_subprocess_text(value: object) -> str:
    return str(value or "").strip()


def normalize_admin_subprocess_key(value: object) -> str:
    return normalize_admin_subprocess_text(value).lower()


def normalize_admin_subprocess_status(row: dict[str, Any], config: AdminSubprocessConfig) -> str:
    raw_status = normalize_admin_subprocess_key(row.get(config.status_field))
    raw_is_active = row.get("is_active")

    if raw_is_active is False:
        return config.inactive_value

    if raw_status in INACTIVE_STATUS_VALUES:
        return config.inactive_value

    return config.active_value


def is_admin_subprocess_row_active(row: dict[str, Any], config: AdminSubprocessConfig) -> bool:
    return normalize_admin_subprocess_status(row, config) == config.active_value


def split_admin_subprocess_rows(
    rows: Iterable[dict[str, Any]],
    config: AdminSubprocessConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active_rows: list[dict[str, Any]] = []
    inactive_rows: list[dict[str, Any]] = []

    for raw_row in rows:
        row = dict(raw_row)

        if is_admin_subprocess_row_active(row, config):
            active_rows.append(row)
        else:
            inactive_rows.append(row)

    return active_rows, inactive_rows


def find_admin_subprocess_row(
    rows: Iterable[dict[str, Any]],
    config: AdminSubprocessConfig,
    edit_key: str,
) -> dict[str, Any] | None:
    clean_edit_key = normalize_admin_subprocess_key(edit_key)

    if not clean_edit_key:
        return None

    for raw_row in rows:
        row = dict(raw_row)
        current_key = normalize_admin_subprocess_key(row.get(config.identity_field))

        if current_key == clean_edit_key:
            return row

    return None


def build_admin_subprocess_state(
    *,
    config: AdminSubprocessConfig,
    rows: Iterable[dict[str, Any]],
    edit_key: str = "",
    success: str = "",
    error: str = "",
    return_url: str = "",
) -> AdminSubprocessState:
    row_list = [dict(row) for row in rows]
    active_rows, inactive_rows = split_admin_subprocess_rows(row_list, config)
    edit_data = find_admin_subprocess_row(row_list, config, edit_key)

    return AdminSubprocessState(
        config=config,
        mode="edit" if edit_data else "create",
        edit_key=edit_key,
        edit_data=edit_data,
        active_rows=active_rows,
        inactive_rows=inactive_rows,
        success=success,
        error=error,
        return_url=return_url,
    )
'''

write_text_v1(PACKAGE_DIR / "service.py", service_content)


####################################################################################
# (4) CRIAR REGISTRY COM CONFIGURACOES ATRIBUIDAS
####################################################################################

registry_content = r'''
from __future__ import annotations

from .models import (
    AdminActionConfig,
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


ENTITY_FIELDS = (
    AdminFieldConfig(
        key="name",
        label="Nome da entidade",
        input_name="entity_name",
        field_type="text",
        required=True,
        max_length=160,
    ),
    AdminFieldConfig(
        key="status",
        label="Estado",
        input_name="entity_status",
        field_type="select",
        required=True,
        options=(
            ("active", "Ativa"),
            ("inactive", "Inativa"),
        ),
    ),
)


SIDEBAR_SECTION_FIELDS = (
    AdminFieldConfig(
        key="label",
        label="Nome da sessão",
        input_name="section_label",
        field_type="text",
        required=True,
        max_length=80,
        placeholder="Informe o nome da sessão",
    ),
    AdminFieldConfig(
        key="visibility_scope_mode",
        label="Sistema",
        input_name="section_visibility_scope_mode",
        field_type="select",
        required=True,
        options=(
            ("all", "Owner e Legado"),
            ("owner", "Owner"),
            ("legado", "Legado"),
        ),
    ),
    AdminFieldConfig(
        key="status",
        label="Estado",
        input_name="section_status",
        field_type="select",
        required=True,
        options=(
            ("ativo", "Ativo"),
            ("inativo", "Inativo"),
        ),
    ),
)


DEFAULT_COLUMNS = (
    AdminColumnConfig(key="label", label="NOME", source="label"),
    AdminColumnConfig(key="system", label="SISTEMA", source="visibility_scope_label"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
)


DEFAULT_ACTIVE_ACTIONS = (
    AdminActionConfig(
        key="move_up",
        label="Subir",
        icon="↑",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="move_down",
        label="Descer",
        icon="↓",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="view",
        label="Visualizar",
        icon="👁",
        action_type="button",
        visible_when=("ativo", "inativo"),
    ),
    AdminActionConfig(
        key="edit",
        label="Editar",
        icon="✎",
        action_type="link",
        visible_when=("ativo", "inativo"),
    ),
)


ENTIDADE_CONFIG = AdminSubprocessConfig(
    key="entidade",
    label="Entidade",
    singular_label="Entidade",
    plural_label="Entidades",
    edit_param="entity_edit_id",
    default_target="create-entity-card",
    edit_target="edit-entity-card",
    create_title="Criar entidade",
    edit_title="Editar entidade",
    active_title="Entidades ativas",
    inactive_title="Entidades inativas",
    create_endpoint="/entities/new",
    update_endpoint="/entities/update",
    save_endpoint="/entities/update",
    delete_endpoint="/entities/delete",
    repository_name="entity",
    repository_class="appverbo.admin_subprocesses.repositories.entity_repository.EntityAdminRepository",
    status_field="entity_status",
    active_value="active",
    inactive_value="inactive",
    identity_field="id",
    label_field="name",
    enabled=True,
    migration_status="reference",
    fields=ENTITY_FIELDS,
    columns=(
        AdminColumnConfig(key="name", label="ENTIDADE", source="name"),
        AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
    ),
    actions=DEFAULT_ACTIVE_ACTIONS,
)


SESSOES_CONFIG = AdminSubprocessConfig(
    key="sessoes",
    label="Sessões",
    singular_label="Sessão",
    plural_label="Sessões",
    edit_param="sidebar_section_edit_key",
    default_target="admin-sidebar-sections-card",
    edit_target="admin-sidebar-sections-form-card",
    create_title="Criar sessão",
    edit_title="Editar sessão",
    active_title="Sessões ativas",
    inactive_title="Sessões inativas",
    create_endpoint="/settings/menu/sidebar-section-save",
    update_endpoint="/settings/menu/sidebar-section-save",
    save_endpoint="/settings/menu/sidebar-section-save",
    move_endpoint="/settings/menu/sidebar-section-move-one",
    repository_name="sidebar_section",
    repository_class="appverbo.admin_subprocesses.repositories.sidebar_section_repository.SidebarSectionAdminRepository",
    status_field="status",
    active_value="ativo",
    inactive_value="inativo",
    identity_field="key",
    label_field="label",
    enabled=True,
    migration_status="native_next",
    fields=SIDEBAR_SECTION_FIELDS,
    columns=DEFAULT_COLUMNS,
    actions=DEFAULT_ACTIVE_ACTIONS,
)


UTILIZADOR_CONFIG = AdminSubprocessConfig(
    key="utilizador",
    label="Utilizador",
    singular_label="Utilizador",
    plural_label="Utilizadores",
    edit_param="user_edit_id",
    default_target="create-user-card",
    edit_target="edit-user-card",
    create_title="Criar utilizador",
    edit_title="Editar utilizador",
    active_title="Utilizadores ativos",
    inactive_title="Utilizadores inativos",
    save_endpoint="/users/update",
    repository_name="user",
    repository_class="",
    enabled=False,
    migration_status="legacy_pending",
)


MENU_CONFIG = AdminSubprocessConfig(
    key="menu",
    label="Menu",
    singular_label="Menu",
    plural_label="Menus",
    edit_param="settings_edit_key",
    default_target="settings-card",
    edit_target="settings-card",
    create_title="Criar menu",
    edit_title="Editar menu",
    active_title="Menus ativos",
    inactive_title="Menus inativos",
    save_endpoint="/settings/menu/save",
    repository_name="menu",
    repository_class="",
    enabled=False,
    migration_status="legacy_pending",
)


CONTAS_CONFIG = AdminSubprocessConfig(
    key="contas",
    label="Contas",
    singular_label="Conta",
    plural_label="Contas",
    edit_param="account_edit_id",
    default_target="admin-account-status-card",
    edit_target="admin-account-status-card",
    create_title="Criar conta",
    edit_title="Editar conta",
    active_title="Contas ativas",
    inactive_title="Contas inativas",
    save_endpoint="",
    repository_name="account",
    repository_class="",
    enabled=False,
    migration_status="legacy_pending",
)


ADMIN_SUBPROCESS_REGISTRY = {
    ENTIDADE_CONFIG.key: ENTIDADE_CONFIG,
    SESSOES_CONFIG.key: SESSOES_CONFIG,
    UTILIZADOR_CONFIG.key: UTILIZADOR_CONFIG,
    MENU_CONFIG.key: MENU_CONFIG,
    CONTAS_CONFIG.key: CONTAS_CONFIG,
}


def get_admin_subprocess_config(key: str) -> AdminSubprocessConfig | None:
    return ADMIN_SUBPROCESS_REGISTRY.get(str(key or "").strip().lower())


def require_admin_subprocess_config(key: str) -> AdminSubprocessConfig:
    config = get_admin_subprocess_config(key)

    if config is None:
        raise KeyError(f"Subprocesso administrativo não configurado: {key}")

    return config


def list_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(ADMIN_SUBPROCESS_REGISTRY.values())


def list_enabled_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(
        config
        for config in ADMIN_SUBPROCESS_REGISTRY.values()
        if config.enabled
    )
'''

write_text_v1(PACKAGE_DIR / "registry.py", registry_content)


####################################################################################
# (5) CRIAR INIT DO PACOTE
####################################################################################

init_content = r'''
from .models import (
    AdminActionConfig,
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
    AdminSubprocessState,
)
from .registry import (
    ADMIN_SUBPROCESS_REGISTRY,
    get_admin_subprocess_config,
    list_admin_subprocess_configs,
    list_enabled_admin_subprocess_configs,
    require_admin_subprocess_config,
)
from .service import build_admin_subprocess_state

__all__ = [
    "AdminActionConfig",
    "AdminColumnConfig",
    "AdminFieldConfig",
    "AdminSubprocessConfig",
    "AdminSubprocessState",
    "ADMIN_SUBPROCESS_REGISTRY",
    "build_admin_subprocess_state",
    "get_admin_subprocess_config",
    "list_admin_subprocess_configs",
    "list_enabled_admin_subprocess_configs",
    "require_admin_subprocess_config",
]
'''

write_text_v1(PACKAGE_DIR / "__init__.py", init_content)


####################################################################################
# (6) CRIAR REPOSITORIES
####################################################################################

repositories_init_content = r'''
from .base import BaseAdminSubprocessRepository

__all__ = ["BaseAdminSubprocessRepository"]
'''

write_text_v1(REPOSITORIES_DIR / "__init__.py", repositories_init_content)


base_repository_content = r'''
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from appverbo.admin_subprocesses.models import AdminSubprocessConfig


class BaseAdminSubprocessRepository(ABC):
    config: AdminSubprocessConfig

    def __init__(self, config: AdminSubprocessConfig) -> None:
        self.config = config

    @abstractmethod
    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    def create(
        self,
        session: Any,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError

    def update(
        self,
        session: Any,
        edit_key: str,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError

    def move(
        self,
        session: Any,
        edit_key: str,
        direction: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError

    def delete(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError
'''

write_text_v1(REPOSITORIES_DIR / "base.py", base_repository_content)


entity_repository_content = r'''
from __future__ import annotations

import importlib
from typing import Any

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository


class EntityAdminRepository(BaseAdminSubprocessRepository):
    def _resolve_entity_model(self) -> type[Any]:
        candidates = (
            "appverbo.models",
            "appverbo.models.entity",
            "appverbo.models.entities",
        )

        for module_name in candidates:
            try:
                module = importlib.import_module(module_name)
            except Exception:
                continue

            entity_model = getattr(module, "Entity", None)

            if entity_model is not None:
                return entity_model

        raise RuntimeError("Modelo Entity não encontrado nos módulos conhecidos.")

    def _to_row(self, entity: Any) -> dict[str, Any]:
        is_active = bool(getattr(entity, "is_active", False))
        return {
            "id": getattr(entity, "id", None),
            "key": str(getattr(entity, "id", "") or ""),
            "name": getattr(entity, "name", "") or getattr(entity, "legal_name", "") or "",
            "label": getattr(entity, "name", "") or getattr(entity, "legal_name", "") or "",
            "status": "active" if is_active else "inactive",
            "status_label": "Ativa" if is_active else "Inativa",
            "is_active": is_active,
        }

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        Entity = self._resolve_entity_model()
        rows = session.query(Entity).order_by(Entity.id.asc()).all()
        return [self._to_row(row) for row in rows]

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if not str(edit_key or "").isdigit():
            return None

        Entity = self._resolve_entity_model()
        entity = session.get(Entity, int(edit_key))

        if entity is None:
            return None

        return self._to_row(entity)
'''

write_text_v1(REPOSITORIES_DIR / "entity_repository.py", entity_repository_content)


sidebar_repository_content = r'''
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository


class SidebarSectionAdminRepository(BaseAdminSubprocessRepository):
    menu_key = "administrativo"

    def _normalize_sections(self, raw_sections: object) -> list[dict[str, Any]]:
        from appverbo.menu_settings import normalize_sidebar_sections

        return [dict(row) for row in normalize_sidebar_sections(raw_sections)]

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        from appverbo.menu_settings import MENU_CONFIG_SIDEBAR_SECTIONS_KEY

        row = session.execute(
            text(
                """
                SELECT menu_config
                FROM sidebar_menu_settings
                WHERE lower(trim(menu_key)) = :menu_key
                LIMIT 1
                """
            ),
            {"menu_key": self.menu_key},
        ).fetchone()

        if not row:
            return []

        raw_config = row[0]

        if isinstance(raw_config, dict):
            menu_config = raw_config
        else:
            menu_config = json.loads(raw_config or "{}")

        return self._normalize_sections(menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY) or [])

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_edit_key = str(edit_key or "").strip().lower()

        if not clean_edit_key:
            return None

        for row in self.list_rows(session, context):
            current_key = str(row.get("key") or "").strip().lower()

            if current_key == clean_edit_key:
                return dict(row)

        return None
'''

write_text_v1(REPOSITORIES_DIR / "sidebar_section_repository.py", sidebar_repository_content)


####################################################################################
# (7) CRIAR MACRO JINJA REUTILIZAVEL
####################################################################################

macro_content = r'''
{% macro render_admin_subprocess_field(field, value="") %}
  <div class="field admin-subprocess-field-v1 {{ field.css_class }}">
    <label for="admin_subprocess_{{ field.key }}">{{ field.label }}{% if field.required %} *{% endif %}</label>

    {% if field.field_type == "select" %}
      <select
        id="admin_subprocess_{{ field.key }}"
        name="{{ field.input_name }}"
        {% if field.required %}required{% endif %}
      >
        {% for option_value, option_label in field.options %}
          <option value="{{ option_value }}" {% if value == option_value %}selected{% endif %}>{{ option_label }}</option>
        {% endfor %}
      </select>
    {% else %}
      <input
        id="admin_subprocess_{{ field.key }}"
        name="{{ field.input_name }}"
        type="{{ field.field_type }}"
        value="{{ value }}"
        {% if field.required %}required{% endif %}
        {% if field.max_length %}maxlength="{{ field.max_length }}"{% endif %}
        {% if field.placeholder %}placeholder="{{ field.placeholder }}"{% endif %}
      >
    {% endif %}
  </div>
{% endmacro %}


{% macro render_admin_subprocess_state(state) %}
  <section
    id="{{ state.target_card_id }}"
    class="card admin-subprocess-card-v1"
    data-admin-subprocess="{{ state.config.key }}"
  >
    {% if state.success %}
      <div class="alert ok">{{ state.success }}</div>
    {% endif %}

    {% if state.error %}
      <div class="alert error">{{ state.error }}</div>
    {% endif %}

    <h2>{% if state.is_editing %}{{ state.config.edit_title }}{% else %}{{ state.config.create_title }}{% endif %}</h2>

    <form method="post" action="{{ state.config.save_endpoint }}" class="admin-subprocess-form-v1">
      <input type="hidden" name="subprocess_key" value="{{ state.config.key }}">
      <input type="hidden" name="subprocess_mode" value="{% if state.is_editing %}edit{% else %}create{% endif %}">
      <input type="hidden" name="subprocess_edit_key" value="{{ state.edit_key }}">
      <input type="hidden" name="subprocess_return_url" value="{{ state.return_url }}">

      <div class="admin-subprocess-grid-v1">
        {% for field in state.config.fields %}
          {% set field_value = state.edit_data.get(field.key, "") if state.edit_data else "" %}
          {{ render_admin_subprocess_field(field, field_value) }}
        {% endfor %}
      </div>

      <div class="form-action-row admin-subprocess-actions-v1">
        <button type="submit" class="action-btn">Guardar</button>
        <a class="action-btn-cancel" href="{{ state.return_url }}">Cancelar</a>
      </div>
    </form>
  </section>
{% endmacro %}
'''

write_text_v1(MACROS_DIR / "admin_subprocess.html", macro_content)


####################################################################################
# (8) CRIAR CSS E JS REUTILIZAVEIS
####################################################################################

css_content = r'''
/* APPVERBO_ADMIN_SUBPROCESSES_V1_START */

.admin-subprocess-card-v1 {
  display: block;
  width: 100%;
  box-sizing: border-box;
}

.admin-subprocess-form-v1 {
  width: 100%;
}

.admin-subprocess-grid-v1 {
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px);
  gap: 12px;
  align-items: end;
  width: 100%;
}

.admin-subprocess-field-v1 label {
  display: block;
  margin-bottom: 6px;
  color: #12213a;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.admin-subprocess-field-v1 input,
.admin-subprocess-field-v1 select {
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

.admin-subprocess-actions-v1 {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}

.admin-subprocess-actions-v1 .action-btn,
.admin-subprocess-actions-v1 .action-btn-cancel {
  min-width: 112px;
  width: 112px;
  height: 38px;
  min-height: 38px;
}

@media (max-width: 1100px) {
  .admin-subprocess-grid-v1 {
    grid-template-columns: 1fr;
  }
}

/* APPVERBO_ADMIN_SUBPROCESSES_V1_END */
'''

write_text_v1(JS_DIR.parent / "css_should_not_exist.tmp", "")
(JS_DIR.parent / "css_should_not_exist.tmp").unlink(missing_ok=True)
write_text_v1(CSS_DIR / "admin_subprocesses_v1.css", css_content)


js_content = r'''
// APPVERBO_ADMIN_SUBPROCESSES_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) VISUALIZAR DETALHES GENERICO
  //###################################################################################

  function instalarVisualizarAdminSubprocessV1() {
    if (window.__appverboAdminSubprocessV1 === true) {
      return;
    }

    window.__appverboAdminSubprocessV1 = true;

    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-view]");

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
  // (2) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarVisualizarAdminSubprocessV1);
  }
  else {
    instalarVisualizarAdminSubprocessV1();
  }
})();
// APPVERBO_ADMIN_SUBPROCESSES_V1_END
'''

write_text_v1(JS_DIR / "admin_subprocesses_v1.js", js_content)


####################################################################################
# (9) ATUALIZAR AGENTS.md COM A NOVA REGRA
####################################################################################

agents_path = resolve_agents_path_v1()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Motor reutilizável de subprocessos administrativos

A partir desta configuração, todo subprocesso administrativo deve seguir o contrato comum `AdminSubprocess`.

Arquivos principais:

- `appverbo/admin_subprocesses/models.py`
- `appverbo/admin_subprocesses/registry.py`
- `appverbo/admin_subprocesses/service.py`
- `appverbo/admin_subprocesses/repositories/base.py`
- `templates/macros/admin_subprocess.html`
- `static/css/modules/admin_subprocesses_v1.css`
- `static/js/modules/admin_subprocesses_v1.js`

Configurações atribuídas inicialmente:

- `entidade`: subprocesso de referência, mantendo o padrão atual server-render.
- `sessoes`: próximo subprocesso a migrar para o padrão nativo reutilizável.
- `utilizador`, `menu` e `contas`: registados como `legacy_pending` para migração posterior.

Regras obrigatórias:

1. URL define `admin_tab` e o parâmetro de edição.
2. Registry identifica a configuração do subprocesso.
3. Repository carrega dados da origem correta.
4. Service monta `AdminSubprocessState`.
5. Template/macro renderiza criar, editar, ativos e inativos.
6. Endpoint grava e redireciona para o `admin_tab` correto.
7. JavaScript não renderiza listas, formulários ou cards.
8. JavaScript só pode executar ações auxiliares.
9. Novos subprocessos devem ser criados adicionando uma configuração no registry e, quando necessário, um repository.
{AGENTS_MARKER_END}"""

if AGENTS_MARKER_START in agents_content and AGENTS_MARKER_END in agents_content:
    agents_content = re.sub(
        re.escape(AGENTS_MARKER_START) + r"[\s\S]*?" + re.escape(AGENTS_MARKER_END),
        agents_rule,
        agents_content,
        count=1,
    )
else:
    agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

agents_path.write_text(agents_content, encoding="utf-8")
print(f"OK: AGENTS.md atualizado em {agents_path}")


####################################################################################
# (10) VALIDAR CONTEUDO CRIADO
####################################################################################

required_files = [
    PACKAGE_DIR / "__init__.py",
    PACKAGE_DIR / "models.py",
    PACKAGE_DIR / "registry.py",
    PACKAGE_DIR / "service.py",
    REPOSITORIES_DIR / "__init__.py",
    REPOSITORIES_DIR / "base.py",
    REPOSITORIES_DIR / "entity_repository.py",
    REPOSITORIES_DIR / "sidebar_section_repository.py",
    MACROS_DIR / "admin_subprocess.html",
    CSS_DIR / "admin_subprocesses_v1.css",
    JS_DIR / "admin_subprocesses_v1.js",
]

for path in required_files:
    if not path.exists():
        fail_v1(f"ficheiro obrigatório não criado: {path}")

registry_text = (PACKAGE_DIR / "registry.py").read_text(encoding="utf-8")

for term in [
    "ENTIDADE_CONFIG",
    "SESSOES_CONFIG",
    "UTILIZADOR_CONFIG",
    "MENU_CONFIG",
    "CONTAS_CONFIG",
    "ADMIN_SUBPROCESS_REGISTRY",
]:
    if term not in registry_text:
        fail_v1(f"termo ausente no registry: {term}")

print("OK: patch_admin_subprocess_config_base_v1 concluído.")
