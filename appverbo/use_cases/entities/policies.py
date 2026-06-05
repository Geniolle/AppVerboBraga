from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.core import ENTITY_PROFILE_SCOPE_OWNER
from appverbo.models import Entity
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import is_entity_within_permissions


# ###################################################################################
# (1) POLITICAS DE PERMISSAO E ESCOPO
# ###################################################################################

def ensure_actor_can_manage_entities_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
) -> str:
    actor_id = int(actor_user["id"])
    actor_login_email = str(actor_user["login_email"] or "")

    if is_admin_user(session, actor_id, actor_login_email):
        return ""

    return "Apenas administradores podem gerir entidades."


def ensure_actor_can_create_entity_v1(
    *,
    permissions: dict[str, Any],
) -> str:
    if permissions.get("can_manage_all_entities"):
        return ""

    return "Apenas a entidade Owner pode criar novas entidades."


def ensure_entity_in_scope_v1(
    *,
    entity_id: int,
    permissions: dict[str, Any],
    action_label: str,
) -> str:
    if is_entity_within_permissions(int(entity_id), permissions):
        return ""

    clean_action = str(action_label or "gerir").strip().lower() or "gerir"
    return f"Sem permissão para {clean_action} esta entidade."


def ensure_can_set_owner_scope_v1(
    *,
    repository: Any,
    session: Session,
    target_profile_scope: str,
    permissions: dict[str, Any],
    ignore_entity_id: int | None = None,
) -> str:
    clean_scope = str(target_profile_scope or "").strip().lower()

    if clean_scope != ENTITY_PROFILE_SCOPE_OWNER:
        return ""

    if not permissions.get("can_manage_all_entities"):
        return "Apenas a entidade Owner pode definir perfil Owner."

    existing_owner_id = repository.find_existing_owner_entity_id(
        session=session,
        ignore_entity_id=ignore_entity_id,
    )

    if existing_owner_id is None:
        return ""

    return "Já existe outra entidade com perfil Owner. Apenas uma é permitida."


# ###################################################################################
# (2) POLITICAS DE ELIMINACAO
# ###################################################################################

def ensure_delete_only_inactive_entity_v1(entity: Entity) -> str:
    if not bool(entity.is_active):
        return ""

    return "Só é permitido eliminar entidades inativas."


def ensure_entity_can_be_deleted_v1(
    *,
    repository: Any,
    session: Session,
    entity_id: int,
) -> str:
    linked_users_count = repository.count_linked_users(
        session=session,
        entity_id=int(entity_id),
    )

    if int(linked_users_count) <= 0:
        return ""

    dependency_summary = repository.get_entity_delete_dependency_summary_v1(
        session=session,
        entity_id=int(entity_id),
    )

    return build_entity_delete_dependency_error_v1(dependency_summary)


# ###################################################################################
# (3) MENSAGENS DE DEPENDENCIAS DE ELIMINACAO
# ###################################################################################

def build_entity_delete_dependency_error_v1(
    dependency_summary: dict[str, Any] | None,
) -> str:
    clean_summary = dependency_summary or {}

    linked_users_count = int(clean_summary.get("linked_users_count") or 0)
    department_membership_count = int(clean_summary.get("department_membership_count") or 0)
    department_count = int(clean_summary.get("department_count") or 0)
    role_count = int(clean_summary.get("role_count") or 0)
    song_count = int(clean_summary.get("song_count") or 0)
    entity_module_entitlement_count = int(
        clean_summary.get("entity_module_entitlement_count") or 0
    )
    process_view_authorization_rule_count = int(
        clean_summary.get("process_view_authorization_rule_count") or 0
    )
    department_names = [
        str(raw_name or "").strip()
        for raw_name in (clean_summary.get("department_membership_department_names") or [])
        if str(raw_name or "").strip()
    ]
    process_view_authorization_rule_labels = [
        str(raw_label or "").strip()
        for raw_label in (clean_summary.get("process_view_authorization_rule_labels") or [])
        if str(raw_label or "").strip()
    ]

    dependency_parts: list[str] = []

    if linked_users_count > 0:
        dependency_parts.append(
            f"{linked_users_count} utilizador{'es' if linked_users_count != 1 else ''} ativo{'s' if linked_users_count != 1 else ''} associado{'s' if linked_users_count != 1 else ''}"
        )

    if department_membership_count > 0:
        membership_label = (
            "vínculo de departamento"
            if department_membership_count == 1
            else "vínculos de departamento"
        )
        detail_suffix = ""

        if department_names:
            detail_suffix = f" ({', '.join(department_names)})"

        dependency_parts.append(
            f"{department_membership_count} {membership_label}{detail_suffix}"
        )

    if department_count > 0:
        dependency_parts.append(
            f"{department_count} departamento{'s' if department_count != 1 else ''} configurado{'s' if department_count != 1 else ''}"
        )

    if role_count > 0:
        dependency_parts.append(
            f"{role_count} função{'ões' if role_count != 1 else ''} configurada{'s' if role_count != 1 else ''}"
        )

    if song_count > 0:
        dependency_parts.append(
            f"{song_count} música{'s' if song_count != 1 else ''} associada{'s' if song_count != 1 else ''}"
        )

    if process_view_authorization_rule_count > 0:
        rule_label = (
            "regra de autorização de visualização"
            if process_view_authorization_rule_count == 1
            else "regras de autorização de visualização"
        )
        detail_suffix = ""

        if process_view_authorization_rule_labels:
            detail_suffix = f" ({'; '.join(process_view_authorization_rule_labels)})"

        dependency_parts.append(
            f"{process_view_authorization_rule_count} {rule_label}{detail_suffix}"
        )

    if entity_module_entitlement_count > 0:
        dependency_parts.append(
            f"{entity_module_entitlement_count} permiss{'ão' if entity_module_entitlement_count == 1 else 'ões'} de módulo configurada{'s' if entity_module_entitlement_count != 1 else ''}"
        )

    if not dependency_parts:
        return ""

    return (
        "Não pode eliminar a entidade porque ainda existem dependências: "
        + "; ".join(dependency_parts)
        + "."
    )
