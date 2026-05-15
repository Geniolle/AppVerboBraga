from __future__ import annotations

from .entidade.configuracao import ENTIDADE_CONFIG
from .models import (
    AdminActionConfig,
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)
from .utilizador.configuracao import UTILIZADOR_CONFIG


####################################################################################
# (1) CAMPOS DOS SUBPROCESSOS
####################################################################################

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


####################################################################################
# (2) AÇÕES PADRÃO
####################################################################################

DEFAULT_ACTIVE_ACTIONS = (
    AdminActionConfig(
        key="move_up",
        label="Subir",
        icon="\u2191",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="move_down",
        label="Descer",
        icon="\u2193",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="view",
        label="Visualizar",
        icon="\U0001f441",
        action_type="button",
        visible_when=("ativo", "inativo", "active", "inactive", "pending", "blocked"),
    ),
    AdminActionConfig(
        key="edit",
        label="Editar",
        icon="\u270e",
        action_type="link",
        visible_when=("ativo", "inativo", "active", "inactive", "pending", "blocked"),
    ),
)


####################################################################################
# (3) CONFIGURAÇÃO - SESSÕES
####################################################################################

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
    mode_field="section_mode",
    edit_key_field="original_section_key",
    return_url_field="sidebar_section_return_url",
    create_mode_value="create",
    edit_mode_value="edit",
    enabled=True,
    migration_status="native_next",
    fields=SIDEBAR_SECTION_FIELDS,
    columns=DEFAULT_COLUMNS,
    actions=DEFAULT_ACTIVE_ACTIONS,
)


####################################################################################
# (4) CONFIGURAÇÃO - UTILIZADOR
####################################################################################

# UTILIZADOR_CONFIG é definido em appverbo/admin_subprocesses/utilizador/configuracao.py


####################################################################################
# (5) CONFIGURAÇÃO - MENU
####################################################################################

MENU_CONFIG = AdminSubprocessConfig(
    key="menu",
    label="Menu",
    singular_label="Menu",
    plural_label="Menus",
    edit_param="settings_edit_key",
    default_target="admin-menu-card",
    edit_target="admin-menu-card",
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


####################################################################################
# (6) CONFIGURAÇÃO - CONTAS
####################################################################################

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


####################################################################################
# (7) REGISTRY ÚNICO
####################################################################################

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
