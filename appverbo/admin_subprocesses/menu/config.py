from __future__ import annotations

from appverbo.admin_subprocesses.models import AdminColumnConfig, AdminFieldConfig, AdminSubprocessConfig


# ###################################################################################
# (1) CONFIGURACAO DO SUBPROCESSO MENU
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
    save_endpoint="/settings/menu/edit",
    create_endpoint="/settings/menu/admin-create",
    update_endpoint="/settings/menu/edit",
    move_endpoint="/settings/menu/admin-move",
    delete_endpoint="/settings/menu/admin-delete",
    repository_name="menu",
    repository_class="",
    enabled=True,
    migration_status="native_split_v1",
    identity_field="key",
    label_field="label",
    fields=(
        AdminFieldConfig(
            key="menu_label",
            label="Nome do menu",
            input_name="menu_label",
            required=True,
            max_length=100,
            placeholder="Ex.: Assiduidade",
        ),
        AdminFieldConfig(
            key="menu_visibility_scope",
            label="Sistema",
            input_name="menu_visibility_scope",
            field_type="select",
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
    ),
    columns=(
        AdminColumnConfig(
            key="label",
            label="Menu lateral",
            source="label",
        ),
        AdminColumnConfig(
            key="visibility_scope_label",
            label="Sistema",
            source="visibility_scope_label",
        ),
        AdminColumnConfig(
            key="status_label",
            label="Estado",
            source="status_label",
        ),
    ),
)
