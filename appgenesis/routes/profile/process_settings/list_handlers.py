from fastapi import Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appgenesis.routes.profile.router import router

from appgenesis.menu_settings import (
    resolve_menu_key_alias,
    update_sidebar_menu_process_lists,
)
from appgenesis.core import SessionLocal
from appgenesis.services.session import get_current_user, get_session_entity_id
from appgenesis.services.auth import is_admin_user
from appgenesis.services.permissions import get_user_entity_permissions

from appgenesis.routes.profile.process_settings.common import (
    _build_settings_redirect_url,
    _build_settings_editor_stay_redirect_url_v1,
)


@router.post("/settings/menu/process-lists", response_class=HTMLResponse)
def edit_sidebar_menu_process_lists_handler(
    request: Request,
    menu_key: str = Form(...),
    process_list_key: list[str] = Form(default=[]),
    process_list_label: list[str] = Form(default=[]),
    process_list_items_csv: list[str] = Form(default=[]),
    process_list_field_type: list[str] = Form(default=[]),
    process_list_source_session_key: list[str] = Form(default=[]),
    process_list_source_menu_key: list[str] = Form(default=[]),
    process_list_source_subprocess_key: list[str] = Form(default=[]),
    process_list_status: list[str] = Form(default=[]),
    process_list_column_key: list[str] = Form(default=[]),
    process_list_column_label: list[str] = Form(default=[]),
    process_list_column_field_key: list[str] = Form(default=[]),
    process_list_column_source_kind: list[str] = Form(default=[]),
    process_list_column_always_visible: list[str] = Form(default=[]),
    process_list_column_responsive_priority: list[str] = Form(default=[]),
    process_list_columns_configured: str = Form(""),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
    return_url: str = Form(""),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)
    if not isinstance(process_list_source_menu_key, list):
        process_list_source_menu_key = []
    if not isinstance(process_list_source_session_key, list):
        process_list_source_session_key = []
    if not isinstance(process_list_source_subprocess_key, list):
        process_list_source_subprocess_key = []

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                    return_url=return_url,
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions.get(
            "can_manage_tenant_structure",
            permissions.get("can_manage_all_entities", False),
        ):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                    return_url=return_url,
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(process_list_key),
            len(process_list_label),
            len(process_list_items_csv),
            len(process_list_field_type),
            len(process_list_source_session_key),
            len(process_list_source_menu_key),
            len(process_list_source_subprocess_key),
            len(process_list_status),
        )

        payload_lists: list[dict[str, str]] = []

        for row_index in range(rows_count):
            label = (
                process_list_label[row_index]
                if row_index < len(process_list_label)
                else ""
            )
            items_csv = (
                process_list_items_csv[row_index]
                if row_index < len(process_list_items_csv)
                else ""
            )
            field_type = (
                process_list_field_type[row_index]
                if row_index < len(process_list_field_type)
                else ""
            )
            source_menu_key = (
                process_list_source_menu_key[row_index]
                if row_index < len(process_list_source_menu_key)
                else ""
            )
            source_session_key = (
                process_list_source_session_key[row_index]
                if row_index < len(process_list_source_session_key)
                else ""
            )
            source_subprocess_key = (
                process_list_source_subprocess_key[row_index]
                if row_index < len(process_list_source_subprocess_key)
                else ""
            )
            raw_status = (
                process_list_status[row_index]
                if row_index < len(process_list_status)
                else ""
            )

            if (
                not str(label or "").strip()
                and not str(items_csv or "").strip()
                and not str(source_menu_key or "").strip()
            ):
                continue

            # normalize field_type values: only 'manual' or 'automatic' allowed
            ft = str(field_type or "").strip().lower()
            if ft not in {"manual", "automatic"}:
                ft = "manual"

            # normalize status values: only 'ativo' or 'inativo' allowed,
            # defaulting to 'ativo' for backward compatibility with legacy lists
            list_status = str(raw_status or "").strip().lower()
            if list_status not in {"ativo", "inativo"}:
                list_status = "ativo"

            payload_lists.append(
                {
                    "key": process_list_key[row_index]
                    if row_index < len(process_list_key)
                    else "",
                    "label": label,
                    "field_type": ft,
                    "items_csv": items_csv if ft == "manual" else "",
                    "source_session_key": source_session_key if ft == "automatic" else "",
                    "source_menu_key": source_menu_key if ft == "automatic" else "",
                    "source_subprocess_key": source_subprocess_key if ft == "automatic" else "",
                    "status": list_status,
                }
            )

        column_rows_count = max(
            len(process_list_column_key),
            len(process_list_column_label),
            len(process_list_column_field_key),
            len(process_list_column_source_kind),
            len(process_list_column_always_visible),
            len(process_list_column_responsive_priority),
        )
        payload_columns: list[dict[str, str]] = []

        for row_index in range(column_rows_count):
            payload_columns.append(
                {
                    "key": process_list_column_key[row_index]
                    if row_index < len(process_list_column_key)
                    else "",
                    "label": process_list_column_label[row_index]
                    if row_index < len(process_list_column_label)
                    else "",
                    "field_key": process_list_column_field_key[row_index]
                    if row_index < len(process_list_column_field_key)
                    else "",
                    "source_kind": process_list_column_source_kind[row_index]
                    if row_index < len(process_list_column_source_kind)
                    else "field",
                    "always_visible": process_list_column_always_visible[row_index]
                    if row_index < len(process_list_column_always_visible)
                    else "0",
                    "responsive_priority": process_list_column_responsive_priority[
                        row_index
                    ]
                    if row_index < len(process_list_column_responsive_priority)
                    else "0",
                }
            )

        ok, error_message = update_sidebar_menu_process_lists(
            session=session,
            menu_key=clean_menu_key,
            raw_lists=payload_lists,
            raw_columns=payload_columns
            if str(process_list_columns_configured or "").strip() == "1"
            else None,
            active_entity_id=selected_entity_id,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message
                    or "Não foi possível atualizar as listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                    return_url=return_url,
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_editor_stay_redirect_url_v1(
                success_message="Listas do processo atualizadas com sucesso.",
                redirect_menu=redirect_menu,
                settings_edit_key=clean_menu_key,
                settings_tab="lista",
                return_url=return_url,
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
