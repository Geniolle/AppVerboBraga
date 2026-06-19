from pathlib import Path
import re

REGISTRY_FILE = Path("appverbo/admin_subprocesses/registry.py")
PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


MENU_BLOCK = '''# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V3_START

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

# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V3_END'''


def find_assignment_block(text: str, assignment_name: str) -> tuple[int, int] | None:
    match = re.search(rf"(?m)^{assignment_name}\s*=\s*AdminSubprocessConfig\s*\(", text)

    if not match:
        return None

    start_index = match.start()
    open_paren_index = text.find("(", match.start())

    if open_paren_index < 0:
        return None

    depth = 0
    in_string = False
    string_quote = ""
    escape_next = False

    for index in range(open_paren_index, len(text)):
        char = text[index]

        if in_string:
            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == string_quote:
                in_string = False
                string_quote = ""

            continue

        if char in {'"', "'"}:
            in_string = True
            string_quote = char
            continue

        if char == "(":
            depth += 1
            continue

        if char == ")":
            depth -= 1

            if depth == 0:
                end_index = index + 1

                while end_index < len(text) and text[end_index] in " \t":
                    end_index += 1

                if end_index < len(text) and text[end_index] == "\r":
                    end_index += 1

                if end_index < len(text) and text[end_index] == "\n":
                    end_index += 1

                return start_index, end_index

    return None


def remove_existing_menu_blocks(text: str) -> str:
    marker_patterns = [
        (
            "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V1_START",
            "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V1_END",
        ),
        (
            "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V2_START",
            "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V2_END",
        ),
        (
            "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V3_START",
            "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V3_END",
        ),
    ]

    for start_marker, end_marker in marker_patterns:
        start_index = text.find(start_marker)
        end_index = text.find(end_marker)

        if start_index >= 0 and end_index >= start_index:
            end_index = end_index + len(end_marker)
            text = text[:start_index] + text[end_index:]

    # Remove MENU_FIELDS e MENU_COLUMNS antigos, se existirem isolados.
    for assignment_name in ("MENU_FIELDS", "MENU_COLUMNS"):
        pattern = rf"(?ms)^\s*{assignment_name}\s*=\s*\(.*?\n\)\s*\n+"
        text = re.sub(pattern, "", text, count=1)

    block = find_assignment_block(text, "MENU_CONFIG")

    if block:
        start_index, end_index = block
        text = text[:start_index] + text[end_index:]

    return text


def insert_menu_block_before_registry(text: str) -> str:
    registry_match = re.search(r"(?m)^ADMIN_SUBPROCESS_REGISTRY\s*=\s*\{", text)

    if registry_match:
        insert_index = registry_match.start()
        return text[:insert_index] + MENU_BLOCK + "\n\n\n" + text[insert_index:]

    # Fallback: inserir antes da primeira função pública do registry.
    function_match = re.search(r"(?m)^def\s+get_admin_subprocess_config\s*\(", text)

    if function_match:
        insert_index = function_match.start()
        return text[:insert_index] + MENU_BLOCK + "\n\n\n" + text[insert_index:]

    raise RuntimeError("Não foi possível localizar ADMIN_SUBPROCESS_REGISTRY nem get_admin_subprocess_config em registry.py")


def ensure_menu_registered(text: str) -> str:
    if "ADMIN_SUBPROCESS_REGISTRY" not in text:
        raise RuntimeError("ADMIN_SUBPROCESS_REGISTRY não encontrado em registry.py")

    if "MENU_CONFIG.key: MENU_CONFIG" in text:
        return text

    registry_match = re.search(r"(?m)^ADMIN_SUBPROCESS_REGISTRY\s*=\s*\{", text)

    if not registry_match:
        raise RuntimeError("Bloco ADMIN_SUBPROCESS_REGISTRY não localizado para registar MENU_CONFIG.")

    line_end = text.find("\n", registry_match.end())

    if line_end < 0:
        raise RuntimeError("Não foi possível inserir MENU_CONFIG no registry.")

    return text[:line_end + 1] + "    MENU_CONFIG.key: MENU_CONFIG,\n" + text[line_end + 1:]


def ensure_imports(text: str) -> str:
    required_names = (
        "AdminActionConfig",
        "AdminColumnConfig",
        "AdminFieldConfig",
        "AdminSubprocessConfig",
    )

    missing = [
        name
        for name in required_names
        if name not in text
    ]

    if not missing:
        return text

    raise RuntimeError(
        "registry.py não possui imports esperados de models.py: " + ", ".join(missing)
    )


def patch_registry() -> None:
    text = read_text(REGISTRY_FILE)
    text = ensure_imports(text)
    text = remove_existing_menu_blocks(text)
    text = insert_menu_block_before_registry(text)
    text = ensure_menu_registered(text)
    write_text(REGISTRY_FILE, text)


def validate_page_handler() -> None:
    text = read_text(PAGE_HANDLER)

    has_current_menu_state = (
        "build_admin_menu_state" in text
        and "admin_menu_state = build_admin_menu_state(" in text
        and '"admin_menu_state": admin_menu_state' in text
    )

    has_legacy_menu_state = (
        "admin_menu_state_v1 = build_admin_subprocess_state(" in text
        and '"admin_menu_state": admin_menu_state_v1' in text
    )

    if not has_current_menu_state and not has_legacy_menu_state:
        raise RuntimeError("admin_menu_state não encontrado em page_handler.py")


def validate_registry() -> None:
    text = read_text(REGISTRY_FILE)

    required = [
        "APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V3_START",
        "MENU_FIELDS = (",
        "MENU_COLUMNS = (",
        "MENU_CONFIG = AdminSubprocessConfig(",
        'key="menu"',
        'default_target="admin-menu-card"',
        'edit_target="settings-menu-edit-card"',
        'enabled=True',
        'migration_status="state_ready"',
        "MENU_CONFIG.key: MENU_CONFIG",
    ]

    missing = [item for item in required if item not in text]

    if missing:
        raise RuntimeError("Validação falhou em registry.py: " + " | ".join(missing))


def main() -> None:
    patch_registry()
    validate_registry()
    validate_page_handler()
    print("OK: registry.py corrigido com MENU_FIELDS, MENU_COLUMNS e MENU_CONFIG state_ready.")


if __name__ == "__main__":
    main()
