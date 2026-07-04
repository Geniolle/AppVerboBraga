
from __future__ import annotations

from .models import (
    AdminActionConfig,
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


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


SIDEBAR_SECTION_FIELDS = (
    AdminFieldConfig(
        key="label",
        label="Nome da sessão",
        input_name="section_label",
        field_type="text",
        required=True,
        max_length=80,
        placeholder="Informe o nome da sessão",
    ),
    AdminFieldConfig(
        key="visibility_scope_mode",
        label="Sistema",
        input_name="section_visibility_scope_mode",
        field_type="select",
        required=True,
        options=(
            ("all", "Default"),
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


DEFAULT_COLUMNS = (
    AdminColumnConfig(key="label", label="NOME", source="label", css_class="admin-col-main-v1", always_visible=True),
    AdminColumnConfig(key="system", label="SISTEMA", source="visibility_scope_label", css_class="admin-col-system-v1"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label", css_class="admin-col-status-v1", always_visible=True),
)


DEFAULT_ACTIVE_ACTIONS = (
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


SIDEBAR_SECTION_DELETE_ACTION = AdminActionConfig(
    key="delete",
    label="Eliminar",
    icon="🗑",
    action_type="post_delete",
    visible_when=("inativo",),
    condition_field="can_delete",
    requires_confirmation=True,
    confirmation_message="Tem a certeza que pretende eliminar esta sessão?",
)


ENTITY_DELETE_ACTION = AdminActionConfig(
    key="delete",
    label="Eliminar",
    icon="🗑",
    action_type="post_delete",
    visible_when=("inactive",),
    requires_confirmation=True,
    confirmation_message="Tem a certeza que pretende eliminar esta entidade?",
)

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
    active_title="Entidades criadas",
    inactive_title="Entidades inativas",
    create_endpoint="/entities/new",
    update_endpoint="/entities/update",
    save_endpoint="/entities/update",
    delete_endpoint="/entities/delete",
    repository_name="entity",
    repository_class="appgenesis.admin_subprocesses.repositories.entity_repository.EntityAdminRepository",
    status_field="entity_status",
    active_value="active",
    inactive_value="inactive",
    identity_field="id",
    label_field="name",
    enabled=True,
    migration_status="native",
    fields=ENTITY_FIELDS,
    columns=(
        AdminColumnConfig(
            key="entity_number",
            label="Nº DA ENTIDADE",
            source="entity_number",
            css_class="admin-col-number-v1",
            sortable=True,
            sort_type="number",
            default_sort="asc",
            responsive_priority=2,
            sort_value_source="entity_number_sort_value",
        ),
        AdminColumnConfig(
            key="name",
            label="NOME",
            source="name",
            css_class="admin-col-main-v1",
            always_visible=True,
        ),
        AdminColumnConfig(
            key="email",
            label="EMAIL",
            source="email",
            css_class="admin-col-email-v1",
            responsive_priority=4,
        ),
        AdminColumnConfig(
            key="phone",
            label="TELEFONE",
            source="phone",
            css_class="admin-col-phone-v1",
            responsive_priority=2,
        ),
        AdminColumnConfig(
            key="responsible_name",
            label="NOME DO RESPONSÁVEL",
            source="responsible_name",
            css_class="admin-col-text-v1",
            responsive_priority=3,
        ),
        AdminColumnConfig(
            key="address",
            label="MORADA",
            source="address",
            css_class="admin-col-text-v1 admin-col-address-v1",
            responsive_priority=7,
        ),
        AdminColumnConfig(
            key="country",
            label="PAÍS",
            source="country",
            css_class="admin-col-country-v1",
            responsive_priority=5,
        ),
        AdminColumnConfig(
            key="created_at",
            label="CRIADO EM",
            source="created_at",
            css_class="admin-col-date-v1",
            responsive_priority=6,
        ),
        AdminColumnConfig(
            key="status",
            label="ESTADO",
            source="status_label",
            css_class="admin-col-status-v1",
            always_visible=True,
        ),
    ),
    actions=(
        AdminActionConfig(key="view", label="Visualizar", icon="👁", action_type="link", visible_when=("active", "inactive")),
        AdminActionConfig(key="edit", label="Editar", icon="✎", action_type="link", visible_when=("active", "inactive")),
        ENTITY_DELETE_ACTION,
    ),
    menu_scope="administrativo",
    table_css_class="admin-entity-table-v1",
    empty_active_message="Sem entidades ativas.",
    empty_inactive_message="Sem entidades inativas.",
    edit_url_extra_params="admin_tab=entidade",
    action_form_key_field="entity_id",
    view_link_param="entity_view",
    status_badge_class="entity-status",
    active_card_id="recent-entities-card",
    inactive_card_id="inactive-entities-card",
    active_table_id="recent-entities-table",
    inactive_table_id="inactive-entities-table",
    active_limiter_id="recent-entities-limiter",
    inactive_limiter_id="inactive-entities-limiter",
)


SESSOES_CONFIG = AdminSubprocessConfig(
    key="sessoes",
    label="Sessões",
    singular_label="Sessão",
    plural_label="Sessões",
    edit_param="sidebar_section_edit_key",
    default_target="admin-sidebar-sections-card",
    edit_target="admin-sidebar-sections-form-card",
    create_title="Criar sessão",
    edit_title="Editar sessão",
    active_title="Sessões ativas",
    inactive_title="Sessões inativas",
    create_endpoint="/settings/menu/sidebar-section-save",
    update_endpoint="/settings/menu/sidebar-section-save",
    save_endpoint="/settings/menu/sidebar-section-save",
    move_endpoint="/settings/menu/sidebar-section-move-one",
    delete_endpoint="/settings/menu/sidebar-section-delete",
    repository_name="sidebar_section",
    repository_class="appgenesis.admin_subprocesses.repositories.sidebar_section_repository.SidebarSectionAdminRepository",
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
    columns=DEFAULT_COLUMNS,
    actions=DEFAULT_ACTIVE_ACTIONS + (SIDEBAR_SECTION_DELETE_ACTION,),
    menu_scope="administrativo,sessoes",
    empty_active_message="Sem sessões ativas.",
    empty_inactive_message="Sem sessões inativas.",
    edit_url_extra_params="admin_tab=sessoes&sidebar_sections_tab=sessoes",
)


AUTHORIZATION_PROFILE_TECHNICAL_FIELDS = (
    AdminFieldConfig(
        key="entity_scope",
        label="Entidade",
        input_name="auth_profile_entity_scope",
        field_type="select",
        required=True,
        options=(
            ("entity", "Entidade atual"),
            ("system", "Todo o sistema"),
        ),
    ),
    AdminFieldConfig(
        key="visibility_scope_mode",
        label="Sistema",
        input_name="auth_profile_visibility_scope_mode",
        field_type="select",
        required=True,
        options=(
            ("all", "Default"),
            ("owner", "Owner"),
            ("legado", "Legado"),
        ),
    ),
    AdminFieldConfig(
        key="status",
        label="Estado",
        input_name="auth_profile_status",
        field_type="select",
        required=True,
        options=(
            ("ativo", "Ativo"),
            ("inativo", "Inativo"),
        ),
    ),
)


AUTH_PROFILE_DELETE_ACTION = AdminActionConfig(
    key="delete",
    label="Eliminar",
    icon="X",
    action_type="post_delete",
    visible_when=("inativo",),
    requires_confirmation=True,
    confirmation_message="Tem a certeza que pretende eliminar este perfil?",
)


AUTHORIZATION_PROFILE_CONFIG = AdminSubprocessConfig(
    key="perfil_de_autorizacao",
    label="Perfil de autorização",
    singular_label="Perfil",
    plural_label="Perfis",
    edit_param="auth_profile_edit_key",
    default_target="auth-profile-card",
    edit_target="auth-profile-form-card",
    create_title="Criar perfil",
    edit_title="Editar perfil",
    active_title="Perfis ativos",
    inactive_title="Perfis inativos",
    save_endpoint="/users/profile/auth-profile-save",
    create_endpoint="/users/profile/auth-profile-save",
    update_endpoint="/users/profile/auth-profile-save",
    delete_endpoint="/users/profile/auth-profile-delete",
    repository_name="auth_profile",
    repository_class="appgenesis.admin_subprocesses.repositories.auth_profile_repository.AuthorizationProfileAdminRepository",
    status_field="status",
    active_value="ativo",
    inactive_value="inativo",
    identity_field="key",
    label_field="label",
    mode_field="auth_profile_mode",
    edit_key_field="original_auth_profile_key",
    return_url_field="auth_profile_return_url",
    create_mode_value="create",
    edit_mode_value="edit",
    enabled=True,
    migration_status="native",
    uses_dynamic_fields=True,
    dynamic_fields_menu_key="perfil_de_autorizacao",
    dynamic_fields_section_header_key="custom_perfil",
    fields=AUTHORIZATION_PROFILE_TECHNICAL_FIELDS,
    columns=(
        AdminColumnConfig(
            key="label",
            label="PERFIL",
            source="label",
            css_class="admin-col-main-v1",
            always_visible=True,
            sortable=True,
            default_sort="asc",
        ),
        AdminColumnConfig(
            key="system",
            label="SISTEMA",
            source="visibility_scope_label",
            css_class="admin-col-system-v1",
        ),
        AdminColumnConfig(
            key="status",
            label="ESTADO",
            source="status_label",
            css_class="admin-col-status-v1",
            always_visible=True,
        ),
    ),
    actions=(
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
        AUTH_PROFILE_DELETE_ACTION,
    ),
    menu_scope="perfil_de_autorizacao",
    empty_active_message="Sem perfis ativos.",
    empty_inactive_message="Sem perfis inativos.",
    action_form_key_field="auth_profile_key",
    active_card_id="auth-profile-active-card",
    inactive_card_id="auth-profile-inactive-card",
    active_table_id="auth-profile-active-table",
    inactive_table_id="auth-profile-inactive-table",
    active_limiter_id="auth-profile-active-limiter",
    inactive_limiter_id="auth-profile-inactive-limiter",
)


OBJETO_AUTORIZACAO_TECHNICAL_FIELDS = (
    AdminFieldConfig(
        key="visibility_scope_mode",
        label="Sistema",
        input_name="auth_objeto_visibility_scope_mode",
        field_type="select",
        required=True,
        options=(
            ("all", "Default"),
            ("owner", "Owner"),
            ("legado", "Legado"),
        ),
    ),
    AdminFieldConfig(
        key="status",
        label="Estado",
        input_name="auth_objeto_status",
        field_type="select",
        required=True,
        options=(
            ("ativo", "Ativo"),
            ("inativo", "Inativo"),
        ),
    ),
)


OBJETO_AUTORIZACAO_CONFIG = AdminSubprocessConfig(
    key="objeto_de_autorizacao",
    label="Objeto de autorização",
    singular_label="Objeto",
    plural_label="Objetos de autorização",
    edit_param="auth_objeto_edit_key",
    default_target="auth-objeto-card",
    edit_target="auth-objeto-form-card",
    create_title="Criar objeto de autorização",
    edit_title="Editar objeto de autorização",
    active_title="Objetos de autorização ativos",
    inactive_title="Objetos de autorização inativos",
    save_endpoint="/users/profile/auth-objeto-save",
    create_endpoint="/users/profile/auth-objeto-save",
    update_endpoint="/users/profile/auth-objeto-save",
    repository_name="objeto_de_autorizacao",
    repository_class="appgenesis.admin_subprocesses.repositories.objeto_autorizacao_repository.ObjetoAutorizacaoAdminRepository",
    status_field="status",
    active_value="ativo",
    inactive_value="inativo",
    identity_field="key",
    label_field="label",
    mode_field="auth_objeto_mode",
    edit_key_field="original_auth_objeto_key",
    return_url_field="auth_objeto_return_url",
    create_mode_value="create",
    edit_mode_value="edit",
    enabled=True,
    migration_status="native",
    uses_dynamic_fields=True,
    dynamic_fields_menu_key="perfil_de_autorizacao",
    dynamic_fields_section_header_key="custom_objeto_de_autorizacao",
    fields=OBJETO_AUTORIZACAO_TECHNICAL_FIELDS,
    columns=(
        AdminColumnConfig(
            key="label",
            label="OBJETO",
            source="label",
            css_class="admin-col-main-v1",
            always_visible=True,
            sortable=True,
            default_sort="asc",
        ),
        AdminColumnConfig(
            key="process",
            label="PROCESSO",
            source="process_label",
            css_class="admin-col-text-v1",
            responsive_priority=3,
        ),
        AdminColumnConfig(
            key="authorization",
            label="AUTORIZAÇÃO",
            source="authorization_label",
            css_class="admin-col-text-v1",
            responsive_priority=4,
        ),
        AdminColumnConfig(
            key="system",
            label="SISTEMA",
            source="visibility_scope_label",
            css_class="admin-col-system-v1",
        ),
        AdminColumnConfig(
            key="status",
            label="ESTADO",
            source="status_label",
            css_class="admin-col-status-v1",
            always_visible=True,
        ),
    ),
    actions=(
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
    ),
    menu_scope="perfil_de_autorizacao",
    empty_active_message="Sem objetos de autorização ativos.",
    empty_inactive_message="Sem objetos de autorização inativos.",
    active_card_id="auth-objeto-active-card",
    inactive_card_id="auth-objeto-inactive-card",
    active_table_id="auth-objeto-active-table",
    inactive_table_id="auth-objeto-inactive-table",
    active_limiter_id="auth-objeto-active-limiter",
    inactive_limiter_id="auth-objeto-inactive-limiter",
)


USER_DELETE_ACTION = AdminActionConfig(
    key="delete",
    label="Eliminar",
    icon="🗑",
    action_type="post_delete",
    visible_when=("inactive",),
    requires_confirmation=True,
    confirmation_message="Tem a certeza que pretende eliminar este utilizador?",
)

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
    active_title="Utilizadores criados",
    inactive_title="Utilizadores inativos",
    save_endpoint="/users/update",
    delete_endpoint="/users/delete",
    repository_name="user",
    repository_class="",
    active_value="active",
    inactive_value="inactive",
    identity_field="id",
    label_field="full_name",
    enabled=True,
    migration_status="native",
    columns=(
        AdminColumnConfig(
            key="name",
            label="NOME",
            source="full_name",
            css_class="admin-col-main-v1",
            sortable=True,
            default_sort="asc",
            always_visible=True,
        ),
        AdminColumnConfig(
            key="email",
            label="EMAIL",
            source="login_email",
            css_class="admin-col-text-v1",
            responsive_priority=1,
        ),
        AdminColumnConfig(
            key="system_profile",
            label="PERFIL NO SISTEMA",
            source="system_type_label",
            css_class="admin-col-text-v1",
            responsive_priority=3,
        ),
        AdminColumnConfig(
            key="phone",
            label="TELEFONE",
            source="primary_phone",
            css_class="admin-col-text-v1",
            responsive_priority=4,
        ),
        AdminColumnConfig(
            key="entity_number",
            label="Nº DA ENTIDADE",
            source="entity_number",
            css_class="admin-col-number-v1",
            responsive_priority=3,
            sort_value_source="entity_number_sort_value",
        ),
        AdminColumnConfig(
            key="entity",
            label="ENTIDADE",
            source="entity_name",
            css_class="admin-col-text-v1",
            responsive_priority=2,
        ),
        AdminColumnConfig(
            key="created_at",
            label="CRIADO EM",
            source="created_at",
            css_class="admin-col-date-v1",
            responsive_priority=5,
        ),
        AdminColumnConfig(
            key="status",
            label="ESTADO",
            source="account_status_label",
            css_class="admin-col-status-v1",
            always_visible=True,
            status_class_source="account_status",
        ),
    ),
    actions=(
        AdminActionConfig(key="view", label="Visualizar", icon="👁", action_type="link", visible_when=("active", "inactive")),
        AdminActionConfig(key="edit", label="Editar", icon="✎", action_type="link", visible_when=("active", "inactive")),
        USER_DELETE_ACTION,
    ),
    menu_scope="administrativo",
    empty_active_message="Sem utilizadores ativos.",
    empty_inactive_message="Sem utilizadores inativos.",
    edit_url_extra_params="admin_tab=utilizador",
    action_form_key_field="user_id",
    view_link_param="user_view",
    status_badge_class="entity-status",
    active_card_id="admin-users-created-card",
    inactive_card_id="inactive-users-card",
    active_table_id="admin-users-table",
    inactive_table_id="inactive-users-table",
    active_limiter_id="admin-users-table-limiter",
    inactive_limiter_id="inactive-users-table-limiter",
)


MENU_FIELDS = (
    AdminFieldConfig(
        key="menu_label",
        label="Nome no menu lateral",
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
            ("all", "Default"),
            ("owner", "Owner"),
            ("legado", "Legado"),
        ),
    ),
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
    AdminActionConfig(
        key="toggle",
        label="Alternar visibilidade",
        icon="👁",
        action_type="toggle_link",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="delete",
        label="Eliminar",
        icon="🗑",
        action_type="post_delete",
        visible_when=("inativo",),
        condition_field="can_delete",
        requires_confirmation=True,
        confirmation_message="Tem a certeza que pretende eliminar este menu?",
    ),
)


MENU_CONFIG = AdminSubprocessConfig(
    key="menu",
    label="Menu",
    singular_label="Menu",
    plural_label="Menus",
    edit_param="settings_edit_key",
    default_target="menu-subprocess-card",
    edit_target="settings-menu-edit-card",
    create_title="Criar menu",
    edit_title="Editar menu",
    active_title="Menus ativos",
    inactive_title="Menus inativos",
    save_endpoint="/settings/menu/menu-save",
    move_endpoint="/settings/menu/menu-move",
    delete_endpoint="/settings/menu/menu-delete",
    repository_name="menu",
    repository_class="appgenesis.admin_subprocesses.repositories.menu_repository.MenuAdminRepository",
    status_field="status",
    active_value="ativo",
    inactive_value="inativo",
    identity_field="key",
    label_field="label",
    mode_field="subprocess_mode",
    edit_key_field="subprocess_edit_key",
    return_url_field="subprocess_return_url",
    enabled=True,
    migration_status="native",
    fields=MENU_FIELDS,
    columns=(
        AdminColumnConfig(key="label", label="MENU LATERAL", source="label", css_class="admin-col-main-v1", always_visible=True),
        AdminColumnConfig(key="entity_number", label="Nº DA ENTIDADE", source="entity_number", css_class="admin-col-number-v1"),
        AdminColumnConfig(key="sidebar_section", label="SESSÃO", source="sidebar_section_label", css_class="admin-col-section-v1"),
        AdminColumnConfig(key="system", label="SISTEMA", source="visibility_scope_label", css_class="admin-col-system-v1"),
        AdminColumnConfig(key="status", label="ESTADO", source="status_label", css_class="admin-col-status-v1", always_visible=True),
    ),
    table_css_class="admin-subprocess-table-menu-v1",
    actions=MENU_ACTIONS,
    menu_scope="administrativo,sessoes",
    empty_active_message="Sem menus ativos.",
    empty_inactive_message="Sem menus inativos.",
    edit_url_extra_params="admin_tab=contas&settings_action=edit",
    action_form_key_field="menu_key",
    toggle_url_extra_params="admin_tab=contas&settings_action=toggle",
    move_up_condition_field="can_move_up",
    move_down_condition_field="can_move_down",
)


CONTAS_CONFIG = AdminSubprocessConfig(
    key="contas",
    label="Contas",
    singular_label="Conta",
    plural_label="Contas",
    edit_param="account_edit_id",
    default_target="admin-account-status-card",
    edit_target="admin-account-status-card",
    create_title="Criar conta",
    edit_title="Editar conta",
    active_title="Contas ativas",
    inactive_title="Contas inativas",
    save_endpoint="",
    repository_name="account",
    repository_class="",
    enabled=False,
    migration_status="legacy_pending",
    menu_scope="administrativo,sessoes",
    empty_active_message="Sem contas ativas.",
    empty_inactive_message="Sem contas inativas.",
)


ADMIN_SUBPROCESS_REGISTRY = {
    ENTIDADE_CONFIG.key: ENTIDADE_CONFIG,
    SESSOES_CONFIG.key: SESSOES_CONFIG,
    AUTHORIZATION_PROFILE_CONFIG.key: AUTHORIZATION_PROFILE_CONFIG,
    OBJETO_AUTORIZACAO_CONFIG.key: OBJETO_AUTORIZACAO_CONFIG,
    UTILIZADOR_CONFIG.key: UTILIZADOR_CONFIG,
    MENU_CONFIG.key: MENU_CONFIG,
    CONTAS_CONFIG.key: CONTAS_CONFIG,
}


def get_admin_subprocess_config(key: str) -> AdminSubprocessConfig | None:
    return ADMIN_SUBPROCESS_REGISTRY.get(str(key or "").strip().lower())


def require_admin_subprocess_config(key: str) -> AdminSubprocessConfig:
    config = get_admin_subprocess_config(key)

    if config is None:
        raise KeyError(f"Subprocesso administrativo não configurado: {key}")

    return config


def list_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(ADMIN_SUBPROCESS_REGISTRY.values())


def list_enabled_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(
        config
        for config in ADMIN_SUBPROCESS_REGISTRY.values()
        if config.enabled
    )
