from __future__ import annotations

from appverbo.admin_subprocesses.models import (
    AdminActionConfig,
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


####################################################################################
# (1) CAMPOS DO SUBPROCESSO UTILIZADOR
####################################################################################

USER_FIELDS = (
    AdminFieldConfig(
        key="full_name",
        label="Nome completo",
        input_name="full_name",
        field_type="text",
        required=True,
        max_length=160,
    ),
    AdminFieldConfig(
        key="primary_phone",
        label="Telefone principal",
        input_name="primary_phone",
        field_type="text",
        required=True,
        max_length=30,
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
        key="account_status",
        label="Estado",
        input_name="account_status",
        field_type="select",
        required=True,
        options=(
            ("pending", "Pendente"),
            ("active", "Ativo"),
            ("inactive", "Inativo"),
            ("blocked", "Bloqueado"),
        ),
    ),
    AdminFieldConfig(
        key="entity_id",
        label="Entidade",
        input_name="entity_id",
        field_type="select",
        required=True,
    ),
    AdminFieldConfig(
        key="profile_id",
        label="Perfil global",
        input_name="profile_id",
        field_type="select",
        required=True,
    ),
)


####################################################################################
# (2) COLUNAS DO SUBPROCESSO UTILIZADOR
####################################################################################

USER_COLUMNS = (
    AdminColumnConfig(key="id", label="ID", source="id"),
    AdminColumnConfig(key="full_name", label="NOME", source="full_name"),
    AdminColumnConfig(key="email", label="EMAIL", source="login_email"),
    AdminColumnConfig(key="phone", label="TELEFONE", source="primary_phone"),
    AdminColumnConfig(key="entity", label="ENTIDADE", source="entity_name"),
    AdminColumnConfig(key="profile", label="PERFIL", source="profile_name"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
    AdminColumnConfig(key="created_at", label="CRIADO EM", source="created_at_label"),
)


####################################################################################
# (3) ACOES DO SUBPROCESSO UTILIZADOR
####################################################################################

USER_ACTIONS = (
    AdminActionConfig(
        key="view",
        label="Exibir",
        icon="view",
        action_type="link",
        visible_when=("active", "inactive", "pending", "blocked"),
    ),
    AdminActionConfig(
        key="edit",
        label="Editar",
        icon="edit",
        action_type="link",
        visible_when=("active", "inactive", "pending", "blocked"),
    ),
)


####################################################################################
# (4) CONFIGURACAO CENTRAL DO SUBPROCESSO UTILIZADOR
####################################################################################

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
    create_endpoint="/users/new",
    delete_endpoint="/users/delete",
    repository_name="user",
    repository_class="appverbo.admin_subprocesses.repositories.user_repository.UserAdminRepository",
    status_field="account_status",
    active_value="active",
    inactive_value="inactive",
    identity_field="id",
    label_field="full_name",
    edit_key_field="user_id",
    enabled=True,
    migration_status="native",
    fields=USER_FIELDS,
    columns=USER_COLUMNS,
    actions=USER_ACTIONS,
)
