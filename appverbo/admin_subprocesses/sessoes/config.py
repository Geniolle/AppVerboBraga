from __future__ import annotations

from appverbo.admin_subprocesses.common.config_defaults import DEFAULT_ADMIN_ACTIONS
from appverbo.admin_subprocesses.models import (
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


# ###################################################################################
# (1) CAMPOS DO SUBPROCESSO SESSOES
# ###################################################################################

SIDEBAR_SECTION_FIELDS = (
    AdminFieldConfig(
        key="label",
        label="Nome da sess\u00e3o",
        input_name="section_label",
        field_type="text",
        required=True,
        max_length=80,
        placeholder="Informe o nome da sess\u00e3o",
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


# ###################################################################################
# (2) COLUNAS DO SUBPROCESSO SESSOES
# ###################################################################################

SIDEBAR_SECTION_COLUMNS = (
    AdminColumnConfig(key="label", label="NOME", source="label"),
    AdminColumnConfig(key="system", label="SISTEMA", source="visibility_scope_label"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
)


# ###################################################################################
# (3) CONFIGURACAO DO SUBPROCESSO SESSOES
# ###################################################################################

SESSOES_CONFIG = AdminSubprocessConfig(
    key="sessoes",
    label="Sess\u00f5es",
    singular_label="Sess\u00e3o",
    plural_label="Sess\u00f5es",
    edit_param="sidebar_section_edit_key",
    default_target="admin-sidebar-sections-card",
    edit_target="admin-sidebar-sections-form-card",
    create_title="Criar sess\u00e3o",
    edit_title="Editar sess\u00e3o",
    active_title="Sess\u00f5es ativas",
    inactive_title="Sess\u00f5es inativas",
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
    columns=SIDEBAR_SECTION_COLUMNS,
    actions=DEFAULT_ADMIN_ACTIONS,
)