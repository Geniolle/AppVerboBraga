from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import unicodedata

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from appverbo.menu_settings import (
    get_sidebar_menu_settings,
    get_visible_sidebar_menu_keys,
    normalize_menu_visibility_scopes,
    resolve_menu_key_alias,
)
from appverbo.models import (
    Department,
    DepartmentMembership,
    DepartmentMembershipStatus,
    Entity,
    MemberEntity,
    MemberEntityStatus,
    ProcessViewAuthorizationRule,
    User,
)
from appverbo.repositories.user_profile_repository import get_active_profile_names_by_user
from appverbo.services.permissions import get_user_entity_permissions

PROCESS_VIEW_AUTHORIZATION_MENU_KEY = "administrativo"
PROCESS_VIEW_AUTHORIZATION_SECTION_KEY = "custom_perfil_de_autorizacao"
PROCESS_VIEW_AUTHORIZATION_ALL_SUBPROCESS_LABEL = "Todos os subprocessos"
PROCESS_VIEW_AUTHORIZATION_ALL_DEPARTMENTS_LABEL = "Todos os departamentos"


# ###################################################################################
# (1) NORMALIZACAO E IDENTIFICACAO
# ###################################################################################


def _normalize_process_view_authorization_lookup_text_v1(raw_value: Any) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(raw_value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    return " ".join(normalized.split())


def _normalize_process_view_authorization_status_v1(raw_value: Any) -> str:
    clean_value = _normalize_process_view_authorization_lookup_text_v1(raw_value)
    if clean_value in {"inactive", "inativo"}:
        return "inactive"
    return "active"


def _serialize_process_view_authorization_status_v1(raw_value: Any) -> str:
    return (
        "inativo"
        if _normalize_process_view_authorization_status_v1(raw_value) == "inactive"
        else "ativo"
    )


def _is_all_subprocess_rule_v1(raw_value: Any) -> bool:
    clean_value = _normalize_process_view_authorization_lookup_text_v1(raw_value)
    return clean_value in {
        _normalize_process_view_authorization_lookup_text_v1(
            PROCESS_VIEW_AUTHORIZATION_ALL_SUBPROCESS_LABEL
        ),
        "todos subprocessos",
    }


def _is_all_departments_rule_v1(raw_value: Any) -> bool:
    clean_value = _normalize_process_view_authorization_lookup_text_v1(raw_value)
    return clean_value in {
        _normalize_process_view_authorization_lookup_text_v1(
            PROCESS_VIEW_AUTHORIZATION_ALL_DEPARTMENTS_LABEL
        ),
        "todos departamentos",
    }


def is_process_view_authorization_section_v1(menu_key: Any, section_key: Any) -> bool:
    clean_menu_key = resolve_menu_key_alias(menu_key)
    clean_section_key = str(section_key or "").strip().lower()
    return (
        clean_menu_key == PROCESS_VIEW_AUTHORIZATION_MENU_KEY
        and clean_section_key == PROCESS_VIEW_AUTHORIZATION_SECTION_KEY
    )


# ###################################################################################
# (2) RESOLVER ALVOS DE PROCESSO / SUBPROCESSO
# ###################################################################################


def resolve_process_view_authorization_targets_v1(
    sidebar_menu_settings: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    process_label: Any,
    subprocess_label: Any,
) -> dict[str, str]:
    clean_process_label = str(process_label or "").strip()
    clean_subprocess_label = str(subprocess_label or "").strip()
    normalized_process_label = _normalize_process_view_authorization_lookup_text_v1(
        clean_process_label
    )
    normalized_subprocess_label = _normalize_process_view_authorization_lookup_text_v1(
        clean_subprocess_label
    )

    section_key_by_label: dict[str, str] = {}
    section_label_by_key: dict[str, str] = {}
    menu_row_by_section_and_label: dict[tuple[str, str], dict[str, Any]] = {}
    menu_row_by_label: dict[str, dict[str, Any]] = {}

    for raw_row in sidebar_menu_settings or []:
        if not isinstance(raw_row, dict):
            continue

        menu_key = resolve_menu_key_alias(raw_row.get("key"))
        if not menu_key:
            continue

        section_key = str(raw_row.get("sidebar_section_key") or "").strip().lower()
        section_label = str(raw_row.get("sidebar_section_label") or "").strip()
        menu_label = str(raw_row.get("label") or menu_key).strip()

        if section_key and section_label:
            section_key_by_label.setdefault(
                _normalize_process_view_authorization_lookup_text_v1(section_label),
                section_key,
            )
            section_label_by_key.setdefault(section_key, section_label)

        normalized_menu_label = _normalize_process_view_authorization_lookup_text_v1(menu_label)
        if normalized_menu_label:
            menu_row_by_label.setdefault(normalized_menu_label, raw_row)
            if section_key:
                menu_row_by_section_and_label.setdefault(
                    (section_key, normalized_menu_label),
                    raw_row,
                )

    resolved_process_key = section_key_by_label.get(normalized_process_label, "")
    resolved_process_label = (
        section_label_by_key.get(resolved_process_key)
        or clean_process_label
    )

    resolved_subprocess_key = ""
    resolved_subprocess_label = (
        PROCESS_VIEW_AUTHORIZATION_ALL_SUBPROCESS_LABEL
        if _is_all_subprocess_rule_v1(clean_subprocess_label)
        else clean_subprocess_label
    )

    if not _is_all_subprocess_rule_v1(clean_subprocess_label):
        target_row = None
        if resolved_process_key:
            target_row = menu_row_by_section_and_label.get(
                (resolved_process_key, normalized_subprocess_label)
            )
        if target_row is None:
            target_row = menu_row_by_label.get(normalized_subprocess_label)

        if isinstance(target_row, dict):
            resolved_subprocess_key = resolve_menu_key_alias(target_row.get("key"))
            resolved_subprocess_label = (
                str(target_row.get("label") or resolved_subprocess_label).strip()
                or resolved_subprocess_label
            )
            if not resolved_process_key:
                resolved_process_key = str(
                    target_row.get("sidebar_section_key") or ""
                ).strip().lower()
                resolved_process_label = (
                    str(target_row.get("sidebar_section_label") or "").strip()
                    or resolved_process_label
                )

    return {
        "process_key": resolved_process_key,
        "process_label": resolved_process_label,
        "subprocess_key": resolved_subprocess_key,
        "subprocess_label": resolved_subprocess_label,
    }


def _resolve_rule_process_target_v1(
    rule: ProcessViewAuthorizationRule,
    sidebar_menu_settings: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> tuple[str, str]:
    stored_process_key = str(rule.process_key or "").strip().lower()
    stored_process_label = str(rule.process_label or "").strip()
    stored_subprocess_label = str(rule.subprocess_label or "").strip()

    resolved_targets = resolve_process_view_authorization_targets_v1(
        sidebar_menu_settings,
        process_label=stored_process_label,
        subprocess_label=stored_subprocess_label,
    )
    resolved_process_key = stored_process_key or resolved_targets.get("process_key") or ""
    resolved_process_label = stored_process_label or resolved_targets.get("process_label") or ""
    return resolved_process_key, resolved_process_label


def _resolve_rule_subprocess_target_v1(
    rule: ProcessViewAuthorizationRule,
    sidebar_menu_settings: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> tuple[str, str]:
    stored_subprocess_key = resolve_menu_key_alias(rule.subprocess_key)
    stored_subprocess_label = str(rule.subprocess_label or "").strip()
    stored_process_label = str(rule.process_label or "").strip()

    if _is_all_subprocess_rule_v1(stored_subprocess_label):
        return "", PROCESS_VIEW_AUTHORIZATION_ALL_SUBPROCESS_LABEL

    resolved_targets = resolve_process_view_authorization_targets_v1(
        sidebar_menu_settings,
        process_label=stored_process_label,
        subprocess_label=stored_subprocess_label,
    )
    resolved_subprocess_key = (
        stored_subprocess_key or resolved_targets.get("subprocess_key") or ""
    )
    resolved_subprocess_label = (
        stored_subprocess_label or resolved_targets.get("subprocess_label") or ""
    )
    return resolved_subprocess_key, resolved_subprocess_label


# ###################################################################################
# (2.1) ESCOPO EFETIVO DAS REGRAS
# ###################################################################################


def _build_process_view_authorization_scope_key_v1(
    rule: ProcessViewAuthorizationRule,
    sidebar_menu_settings: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> tuple[str, str]:
    normalized_profile_name = _normalize_process_view_authorization_lookup_text_v1(
        rule.profile_name
    )
    resolved_process_key, resolved_process_label = _resolve_rule_process_target_v1(
        rule,
        sidebar_menu_settings,
    )
    normalized_process_scope = (
        str(resolved_process_key or "").strip().lower()
        or _normalize_process_view_authorization_lookup_text_v1(
            resolved_process_label or rule.process_label
        )
    )
    return normalized_profile_name, normalized_process_scope


def _select_effective_process_view_authorization_rules_v1(
    rules: list[ProcessViewAuthorizationRule],
    *,
    normalized_profile_names: set[str],
    selected_entity_id: int | None,
    sidebar_menu_settings: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> list[ProcessViewAuthorizationRule]:
    grouped_rules_by_scope: dict[tuple[str, str], list[ProcessViewAuthorizationRule]] = {}

    for rule in rules:
        normalized_profile_name, normalized_process_scope = (
            _build_process_view_authorization_scope_key_v1(
                rule,
                sidebar_menu_settings,
            )
        )
        if (
            not normalized_profile_name
            or normalized_profile_name not in normalized_profile_names
            or not normalized_process_scope
        ):
            continue
        grouped_rules_by_scope.setdefault(
            (normalized_profile_name, normalized_process_scope),
            [],
        ).append(rule)

    effective_rules: list[ProcessViewAuthorizationRule] = []
    for grouped_rules in grouped_rules_by_scope.values():
        if selected_entity_id is not None:
            entity_specific_rules = [
                rule
                for rule in grouped_rules
                if rule.entity_id is not None
                and int(rule.entity_id) == int(selected_entity_id)
            ]
            if entity_specific_rules:
                effective_rules.extend(entity_specific_rules)
                continue

        global_rules = [rule for rule in grouped_rules if rule.entity_id is None]
        effective_rules.extend(global_rules)

    return effective_rules


# ###################################################################################
# (2.2) RESOLVER DEPARTAMENTO DA REGRA
# ###################################################################################


def _find_active_department_for_authorization_v1(
    session: Session,
    *,
    selected_entity_id: int,
    department_name: str,
) -> Department | None:
    clean_department_name = " ".join(str(department_name or "").strip().split())
    if not clean_department_name:
        return None

    return session.execute(
        select(Department)
        .where(
            Department.entity_id == int(selected_entity_id),
            Department.is_active.is_(True),
            func.lower(func.trim(Department.name)) == clean_department_name.lower(),
        )
        .limit(1)
    ).scalar_one_or_none()


def _resolve_process_view_authorization_department_name_v1(
    session: Session,
    *,
    selected_entity_id: int | None,
    raw_department_name: Any,
) -> tuple[str, str]:
    clean_department_name = " ".join(str(raw_department_name or "").strip().split())[:150]
    if not clean_department_name or _is_all_departments_rule_v1(clean_department_name):
        return PROCESS_VIEW_AUTHORIZATION_ALL_DEPARTMENTS_LABEL, ""

    if selected_entity_id is None:
        return clean_department_name, ""

    resolved_department = _find_active_department_for_authorization_v1(
        session,
        selected_entity_id=int(selected_entity_id),
        department_name=clean_department_name,
    )
    if resolved_department is None:
        return "", "Departamento inválido para a entidade selecionada."

    return str(resolved_department.name or "").strip()[:150], ""


# ###################################################################################
# (3) CONSULTA E SERIALIZACAO DAS REGRAS
# ###################################################################################


def list_process_view_authorization_rules_v1(
    session: Session,
    *,
    selected_entity_id: int | None,
) -> list[ProcessViewAuthorizationRule]:
    stmt = select(ProcessViewAuthorizationRule)
    if selected_entity_id is None:
        stmt = stmt.where(ProcessViewAuthorizationRule.entity_id.is_(None))
    else:
        stmt = stmt.where(
            or_(
                ProcessViewAuthorizationRule.entity_id == int(selected_entity_id),
                ProcessViewAuthorizationRule.entity_id.is_(None),
            )
        )

    return list(
        session.execute(
            stmt.order_by(
                ProcessViewAuthorizationRule.created_at.desc(),
                ProcessViewAuthorizationRule.id.desc(),
            )
        ).scalars()
    )


def _format_process_view_authorization_created_at_v1(raw_value: Any) -> str:
    if isinstance(raw_value, datetime):
        if raw_value.tzinfo is None:
            raw_value = raw_value.replace(tzinfo=timezone.utc)
        else:
            raw_value = raw_value.astimezone(timezone.utc)
        return raw_value.strftime("%Y-%m-%d %H:%M UTC")
    return str(raw_value or "").strip()


def build_process_view_authorization_history_rows_v1(
    session: Session,
    *,
    selected_entity_id: int | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule in list_process_view_authorization_rules_v1(
        session,
        selected_entity_id=selected_entity_id,
    ):
        rows.append(
            {
                "record_id": str(rule.id),
                "created_at": _format_process_view_authorization_created_at_v1(
                    rule.created_at
                ),
                "section_key": PROCESS_VIEW_AUTHORIZATION_SECTION_KEY,
                "values": {
                    "custom_perfil": str(rule.profile_name or "").strip(),
                    "custom_processo": str(rule.process_label or "").strip(),
                    "custom_subprocesso": (
                        str(rule.subprocess_label or "").strip()
                        or PROCESS_VIEW_AUTHORIZATION_ALL_SUBPROCESS_LABEL
                    ),
                    "custom_departamento": (
                        str(rule.department_name or "").strip()
                        or PROCESS_VIEW_AUTHORIZATION_ALL_DEPARTMENTS_LABEL
                    ),
                    "__estado": _serialize_process_view_authorization_status_v1(
                        rule.status
                    ),
                },
            }
        )
    return rows


def _get_process_view_authorization_rule_for_scope_v1(
    session: Session,
    *,
    record_id: Any,
    selected_entity_id: int | None,
) -> ProcessViewAuthorizationRule | None:
    clean_record_id = str(record_id or "").strip()
    if not clean_record_id:
        return None

    try:
        parsed_record_id = int(clean_record_id)
    except (TypeError, ValueError):
        return None

    rule = session.get(ProcessViewAuthorizationRule, parsed_record_id)
    if rule is None:
        return None

    if rule.entity_id is None:
        return rule

    if selected_entity_id is None:
        return None

    return rule if int(rule.entity_id) == int(selected_entity_id) else None


def save_process_view_authorization_rule_v1(
    session: Session,
    *,
    sidebar_menu_settings: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    selected_entity_id: int | None,
    current_user_id: int | None,
    requested_history_action: str,
    requested_history_record_id: str,
    submitted_section_values: dict[str, str],
) -> tuple[str, list[dict[str, Any]], str]:
    clean_profile_name = str(submitted_section_values.get("custom_perfil") or "").strip()
    clean_process_label = str(submitted_section_values.get("custom_processo") or "").strip()
    clean_subprocess_label = str(
        submitted_section_values.get("custom_subprocesso") or ""
    ).strip()
    clean_status = _normalize_process_view_authorization_status_v1(
        submitted_section_values.get("__estado")
    )

    if not clean_profile_name:
        return "", [], "Perfil é obrigatório."
    if not clean_process_label:
        return "", [], "Processo é obrigatório."

    resolved_department_name, department_error = (
        _resolve_process_view_authorization_department_name_v1(
            session,
            selected_entity_id=selected_entity_id,
            raw_department_name=submitted_section_values.get("custom_departamento"),
        )
    )
    if department_error:
        return "", [], department_error

    resolved_targets = resolve_process_view_authorization_targets_v1(
        sidebar_menu_settings,
        process_label=clean_process_label,
        subprocess_label=clean_subprocess_label,
    )

    target_rule = None
    if requested_history_action == "update":
        target_rule = _get_process_view_authorization_rule_for_scope_v1(
            session,
            record_id=requested_history_record_id,
            selected_entity_id=selected_entity_id,
        )
        if target_rule is None:
            return "", [], "Registo não encontrado para editar."
    else:
        target_rule = ProcessViewAuthorizationRule(
            entity_id=selected_entity_id,
            created_by_user_id=current_user_id,
        )
        session.add(target_rule)

    if requested_history_action == "update":
        if target_rule.entity_id is not None:
            target_rule.entity_id = selected_entity_id
    else:
        target_rule.entity_id = selected_entity_id
    target_rule.profile_name = clean_profile_name[:100]
    target_rule.process_key = (
        str(resolved_targets.get("process_key") or "").strip().lower() or None
    )
    target_rule.process_label = (
        str(resolved_targets.get("process_label") or clean_process_label).strip()[:120]
    )
    target_rule.subprocess_key = (
        resolve_menu_key_alias(resolved_targets.get("subprocess_key")) or None
    )
    target_rule.subprocess_label = (
        str(
            resolved_targets.get("subprocess_label")
            or clean_subprocess_label
            or PROCESS_VIEW_AUTHORIZATION_ALL_SUBPROCESS_LABEL
        ).strip()[:120]
    )
    target_rule.department_name = resolved_department_name
    target_rule.status = clean_status
    target_rule.updated_by_user_id = current_user_id

    try:
        session.commit()
    except Exception:
        session.rollback()
        return "", [], "Falha ao gravar a regra de autorização."

    success_message = (
        "Regra de autorização atualizada com sucesso."
        if requested_history_action == "update"
        else "Regra de autorização criada com sucesso."
    )
    refreshed_rows = build_process_view_authorization_history_rows_v1(
        session,
        selected_entity_id=selected_entity_id,
    )
    return success_message, refreshed_rows, ""


def delete_process_view_authorization_rule_v1(
    session: Session,
    *,
    selected_entity_id: int | None,
    requested_history_record_id: str,
) -> tuple[str, list[dict[str, Any]], str]:
    target_rule = _get_process_view_authorization_rule_for_scope_v1(
        session,
        record_id=requested_history_record_id,
        selected_entity_id=selected_entity_id,
    )
    if target_rule is None:
        return "", [], "Registo não encontrado para eliminar."

    session.delete(target_rule)
    try:
        session.commit()
    except Exception:
        session.rollback()
        return "", [], "Falha ao eliminar a regra de autorização."

    refreshed_rows = build_process_view_authorization_history_rows_v1(
        session,
        selected_entity_id=selected_entity_id,
    )
    return "Regra de autorização eliminada com sucesso.", refreshed_rows, ""


# ###################################################################################
# (4) MATCH DO UTILIZADOR LOGADO
# ###################################################################################


def _get_user_department_names_by_entity_v1(
    session: Session,
    *,
    actor_user_id: int | None,
    selected_entity_id: int | None,
) -> set[str]:
    if actor_user_id is None or selected_entity_id is None:
        return set()

    rows = session.execute(
        select(Department.name)
        .join(DepartmentMembership, DepartmentMembership.department_id == Department.id)
        .join(MemberEntity, MemberEntity.id == DepartmentMembership.member_entity_id)
        .join(User, User.member_id == MemberEntity.member_id)
        .where(
            User.id == int(actor_user_id),
            MemberEntity.entity_id == int(selected_entity_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            DepartmentMembership.status == DepartmentMembershipStatus.ACTIVE.value,
            Department.is_active.is_(True),
        )
    ).scalars().all()

    return {
        _normalize_process_view_authorization_lookup_text_v1(raw_name)
        for raw_name in rows
        if str(raw_name or "").strip()
    }


def build_process_view_authorized_sidebar_menu_keys_v1(
    session: Session,
    *,
    actor_user_id: int | None,
    selected_entity_id: int | None,
    current_entity_scope: str,
    sidebar_menu_settings: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> set[str]:
    if actor_user_id is None:
        return set()

    normalized_profile_names = {
        _normalize_process_view_authorization_lookup_text_v1(profile_name)
        for profile_name in get_active_profile_names_by_user(session, int(actor_user_id))
        if str(profile_name or "").strip()
    }
    if not normalized_profile_names:
        return set()

    normalized_department_names = _get_user_department_names_by_entity_v1(
        session,
        actor_user_id=actor_user_id,
        selected_entity_id=selected_entity_id,
    )

    clean_entity_scope = str(current_entity_scope or "").strip().lower()
    visible_candidate_keys_by_section: dict[str, set[str]] = {}
    visible_candidate_rows_by_key: dict[str, dict[str, Any]] = {}

    for raw_row in sidebar_menu_settings or []:
        if not isinstance(raw_row, dict):
            continue

        menu_key = resolve_menu_key_alias(raw_row.get("key"))
        if not menu_key:
            continue
        if not raw_row.get("is_active") or raw_row.get("is_deleted"):
            continue

        visibility_scopes = normalize_menu_visibility_scopes(
            raw_row.get("visibility_scopes")
        )
        if clean_entity_scope and clean_entity_scope not in visibility_scopes:
            continue

        visible_candidate_rows_by_key[menu_key] = raw_row
        section_key = str(raw_row.get("sidebar_section_key") or "").strip().lower()
        if section_key:
            visible_candidate_keys_by_section.setdefault(section_key, set()).add(menu_key)

    if not visible_candidate_rows_by_key:
        return set()

    stmt = select(ProcessViewAuthorizationRule).where(
        ProcessViewAuthorizationRule.status == "active"
    )
    if selected_entity_id is None:
        stmt = stmt.where(ProcessViewAuthorizationRule.entity_id.is_(None))
    else:
        stmt = stmt.where(
            or_(
                ProcessViewAuthorizationRule.entity_id == int(selected_entity_id),
                ProcessViewAuthorizationRule.entity_id.is_(None),
            )
        )

    candidate_rules = list(session.execute(stmt).scalars())
    effective_rules = _select_effective_process_view_authorization_rules_v1(
        candidate_rules,
        normalized_profile_names=normalized_profile_names,
        selected_entity_id=selected_entity_id,
        sidebar_menu_settings=sidebar_menu_settings,
    )

    authorized_menu_keys: set[str] = set()
    for rule in effective_rules:

        normalized_rule_department = _normalize_process_view_authorization_lookup_text_v1(
            rule.department_name
        )
        if (
            normalized_rule_department
            and not _is_all_departments_rule_v1(rule.department_name)
            and normalized_rule_department not in normalized_department_names
        ):
            continue

        resolved_subprocess_key, _ = _resolve_rule_subprocess_target_v1(
            rule,
            sidebar_menu_settings,
        )
        if resolved_subprocess_key:
            if resolved_subprocess_key in visible_candidate_rows_by_key:
                authorized_menu_keys.add(resolved_subprocess_key)
            continue

        resolved_process_key, _ = _resolve_rule_process_target_v1(
            rule,
            sidebar_menu_settings,
        )
        if not resolved_process_key:
            continue

        authorized_menu_keys.update(
            visible_candidate_keys_by_section.get(resolved_process_key, set())
        )

    return authorized_menu_keys


# ###################################################################################
# (5) VISIBILIDADE EFETIVA DO SIDEBAR
# ###################################################################################


def build_effective_sidebar_visibility_v1(
    session: Session,
    *,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    sidebar_menu_settings: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
) -> dict[str, Any]:
    settings = [
        dict(raw_row or {})
        for raw_row in (
            sidebar_menu_settings
            if sidebar_menu_settings is not None
            else get_sidebar_menu_settings(
                session,
                selected_entity_id=selected_entity_id,
            )
        )
    ]

    permissions = {
        "is_admin": False,
        "has_owner_membership": False,
        "can_manage_all_entities": False,
        "selected_entity_id": selected_entity_id,
        "allowed_entity_ids": set(),
    }
    resolved_selected_entity_id = selected_entity_id
    current_user_is_admin = False

    if actor_user_id is not None:
        permissions = get_user_entity_permissions(
            session,
            int(actor_user_id),
            str(actor_login_email or ""),
            selected_entity_id,
        )
        resolved_selected_entity_id = permissions.get("selected_entity_id")
        current_user_is_admin = bool(permissions.get("is_admin"))

    current_entity_scope = ""
    if resolved_selected_entity_id is not None:
        raw_entity_scope = session.execute(
            select(Entity.profile_scope)
            .where(Entity.id == int(resolved_selected_entity_id))
            .limit(1)
        ).scalar_one_or_none()
        current_entity_scope = str(raw_entity_scope or "").strip().lower()

    base_visible_sidebar_menu_keys = get_visible_sidebar_menu_keys(
        settings,
        current_user_is_admin=current_user_is_admin,
        current_entity_scope=current_entity_scope,
    )
    granted_sidebar_menu_keys = build_process_view_authorized_sidebar_menu_keys_v1(
        session,
        actor_user_id=actor_user_id,
        selected_entity_id=resolved_selected_entity_id,
        current_entity_scope=current_entity_scope,
        sidebar_menu_settings=settings,
    )

    effective_visible_sidebar_menu_keys = {
        str(raw_key or "").strip().lower()
        for raw_key in base_visible_sidebar_menu_keys
        if str(raw_key or "").strip()
    }
    effective_visible_sidebar_menu_keys.update(granted_sidebar_menu_keys)
    effective_visible_sidebar_menu_keys.add("home")

    return {
        "permissions": permissions,
        "selected_entity_id": resolved_selected_entity_id,
        "current_user_is_admin": current_user_is_admin,
        "current_entity_scope": current_entity_scope,
        "sidebar_menu_settings": settings,
        "granted_sidebar_menu_keys": sorted(granted_sidebar_menu_keys),
        "visible_sidebar_menu_keys": sorted(effective_visible_sidebar_menu_keys),
    }


__all__ = [
    "PROCESS_VIEW_AUTHORIZATION_ALL_DEPARTMENTS_LABEL",
    "PROCESS_VIEW_AUTHORIZATION_ALL_SUBPROCESS_LABEL",
    "PROCESS_VIEW_AUTHORIZATION_MENU_KEY",
    "PROCESS_VIEW_AUTHORIZATION_SECTION_KEY",
    "build_effective_sidebar_visibility_v1",
    "build_process_view_authorization_history_rows_v1",
    "build_process_view_authorized_sidebar_menu_keys_v1",
    "delete_process_view_authorization_rule_v1",
    "is_process_view_authorization_section_v1",
    "resolve_process_view_authorization_targets_v1",
    "save_process_view_authorization_rule_v1",
]
