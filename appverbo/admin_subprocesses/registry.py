from __future__ import annotations


from .models import AdminActionConfig, AdminColumnConfig, AdminFieldConfig, AdminSubprocessConfig
from appverbo.admin_subprocesses.contas.config import CONTAS_CONFIG
from appverbo.admin_subprocesses.entidade.config import ENTIDADE_CONFIG
from appverbo.admin_subprocesses.models import AdminSubprocessConfig
from appverbo.admin_subprocesses.sessoes import SESSOES_CONFIG
from appverbo.admin_subprocesses.utilizador.config import UTILIZADOR_CONFIG


# ###################################################################################
# (1) REGISTO CENTRAL DOS SUBPROCESSOS ADMINISTRATIVOS
# ###################################################################################

# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V5_START

MENU_FIELDS = (
    AdminFieldConfig(
        key="label",
        label="Nome do menu",
        input_name="menu_label",
        field_type="text",
        required=True,
        max_length=80,
        placeholder="Informe o nome do menu",
    ),
    AdminFieldConfig(
        key="visibility_scope_mode",
        label="Sistema",
        input_name="menu_visibility_scope",
        field_type="select",
        required=True,
        options=(
            ("all", "Owner e Legado"),
            ("owner", "Owner"),
            ("legado", "Legado"),
        ),
    ),
    AdminFieldConfig(
        key="sidebar_section",
        label="Sessão",
        input_name="menu_sidebar_section",
        field_type="text",
        required=False,
        max_length=80,
        placeholder="Exemplo: igreja",
    ),
    AdminFieldConfig(
        key="status",
        label="Estado",
        input_name="menu_status",
        field_type="select",
        required=True,
        options=(
            ("ativo", "Ativo"),
            ("inativo", "Inativo"),
        ),
    ),
)


MENU_COLUMNS = (
    AdminColumnConfig(key="label", label="MENU", source="label"),
    AdminColumnConfig(key="section", label="SESSÃO", source="sidebar_section_label"),
    AdminColumnConfig(key="system", label="SISTEMA", source="visibility_scope_label"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
)




MENU_ACTIONS = (
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

MENU_CONFIG = AdminSubprocessConfig(
    key="menu",
    label="Menu",
    singular_label="Menu",
    plural_label="Menus",
    edit_param="settings_edit_key",
    default_target="admin-menu-card",
    edit_target="settings-menu-edit-card",
    create_title="Criar menu",
    edit_title="Editar menu",
    active_title="Menus ativos",
    inactive_title="Menus inativos",
    create_endpoint="/settings/menu/create",
    update_endpoint="/settings/menu/edit",
    save_endpoint="/settings/menu/edit",
    move_endpoint="/settings/menu/move",
    repository_name="menu",
    repository_class="",
    status_field="status",
    active_value="ativo",
    inactive_value="inativo",
    identity_field="key",
    label_field="label",
    mode_field="settings_action",
    edit_key_field="menu_key",
    return_url_field="menu_return_url",
    create_mode_value="create",
    edit_mode_value="edit",
    enabled=True,
    migration_status="state_ready",
    fields=MENU_FIELDS,
    columns=MENU_COLUMNS,
    actions=MENU_ACTIONS,
)

# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V5_END


ADMIN_SUBPROCESS_REGISTRY: dict[str, AdminSubprocessConfig] = {
    ENTIDADE_CONFIG.key: ENTIDADE_CONFIG,
    SESSOES_CONFIG.key: SESSOES_CONFIG,
    UTILIZADOR_CONFIG.key: UTILIZADOR_CONFIG,
    MENU_CONFIG.key: MENU_CONFIG,
    CONTAS_CONFIG.key: CONTAS_CONFIG,
}


# ###################################################################################
# (2) CONSULTA DE CONFIGURACOES
# ###################################################################################

def get_admin_subprocess_config(key: str) -> AdminSubprocessConfig | None:
    return ADMIN_SUBPROCESS_REGISTRY.get(str(key or "").strip().lower())


def require_admin_subprocess_config(key: str) -> AdminSubprocessConfig:
    config = get_admin_subprocess_config(key)

    if config is None:
        raise KeyError(f"Subprocesso administrativo n\u00e3o configurado: {key}")

    return config


def list_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(ADMIN_SUBPROCESS_REGISTRY.values())


def list_enabled_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(
        config
        for config in ADMIN_SUBPROCESS_REGISTRY.values()
        if config.enabled
    )
