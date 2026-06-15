from __future__ import annotations

from appverbo.admin_subprocesses.models import (
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


# ###################################################################################
# (1) CAMPOS DO SUBPROCESSO PERFIL
# ###################################################################################

PERFIL_FIELDS = (
    AdminFieldConfig(
        key="name",
        label="Nome do perfil",
        input_name="profile_name",
        field_type="text",
        required=True,
        max_length=100,
        placeholder="Informe o nome do perfil",
    ),
    AdminFieldConfig(
        key="description",
        label="Descrição",
        input_name="profile_description",
        field_type="text",
        required=False,
        max_length=255,
        placeholder="Descrição opcional",
    ),
    AdminFieldConfig(
        key="visibility_scope_mode",
        label="[SISTEMA]",
        input_name="section_visibility_scope_mode",
        field_type="select",
        required=True,
        options=(
            ("entity", "Esta entidade"),
            ("all", "Todos os sistemas"),
        ),
    ),
    AdminFieldConfig(
        key="status",
        label="Estado",
        input_name="profile_status",
        field_type="select",
        required=True,
        options=(
            ("ativo", "Ativo"),
            ("inativo", "Inativo"),
        ),
    ),
)


# ###################################################################################
# (2) COLUNAS DO SUBPROCESSO PERFIL
# ###################################################################################

PERFIL_COLUMNS = (
    AdminColumnConfig(key="name", label="NOME", source="name"),
    AdminColumnConfig(key="visibility_scope_mode", label="SISTEMA", source="visibility_scope_label"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
)


# ###################################################################################
# (3) CONFIGURACAO DO SUBPROCESSO PERFIL
# ###################################################################################

PERFIL_CONFIG = AdminSubprocessConfig(
    key="perfil",
    label="Perfil",
    singular_label="Perfil",
    plural_label="Perfis",
    edit_param="profile_edit_id",
    default_target="admin-perfil-card",
    edit_target="admin-perfil-card-edit",
    create_title="Criar perfil",
    edit_title="Editar perfil",
    active_title="Perfis ativos",
    inactive_title="Perfis inativos",
    create_endpoint="/settings/perfil/save",
    update_endpoint="/settings/perfil/save",
    save_endpoint="/settings/perfil/save",
    delete_endpoint="/settings/perfil/delete",
    repository_name="profile",
    repository_class="appverbo.admin_subprocesses.repositories.profile_repository.ProfileAdminRepository",
    status_field="status",
    active_value="ativo",
    inactive_value="inativo",
    identity_field="id",
    label_field="name",
    mode_field="subprocess_mode",
    edit_key_field="subprocess_edit_key",
    return_url_field="subprocess_return_url",
    create_mode_value="create",
    edit_mode_value="edit",
    enabled=True,
    migration_status="native",
    table_name="profiles",
    fields=PERFIL_FIELDS,
    columns=PERFIL_COLUMNS,
)
