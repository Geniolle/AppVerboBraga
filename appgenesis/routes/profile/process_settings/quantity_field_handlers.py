from fastapi import Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appgenesis.routes.profile.router import router

from appgenesis.menu_settings import (
    resolve_menu_key_alias,
    update_sidebar_menu_process_quantity_fields_v1,
)
from appgenesis.core import SessionLocal

from appgenesis.routes.profile.process_settings.common import (
    _build_settings_redirect_url,
    _build_settings_editor_stay_redirect_url_v1,
    _require_menu_settings_owner_v1,
)


@router.post("/settings/menu/process-quantity-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_quantity_fields_handler(
    request: Request,
    menu_key: str = Form(...),
    quantity_rule_key: list[str] = Form(default=[]),
    quantity_rule_label: list[str] = Form(default=[]),
    quantity_field_key: list[str] = Form(default=[]),
    quantity_repeated_field_keys_json: list[str] = Form(default=[]),
    quantity_header_key: list[str] = Form(default=[]),
    quantity_max_items: list[str] = Form(default=[]),
    quantity_item_label: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
    return_url: str = Form(""),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
            settings_edit_key=clean_menu_key,
            settings_action="edit",
            settings_tab="campos-quantidade",
            return_url=return_url,
        )
        if blocked_response is not None:
            return blocked_response

        rows_count = max(
            len(quantity_rule_key),
            len(quantity_rule_label),
            len(quantity_field_key),
            len(quantity_repeated_field_keys_json),
            len(quantity_header_key),
            len(quantity_max_items),
            len(quantity_item_label),
        )

        payload_rules: list[dict[str, str]] = []
        for row_index in range(rows_count):
            payload_rules.append(
                {
                    "key": quantity_rule_key[row_index]
                    if row_index < len(quantity_rule_key)
                    else "",
                    "label": quantity_rule_label[row_index]
                    if row_index < len(quantity_rule_label)
                    else "",
                    "quantity_field_key": quantity_field_key[row_index]
                    if row_index < len(quantity_field_key)
                    else "",
                    "repeated_field_keys": (
                        quantity_repeated_field_keys_json[row_index]
                        if row_index < len(quantity_repeated_field_keys_json)
                        else ""
                    ),
                    "header_key": quantity_header_key[row_index]
                    if row_index < len(quantity_header_key)
                    else "",
                    "max_items": quantity_max_items[row_index]
                    if row_index < len(quantity_max_items)
                    else "",
                    "item_label": quantity_item_label[row_index]
                    if row_index < len(quantity_item_label)
                    else "",
                }
            )

        ok, error_message = update_sidebar_menu_process_quantity_fields_v1(
            session=session,
            menu_key=clean_menu_key,
            raw_fields=payload_rules,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message
                    or "Não foi possível atualizar os Campos Quantidade.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-quantidade",
                    return_url=return_url,
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campos Quantidade atualizados com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                return_url=return_url,
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
