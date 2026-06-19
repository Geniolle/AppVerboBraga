from __future__ import annotations

from appverbo.admin_subprocesses.models import (
    AdminActionConfig,
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


####################################################################################
# (1) CAMPOS DO SUBPROCESSO ENTIDADE
####################################################################################

ENTITY_FIELDS = (
    AdminFieldConfig(
        key="internal_number",
        label="Nº Entidade",
        input_name="internal_number",
        field_type="readonly",
        visible_on_create=False,
        readonly_on_edit=True,
    ),
    AdminFieldConfig(
        key="name",
        label="Nome da entidade",
        input_name="name",
        field_type="text",
        required=True,
        max_length=150,
    ),
    AdminFieldConfig(
        key="acronym",
        label="Acrónimo (opcional)",
        input_name="acronym",
        field_type="text",
        required=False,
        max_length=5,
    ),
    AdminFieldConfig(
        key="tax_id",
        label="Nº Identificação Fiscal",
        input_name="tax_id",
        field_type="text",
        required=True,
        max_length=20,
    ),
    AdminFieldConfig(
        key="profile_scope",
        label="Sistema",
        input_name="entity_profile_scope",
        field_type="select",
        required=True,
        options=(
            ("owner", "Owner"),
            ("legado", "Legado"),
        ),
    ),
    AdminFieldConfig(
        key="email",
        label="Email",
        input_name="email",
        field_type="email",
        required=True,
        max_length=150,
    ),
    AdminFieldConfig(
        key="phone",
        label="Telefone",
        input_name="phone",
        field_type="tel",
        required=True,
        max_length=15,
    ),
    AdminFieldConfig(
        key="responsible_name",
        label="Nome do responsável",
        input_name="responsible_name",
        field_type="text",
        required=True,
    ),
    AdminFieldConfig(
        key="address",
        label="Morada",
        input_name="address",
        field_type="text",
        required=True,
    ),
    AdminFieldConfig(
        key="door_number",
        label="Nº da porta",
        input_name="door_number",
        field_type="text",
        required=True,
        max_length=15,
    ),
    AdminFieldConfig(
        key="freguesia",
        label="Freguesia",
        input_name="freguesia",
        field_type="text",
        required=True,
    ),
    AdminFieldConfig(
        key="postal_code",
        label="Código postal",
        input_name="postal_code",
        field_type="text",
        required=True,
        max_length=30,
    ),
    AdminFieldConfig(
        key="city",
        label="Cidade",
        input_name="city",
        field_type="text",
        required=True,
        max_length=120,
    ),
    AdminFieldConfig(
        key="country",
        label="País",
        input_name="country",
        field_type="text",
        required=True,
        max_length=50,
    ),
    AdminFieldConfig(
        key="status",
        label="Estado da entidade",
        input_name="entity_status",
        field_type="select",
        required=True,
        options=(
            ("active", "Ativo"),
            ("inactive", "Inativo"),
        ),
    ),
    AdminFieldConfig(
        key="created_at",
        label="Data da criação",
        input_name="created_at",
        field_type="readonly",
        visible_on_create=False,
        readonly_on_edit=True,
    ),
    AdminFieldConfig(
        key="logo_url",
        label="Imagem/ícone da entidade (ficheiro opcional)",
        input_name="entity_logo_file",
        field_type="file",
        required=False,
        accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml",
        remove_input_name="remove_logo",
    ),
)


####################################################################################
# (2) ACOES DO SUBPROCESSO ENTIDADE
####################################################################################

ENTIDADE_ACTIONS = (
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
        icon="✎",
        action_type="link",
        visible_when=("ativo", "inativo", "active", "inactive", "pending", "blocked"),
    ),
)


####################################################################################
# (3) CONFIGURACAO CENTRAL DO SUBPROCESSO ENTIDADE
####################################################################################

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
    view_title="Exibir entidade",
    active_title="Entidades ativas",
    inactive_title="Entidades inativas",
    create_endpoint="/entities/new",
    update_endpoint="/entities/update",
    save_endpoint="/entities/update",
    delete_endpoint="/entities/delete",
    repository_name="entity",
    repository_class="appverbo.admin_subprocesses.repositories.entity_repository.EntityAdminRepository",
    status_field="status",
    active_value="active",
    inactive_value="inactive",
    identity_field="id",
    label_field="name",
    edit_key_field="entity_id",
    delete_key_field="entity_id",
    enabled=True,
    migration_status="native",
    table_name="entities",
    form_enctype="multipart/form-data",
    fields=ENTITY_FIELDS,
    columns=(
        AdminColumnConfig(key="internal_number", label="Nº ENTIDADE", source="internal_number"),
        AdminColumnConfig(key="name", label="NOME", source="name"),
        AdminColumnConfig(key="system", label="SISTEMA", source="profile_scope_label"),
        AdminColumnConfig(key="phone", label="TELEFONE", source="phone"),
        AdminColumnConfig(key="address", label="MORADA", source="address"),
        AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
        AdminColumnConfig(key="created_at", label="CRIADO EM", source="created_at"),
    ),
    actions=ENTIDADE_ACTIONS,
)
