from pathlib import Path
import re

REGISTRY_FILE = Path("appverbo/admin_subprocesses/registry.py")
PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def replace_marked_block(text: str, start_marker: str, end_marker: str, replacement: str) -> tuple[str, bool]:
    start_index = text.find(start_marker)
    end_index = text.find(end_marker)

    if start_index < 0 or end_index < 0 or end_index < start_index:
        return text, False

    end_index = end_index + len(end_marker)
    return text[:start_index] + replacement + text[end_index:], True


def remove_legacy_menu_config_block(text: str) -> str:
    pattern = (
        r"\n\nMENU_CONFIG\s*=\s*AdminSubprocessConfig\("
        r".*?"
        r"\n\)"
        r"(?=\n\n\nCONTAS_CONFIG\s*=|\n\nCONTAS_CONFIG\s*=|\n\n\nADMIN_SUBPROCESS_REGISTRY\s*=|\n\nADMIN_SUBPROCESS_REGISTRY\s*=)"
    )

    text, _count = re.subn(pattern, "\n\n", text, count=1, flags=re.DOTALL)
    return text


def ensure_menu_config_registry() -> None:
    text = read_text(REGISTRY_FILE)

    menu_block = '''# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V2_START

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

# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V2_END'''

    start_marker = "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V2_START"
    end_marker = "# APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V2_END"

    text, replaced = replace_marked_block(text, start_marker, end_marker, menu_block)

    if not replaced:
        text = remove_legacy_menu_config_block(text)

        insert_anchor = None

        for candidate in (
            "\n\n\nCONTAS_CONFIG =",
            "\n\nCONTAS_CONFIG =",
            "\n\n\nADMIN_SUBPROCESS_REGISTRY =",
            "\n\nADMIN_SUBPROCESS_REGISTRY =",
        ):
            if candidate in text:
                insert_anchor = candidate
                break

        if not insert_anchor:
            raise RuntimeError("Não foi possível localizar anchor para inserir MENU_CONFIG em registry.py")

        text = text.replace(insert_anchor, "\n\n" + menu_block + insert_anchor, 1)

    if "ADMIN_SUBPROCESS_REGISTRY" not in text:
        raise RuntimeError("ADMIN_SUBPROCESS_REGISTRY não encontrado em registry.py")

    if "MENU_CONFIG.key: MENU_CONFIG" not in text:
        registry_start = text.find("ADMIN_SUBPROCESS_REGISTRY = {")
        if registry_start < 0:
            raise RuntimeError("Bloco ADMIN_SUBPROCESS_REGISTRY não encontrado em registry.py")

        insert_pos = text.find("\n", registry_start)
        if insert_pos < 0:
            raise RuntimeError("Não foi possível inserir MENU_CONFIG no registry.")

        text = text[:insert_pos + 1] + "    MENU_CONFIG.key: MENU_CONFIG,\n" + text[insert_pos + 1:]

    write_text(REGISTRY_FILE, text)


def ensure_page_handler_state_is_present() -> None:
    text = read_text(PAGE_HANDLER)

    # O ambiente local já pode ter a implementação nova:
    # from appverbo.admin_subprocesses.menu.service import build_admin_menu_state
    # admin_menu_state = build_admin_menu_state(...)
    # "admin_menu_state": admin_menu_state,
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
        raise RuntimeError(
            "page_handler.py não possui admin_menu_state reconhecido. "
            "Não será aplicada alteração automática para evitar colisão com o estado local."
        )

    # Garante que o target canónico do Menu é admin-menu-card.
    text = text.replace(
        'return_url="/users/new?menu=administrativo&admin_tab=menu&target=admin-account-status-card#admin-account-status-card"',
        'return_url="/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card"',
    )

    text = text.replace(
        'return_url="/users/new?menu=administrativo&admin_tab=menu&target=settings-card#settings-card"',
        'return_url="/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card"',
    )

    write_text(PAGE_HANDLER, text)


def validate_files() -> None:
    registry_text = read_text(REGISTRY_FILE)
    page_text = read_text(PAGE_HANDLER)

    required_registry_snippets = [
        "APPVERBO_ADMIN_MENU_SUBPROCESS_CONFIG_V2_START",
        "MENU_FIELDS = (",
        "MENU_COLUMNS = (",
        'key="menu"',
        'default_target="admin-menu-card"',
        'edit_target="settings-menu-edit-card"',
        'enabled=True',
        'migration_status="state_ready"',
        "MENU_CONFIG.key: MENU_CONFIG",
    ]

    missing_registry = [
        snippet
        for snippet in required_registry_snippets
        if snippet not in registry_text
    ]

    if missing_registry:
        raise RuntimeError("Validação falhou em registry.py: " + " | ".join(missing_registry))

    has_current_menu_state = (
        "build_admin_menu_state" in page_text
        and "admin_menu_state = build_admin_menu_state(" in page_text
        and '"admin_menu_state": admin_menu_state' in page_text
    )

    has_legacy_menu_state = (
        "admin_menu_state_v1 = build_admin_subprocess_state(" in page_text
        and '"admin_menu_state": admin_menu_state_v1' in page_text
    )

    if not has_current_menu_state and not has_legacy_menu_state:
        raise RuntimeError("Validação falhou: admin_menu_state não encontrado em page_handler.py")


def main() -> None:
    ensure_menu_config_registry()
    ensure_page_handler_state_is_present()
    validate_files()
    print("OK: MENU_CONFIG v2 preparado e admin_menu_state local reconhecido.")


if __name__ == "__main__":
    main()
