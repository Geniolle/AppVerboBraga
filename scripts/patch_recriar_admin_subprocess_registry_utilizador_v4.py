from __future__ import annotations

from pathlib import Path


####################################################################################
# (1) UTILITÁRIOS
####################################################################################

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


####################################################################################
# (2) RECRIAR REGISTRY.PY COMPLETO E PADRONIZADO
####################################################################################

registry_path = ROOT / "appverbo" / "admin_subprocesses" / "registry.py"

registry_content = '''\
from __future__ import annotations

from .models import (
    AdminActionConfig,
    AdminColumnConfig,
    AdminFieldConfig,
    AdminSubprocessConfig,
)


####################################################################################
# (1) CAMPOS DOS SUBPROCESSOS
####################################################################################

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


USER_FIELDS = (
    AdminFieldConfig(
        key="full_name",
        label="Nome completo",
        input_name="user_full_name",
        field_type="text",
        required=True,
        max_length=160,
    ),
    AdminFieldConfig(
        key="login_email",
        label="Email",
        input_name="user_login_email",
        field_type="email",
        required=True,
        max_length=150,
    ),
    AdminFieldConfig(
        key="account_status",
        label="Estado",
        input_name="user_account_status",
        field_type="select",
        required=True,
        options=(
            ("pending", "Pendente"),
            ("active", "Ativo"),
            ("inactive", "Inativo"),
            ("blocked", "Bloqueado"),
        ),
    ),
)


####################################################################################
# (2) COLUNAS DOS SUBPROCESSOS
####################################################################################

DEFAULT_COLUMNS = (
    AdminColumnConfig(key="label", label="NOME", source="label"),
    AdminColumnConfig(key="system", label="SISTEMA", source="visibility_scope_label"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
)


USER_COLUMNS = (
    AdminColumnConfig(key="full_name", label="UTILIZADOR", source="full_name"),
    AdminColumnConfig(key="email", label="EMAIL", source="login_email"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
)


####################################################################################
# (3) AÇÕES PADRÃO
####################################################################################

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
# (4) CONFIGURAÇÃO - ENTIDADE
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
    actions=DEFAULT_ACTIVE_ACTIONS,
)


####################################################################################
# (5) CONFIGURAÇÃO - SESSÕES
####################################################################################

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
    columns=DEFAULT_COLUMNS,
    actions=DEFAULT_ACTIVE_ACTIONS,
)


####################################################################################
# (6) CONFIGURAÇÃO - UTILIZADOR
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
    repository_name="user",
    repository_class="appverbo.admin_subprocesses.repositories.user_repository.UserAdminRepository",
    status_field="account_status",
    active_value="active",
    inactive_value="inactive",
    identity_field="id",
    label_field="full_name",
    enabled=True,
    migration_status="native_shadow",
    fields=USER_FIELDS,
    columns=USER_COLUMNS,
    actions=DEFAULT_ACTIVE_ACTIONS,
)


####################################################################################
# (7) CONFIGURAÇÃO - MENU
####################################################################################

MENU_CONFIG = AdminSubprocessConfig(
    key="menu",
    label="Menu",
    singular_label="Menu",
    plural_label="Menus",
    edit_param="settings_edit_key",
    default_target="admin-menu-card",
    edit_target="admin-menu-card",
    create_title="Criar menu",
    edit_title="Editar menu",
    active_title="Menus ativos",
    inactive_title="Menus inativos",
    save_endpoint="/settings/menu/save",
    repository_name="menu",
    repository_class="",
    enabled=False,
    migration_status="legacy_pending",
)


####################################################################################
# (8) CONFIGURAÇÃO - CONTAS
####################################################################################

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
)


####################################################################################
# (9) REGISTRY ÚNICO
####################################################################################

ADMIN_SUBPROCESS_REGISTRY = {
    ENTIDADE_CONFIG.key: ENTIDADE_CONFIG,
    SESSOES_CONFIG.key: SESSOES_CONFIG,
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
'''

write_text(registry_path, registry_content)


####################################################################################
# (3) RECRIAR RUNTIME ÚNICO
####################################################################################

runtime_path = ROOT / "appverbo" / "admin_subprocesses" / "runtime.py"

runtime_content = '''\
from __future__ import annotations

import importlib
from typing import Any

from appverbo.admin_subprocesses.models import (
    AdminSubprocessConfig,
    AdminSubprocessState,
)
from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.admin_subprocesses.service import build_admin_subprocess_state


####################################################################################
# (1) CARREGAMENTO ISOLADO DO REPOSITÓRIO DO SUBPROCESSO
####################################################################################

def load_admin_subprocess_repository(
    config: AdminSubprocessConfig,
) -> BaseAdminSubprocessRepository | None:
    repository_class_path = str(config.repository_class or "").strip()

    if not repository_class_path:
        return None

    module_name, separator, class_name = repository_class_path.rpartition(".")

    if not separator or not module_name or not class_name:
        raise RuntimeError(
            f"repository_class inválido para subprocesso {config.key}: "
            f"{repository_class_path}"
        )

    module = importlib.import_module(module_name)
    repository_class = getattr(module, class_name, None)

    if repository_class is None:
        raise RuntimeError(
            f"Classe de repository não encontrada para subprocesso {config.key}: "
            f"{repository_class_path}"
        )

    try:
        repository = repository_class(config)
    except TypeError:
        repository = repository_class()

    if not isinstance(repository, BaseAdminSubprocessRepository):
        raise RuntimeError(
            f"Repository do subprocesso {config.key} não herda "
            "BaseAdminSubprocessRepository."
        )

    return repository


####################################################################################
# (2) CONSTRUÇÃO ÚNICA DO STATE DO SUBPROCESSO
####################################################################################

def build_admin_subprocess_state_from_repository(
    *,
    config: AdminSubprocessConfig,
    session: Any,
    edit_key: str = "",
    success: str = "",
    error: str = "",
    return_url: str = "",
    context: dict[str, Any] | None = None,
) -> AdminSubprocessState | None:
    if not config.enabled:
        return None

    repository = load_admin_subprocess_repository(config)

    if repository is None:
        return None

    rows = repository.list_rows(session, context or {})

    return build_admin_subprocess_state(
        config=config,
        rows=rows,
        edit_key=edit_key,
        success=success,
        error=error,
        return_url=return_url,
    )
'''

write_text(runtime_path, runtime_content)


####################################################################################
# (4) RECRIAR REPOSITORY DO UTILIZADOR
####################################################################################

user_repository_path = (
    ROOT
    / "appverbo"
    / "admin_subprocesses"
    / "repositories"
    / "user_repository.py"
)

user_repository_content = '''\
from __future__ import annotations

from typing import Any

from sqlalchemy import select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.models import Member, MemberEntity, MemberEntityStatus, User
from appverbo.services.user_status import (
    is_user_account_status_active_v1,
    normalize_user_account_status_v1,
    user_account_status_label_pt_v1,
)


####################################################################################
# (1) REPOSITORY NATIVA DO SUBPROCESSO UTILIZADOR
####################################################################################

class UserAdminRepository(BaseAdminSubprocessRepository):
    """
    Repository isolada para o subprocesso Utilizador.

    Esta versão é segura para escala:
    - usa SELECT por colunas, sem carregar objetos ORM completos;
    - evita N+1 em Member;
    - respeita escopo de entidades quando recebido no context;
    - não altera ainda o fluxo legado de criação/edição.
    """

    def _resolve_allowed_entity_ids(
        self,
        context: dict[str, Any] | None,
    ) -> set[int] | None:
        if not isinstance(context, dict):
            return None

        raw_allowed_entity_ids = context.get("allowed_entity_ids")

        if raw_allowed_entity_ids is None:
            return None

        allowed_entity_ids: set[int] = set()

        for raw_id in raw_allowed_entity_ids:
            try:
                allowed_entity_ids.add(int(raw_id))
            except (TypeError, ValueError):
                continue

        return allowed_entity_ids

    def _resolve_scoped_member_ids(
        self,
        session: Any,
        allowed_entity_ids: set[int] | None,
    ) -> set[int] | None:
        if allowed_entity_ids is None:
            return None

        if not allowed_entity_ids:
            return set()

        rows = session.execute(
            select(MemberEntity.member_id)
            .where(
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                MemberEntity.entity_id.in_(allowed_entity_ids),
            )
            .distinct()
        ).scalars().all()

        return {
            int(member_id)
            for member_id in rows
            if member_id is not None
        }

    def _build_base_stmt(self):
        return (
            select(
                User.id.label("id"),
                User.member_id.label("member_id"),
                Member.full_name.label("full_name"),
                Member.primary_phone.label("primary_phone"),
                User.login_email.label("login_email"),
                User.account_status.label("account_status"),
                User.created_at.label("created_at"),
            )
            .join(Member, Member.id == User.member_id)
        )

    def _to_row(self, row: Any) -> dict[str, Any]:
        normalized_status = normalize_user_account_status_v1(row.account_status)
        is_active = is_user_account_status_active_v1(normalized_status)

        full_name = str(row.full_name or "").strip()
        primary_phone = str(row.primary_phone or "").strip()
        login_email = str(row.login_email or "").strip().lower()

        return {
            "id": row.id,
            "key": str(row.id or ""),
            "member_id": row.member_id,
            "full_name": full_name,
            "name": full_name,
            "label": full_name or login_email,
            "login_email": login_email,
            "email": login_email,
            "primary_phone": primary_phone,
            "phone": primary_phone,
            "account_status": normalized_status,
            "status": normalized_status,
            "status_label": user_account_status_label_pt_v1(normalized_status),
            "is_active": is_active,
            "created_at": row.created_at,
        }

    def list_rows(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        allowed_entity_ids = self._resolve_allowed_entity_ids(context)
        scoped_member_ids = self._resolve_scoped_member_ids(
            session,
            allowed_entity_ids,
        )

        if scoped_member_ids is not None and not scoped_member_ids:
            return []

        stmt = self._build_base_stmt().order_by(User.id.desc())

        if scoped_member_ids is not None:
            stmt = stmt.where(User.member_id.in_(scoped_member_ids))

        rows = session.execute(stmt).all()

        return [self._to_row(row) for row in rows]

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_edit_key = str(edit_key or "").strip()

        if not clean_edit_key.isdigit():
            return None

        allowed_entity_ids = self._resolve_allowed_entity_ids(context)
        scoped_member_ids = self._resolve_scoped_member_ids(
            session,
            allowed_entity_ids,
        )

        if scoped_member_ids is not None and not scoped_member_ids:
            return None

        stmt = self._build_base_stmt().where(User.id == int(clean_edit_key))

        if scoped_member_ids is not None:
            stmt = stmt.where(User.member_id.in_(scoped_member_ids))

        row = session.execute(stmt).one_or_none()

        if row is None:
            return None

        return self._to_row(row)
'''

write_text(user_repository_path, user_repository_content)


####################################################################################
# (5) CRIAR SCRIPT DE VALIDAÇÃO
####################################################################################

check_script_path = ROOT / "scripts" / "check_admin_subprocess_utilizador_v1.py"

check_script_content = '''\
from __future__ import annotations

from appverbo.admin_subprocesses.registry import require_admin_subprocess_config
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository
from appverbo.core import SessionLocal


####################################################################################
# (1) VALIDAR STATE NATIVO DO SUBPROCESSO UTILIZADOR
####################################################################################

def main() -> None:
    config = require_admin_subprocess_config("utilizador")

    if not config.enabled:
        raise RuntimeError("Subprocesso Utilizador não está ativo no registry.")

    if not config.repository_class:
        raise RuntimeError("Subprocesso Utilizador sem repository_class.")

    with SessionLocal() as session:
        state = build_admin_subprocess_state_from_repository(
            config=config,
            session=session,
            edit_key="",
            success="",
            error="",
            return_url="/users/new?menu=administrativo&admin_tab=utilizador",
            context={},
        )

    if state is None:
        raise RuntimeError("Não foi possível construir o state do Utilizador.")

    print("OK: state do subprocesso Utilizador criado.")
    print(f"Config: {state.config.key} - {state.config.label}")
    print(f"Ativos: {len(state.active_rows)}")
    print(f"Inativos/Pendentes/Bloqueados: {len(state.inactive_rows)}")


if __name__ == "__main__":
    main()
'''

write_text(check_script_path, check_script_content)


####################################################################################
# (6) RESULTADO
####################################################################################

print("OK: registry e subprocesso Utilizador v4 recriados com sucesso.")
