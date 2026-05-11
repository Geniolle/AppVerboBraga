from __future__ import annotations

from appverbo.admin_subprocesses.common.config_defaults import DEFAULT_ADMIN_ACTIONS
from appverbo.admin_subprocesses.models import (
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


# ###################################################################################
# (1) CAMPOS DO SUBPROCESSO ENTIDADE
# ###################################################################################

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


# ###################################################################################
# (2) CONFIGURACAO DO SUBPROCESSO ENTIDADE
# ###################################################################################

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
    actions=DEFAULT_ADMIN_ACTIONS,
)