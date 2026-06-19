from pathlib import Path
import re

REGISTRY_FILE = Path("appverbo/admin_subprocesses/registry.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def ensure_menu_actions(text: str) -> str:
    if "MENU_ACTIONS = (" in text:
        text = text.replace("actions=DEFAULT_ACTIVE_ACTIONS,", "actions=MENU_ACTIONS,")
        return text

    menu_actions = '''

MENU_ACTIONS = (
    AdminActionConfig(
        key="move_up",
        label="Subir",
        icon="↑",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="move_down",
        label="Descer",
        icon="↓",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="view",
        label="Visualizar",
        icon="👁",
        action_type="button",
        visible_when=("ativo", "inativo"),
    ),
    AdminActionConfig(
        key="edit",
        label="Editar",
        icon="✎",
        action_type="link",
        visible_when=("ativo", "inativo"),
    ),
)
'''

    marker = "MENU_CONFIG = AdminSubprocessConfig("

    if marker not in text:
        raise RuntimeError("MENU_CONFIG não encontrado em registry.py")

    text = text.replace(marker, menu_actions + "\n" + marker, 1)
    text = text.replace("actions=DEFAULT_ACTIVE_ACTIONS,", "actions=MENU_ACTIONS,")

    return text


def validate_registry(text: str) -> None:
    required = [
        "MENU_FIELDS = (",
        "MENU_COLUMNS = (",
        "MENU_ACTIONS = (",
        "MENU_CONFIG = AdminSubprocessConfig(",
        'key="menu"',
        'default_target="admin-menu-card"',
        'edit_target="settings-menu-edit-card"',
        'enabled=True',
        'migration_status="state_ready"',
        "actions=MENU_ACTIONS,",
    ]

    missing = [item for item in required if item not in text]

    if missing:
        raise RuntimeError("Validação falhou em registry.py: " + " | ".join(missing))

    if "actions=DEFAULT_ACTIVE_ACTIONS," in text:
        raise RuntimeError("Ainda existe actions=DEFAULT_ACTIVE_ACTIONS em registry.py")


def main() -> None:
    text = read_text(REGISTRY_FILE)
    text = ensure_menu_actions(text)
    validate_registry(text)
    write_text(REGISTRY_FILE, text)
    print("OK: MENU_ACTIONS definido e MENU_CONFIG corrigido.")


if __name__ == "__main__":
    main()
