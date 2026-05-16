from __future__ import annotations

from appverbo.admin_subprocesses.models import (
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


# ###################################################################################
# (1) CAMPOS DO SUBPROCESSO MENU
# ###################################################################################

MENU_FIELDS = (
    AdminFieldConfig(
        key="menu_label",
        label="Nome do menu",
        input_name="menu_label",
        field_type="text",
        required=True,
        max_length=100,
        placeholder="Ex.: Assiduidade",
    ),
    AdminFieldConfig(
        key="menu_visibility_scope",
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
        key="menu_section",
        label="Sessão",
        input_name="menu_section",
        field_type="select",
        options_source="sidebar_sections",
    ),
)


# ###################################################################################
# (2) COLUNAS DO SUBPROCESSO MENU
# ###################################################################################

MENU_COLUMNS = (
    AdminColumnConfig(key="label", label="MENU", source="label"),
    AdminColumnConfig(key="menu_key", label="CHAVE", source="key"),
    AdminColumnConfig(key="menu_section_label", label="GRUPO", source="menu_section_label"),
    AdminColumnConfig(key="status_label", label="ESTADO", source="status_label"),
)


# ###################################################################################
# (3) CONFIGURACAO CENTRAL DO SUBPROCESSO MENU
# ###################################################################################

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
    save_endpoint="/settings/menu/save",
    create_endpoint="/settings/menu/create",
    update_endpoint="/settings/menu/edit",
    move_endpoint="/settings/menu/move",
    delete_endpoint="/settings/menu/delete",
    repository_name="menu",
    repository_class="appverbo.admin_subprocesses.repositories.menu_repository.MenuAdminRepository",
    status_field="status",
    active_value="active",
    inactive_value="inactive",
    identity_field="key",
    label_field="label",
    enabled=True,
    migration_status="native_next",
    fields=MENU_FIELDS,
    columns=MENU_COLUMNS,
)
