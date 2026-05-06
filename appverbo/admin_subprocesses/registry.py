
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
    delete_endpoint="/settings/menu/sidebar-section-delete-one",
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
