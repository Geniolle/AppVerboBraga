from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import urlencode

from appverbo.core import *  # noqa: F403,F401
from appverbo.menu_settings import (
    MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
    MENU_DOCUMENTOS_FIELD_LABELS,
    MENU_DOCUMENTOS_FIELD_OPTIONS,
    MENU_DOCUMENTOS_FIELDS_DEFAULT,
    get_sidebar_menu_settings,
    get_visible_sidebar_menu_keys,
    normalize_sidebar_sections,
)
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.profile import (
    build_menu_process_records_storage_key,
    build_menu_process_field_storage_key,
    parse_menu_process_records,
    parse_member_profile_fields,
)

def get_page_data(
    session: Session,
    actor_user_id: int | None = None,
    actor_login_email: str = "",
    selected_entity_id: int | None = None,
) -> dict[str, Any]:
    entity_superuser_profile_name = ENTITY_SUPERUSER_PROFILE_NAME.strip() or "SUPER USER"
    permissions = {
        "is_admin": False,
        "has_owner_membership": False,
        "can_manage_all_entities": False,
        "selected_entity_id": selected_entity_id,
        "allowed_entity_ids": set(),
    }
    allowed_entity_ids: set[int] | None = None
    if actor_user_id is not None:
        permissions = get_user_entity_permissions(
            session,
            actor_user_id,
            actor_login_email,
            selected_entity_id,
        )
        allowed_entity_ids = set(permissions["allowed_entity_ids"])
        selected_entity_id = permissions["selected_entity_id"]
    current_user_is_admin = bool(permissions["is_admin"])
    current_entity_scope = ""
    if selected_entity_id is not None:
        raw_entity_scope = session.execute(
            select(Entity.profile_scope)
           .where(Entity.id == selected_entity_id)
           .limit(1)
        ).scalar_one_or_none()
        current_entity_scope = str(raw_entity_scope or "").strip().lower()

    sidebar_menu_settings = get_sidebar_menu_settings(session)
    visible_sidebar_menu_keys = get_visible_sidebar_menu_keys(
        sidebar_menu_settings,
        current_user_is_admin=current_user_is_admin,
        current_entity_scope=current_entity_scope,
    )
    administrativo_menu = next(
        (
            row
            for row in sidebar_menu_settings
            if str(row.get("key") or "").strip().lower() == "administrativo"
        ),
        None,
    )
    sidebar_section_options = normalize_sidebar_sections(
        (administrativo_menu or {}).get("menu_config", {}).get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )
    actor_profile_fields: dict[str, str] = {}
    if actor_user_id is not None:
        raw_profile_fields = session.execute(
            select(Member.profile_custom_fields)
           .join(User, User.member_id == Member.id)
           .where(User.id == actor_user_id)
           .limit(1)
        ).scalar_one_or_none()
        actor_profile_fields = parse_member_profile_fields(raw_profile_fields)
    menu_process_values_map: dict[str, dict[str, str]] = {}
    menu_process_history_map: dict[str, list[dict[str, Any]]] = {}
    for sidebar_item in sidebar_menu_settings:
        menu_key = str(sidebar_item.get("key") or "").strip().lower()
        if not menu_key or menu_key in {"home", "perfil", "administrativo", "documentos"}:
            continue
        visible_rows = (
            sidebar_item.get("process_visible_field_rows")
            if isinstance(sidebar_item.get("process_visible_field_rows"), list)
            else []
        )
        menu_values: dict[str, str] = {}
        for raw_row in visible_rows:
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            if not field_key:
                continue
            storage_key = build_menu_process_field_storage_key(menu_key, field_key)
            if not storage_key:
                continue
            storage_value = actor_profile_fields.get(storage_key)
            if storage_value is None:
                continue
            menu_values[field_key] = storage_value
        if menu_values:
            menu_process_values_map[menu_key] = menu_values
        history_storage_key = build_menu_process_records_storage_key(menu_key)
        if history_storage_key:
            menu_history_rows = parse_menu_process_records(actor_profile_fields.get(history_storage_key))
            if menu_history_rows:
                menu_process_history_map[menu_key] = menu_history_rows
    profile_personal_visible_fields = list(MENU_DOCUMENTOS_FIELDS_DEFAULT)
    profile_personal_field_labels = dict(MENU_DOCUMENTOS_FIELD_LABELS)
    profile_personal_field_types: dict[str, str] = {}
    profile_personal_field_header_map: dict[str, str] = {}
    profile_personal_custom_field_meta: dict[str, dict[str, Any]] = {}
    for sidebar_item in sidebar_menu_settings:
        if str(sidebar_item.get("key") or "") != "documentos":
            continue
        options = sidebar_item.get("process_field_options") or []
        option_labels = {
            str(item.get("key") or "").strip().lower(): str(item.get("label") or "").strip()
            for item in options
            if str(item.get("key") or "").strip()
        }
        option_types = {
            str(item.get("key") or "").strip().lower(): str(item.get("field_type") or "").strip().lower()
            for item in options
            if str(item.get("key") or "").strip()
        }
        if option_labels:
            profile_personal_field_labels = option_labels
        if option_types:
            profile_personal_field_types = option_types
        raw_header_map = sidebar_item.get("process_visible_field_header_map")
        if isinstance(raw_header_map, dict):
            profile_personal_field_header_map = {
                str(raw_key or "").strip().lower(): str(raw_value or "").strip().lower()
                for raw_key, raw_value in raw_header_map.items()
                if str(raw_key or "").strip() and str(raw_value or "").strip()
            }
        for custom_field in sidebar_item.get("process_additional_fields") or []:
            clean_key = str(custom_field.get("key") or "").strip().lower()
            if not clean_key.startswith("custom_"):
                continue
            field_type = str(custom_field.get("field_type") or "text").strip().lower()
            if field_type not in {"text", "number", "email", "phone", "date", "flag", "header"}:
                field_type = "text"
            try:
                parsed_size = int(str(custom_field.get("size") or "").strip())
            except (TypeError, ValueError):
                parsed_size = 30
            if field_type in {"text", "number", "email", "phone"}:
                field_size: int | None = max(1, min(parsed_size, 255))
            else:
                field_size = None
            raw_required = custom_field.get("is_required", custom_field.get("required"))
            if isinstance(raw_required, bool):
                is_required = raw_required
            else:
                is_required = str(raw_required or "").strip().lower() in {"1", "true", "sim", "yes", "on"}
            if field_type == "header":
                is_required = False
            profile_personal_custom_field_meta[clean_key] = {
                "field_type": field_type,
                "size": field_size,
                "is_required": is_required,
            }
        visible_raw = sidebar_item.get("process_visible_fields") or []
        visible_fields = [
            str(raw_key or "").strip().lower()
            for raw_key in visible_raw
            if str(raw_key or "").strip().lower() in profile_personal_field_labels
        ]
        if visible_fields:
            profile_personal_visible_fields = visible_fields
        elif profile_personal_field_labels:
            profile_personal_visible_fields = [
                field_key
                for field_key in MENU_DOCUMENTOS_FIELDS_DEFAULT
                if field_key in profile_personal_field_labels
            ]
            if not profile_personal_visible_fields:
                profile_personal_visible_fields = [next(iter(profile_personal_field_labels.keys()))]
        break

    profile_personal_sections: list[dict[str, str]] = [{"key": "geral", "label": "Geral"}]
    profile_personal_field_section_map: dict[str, str] = {}
    header_section_order: list[str] = []
    header_section_seen: set[str] = set()
    for field_key in profile_personal_visible_fields:
        clean_field_key = str(field_key or "").strip().lower()
        if not clean_field_key:
            continue
        field_type = str(profile_personal_field_types.get(clean_field_key) or "").strip().lower()
        if field_type == "header" and clean_field_key not in header_section_seen:
            header_section_order.append(clean_field_key)
            header_section_seen.add(clean_field_key)
    for header_key in profile_personal_field_header_map.values():
        clean_header_key = str(header_key or "").strip().lower()
        if not clean_header_key or clean_header_key in header_section_seen:
            continue
        if str(profile_personal_field_types.get(clean_header_key) or "").strip().lower() != "header":
            continue
        header_section_order.append(clean_header_key)
        header_section_seen.add(clean_header_key)

    if header_section_order:
        for section_key in header_section_order:
            section_label = profile_personal_field_labels.get(section_key, "Aba")
            profile_personal_sections.append({"key": section_key, "label": section_label})
        for field_key in profile_personal_visible_fields:
            clean_field_key = str(field_key or "").strip().lower()
            if not clean_field_key:
                continue
            field_type = str(profile_personal_field_types.get(clean_field_key) or "").strip().lower()
            if field_type == "header":
                continue
            header_key = str(profile_personal_field_header_map.get(clean_field_key) or "").strip().lower()
            if header_key in header_section_seen:
                profile_personal_field_section_map[clean_field_key] = header_key
            else:
                profile_personal_field_section_map[clean_field_key] = "geral"
        has_geral_fields = any(
            section_key == "geral" for section_key in profile_personal_field_section_map.values()
        )
        if not has_geral_fields:
            profile_personal_sections = [
                section for section in profile_personal_sections if section.get("key") != "geral"
            ]
    else:
        active_section_key = "geral"
        seen_section_keys = {"geral"}
        for field_key in profile_personal_visible_fields:
            clean_field_key = str(field_key or "").strip().lower()
            if not clean_field_key:
                continue
            field_type = str(profile_personal_field_types.get(clean_field_key) or "").strip().lower()
            if field_type == "header":
                section_key = clean_field_key
                section_label = profile_personal_field_labels.get(clean_field_key, "Aba")
                if section_key not in seen_section_keys:
                    profile_personal_sections.append({"key": section_key, "label": section_label})
                    seen_section_keys.add(section_key)
                active_section_key = section_key
                continue
            profile_personal_field_section_map[clean_field_key] = active_section_key
        if len(profile_personal_sections) > 1:
            has_geral_fields = any(
                section_key == "geral" for section_key in profile_personal_field_section_map.values()
            )
            if not has_geral_fields:
                profile_personal_sections = [
                    section for section in profile_personal_sections if section.get("key") != "geral"
                ]


    required_profile_fields = ["nome", "telefone", "email", "pais"]

    for required_field in required_profile_fields:
        if required_field not in profile_personal_field_labels:
            profile_personal_field_labels[required_field] = {
                "nome": "Nome",
                "telefone": "Telefone",
                "email": "Email",
                "pais": "País",
            }[required_field]

        if required_field not in profile_personal_visible_fields:
            if required_field == "pais" and "telefone" in profile_personal_visible_fields:
                profile_personal_visible_fields.insert(
                    profile_personal_visible_fields.index("telefone") + 1,
                    required_field,
                )
            elif required_field == "email" and "telefone" in profile_personal_visible_fields:
                profile_personal_visible_fields.insert(
                    profile_personal_visible_fields.index("telefone") + 1,
                    required_field,
                )
            elif required_field == "telefone" and "nome" in profile_personal_visible_fields:
                profile_personal_visible_fields.insert(
                    profile_personal_visible_fields.index("nome") + 1,
                    required_field,
                )
            else:
                profile_personal_visible_fields.append(required_field)

    if "pais" not in profile_personal_field_section_map:
        profile_personal_field_section_map["pais"] = profile_personal_field_section_map.get("telefone", "geral")

    if "nome" not in profile_personal_field_section_map:
        profile_personal_field_section_map["nome"] = "geral"

    if "telefone" not in profile_personal_field_section_map:
        profile_personal_field_section_map["telefone"] = profile_personal_field_section_map.get("nome", "geral")

    if "email" not in profile_personal_field_section_map:
        profile_personal_field_section_map["email"] = profile_personal_field_section_map.get("telefone", "geral")


    scoped_entity_ids = sorted(allowed_entity_ids) if allowed_entity_ids is not None else []
    apply_scope_filter = allowed_entity_ids is not None

    entities_stmt = (
        select(Entity.id, Entity.name, Entity.internal_number)
       .where(Entity.is_active.is_(True))
       .order_by(Entity.name)
    )
    if apply_scope_filter:
        if scoped_entity_ids:
            entities_stmt = entities_stmt.where(Entity.id.in_(scoped_entity_ids))
        else:
            entities_stmt = entities_stmt.where(Entity.id == -1)
    entities = session.execute(entities_stmt).all()

    profiles_for_form = get_allowed_global_profiles_for_form(session)

    entity_rows_stmt = (
        select(
            Entity.id,
            Entity.internal_number,
            Entity.name,
            Entity.acronym,
            Entity.tax_id,
            Entity.email,
            Entity.responsible_name,
            Entity.door_number,
            Entity.phone,
            Entity.address,
            Entity.freguesia,
            Entity.postal_code,
            Entity.country,
            Entity.description,
            Entity.profile_scope,
            Entity.logo_url,
            Entity.is_active,
            Entity.created_at,
        )
       .order_by(Entity.id.desc())
    )
    if apply_scope_filter:
        if scoped_entity_ids:
            entity_rows_stmt = entity_rows_stmt.where(Entity.id.in_(scoped_entity_ids))
        else:
            entity_rows_stmt = entity_rows_stmt.where(Entity.id == -1)

    recent_entities = session.execute(
        entity_rows_stmt.where(Entity.is_active.is_(True)).limit(10)
    ).all()
    inactive_entities_rows = session.execute(
        entity_rows_stmt.where(Entity.is_active.is_not(True))
    ).all()

    user_rows = session.execute(
        select(
            User.id,
            User.member_id,
            Member.full_name,
            Member.primary_phone,
            User.login_email,
            User.account_status,
            User.created_at,
        )
       .join(Member, Member.id == User.member_id)
       .order_by(User.id.desc())
    ).all()

    if apply_scope_filter:
        if scoped_entity_ids:
            scoped_member_ids = {
                int(raw_id)
                for raw_id in session.execute(
                    select(MemberEntity.member_id)
                   .where(
                        MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                        MemberEntity.entity_id.in_(scoped_entity_ids),
                    )
                   .distinct()
                ).scalars().all()
            }
            user_rows = [
                row for row in user_rows if int(row.member_id) in scoped_member_ids
            ]
        else:
            user_rows = []

    member_ids = [int(row.member_id) for row in user_rows]
    user_ids = [int(row.id) for row in user_rows]

    entity_name_by_member_id: dict[int, str] = {}
    entity_id_by_member_id: dict[int, int] = {}
    if member_ids:
        entity_name_stmt = (
            select(MemberEntity.member_id, MemberEntity.entity_id, Entity.name)
           .join(Entity, Entity.id == MemberEntity.entity_id)
           .where(MemberEntity.member_id.in_(member_ids))
           .order_by(MemberEntity.member_id.asc(), MemberEntity.id.asc())
        )
        if apply_scope_filter and scoped_entity_ids:
            entity_name_stmt = entity_name_stmt.where(MemberEntity.entity_id.in_(scoped_entity_ids))
        elif apply_scope_filter:
            entity_name_stmt = entity_name_stmt.where(MemberEntity.entity_id == -1)

        for row in session.execute(entity_name_stmt).all():
            member_id_value = int(row.member_id)
            if member_id_value not in entity_name_by_member_id:
                entity_id_by_member_id[member_id_value] = int(row.entity_id)
                entity_name_by_member_id[member_id_value] = row.name

    profile_name_by_user_id: dict[int, str] = {}
    superuser_user_ids: set[int] = set()
    if user_ids:
        profile_rows = session.execute(
            select(UserProfile.user_id, Profile.name)
           .join(Profile, Profile.id == UserProfile.profile_id)
           .where(UserProfile.user_id.in_(user_ids), UserProfile.is_active.is_(True))
           .order_by(UserProfile.user_id.asc(), UserProfile.id.asc())
        ).all()
        for row in profile_rows:
            user_id_value = int(row.user_id)
            if user_id_value not in profile_name_by_user_id:
                profile_name_by_user_id[user_id_value] = row.name

        superuser_rows = session.execute(
            select(UserProfile.user_id)
           .join(Profile, Profile.id == UserProfile.profile_id)
           .where(
                UserProfile.user_id.in_(user_ids),
                UserProfile.is_active.is_(True),
                Profile.is_active.is_(True),
                func.lower(Profile.name) == entity_superuser_profile_name.lower(),
            )
        ).all()
        superuser_user_ids = {int(row.user_id) for row in superuser_rows}

    all_users = [
        {
            "id": row.id,
            "member_id": row.member_id,
            "full_name": row.full_name,
            "primary_phone": row.primary_phone or "-",
            "login_email": row.login_email,
            "account_status": row.account_status,
            "entity_id": entity_id_by_member_id.get(int(row.member_id)),
            "entity_name": entity_name_by_member_id.get(int(row.member_id), "-"),
            "profile_name": profile_name_by_user_id.get(int(row.id), "-"),
            "is_entity_superuser": int(row.id) in superuser_user_ids,
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M") if row.created_at else "-",
        }
        for row in user_rows
    ]
    pending_users = [
        row for row in all_users if row["account_status"] == UserAccountStatus.PENDING.value
    ]
    created_users = [
        row for row in all_users if row["account_status"] != UserAccountStatus.PENDING.value
    ]
    superuser_users = [row for row in all_users if row["is_entity_superuser"]]
    recent_users = all_users[:10]

    account_status_map = {
        UserAccountStatus.ACTIVE.value: 0,
        UserAccountStatus.PENDING.value: 0,
        UserAccountStatus.INACTIVE.value: 0,
        UserAccountStatus.BLOCKED.value: 0,
    }
    for row in all_users:
        normalized_status = str(row.get("account_status") or "").strip().lower()
        if normalized_status not in account_status_map:
            account_status_map[normalized_status] = 0
        account_status_map[normalized_status] += 1
    account_status_summary = [
        {"status": UserAccountStatus.ACTIVE.value, "count": account_status_map.get(UserAccountStatus.ACTIVE.value, 0)},
        {"status": UserAccountStatus.PENDING.value, "count": account_status_map.get(UserAccountStatus.PENDING.value, 0)},
        {"status": UserAccountStatus.INACTIVE.value, "count": account_status_map.get(UserAccountStatus.INACTIVE.value, 0)},
        {"status": UserAccountStatus.BLOCKED.value, "count": account_status_map.get(UserAccountStatus.BLOCKED.value, 0)},
    ]

    def serialize_entity_row(row: Any) -> dict[str, Any]:
        return {
            "id": row.id,
            "internal_number": row.internal_number if row.internal_number is not None else "-",
            "name": row.name,
            "acronym": row.acronym or "",
            "tax_id": row.tax_id or "",
            "email": row.email or "",
            "responsible_name": row.responsible_name or "",
            "door_number": row.door_number or "",
            "phone": row.phone or "",
            "address": row.address or "",
            "freguesia": row.freguesia or "",
            "postal_code": row.postal_code or "",
            "country": row.country or "",
            "description": row.description or "",
            "profile_scope": (row.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO),
            "profile_scope_label": (
                "Owner"
                if (row.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO) == ENTITY_PROFILE_SCOPE_OWNER
                else "Legado"
            ),
            "logo_url": row.logo_url or "",
            "is_active": bool(row.is_active),
            "status_label": "Ativa" if row.is_active else "Inativa",
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M") if row.created_at else "-",
        }

    return {
        "entities": [
            {
                "id": row.id,
                "name": row.name,
                "internal_number": row.internal_number,
            }
            for row in entities
        ],
        "profiles": profiles_for_form,
        "account_status_summary": account_status_summary,
        "recent_entities": [serialize_entity_row(row) for row in recent_entities],
        "inactive_entities": [serialize_entity_row(row) for row in inactive_entities_rows],
        "recent_users": [
            {
                "id": row["id"],
                "full_name": row["full_name"],
                "login_email": row["login_email"],
                "account_status": row["account_status"],
                "created_at": row["created_at"],
            }
            for row in recent_users
        ],
        "all_users": all_users,
        "created_users": created_users,
        "pending_users": pending_users,
        "superuser_users": superuser_users,
        "entity_permissions": permissions,
        "current_user_can_manage_all_entities": bool(permissions["can_manage_all_entities"]),
        "current_entity_scope": current_entity_scope,
        "sidebar_menu_settings": sidebar_menu_settings,
        "sidebar_section_options": sidebar_section_options,
        "visible_sidebar_menu_keys": sorted(visible_sidebar_menu_keys),
        "menu_process_values_map": menu_process_values_map,
        "menu_process_history_map": menu_process_history_map,
        "profile_personal_visible_fields": profile_personal_visible_fields,
        "profile_personal_field_labels": profile_personal_field_labels,
        "profile_personal_field_section_map": profile_personal_field_section_map,
        "profile_personal_sections": profile_personal_sections,
        "profile_personal_custom_field_meta": profile_personal_custom_field_meta,
        "menu_documentos_field_options": [dict(item) for item in MENU_DOCUMENTOS_FIELD_OPTIONS],
        "menu_documentos_field_labels": dict(MENU_DOCUMENTOS_FIELD_LABELS),
        "dashboard_data": get_home_dashboard_data(
            session,
            allowed_entity_ids=allowed_entity_ids,
        ),
    }

def get_home_dashboard_data(
    session: Session,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, Any]:
    apply_scope_filter = allowed_entity_ids is not None
    scoped_entity_ids = sorted(allowed_entity_ids) if allowed_entity_ids is not None else []

    entity_counts_stmt = select(Entity.is_active, func.count(Entity.id)).group_by(Entity.is_active)
    if apply_scope_filter:
        if scoped_entity_ids:
            entity_counts_stmt = entity_counts_stmt.where(Entity.id.in_(scoped_entity_ids))
        else:
            entity_counts_stmt = entity_counts_stmt.where(Entity.id == -1)

    entity_counts = session.execute(entity_counts_stmt).all()
    active_entities = 0
    inactive_entities = 0
    for row in entity_counts:
        if bool(row.is_active):
            active_entities = int(row[1])
        else:
            inactive_entities = int(row[1])

    if apply_scope_filter:
        if scoped_entity_ids:
            scoped_user_ids = [
                int(raw_id)
                for raw_id in session.execute(
                    select(User.id)
                   .join(MemberEntity, MemberEntity.member_id == User.member_id)
                   .where(
                        MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                        MemberEntity.entity_id.in_(scoped_entity_ids),
                    )
                   .distinct()
                ).scalars().all()
            ]
        else:
            scoped_user_ids = []
    else:
        scoped_user_ids = []

    profile_count_map: dict[str, int] = {}
    if not apply_scope_filter or scoped_user_ids:
        user_profile_join_condition = (
            (UserProfile.profile_id == Profile.id)
            & (UserProfile.is_active.is_(True))
        )
        if apply_scope_filter:
            user_profile_join_condition = (
                user_profile_join_condition
                & (UserProfile.user_id.in_(scoped_user_ids))
            )

        profile_rows = session.execute(
            select(Profile.name, func.count(func.distinct(UserProfile.user_id)))
           .select_from(Profile)
           .outerjoin(UserProfile, user_profile_join_condition)
           .where(func.lower(Profile.name).in_(ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED))
           .group_by(Profile.id, Profile.name)
        ).all()
        for row in profile_rows:
            profile_count_map[normalize_profile_name(row.name)] = int(row[1])

    profile_labels = list(ALLOWED_GLOBAL_PROFILE_NAMES)
    profile_values = [
        profile_count_map.get(normalize_profile_name(label), 0) for label in profile_labels
    ]

    total_entities = active_entities + inactive_entities
    if apply_scope_filter:
        total_users = len(scoped_user_ids)
    else:
        total_users = session.scalar(select(func.count(User.id))) or 0

    return {
        "entity_status": {
            "labels": ["Ativas", "Inativas"],
            "values": [active_entities, inactive_entities],
        },
        "users_by_profile": {
            "labels": profile_labels,
            "values": profile_values,
        },
        "totals": {
            "entities": int(total_entities),
            "users": int(total_users),
            "active_entities": int(active_entities),
            "inactive_entities": int(inactive_entities),
        },
    }

def get_form_defaults() -> dict[str, str]:
    return {
        "full_name": "",
        "primary_phone": "",
        "email": "",
        "entity_id": "",
        "entity_name": "",
        "account_status": UserAccountStatus.ACTIVE.value,
        "profile_id": "",
    }

def get_entity_form_defaults() -> dict[str, str]:
    return {
        "name": "",
        "acronym": "",
        "tax_id": "",
        "email": "",
        "responsible_name": "",
        "door_number": "",
        "address": "",
        "freguesia": "",
        "postal_code": "",
        "country": "",
        "phone": "",
        "description": "",
        "profile_scope": ENTITY_PROFILE_SCOPE_LEGADO,
        "created_at": date.today().strftime("%d/%m/%Y"),
    }

def get_entity_edit_defaults() -> dict[str, str]:
    return {
        "id": "",
        "internal_number": "-",
        "name": "",
        "acronym": "",
        "tax_id": "",
        "email": "",
        "responsible_name": "",
        "door_number": "",
        "address": "",
        "freguesia": "",
        "postal_code": "",
        "country": "",
        "phone": "",
        "description": "",
        "profile_scope": ENTITY_PROFILE_SCOPE_LEGADO,
        "created_at": "",
        "logo_url": "",
        "status": "active",
    }

def get_entity_edit_data(
    session: Session,
    entity_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, str]:
    defaults = get_entity_edit_defaults()
    if entity_id is None:
        return defaults

    if allowed_entity_ids is not None and int(entity_id) not in allowed_entity_ids:
        return defaults

    entity = session.get(Entity, entity_id)
    if entity is None:
        return defaults

    return {
        "id": str(entity.id),
        "internal_number": str(entity.internal_number) if entity.internal_number is not None else "-",
        "name": entity.name or "",
        "acronym": entity.acronym or "",
        "tax_id": entity.tax_id or "",
        "email": entity.email or "",
        "responsible_name": entity.responsible_name or "",
        "door_number": entity.door_number or "",
        "address": entity.address or "",
        "freguesia": entity.freguesia or "",
        "postal_code": entity.postal_code or "",
        "country": entity.country or "",
        "phone": entity.phone or "",
        "description": entity.description or "",
        "profile_scope": entity.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO,
        "created_at": entity.created_at.strftime("%d/%m/%Y") if entity.created_at else "",
        "logo_url": entity.logo_url or "",
        "status": "active" if entity.is_active else "inactive",
    }

def get_user_edit_defaults() -> dict[str, str]:
    return {
        "id": "",
        "full_name": "",
        "primary_phone": "",
        "email": "",
        "entity_id": "",
        "entity_name": "",
        "account_status": UserAccountStatus.ACTIVE.value,
        "profile_id": "",
    }

def get_user_edit_data(
    session: Session,
    user_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, str]:
    defaults = get_user_edit_defaults()
    if user_id is None:
        return defaults

    row = session.execute(
        select(
            User.id,
            User.member_id,
            Member.full_name,
            Member.primary_phone,
            User.login_email,
            User.account_status,
        )
       .join(Member, Member.id == User.member_id)
       .where(User.id == user_id)
    ).one_or_none()
    if row is None:
        return defaults

    member_entity_stmt = (
        select(MemberEntity.entity_id)
       .where(MemberEntity.member_id == row.member_id)
       .order_by(MemberEntity.id.asc())
    )
    if allowed_entity_ids is not None:
        if allowed_entity_ids:
            member_entity_stmt = member_entity_stmt.where(
                MemberEntity.entity_id.in_(sorted(allowed_entity_ids))
            )
        else:
            return defaults

    member_entity_id = session.scalar(member_entity_stmt.limit(1))
    if allowed_entity_ids is not None and member_entity_id is None:
        return defaults

    profile_id = session.scalar(
        select(UserProfile.profile_id)
       .where(UserProfile.user_id == row.id, UserProfile.is_active.is_(True))
       .order_by(UserProfile.id.asc())
       .limit(1)
    )

    return {
        "id": str(row.id),
        "full_name": row.full_name or "",
        "primary_phone": row.primary_phone or "",
        "email": row.login_email or "",
        "entity_id": str(member_entity_id) if member_entity_id is not None else "",
        "entity_name": (
            session.execute(
                select(Entity.name).where(Entity.id == member_entity_id).limit(1)
            ).scalar_one_or_none()
            if member_entity_id is not None
            else ""
        )
        or "",
        "account_status": row.account_status or UserAccountStatus.ACTIVE.value,
        "profile_id": str(profile_id) if profile_id is not None else "",
    }

def get_next_entity_internal_number(session: Session) -> int:
    used_numbers = session.scalars(
        select(Entity.internal_number)
       .where(
            Entity.internal_number.is_not(None),
            Entity.internal_number >= ENTITY_INTERNAL_NUMBER_MIN,
            Entity.internal_number <= ENTITY_INTERNAL_NUMBER_MAX,
        )
       .order_by(Entity.internal_number.asc())
    ).all()
    used_set = {int(number) for number in used_numbers if isinstance(number, int)}
    for candidate in range(ENTITY_INTERNAL_NUMBER_MIN, ENTITY_INTERNAL_NUMBER_MAX + 1):
        if candidate not in used_set:
            return candidate
    return ENTITY_INTERNAL_NUMBER_MAX

def build_users_new_url(**query_params: str) -> str:
    clean_query_params = {
        key: value
        for key, value in query_params.items()
        if isinstance(value, str) and value.strip()
    }
    if not clean_query_params:
        return "/users/new"
    return f"/users/new?{urlencode(clean_query_params)}"

__all__ = [
    "get_page_data",
    "get_home_dashboard_data",
    "get_form_defaults",
    "get_entity_form_defaults",
    "get_entity_edit_defaults",
    "get_entity_edit_data",
    "get_user_edit_defaults",
    "get_user_edit_data",
    "get_next_entity_internal_number",
    "build_users_new_url",
]
