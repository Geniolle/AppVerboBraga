from pathlib import Path
import re

REGISTRY_FILE = Path("appverbo/admin_subprocesses/registry.py")
PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")


MENU_BLOCK = '''# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V4_START

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

# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V4_END'''


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def ensure_model_imports(text: str) -> str:
    required_import = (
        "from .models import AdminActionConfig, AdminColumnConfig, "
        "AdminFieldConfig, AdminSubprocessConfig"
    )

    required_names = [
        "AdminActionConfig",
        "AdminColumnConfig",
        "AdminFieldConfig",
        "AdminSubprocessConfig",
    ]

    if all(name in text for name in required_names):
        return text

    future_match = re.search(r"(?m)^from __future__ import annotations\s*$", text)

    if future_match:
        insert_at = future_match.end()
        return text[:insert_at] + "\n\n" + required_import + text[insert_at:]

    return required_import + "\n\n" + text


def remove_marked_blocks(text: str) -> str:
    marker_versions = ("V1", "V2", "V3", "V4")

    for version in marker_versions:
        start_marker = f"# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_{version}_START"
        end_marker = f"# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_{version}_END"

        start = text.find(start_marker)
        end = text.find(end_marker)

        if start >= 0 and end >= start:
            end = end + len(end_marker)
            text = text[:start] + text[end:]

    return text


def remove_tuple_assignment(text: str, assignment_name: str) -> str:
    pattern = rf"(?ms)^\s*{assignment_name}\s*=\s*\(.*?\n\)\s*\n*"
    return re.sub(pattern, "", text, count=1)


def find_admin_subprocess_assignment(text: str, assignment_name: str) -> tuple[int, int] | None:
    match = re.search(rf"(?m)^{assignment_name}\s*=\s*AdminSubprocessConfig\s*\(", text)

    if not match:
        return None

    start = match.start()
    open_paren = text.find("(", match.start())

    if open_paren < 0:
        return None

    depth = 0
    in_string = False
    quote = ""
    escape = False

    for index in range(open_paren, len(text)):
        char = text[index]

        if in_string:
            if escape:
                escape = False
                continue

            if char == "\\":
                escape = True
                continue

            if char == quote:
                in_string = False
                quote = ""

            continue

        if char in ("'", '"'):
            in_string = True
            quote = char
            continue

        if char == "(":
            depth += 1
            continue

        if char == ")":
            depth -= 1

            if depth == 0:
                end = index + 1

                while end < len(text) and text[end] in " \t\r\n":
                    end += 1

                return start, end

    return None


def remove_existing_menu_config(text: str) -> str:
    text = remove_marked_blocks(text)
    text = remove_tuple_assignment(text, "MENU_FIELDS")
    text = remove_tuple_assignment(text, "MENU_COLUMNS")

    block = find_admin_subprocess_assignment(text, "MENU_CONFIG")

    if block:
        start, end = block
        text = text[:start] + text[end:]

    return text


def insert_menu_block(text: str) -> str:
    registry_match = re.search(r"(?m)^ADMIN_SUBPROCESS_REGISTRY\s*=\s*\{", text)

    if not registry_match:
        raise RuntimeError("ADMIN_SUBPROCESS_REGISTRY não encontrado em registry.py")

    insert_at = registry_match.start()
    return text[:insert_at] + MENU_BLOCK + "\n\n\n" + text[insert_at:]


def ensure_menu_registry_entry(text: str) -> str:
    if "MENU_CONFIG.key: MENU_CONFIG" in text:
        return text

    registry_match = re.search(r"(?m)^ADMIN_SUBPROCESS_REGISTRY\s*=\s*\{", text)

    if not registry_match:
        raise RuntimeError("ADMIN_SUBPROCESS_REGISTRY não encontrado para inserir MENU_CONFIG.")

    line_end = text.find("\n", registry_match.end())

    if line_end < 0:
        raise RuntimeError("Não foi possível inserir MENU_CONFIG no registry.")

    return text[:line_end + 1] + "    MENU_CONFIG.key: MENU_CONFIG,\n" + text[line_end + 1:]


def patch_registry() -> None:
    text = read_text(REGISTRY_FILE)
    text = ensure_model_imports(text)
    text = remove_existing_menu_config(text)
    text = insert_menu_block(text)
    text = ensure_menu_registry_entry(text)
    write_text(REGISTRY_FILE, text)


def validate_page_handler() -> None:
    text = read_text(PAGE_HANDLER)

    has_menu_state = (
        (
            "build_admin_menu_state" in text
            and "admin_menu_state = build_admin_menu_state(" in text
            and '"admin_menu_state": admin_menu_state' in text
        )
        or
        (
            "admin_menu_state_v1 = build_admin_subprocess_state(" in text
            and '"admin_menu_state": admin_menu_state_v1' in text
        )
    )

    if not has_menu_state:
        raise RuntimeError("admin_menu_state não encontrado em page_handler.py")


def validate_registry() -> None:
    text = read_text(REGISTRY_FILE)

    required = [
        "AdminActionConfig",
        "AdminColumnConfig",
        "AdminFieldConfig",
        "AdminSubprocessConfig",
        "APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V4_START",
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
    print("OK: registry.py corrigido com imports, MENU_FIELDS, MENU_COLUMNS e MENU_CONFIG state_ready.")


if __name__ == "__main__":
    main()
