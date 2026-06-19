from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path.cwd()
BACKUP_ROOT = ROOT / "backups" / ("refatorar_utilizador_isolado_v1_" + "20260513_090550")


####################################################################################
# (1) HELPERS DE FICHEIRO
####################################################################################

def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def backup_file(path: Path) -> None:
    if not path.exists():
        return

    backup_path = BACKUP_ROOT / path.relative_to(ROOT)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)
    print(f"Backup criado: {rel(backup_path)}")


def write_changed(path: Path, content: str) -> bool:
    old = read_text(path) if path.exists() else None

    if old == content:
        print(f"Sem alteração: {rel(path)}")
        return False

    backup_file(path)
    write_text(path, content)
    print(f"Atualizado: {rel(path)}")
    return True


def ensure_import(text: str, import_line: str) -> str:
    if import_line in text:
        return text

    lines = text.splitlines()
    insert_at = 0

    for index, line in enumerate(lines):
        if line.startswith("from __future__ import"):
            insert_at = index + 1

    lines.insert(insert_at, import_line)
    return "\n".join(lines) + "\n"


def replace_marker_block(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )

    if pattern.search(text):
        return pattern.sub(replacement.strip(), text)

    return text


def remove_marker_block(text: str, start_marker: str, end_marker: str) -> str:
    pattern = re.compile(
        r"\n*" + re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\n*",
        re.DOTALL,
    )
    return pattern.sub("\n", text)


def replace_balanced_assignment(
    text: str,
    assignment_name: str,
    replacement: str,
) -> str:
    pattern = re.compile(
        rf"(?m)^[ \t]*{re.escape(assignment_name)}[ \t]*=[ \t]*AdminSubprocessConfig[ \t]*\("
    )
    match = pattern.search(text)

    if match is None:
        return text

    start = match.start()
    index = match.end() - 1
    depth = 0
    in_string: str | None = None
    escaped = False

    while index < len(text):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
        else:
            if char in {"'", '"'}:
                in_string = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    index += 1
                    while index < len(text) and text[index] in {" ", "\t", "\r", "\n"}:
                        index += 1
                    break

        index += 1

    return text[:start] + replacement.strip() + "\n\n" + text[index:]


####################################################################################
# (2) CONTEÚDO DOS NOVOS FICHEIROS ISOLADOS
####################################################################################

INIT_PY = '''from __future__ import annotations

from .configuracao import (
    USER_ACTIONS,
    USER_COLUMNS,
    USER_FIELDS,
    UTILIZADOR_CONFIG,
)
from .pagina import montar_estado_pagina_utilizador_v1
from .urls import (
    montar_url_editar_utilizador_v1,
    montar_url_exibir_utilizador_v1,
    montar_url_fechar_utilizador_v1,
)

__all__ = (
    "USER_ACTIONS",
    "USER_COLUMNS",
    "USER_FIELDS",
    "UTILIZADOR_CONFIG",
    "montar_estado_pagina_utilizador_v1",
    "montar_url_editar_utilizador_v1",
    "montar_url_exibir_utilizador_v1",
    "montar_url_fechar_utilizador_v1",
)
'''


CONFIGURACAO_PY = '''from __future__ import annotations

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
# (3) AÇÕES DO SUBPROCESSO UTILIZADOR
####################################################################################

USER_ACTIONS = (
    AdminActionConfig(
        key="view",
        label="Exibir",
        icon="👁",
        action_type="link",
        visible_when=("active", "inactive", "pending", "blocked"),
    ),
    AdminActionConfig(
        key="edit",
        label="Editar",
        icon="✎",
        action_type="link",
        visible_when=("active", "inactive", "pending", "blocked"),
    ),
)


####################################################################################
# (4) CONFIGURAÇÃO CENTRAL DO SUBPROCESSO UTILIZADOR
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
    actions=USER_ACTIONS,
)
'''


URLS_PY = '''from __future__ import annotations

from typing import Any
from urllib.parse import urlencode


####################################################################################
# (1) NORMALIZAÇÃO DO IDENTIFICADOR DO UTILIZADOR
####################################################################################

def _normalizar_user_id_v1(user_id: Any) -> str:
    clean_user_id = str(user_id or "").strip()

    if not clean_user_id.isdigit():
        return ""

    return clean_user_id


####################################################################################
# (2) URL BASE DO SUBPROCESSO UTILIZADOR
####################################################################################

def montar_url_base_utilizador_v1() -> str:
    params = (
        ("menu", "administrativo"),
        ("admin_tab", "utilizador"),
    )

    return "/users/new?" + urlencode(params)


####################################################################################
# (3) URL DE EXIBIR UTILIZADOR
####################################################################################

def montar_url_exibir_utilizador_v1(user_id: Any) -> str:
    clean_user_id = _normalizar_user_id_v1(user_id)

    if not clean_user_id:
        return montar_url_base_utilizador_v1()

    params = (
        ("menu", "administrativo"),
        ("admin_tab", "utilizador"),
        ("user_edit_id", clean_user_id),
        ("user_view", "1"),
        ("target", "edit-user-card"),
    )

    return "/users/new?" + urlencode(params) + "#edit-user-card"


####################################################################################
# (4) URL DE EDITAR UTILIZADOR
####################################################################################

def montar_url_editar_utilizador_v1(user_id: Any) -> str:
    clean_user_id = _normalizar_user_id_v1(user_id)

    if not clean_user_id:
        return montar_url_base_utilizador_v1()

    params = (
        ("menu", "administrativo"),
        ("admin_tab", "utilizador"),
        ("user_edit_id", clean_user_id),
        ("user_view", "0"),
        ("target", "edit-user-card"),
    )

    return "/users/new?" + urlencode(params) + "#edit-user-card"


####################################################################################
# (5) URL DE FECHAR UTILIZADOR
####################################################################################

def montar_url_fechar_utilizador_v1() -> str:
    return montar_url_base_utilizador_v1()
'''


PAGINA_PY = '''from __future__ import annotations

from typing import Any

from appverbo.admin_subprocesses.registry import get_admin_subprocess_config
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository

from .urls import montar_url_fechar_utilizador_v1


####################################################################################
# (1) CONSTRUÇÃO ISOLADA DO STATE DO SUBPROCESSO UTILIZADOR
####################################################################################

def montar_estado_pagina_utilizador_v1(
    *,
    session: Any,
    user_edit_id: str | int | None = "",
    user_view: str | None = "",
    selected_entity_id: int | None = None,
    allowed_entity_ids: list[int] | set[int] | tuple[int, ...] | None = None,
    success: str = "",
    error: str = "",
):
    config = get_admin_subprocess_config("utilizador")

    if config is None or not config.enabled:
        return None

    clean_user_edit_id = str(user_edit_id or "").strip()

    context = {
        "selected_entity_id": selected_entity_id,
        "allowed_entity_ids": allowed_entity_ids or [],
        "user_view": str(user_view or "").strip(),
    }

    return build_admin_subprocess_state_from_repository(
        config=config,
        session=session,
        edit_key=clean_user_edit_id,
        success=success or "",
        error=error or "",
        return_url=montar_url_fechar_utilizador_v1(),
        context=context,
    )
'''


RUNTIME_PY = '''from __future__ import annotations

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


USER_REPOSITORY_PY = '''from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.admin_subprocesses.utilizador.urls import (
    montar_url_editar_utilizador_v1,
    montar_url_exibir_utilizador_v1,
    montar_url_fechar_utilizador_v1,
)
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    Profile,
    User,
    UserProfile,
)
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

    Regras de performance:
    - SELECT explícito por colunas;
    - evita N+1 para entidades e perfis;
    - respeita escopo de entidades recebido no context;
    - não altera criação, convite, edição ou geração de link legado.
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

    def _format_datetime_label(self, raw_value: Any) -> str:
        if raw_value is None:
            return "-"

        if isinstance(raw_value, datetime):
            return raw_value.strftime("%Y-%m-%d %H:%M")

        value = str(raw_value or "").strip()

        if not value:
            return "-"

        return value[:16]

    def _build_entity_names_by_member_id(
        self,
        session: Any,
        member_ids: set[int],
    ) -> dict[int, str]:
        if not member_ids:
            return {}

        rows = session.execute(
            select(
                MemberEntity.member_id.label("member_id"),
                Entity.name.label("entity_name"),
            )
            .join(Entity, Entity.id == MemberEntity.entity_id)
            .where(
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                MemberEntity.member_id.in_(member_ids),
            )
            .order_by(Entity.name.asc())
        ).all()

        names_by_member_id: dict[int, list[str]] = {}

        for row in rows:
            member_id = int(row.member_id)
            entity_name = str(row.entity_name or "").strip()

            if not entity_name:
                continue

            names_by_member_id.setdefault(member_id, [])

            if entity_name not in names_by_member_id[member_id]:
                names_by_member_id[member_id].append(entity_name)

        return {
            member_id: ", ".join(entity_names)
            for member_id, entity_names in names_by_member_id.items()
        }

    def _build_profile_names_by_user_id(
        self,
        session: Any,
        user_ids: set[int],
    ) -> dict[int, str]:
        if not user_ids:
            return {}

        rows = session.execute(
            select(
                UserProfile.user_id.label("user_id"),
                Profile.name.label("profile_name"),
            )
            .join(Profile, Profile.id == UserProfile.profile_id)
            .where(
                UserProfile.is_active.is_(True),
                UserProfile.user_id.in_(user_ids),
            )
            .order_by(Profile.name.asc())
        ).all()

        names_by_user_id: dict[int, list[str]] = {}

        for row in rows:
            user_id = int(row.user_id)
            profile_name = str(row.profile_name or "").strip()

            if not profile_name:
                continue

            names_by_user_id.setdefault(user_id, [])

            if profile_name not in names_by_user_id[user_id]:
                names_by_user_id[user_id].append(profile_name)

        return {
            user_id: ", ".join(profile_names)
            for user_id, profile_names in names_by_user_id.items()
        }

    def _to_row(
        self,
        row: Any,
        entity_names_by_member_id: dict[int, str] | None = None,
        profile_names_by_user_id: dict[int, str] | None = None,
    ) -> dict[str, Any]:
        entity_names_by_member_id = entity_names_by_member_id or {}
        profile_names_by_user_id = profile_names_by_user_id or {}

        normalized_status = normalize_user_account_status_v1(row.account_status)
        is_active = is_user_account_status_active_v1(normalized_status)

        user_id = int(row.id)
        member_id = int(row.member_id)
        full_name = str(row.full_name or "").strip()
        primary_phone = str(row.primary_phone or "").strip()
        login_email = str(row.login_email or "").strip().lower()
        entity_name = entity_names_by_member_id.get(member_id, "-")
        profile_name = profile_names_by_user_id.get(user_id, "-")
        created_at_label = self._format_datetime_label(row.created_at)

        return {
            "id": user_id,
            "key": str(user_id),
            "member_id": member_id,
            "full_name": full_name,
            "name": full_name,
            "label": full_name or login_email,
            "login_email": login_email,
            "email": login_email,
            "primary_phone": primary_phone or "-",
            "phone": primary_phone or "-",
            "entity_name": entity_name,
            "profile_name": profile_name,
            "account_status": normalized_status,
            "status": normalized_status,
            "status_label": user_account_status_label_pt_v1(normalized_status),
            "is_active": is_active,
            "created_at": row.created_at,
            "created_at_label": created_at_label,
            "view_url": montar_url_exibir_utilizador_v1(user_id),
            "edit_url": montar_url_editar_utilizador_v1(user_id),
            "close_url": montar_url_fechar_utilizador_v1(),
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

        user_ids = {
            int(row.id)
            for row in rows
            if row.id is not None
        }
        member_ids = {
            int(row.member_id)
            for row in rows
            if row.member_id is not None
        }

        entity_names_by_member_id = self._build_entity_names_by_member_id(
            session,
            member_ids,
        )
        profile_names_by_user_id = self._build_profile_names_by_user_id(
            session,
            user_ids,
        )

        return [
            self._to_row(
                row,
                entity_names_by_member_id=entity_names_by_member_id,
                profile_names_by_user_id=profile_names_by_user_id,
            )
            for row in rows
        ]

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

        member_ids = {int(row.member_id)}
        user_ids = {int(row.id)}

        entity_names_by_member_id = self._build_entity_names_by_member_id(
            session,
            member_ids,
        )
        profile_names_by_user_id = self._build_profile_names_by_user_id(
            session,
            user_ids,
        )

        return self._to_row(
            row,
            entity_names_by_member_id=entity_names_by_member_id,
            profile_names_by_user_id=profile_names_by_user_id,
        )
'''


CONTRACT_PY = '''from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) HELPERS
####################################################################################

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


####################################################################################
# (2) CONTRATO DA REFATORAÇÃO DO SUBPROCESSO UTILIZADOR
####################################################################################

def main() -> None:
    registry = read("appverbo/admin_subprocesses/registry.py")
    configuracao = read("appverbo/admin_subprocesses/utilizador/configuracao.py")
    urls = read("appverbo/admin_subprocesses/utilizador/urls.py")
    pagina = read("appverbo/admin_subprocesses/utilizador/pagina.py")
    repository = read("appverbo/admin_subprocesses/repositories/user_repository.py")
    page_handler = read("appverbo/routes/profile/page_handler.py")

    assert_true(
        "from .utilizador.configuracao import UTILIZADOR_CONFIG" in registry
        or "from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG" in registry,
        "registry.py deve importar UTILIZADOR_CONFIG de utilizador/configuracao.py",
    )

    assert_true(
        "UTILIZADOR_CONFIG = AdminSubprocessConfig(" not in registry,
        "registry.py não deve manter definição inline de UTILIZADOR_CONFIG",
    )

    assert_true(
        'enabled=True' in configuracao and 'migration_status="native_shadow"' in configuracao,
        "configuracao.py deve manter Utilizador enabled=True e native_shadow",
    )

    assert_true(
        "montar_url_exibir_utilizador_v1" in urls
        and "montar_url_editar_utilizador_v1" in urls
        and "montar_url_fechar_utilizador_v1" in urls,
        "urls.py deve centralizar URLs de Exibir, Editar e Fechar",
    )

    assert_true(
        "montar_estado_pagina_utilizador_v1" in pagina,
        "pagina.py deve centralizar o state do subprocesso Utilizador",
    )

    assert_true(
        "view_url" in repository
        and "edit_url" in repository
        and "montar_url_exibir_utilizador_v1" in repository,
        "UserAdminRepository deve entregar URLs de ação por linha",
    )

    assert_true(
        "montar_estado_pagina_utilizador_v1" in page_handler,
        "page_handler.py deve chamar a montagem isolada do state do Utilizador",
    )

    partial_path = ROOT / "templates/partials/admin_user_shadow_readonly_v1.html"

    if partial_path.exists():
        partial = partial_path.read_text(encoding="utf-8")

        assert_true(
            'row.get("view_url")' in partial or "row.get('view_url')" in partial,
            "partial do Utilizador deve usar view_url vindo do repository",
        )

        assert_true(
            'row.get("edit_url")' in partial or "row.get('edit_url')" in partial,
            "partial do Utilizador deve usar edit_url vindo do repository",
        )

        assert_true(
            '{% set view_url = "/users/new?menu=administrativo' not in partial,
            "partial do Utilizador não deve montar URL de Exibir manualmente",
        )

        assert_true(
            '{% set edit_url = "/users/new?menu=administrativo' not in partial,
            "partial do Utilizador não deve montar URL de Editar manualmente",
        )

    print("OK: contrato do subprocesso Utilizador isolado validado com sucesso.")


if __name__ == "__main__":
    main()
'''


####################################################################################
# (3) ESCREVER NOVOS FICHEIROS
####################################################################################

def escrever_ficheiros_isolados() -> None:
    write_changed(ROOT / "appverbo/admin_subprocesses/utilizador/__init__.py", INIT_PY)
    write_changed(ROOT / "appverbo/admin_subprocesses/utilizador/configuracao.py", CONFIGURACAO_PY)
    write_changed(ROOT / "appverbo/admin_subprocesses/utilizador/urls.py", URLS_PY)
    write_changed(ROOT / "appverbo/admin_subprocesses/utilizador/pagina.py", PAGINA_PY)

    runtime_path = ROOT / "appverbo/admin_subprocesses/runtime.py"

    if runtime_path.exists():
        runtime_text = read_text(runtime_path)

        if "build_admin_subprocess_state_from_repository" not in runtime_text:
            write_changed(runtime_path, RUNTIME_PY)
        else:
            print(f"Runtime existente preservado: {rel(runtime_path)}")
    else:
        write_changed(runtime_path, RUNTIME_PY)

    write_changed(ROOT / "appverbo/admin_subprocesses/repositories/user_repository.py", USER_REPOSITORY_PY)
    write_changed(ROOT / "scripts/check_utilizador_subprocess_contract_v1.py", CONTRACT_PY)


####################################################################################
# (4) PATCH DO REGISTRY
####################################################################################

def patch_registry() -> None:
    path = ROOT / "appverbo/admin_subprocesses/registry.py"

    if not path.exists():
        raise RuntimeError("registry.py não encontrado.")

    text = read_text(path)

    text = text.replace(
        "from appverbo.admin_subprocesses.utilizador.config import UTILIZADOR_CONFIG",
        "from .utilizador.configuracao import UTILIZADOR_CONFIG",
    )
    text = text.replace(
        "from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG",
        "from .utilizador.configuracao import UTILIZADOR_CONFIG",
    )

    text = ensure_import(
        text,
        "from .utilizador.configuracao import UTILIZADOR_CONFIG",
    )

    text = replace_balanced_assignment(
        text,
        "UTILIZADOR_CONFIG",
        "# UTILIZADOR_CONFIG é definido em appverbo/admin_subprocesses/utilizador/configuracao.py",
    )

    write_changed(path, text)


####################################################################################
# (5) PATCH DO PAGE_HANDLER
####################################################################################

def patch_page_handler() -> None:
    path = ROOT / "appverbo/routes/profile/page_handler.py"

    if not path.exists():
        raise RuntimeError("page_handler.py não encontrado.")

    text = read_text(path)

    text = ensure_import(
        text,
        "from appverbo.admin_subprocesses.utilizador.pagina import montar_estado_pagina_utilizador_v1",
    )

    start_marker = "    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_START"
    end_marker = "    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_END"

    state_block = """
    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_START
    admin_subprocess_state_utilizador_v1 = None

    if resolved_admin_tab == "utilizador":
        admin_subprocess_state_utilizador_v1 = montar_estado_pagina_utilizador_v1(
            session=session,
            user_edit_id=clean_user_edit_id,
            user_view=user_view,
            selected_entity_id=selected_entity_id,
            allowed_entity_ids=entity_permissions["allowed_entity_ids"],
            success=success or "",
            error=error or "",
        )
    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_END
""".rstrip()

    if start_marker in text and end_marker in text:
        text = replace_marker_block(text, start_marker, end_marker, state_block)
    else:
        context_match = re.search(r"(?m)^([ \t]*)context[ \t]*=[ \t]*\{", text)

        if context_match is None:
            raise RuntimeError("Não foi possível localizar o bloco context = { em page_handler.py.")

        indent = context_match.group(1)
        adjusted_block = "\n".join(
            (indent + line[4:] if line.startswith("    ") else indent + line)
            for line in state_block.splitlines()
        )
        text = text[:context_match.start()] + adjusted_block + "\n\n" + text[context_match.start():]

    old_context_line = '        "admin_subprocess_state": admin_subprocess_state_v2,'
    new_context_lines = (
        '        "admin_subprocess_state": admin_subprocess_state_utilizador_v1 if resolved_admin_tab == "utilizador" else admin_subprocess_state_v2,\n'
        '        "admin_subprocess_state_utilizador": admin_subprocess_state_utilizador_v1,\n'
        '        "admin_subprocess_shadow_state_v1": admin_subprocess_state_utilizador_v1,'
    )

    if old_context_line in text:
        text = text.replace(old_context_line, new_context_lines)
    elif '"admin_subprocess_state_utilizador"' not in text:
        page_data_marker = "        **page_data,"
        if page_data_marker not in text:
            raise RuntimeError("Não foi possível inserir state do Utilizador no context.")
        text = text.replace(
            page_data_marker,
            new_context_lines + "\n" + page_data_marker,
            1,
        )

    write_changed(path, text)


####################################################################################
# (6) PATCH DO PARTIAL DO UTILIZADOR
####################################################################################

def patch_partial_utilizador() -> None:
    path = ROOT / "templates/partials/admin_user_shadow_readonly_v1.html"

    if not path.exists():
        print("AVISO: partial admin_user_shadow_readonly_v1.html não encontrado. Nenhum patch aplicado.")
        return

    text = read_text(path)

    text = re.sub(
        r'{%\s*set\s+view_url\s*=.*?%}',
        '{% set view_url = row.get("view_url") or "" %}',
        text,
        count=1,
    )
    text = re.sub(
        r'{%\s*set\s+edit_url\s*=.*?%}',
        '{% set edit_url = row.get("edit_url") or "" %}',
        text,
        count=1,
    )
    text = re.sub(
        r'{%\s*set\s+close_url\s*=.*?%}',
        '{% set close_url = row.get("close_url") or "/users/new?menu=administrativo&admin_tab=utilizador" %}',
        text,
        count=1,
    )

    write_changed(path, text)


####################################################################################
# (7) EXECUÇÃO
####################################################################################

def main() -> None:
    escrever_ficheiros_isolados()
    patch_registry()
    patch_page_handler()
    patch_partial_utilizador()


if __name__ == "__main__":
    main()
