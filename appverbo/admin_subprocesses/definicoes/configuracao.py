from __future__ import annotations

from appverbo.admin_subprocesses.models import (
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


####################################################################################
# (1) CAMPOS DO SUBPROCESSO DEFINICOES
####################################################################################

DEFINICOES_FIELDS = (
    AdminFieldConfig(
        key="parameter_name",
        label="NOME DO PARÂMETRO",
        input_name="definition_parameter_name",
        field_type="text",
        required=True,
        max_length=160,
    ),
    AdminFieldConfig(
        key="parameter_type",
        label="TIPO",
        input_name="definition_type",
        field_type="select",
        required=True,
        options=(
            ("tamanho", "Tamanho"),
            ("fonte", "Fonte"),
            ("cor", "Cor"),
            ("icone", "Ícone"),
        ),
    ),
    AdminFieldConfig(
        key="initial_value",
        label="VALOR INICIAL",
        input_name="definition_initial_value",
        field_type="text",
        required=True,
        max_length=255,
        placeholder="Ex.: music, home, building, users, wallet",
    ),
    AdminFieldConfig(
        key="process_name",
        label="PROCESSO",
        input_name="definition_process",
        field_type="select",
        required=True,
        options=(("", "Selecione"),),
        options_source="session_processes",
    ),
    AdminFieldConfig(
        key="subprocess_name",
        label="SUBPROCESSO",
        input_name="definition_subprocess",
        field_type="select",
        required=True,
        options=(("", "Selecione"),),
        options_source="menu_subprocesses",
    ),
    AdminFieldConfig(
        key="entity_scope_label",
        label="ENTIDADE",
        input_name="definition_entity_scope_label",
        field_type="readonly",
        readonly_on_create=True,
        readonly_on_edit=True,
        css_class="admin-subprocess-scope-field-v1",
    ),
    AdminFieldConfig(
        key="status",
        label="ESTADO",
        input_name="definition_status",
        field_type="select",
        required=True,
        options=(
            ("active", "Ativo"),
            ("inactive", "Inativo"),
        ),
    ),
)


####################################################################################
# (2) COLUNAS DO SUBPROCESSO DEFINICOES
####################################################################################

DEFINICOES_COLUMNS = (
    AdminColumnConfig(key="parameter_name", label="NOME DO PARÂMETRO", source="parameter_name"),
    AdminColumnConfig(key="parameter_type", label="TIPO", source="parameter_type_label"),
    AdminColumnConfig(key="initial_value", label="VALOR INICIAL", source="initial_value"),
    AdminColumnConfig(key="process_name", label="PROCESSO", source="process_name"),
    AdminColumnConfig(key="subprocess_name", label="SUBPROCESSO", source="subprocess_name"),
    AdminColumnConfig(key="entity_scope_label", label="ENTIDADE", source="entity_scope_label"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
)


####################################################################################
# (3) CONFIGURACAO CENTRAL DO SUBPROCESSO DEFINICOES
####################################################################################

DEFINICOES_CONFIG = AdminSubprocessConfig(
    key="definicoes",
    label="Definições",
    singular_label="Definição",
    plural_label="Definições",
    edit_param="definition_edit_id",
    default_target="admin-definicoes-card",
    edit_target="admin-definicoes-card-edit",
    create_title="Criar Definição",
    edit_title="Editar Definição",
    active_title="Definições ativas",
    inactive_title="Definições inativas",
    create_endpoint="/settings/definicoes/save",
    update_endpoint="/settings/definicoes/save",
    save_endpoint="/settings/definicoes/save",
    delete_endpoint="/settings/definicoes/delete",
    repository_name="definition",
    repository_class="appverbo.admin_subprocesses.repositories.definition_repository.DefinitionAdminRepository",
    status_field="status",
    active_value="active",
    inactive_value="inactive",
    identity_field="id",
    label_field="parameter_name",
    enabled=True,
    migration_status="native",
    fields=DEFINICOES_FIELDS,
    columns=DEFINICOES_COLUMNS,
)
