from __future__ import annotations

import re
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


def replace_once(content: str, old: str, new: str, label: str) -> str:
    if old not in content:
        raise RuntimeError(f"Bloco não encontrado para substituir: {label}")
    return content.replace(old, new, 1)


####################################################################################
# (2) RECRIAR RUNTIME ÚNICO DOS SUBPROCESSOS
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

    repository = repository_class(config)

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
# (3) RECRIAR REPOSITORY DO UTILIZADOR COM LEITURA ESCALÁVEL
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
# (4) ATUALIZAR REGISTRY.PY DE FORMA ROBUSTA
####################################################################################

registry_path = ROOT / "appverbo" / "admin_subprocesses" / "registry.py"
registry_content = read_text(registry_path)

user_fields_block = '''\

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


USER_COLUMNS = (
    AdminColumnConfig(key="full_name", label="UTILIZADOR", source="full_name"),
    AdminColumnConfig(key="email", label="EMAIL", source="login_email"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
)

'''

if "USER_FIELDS = (" not in registry_content:
    utilizador_index = registry_content.find("UTILIZADOR_CONFIG = AdminSubprocessConfig(")

    if utilizador_index < 0:
        raise RuntimeError("UTILIZADOR_CONFIG não encontrado no registry.py")

    registry_content = (
        registry_content[:utilizador_index]
        + user_fields_block
        + registry_content[utilizador_index:]
    )

new_user_config = '''UTILIZADOR_CONFIG = AdminSubprocessConfig(
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
)'''

pattern = (
    r"UTILIZADOR_CONFIG\s*=\s*AdminSubprocessConfig\("
    r"[\s\S]*?"
    r"\)\s*\n\s*\n\s*MENU_CONFIG\s*=\s*AdminSubprocessConfig\("
)

replacement = new_user_config + "\n\n\nMENU_CONFIG = AdminSubprocessConfig("

registry_content, count = re.subn(
    pattern,
    replacement,
    registry_content,
    count=1,
)

if count != 1:
    raise RuntimeError("Não foi possível substituir UTILIZADOR_CONFIG no registry.py")

write_text(registry_path, registry_content)


####################################################################################
# (5) LIGAR PAGE_HANDLER.PY AO RUNTIME ÚNICO EM MODO SHADOW
####################################################################################

page_handler_path = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
page_handler_content = read_text(page_handler_path)

runtime_import = (
    "from appverbo.admin_subprocesses.runtime import "
    "build_admin_subprocess_state_from_repository\n"
)

if "build_admin_subprocess_state_from_repository" not in page_handler_content:
    service_import = "from appverbo.admin_subprocesses.service import build_admin_subprocess_state\n"

    if service_import not in page_handler_content:
        raise RuntimeError("Import de build_admin_subprocess_state não encontrado no page_handler.py")

    page_handler_content = page_handler_content.replace(
        service_import,
        service_import + runtime_import,
        1,
    )

if "admin_subprocess_shadow_state_v1 = None" not in page_handler_content:
    state_marker = "    admin_subprocess_state_v2 = None\n"

    if state_marker not in page_handler_content:
        raise RuntimeError("Inicialização de admin_subprocess_state_v2 não encontrada.")

    page_handler_content = page_handler_content.replace(
        state_marker,
        state_marker + "    admin_subprocess_shadow_state_v1 = None\n",
        1,
    )

utilizador_shadow_block = '''
    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_START
    # Estado nativo em paralelo para validar o subprocesso Utilizador sem trocar a tela legada.
    # Isto garante que a aba Utilizador pode evoluir para o processo único sem afetar Sessões,
    # Entidade ou o fluxo atual de criação/edição de utilizadores.
    if resolved_admin_tab == "utilizador":
        utilizador_subprocess_config_v1 = get_admin_subprocess_config("utilizador")

        if utilizador_subprocess_config_v1 is not None:
            admin_subprocess_shadow_state_v1 = build_admin_subprocess_state_from_repository(
                config=utilizador_subprocess_config_v1,
                session=session,
                edit_key=clean_user_edit_id,
                success=success or "",
                error=error or "",
                return_url="/users/new?menu=administrativo&admin_tab=utilizador&target=create-user-card#create-user-card",
                context={
                    "current_user": current_user,
                    "selected_entity_id": selected_entity_id,
                    "allowed_entity_ids": entity_permissions["allowed_entity_ids"],
                    "can_manage_all_entities": entity_permissions["can_manage_all_entities"],
                },
            )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_END
'''

if "APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_START" not in page_handler_content:
    sessoes_end_marker = "    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_END\n"

    if sessoes_end_marker in page_handler_content:
        page_handler_content = page_handler_content.replace(
            sessoes_end_marker,
            sessoes_end_marker + utilizador_shadow_block,
            1,
        )
    else:
        context_marker = "    context = {\n"

        if context_marker not in page_handler_content:
            raise RuntimeError("Não foi possível localizar ponto para inserir shadow state.")

        page_handler_content = page_handler_content.replace(
            context_marker,
            utilizador_shadow_block + "\n" + context_marker,
            1,
        )

if '"admin_subprocess_shadow_state": admin_subprocess_shadow_state_v1,' not in page_handler_content:
    context_line = '        "admin_subprocess_state": admin_subprocess_state_v2,\n'

    if context_line not in page_handler_content:
        raise RuntimeError("Linha admin_subprocess_state não encontrada no contexto.")

    page_handler_content = page_handler_content.replace(
        context_line,
        context_line + '        "admin_subprocess_shadow_state": admin_subprocess_shadow_state_v1,\n',
        1,
    )

write_text(page_handler_path, page_handler_content)


####################################################################################
# (6) CRIAR SCRIPT DE VALIDAÇÃO DO STATE DO UTILIZADOR
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
# (7) RESULTADO DO PATCH
####################################################################################

print("OK: patch corretivo admin_subprocess_utilizador_native_shadow_v2 aplicado.")
print("Atualizado: appverbo/admin_subprocesses/runtime.py")
print("Atualizado: appverbo/admin_subprocesses/repositories/user_repository.py")
print("Atualizado: appverbo/admin_subprocesses/registry.py")
print("Atualizado: appverbo/routes/profile/page_handler.py")
print("Criado/atualizado: scripts/check_admin_subprocess_utilizador_v1.py")
