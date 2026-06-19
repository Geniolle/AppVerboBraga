from pathlib import Path

REGISTRY_FILE = Path("appverbo/admin_subprocesses/registry.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def patch_registry() -> None:
    text = read_text(REGISTRY_FILE)

    text = text.replace(
        "from appverbo.admin_subprocesses.menu.config import MENU_CONFIG\n",
        "",
    )
    text = text.replace(
        "from appverbo.admin_subprocesses.menu.config import MENU_CONFIG\r\n",
        "",
    )

    text = text.replace("actions=DEFAULT_ACTIVE_ACTIONS,", "actions=MENU_ACTIONS,")

    if "MENU_ACTIONS = (" not in text:
        marker = "MENU_CONFIG = AdminSubprocessConfig("

        if marker not in text:
            raise RuntimeError("MENU_CONFIG não encontrado para inserir MENU_ACTIONS.")

        menu_actions = '''

MENU_ACTIONS = (
    AdminActionConfig(
        key="move_up",
        label="Subir",
        icon="up",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="move_down",
        label="Descer",
        icon="down",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="view",
        label="Visualizar",
        icon="view",
        action_type="button",
        visible_when=("ativo", "inativo"),
    ),
    AdminActionConfig(
        key="edit",
        label="Editar",
        icon="edit",
        action_type="link",
        visible_when=("ativo", "inativo"),
    ),
)
'''

        text = text.replace(marker, menu_actions + "\n" + marker, 1)

    required = [
        "MENU_FIELDS = (",
        "MENU_COLUMNS = (",
        "MENU_ACTIONS = (",
        "MENU_CONFIG = AdminSubprocessConfig(",
        "actions=MENU_ACTIONS,",
        'migration_status="state_ready"',
        "MENU_CONFIG.key: MENU_CONFIG",
    ]

    missing = [item for item in required if item not in text]

    if missing:
        raise RuntimeError("registry.py incompleto: " + " | ".join(missing))

    if "from appverbo.admin_subprocesses.menu.config import MENU_CONFIG" in text:
        raise RuntimeError("Import antigo de MENU_CONFIG ainda existe no registry.py.")

    if "actions=DEFAULT_ACTIVE_ACTIONS," in text:
        raise RuntimeError("actions=DEFAULT_ACTIVE_ACTIONS ainda existe no registry.py.")

    write_text(REGISTRY_FILE, text)


def main() -> None:
    patch_registry()
    print("OK: registry.py corrigido. Import antigo removido e MENU_ACTIONS garantido.")


if __name__ == "__main__":
    main()
