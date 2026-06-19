from pathlib import Path
import re

REGISTRY_FILE = Path("appverbo/admin_subprocesses/registry.py")
PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def replace_between_markers(text: str, start_marker: str, end_marker: str, replacement: str) -> tuple[str, bool]:
    start_index = text.find(start_marker)
    end_index = text.find(end_marker)

    if start_index < 0 or end_index < 0 or end_index < start_index:
        return text, False

    end_index = end_index + len(end_marker)
    return text[:start_index] + replacement + text[end_index:], True


def patch_registry() -> None:
    text = read_text(REGISTRY_FILE)

    menu_config_block = '''# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V1_START

MENU_FIELDS = (
    AdminFieldConfig(
        key="label",
        label="Nome do menu",
        input_name="menu_label",
        field_type="text",
        required=True,
        max_length=80,
        placeholder="Informe o nome do menu",
    ),
    AdminFieldConfig(
        key="visibility_scope_mode",
        label="Sistema",
        input_name="menu_visibility_scope",
        field_type="select",
        required=True,
        options=(
            ("all", "Owner e Legado"),
            ("owner", "Owner"),
            ("legado", "Legado"),
        ),
    ),
    AdminFieldConfig(
        key="sidebar_section",
        label="Sessão",
        input_name="menu_sidebar_section",
        field_type="text",
        required=False,
        max_length=80,
        placeholder="Exemplo: igreja",
    ),
    AdminFieldConfig(
        key="status",
        label="Estado",
        input_name="menu_status",
        field_type="select",
        required=True,
        options=(
            ("ativo", "Ativo"),
            ("inativo", "Inativo"),
        ),
    ),
)


MENU_COLUMNS = (
    AdminColumnConfig(key="label", label="MENU", source="label"),
    AdminColumnConfig(key="section", label="SESSÃO", source="sidebar_section_label"),
    AdminColumnConfig(key="system", label="SISTEMA", source="visibility_scope_label"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
)


MENU_CONFIG = AdminSubprocessConfig(
    key="menu",
    label="Menu",
    singular_label="Menu",
    plural_label="Menus",
    edit_param="settings_edit_key",
    default_target="admin-menu-card",
    edit_target="settings-menu-edit-card",
    create_title="Criar menu",
    edit_title="Editar menu",
    active_title="Menus ativos",
    inactive_title="Menus inativos",
    create_endpoint="/settings/menu/create",
    update_endpoint="/settings/menu/edit",
    save_endpoint="/settings/menu/edit",
    move_endpoint="/settings/menu/move",
    repository_name="menu",
    repository_class="",
    status_field="status",
    active_value="ativo",
    inactive_value="inativo",
    identity_field="key",
    label_field="label",
    mode_field="settings_action",
    edit_key_field="menu_key",
    return_url_field="menu_return_url",
    create_mode_value="create",
    edit_mode_value="edit",
    enabled=True,
    migration_status="state_ready",
    fields=MENU_FIELDS,
    columns=MENU_COLUMNS,
    actions=DEFAULT_ACTIVE_ACTIONS,
)

# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V1_END'''

    start_marker = "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V1_START"
    end_marker = "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V1_END"

    text, replaced_marked_block = replace_between_markers(
        text,
        start_marker,
        end_marker,
        menu_config_block,
    )

    if not replaced_marked_block:
        start = text.find("MENU_CONFIG = AdminSubprocessConfig(")
        end = text.find("\n\n\nCONTAS_CONFIG =", start)

        if start < 0 or end < 0:
            raise RuntimeError("Não foi possível localizar bloco MENU_CONFIG em registry.py")

        text = text[:start] + menu_config_block + text[end:]

    write_text(REGISTRY_FILE, text)


def ensure_menu_helpers(text: str) -> str:
    marker = "APPVERBO_ADMIN_MENU_STATE_HELPERS_V1_START"

    if marker in text:
        return text

    helper_block = '''

# APPVERBO_ADMIN_MENU_STATE_HELPERS_V1_START

def _normalize_admin_menu_status_v1(raw_status: object, raw_is_active: object = None) -> str:
    if raw_is_active is False:
        return "inativo"

    clean_status = str(raw_status or "").strip().lower()

    if clean_status in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def _normalize_admin_menu_status_label_v1(raw_status: object, raw_is_active: object = None) -> str:
    return "Inativo" if _normalize_admin_menu_status_v1(raw_status, raw_is_active) == "inativo" else "Ativo"


def _normalize_admin_menu_scope_label_v1(row: dict[str, Any]) -> str:
    for key in (
        "visibility_scope_label",
        "menu_visibility_scope_label",
        "scope_label",
        "system_label",
    ):
        value = str(row.get(key) or "").strip()
        if value:
            return value

    raw_config = row.get("menu_config")
    if isinstance(raw_config, dict):
        raw_scope = str(
            raw_config.get("visibility_scope_mode")
            or raw_config.get("scope_mode")
            or raw_config.get("scope")
            or ""
        ).strip().lower()
    else:
        raw_scope = str(
            row.get("visibility_scope_mode")
            or row.get("menu_visibility_scope")
            or row.get("scope")
            or ""
        ).strip().lower()

    if raw_scope == "owner":
        return "Owner"

    if raw_scope == "legado":
        return "Legado"

    return "Owner e Legado"


def _normalize_admin_menu_section_label_v1(row: dict[str, Any]) -> str:
    for key in (
        "sidebar_section_label",
        "section_label",
        "menu_section_label",
        "section",
    ):
        value = str(row.get(key) or "").strip()
        if value:
            return value

    raw_config = row.get("menu_config")
    if isinstance(raw_config, dict):
        value = str(
            raw_config.get("sidebar_section_label")
            or raw_config.get("sidebar_section")
            or raw_config.get("section_label")
            or ""
        ).strip()
        if value:
            return value

    value = str(
        row.get("sidebar_section")
        or row.get("menu_sidebar_section")
        or ""
    ).strip()

    return value or "-"


def _normalize_admin_menu_rows_v1(raw_rows: object) -> list[dict[str, Any]]:
    if not isinstance(raw_rows, list):
        return []

    normalized_rows: list[dict[str, Any]] = []

    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            continue

        row = dict(raw_row)
        menu_key = str(row.get("key") or row.get("menu_key") or "").strip().lower()
        menu_label = str(row.get("label") or row.get("menu_label") or menu_key).strip()

        if not menu_key:
            continue

        raw_is_active = row.get("is_active", row.get("is_visible", row.get("visible")))
        raw_status = row.get("status", row.get("menu_status", raw_is_active))
        normalized_status = _normalize_admin_menu_status_v1(raw_status, raw_is_active)

        row["key"] = menu_key
        row["label"] = menu_label or menu_key
        row["status"] = normalized_status
        row["status_label"] = _normalize_admin_menu_status_label_v1(raw_status, raw_is_active)
        row["is_active"] = normalized_status == "ativo"
        row["visibility_scope_label"] = _normalize_admin_menu_scope_label_v1(row)
        row["sidebar_section_label"] = _normalize_admin_menu_section_label_v1(row)

        normalized_rows.append(row)

    return normalized_rows

# APPVERBO_ADMIN_MENU_STATE_HELPERS_V1_END
'''

    anchor = "\n\n@router.get(\"/users/new\", response_class=HTMLResponse)\n"

    if anchor not in text:
        raise RuntimeError("Anchor da rota /users/new não encontrado em page_handler.py")

    return text.replace(anchor, helper_block + anchor, 1)


def ensure_menu_state_block(text: str) -> str:
    marker = "APPVERBO_ADMIN_MENU_SUBPROCESS_STATE_V1_START"

    if marker in text:
        return text

    state_block = '''    # APPVERBO_ADMIN_MENU_SUBPROCESS_STATE_V1_START
    admin_menu_state_v1 = None

    if resolved_admin_tab == "menu":
        menu_subprocess_config_v1 = get_admin_subprocess_config("menu")

        if menu_subprocess_config_v1 is not None:
            admin_menu_rows_v1 = _normalize_admin_menu_rows_v1(
                page_data.get("sidebar_menu_settings", [])
            )

            admin_menu_state_v1 = build_admin_subprocess_state(
                config=menu_subprocess_config_v1,
                rows=admin_menu_rows_v1,
                edit_key=clean_settings_edit_key,
                success=settings_success if resolved_admin_tab == "menu" else "",
                error=settings_error if resolved_admin_tab == "menu" else "",
                return_url="/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card",
            )
    # APPVERBO_ADMIN_MENU_SUBPROCESS_STATE_V1_END

'''

    anchor = "    context = {\n"

    if anchor not in text:
        raise RuntimeError("Anchor do context não encontrado em page_handler.py")

    return text.replace(anchor, state_block + anchor, 1)


def ensure_context_entry(text: str) -> str:
    if '"admin_menu_state": admin_menu_state_v1,' in text:
        return text

    anchor = '        "admin_subprocess_state": admin_subprocess_state_v2,\n'

    if anchor not in text:
        raise RuntimeError("Anchor admin_subprocess_state não encontrado no context em page_handler.py")

    replacement = anchor + '        "admin_menu_state": admin_menu_state_v1,\n'

    return text.replace(anchor, replacement, 1)


def ensure_menu_target(text: str) -> str:
    text = text.replace(
        '''        if resolved_admin_tab in {"menu", "contas", "definicoes"}:
            return "#admin-account-status-card", ""
''',
        '''        if resolved_admin_tab in {"menu", "contas", "definicoes"}:
            return "#admin-menu-card", ""
''',
        1,
    )

    text = text.replace(
        '''        if resolved_admin_tab == "menu":
            return "#admin-account-status-card", ""
''',
        '''        if resolved_admin_tab == "menu":
            return "#admin-menu-card", ""
''',
        1,
    )

    return text


def patch_page_handler() -> None:
    text = read_text(PAGE_HANDLER)
    text = ensure_menu_helpers(text)
    text = ensure_menu_state_block(text)
    text = ensure_context_entry(text)
    text = ensure_menu_target(text)
    write_text(PAGE_HANDLER, text)


def validate_files() -> None:
    registry_text = read_text(REGISTRY_FILE)
    page_text = read_text(PAGE_HANDLER)

    required_registry_snippets = [
        "APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V1_START",
        "MENU_FIELDS = (",
        "MENU_COLUMNS = (",
        'key="menu"',
        'default_target="admin-menu-card"',
        'edit_target="settings-menu-edit-card"',
        'enabled=True',
        'migration_status="state_ready"',
    ]

    required_page_snippets = [
        "APPVERBO_ADMIN_MENU_STATE_HELPERS_V1_START",
        "def _normalize_admin_menu_rows_v1",
        "APPVERBO_ADMIN_MENU_SUBPROCESS_STATE_V1_START",
        'menu_subprocess_config_v1 = get_admin_subprocess_config("menu")',
        "admin_menu_state_v1 = build_admin_subprocess_state(",
        '"admin_menu_state": admin_menu_state_v1,',
        'return_url="/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card"',
    ]

    missing_registry = [snippet for snippet in required_registry_snippets if snippet not in registry_text]
    missing_page = [snippet for snippet in required_page_snippets if snippet not in page_text]

    if missing_registry:
        raise RuntimeError("Validação falhou em registry.py: " + " | ".join(missing_registry))

    if missing_page:
        raise RuntimeError("Validação falhou em page_handler.py: " + " | ".join(missing_page))


def main() -> None:
    patch_registry()
    patch_page_handler()
    validate_files()
    print("OK: admin_menu_state v1 criado e configuração do subprocesso Menu preparada.")


if __name__ == "__main__":
    main()
