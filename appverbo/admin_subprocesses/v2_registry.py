from __future__ import annotations

from .v2_models import (
    AdminActionConfigV2,
    AdminColumnConfigV2,
    AdminFieldConfigV2,
    AdminFieldOptionV2,
    AdminSubprocessConfigV2,
)


# ###################################################################################
# (1) ENTIDADE 100% DECLARATIVA
# ###################################################################################

ENTIDADE_CONFIG_V2 = AdminSubprocessConfigV2(
    key="entidade",
    label="Entidade",
    singular_label="Entidade",
    create_title="Criar entidade",
    edit_title="Editar entidade",
    active_title="Entidades ativas",
    inactive_title="Entidades inativas",
    repository_class_path="appverbo.admin_subprocesses.v2_entity_repository.EntityAdminSubprocessRepositoryV2",
    identity_field="id",
    label_field="name",
    status_field="status",
    active_value="active",
    inactive_value="inactive",
    default_target="admin-subprocess-v2-entidade",
    edit_target="admin-subprocess-v2-entidade-edit",
    edit_param="entity_edit_id",
    grid_columns=4,
    fields=(
        AdminFieldConfigV2(
            key="internal_number",
            label="Nº cliente",
            field_type="readonly",
            visible_on_create=False,
            readonly_on_edit=True,
        ),
        AdminFieldConfigV2(
            key="name",
            label="Nome da entidade",
            required=True,
            max_length=150,
            placeholder="Nome completo da entidade",
        ),
        AdminFieldConfigV2(
            key="acronym",
            label="Acrónimo",
            max_length=30,
            placeholder="Ex.: VB",
        ),
        AdminFieldConfigV2(
            key="tax_id",
            label="Nº Identificação Fiscal",
            required=True,
            max_length=40,
        ),
        AdminFieldConfigV2(
            key="profile_scope",
            label="Perfil da entidade",
            field_type="select",
            input_name="entity_profile_scope",
            required=True,
            options=(
                AdminFieldOptionV2("legado", "Legado"),
                AdminFieldOptionV2("owner", "Owner"),
            ),
        ),
        AdminFieldConfigV2(
            key="status",
            label="Estado",
            field_type="select",
            default_value="active",
            options=(
                AdminFieldOptionV2("active", "Ativo"),
                AdminFieldOptionV2("inactive", "Inativo"),
            ),
        ),
        AdminFieldConfigV2(
            key="email",
            label="Email",
            field_type="email",
            required=True,
            max_length=150,
        ),
        AdminFieldConfigV2(
            key="phone",
            label="Telefone",
            field_type="tel",
            required=True,
            max_length=30,
        ),
        AdminFieldConfigV2(
            key="responsible_name",
            label="Nome do responsável",
            required=True,
            max_length=200,
        ),
        AdminFieldConfigV2(
            key="address",
            label="Morada",
            required=True,
            max_length=255,
            grid_span=2,
        ),
        AdminFieldConfigV2(
            key="door_number",
            label="Nº da porta",
            required=True,
            max_length=30,
        ),
        AdminFieldConfigV2(
            key="freguesia",
            label="Freguesia",
            required=True,
            max_length=120,
        ),
        AdminFieldConfigV2(
            key="postal_code",
            label="Código postal",
            required=True,
            max_length=30,
        ),
        AdminFieldConfigV2(
            key="city",
            label="Cidade",
            required=True,
            max_length=120,
        ),
        AdminFieldConfigV2(
            key="country",
            label="País",
            required=True,
            max_length=120,
        ),
        AdminFieldConfigV2(
            key="logo_url",
            label="Imagem/ícone da entidade",
            field_type="file",
            input_name="entity_logo_file",
            full_width=True,
            help_text="PNG, JPG, WEBP, GIF ou SVG até 5MB.",
        ),
        AdminFieldConfigV2(
            key="description",
            label="Descrição",
            field_type="textarea",
            full_width=True,
            grid_span=4,
        ),
    ),
    columns=(
        AdminColumnConfigV2("internal_number", "Nº cliente"),
        AdminColumnConfigV2("name", "Nome"),
        AdminColumnConfigV2("profile_scope_label", "Perfil"),
        AdminColumnConfigV2("city", "Cidade"),
        AdminColumnConfigV2("created_at_display", "Criado em"),
        AdminColumnConfigV2("status_label", "Estado", column_type="badge"),
    ),
    actions=(
        AdminActionConfigV2("view", "Visualizar", "👁", "view"),
        AdminActionConfigV2("edit", "Editar", "✎", "edit"),
        AdminActionConfigV2(
            "delete",
            "Eliminar",
            "🗑",
            "delete",
            allowed_statuses=("inactive",),
            confirm_message="Confirmar eliminação desta entidade inativa?",
        ),
    ),
    migration_status="native_v2",
)


# ###################################################################################
# (2) REGISTRY
# ###################################################################################

ADMIN_SUBPROCESS_REGISTRY_V2 = {
    ENTIDADE_CONFIG_V2.key: ENTIDADE_CONFIG_V2,
}


def get_admin_subprocess_config_v2(key: str) -> AdminSubprocessConfigV2 | None:
    return ADMIN_SUBPROCESS_REGISTRY_V2.get(str(key or "").strip().lower())


def list_admin_subprocess_configs_v2() -> list[AdminSubprocessConfigV2]:
    return list(ADMIN_SUBPROCESS_REGISTRY_V2.values())
