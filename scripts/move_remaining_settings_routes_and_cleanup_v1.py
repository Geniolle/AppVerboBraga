from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

SETTINGS_HANDLERS_PATH = Path("appverbo/routes/profile/settings_handlers.py")
SETTINGS_PACKAGE_DIR = Path("appverbo/routes/profile/settings")
SIDEBAR_HANDLERS_PATH = SETTINGS_PACKAGE_DIR / "sidebar_sections_handlers.py"
MENU_CRUD_HANDLERS_PATH = SETTINGS_PACKAGE_DIR / "menu_crud_handlers.py"

AGGREGATOR_START = "# APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_START"
AGGREGATOR_END = "# APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_END"

ROUTES_TO_MOVE = {
    "/settings/menu/sidebar-section-delete-one": SIDEBAR_HANDLERS_PATH,
    "/settings/menu/admin-create": MENU_CRUD_HANDLERS_PATH,
    "/settings/menu/admin-move": MENU_CRUD_HANDLERS_PATH,
    "/settings/menu/admin-delete": MENU_CRUD_HANDLERS_PATH,
}


####################################################################################
# (2) FUNÇÕES AUXILIARES
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Ficheiro obrigatório não encontrado: {path}")


def find_route_decorator_start_v1(content: str, route_path: str) -> int:
    patterns = [
        rf'(?m)^@router\.(?:get|post|put|patch|delete)\("{re.escape(route_path)}"',
        rf"(?m)^@router\.(?:get|post|put|patch|delete)\('{re.escape(route_path)}'",
    ]

    positions = []

    for pattern in patterns:
        match = re.search(pattern, content)

        if match:
            positions.append(match.start())

    return min(positions) if positions else -1


def include_heading_before_decorator_v1(content: str, decorator_start: int) -> int:
    line_start = content.rfind("\n", 0, decorator_start)

    if line_start < 0:
        line_start = 0
    else:
        line_start += 1

    prefix = content[:line_start]
    lines = prefix.splitlines(keepends=True)

    collected_length = 0
    index = len(lines) - 1

    while index >= 0:
        clean_line = lines[index].strip()

        if not clean_line:
            collected_length += len(lines[index])
            index -= 1
            continue

        if clean_line.startswith("#"):
            collected_length += len(lines[index])
            index -= 1
            continue

        break

    return max(0, line_start - collected_length)


def find_endpoint_end_v1(content: str, decorator_start: int) -> int:
    def_match = re.search(r"(?m)^def\s+\w+\s*\(", content[decorator_start:])

    if not def_match:
        raise RuntimeError("Não foi possível encontrar def após decorator.")

    search_start = decorator_start + def_match.end()

    next_pattern = re.compile(
        r"(?m)^(?=@router\.|def\s+|# APPVERBO_|# ###################################################################################)",
    )

    next_match = next_pattern.search(content, search_start)

    if next_match:
        return next_match.start()

    return len(content)


def extract_endpoint_by_route_v1(content: str, route_path: str) -> tuple[str, str, bool]:
    decorator_start = find_route_decorator_start_v1(content, route_path)

    if decorator_start < 0:
        return "", content, False

    block_start = include_heading_before_decorator_v1(content, decorator_start)
    block_end = find_endpoint_end_v1(content, decorator_start)

    block = content[block_start:block_end].strip()
    updated_content = content[:block_start].rstrip() + "\n\n" + content[block_end:].lstrip()

    return block, updated_content, True


def ensure_import_line_v1(content: str, import_line: str) -> str:
    if import_line in content:
        return content

    lines = content.splitlines()
    insert_index = 0

    for index, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_index = index + 1

    lines.insert(insert_index, import_line)

    return "\n".join(lines).rstrip() + "\n"


def append_moved_blocks_v1(destination_path: Path, blocks: list[str], marker_name: str) -> None:
    if not blocks:
        return

    content = read_text_v1(destination_path)

    start_marker = f"# APPVERBO_REMAINING_ROUTES_{marker_name}_V1_START"
    end_marker = f"# APPVERBO_REMAINING_ROUTES_{marker_name}_V1_END"

    if start_marker in content and end_marker in content:
        print(f"INFO: bloco {marker_name} já existe em {destination_path}.")
        return

    block_content = (
        f"\n\n{start_marker}\n\n"
        + "\n\n\n".join(blocks).strip()
        + f"\n\n{end_marker}\n"
    )

    write_text_v1(destination_path, content.rstrip() + block_content)


def find_router_decorators_v1(content: str) -> list[tuple[int, str]]:
    decorators = []

    for match in re.finditer(
        r"(?m)^\s*@router\.(?:get|post|put|patch|delete)\(",
        content,
    ):
        line_number = content.count("\n", 0, match.start()) + 1
        line_text = content.splitlines()[line_number - 1].strip()
        decorators.append((line_number, line_text))

    return decorators


####################################################################################
# (3) MOVER ROTAS RESTANTES
####################################################################################

def move_remaining_routes_v1() -> None:
    require_file_v1(SETTINGS_HANDLERS_PATH)
    require_file_v1(SIDEBAR_HANDLERS_PATH)
    require_file_v1(MENU_CRUD_HANDLERS_PATH)

    settings_content = read_text_v1(SETTINGS_HANDLERS_PATH)

    moved_by_destination: dict[Path, list[str]] = {
        SIDEBAR_HANDLERS_PATH: [],
        MENU_CRUD_HANDLERS_PATH: [],
    }

    found_routes: list[str] = []

    for route_path, destination_path in ROUTES_TO_MOVE.items():
        block, settings_content, found = extract_endpoint_by_route_v1(
            settings_content,
            route_path,
        )

        if found:
            moved_by_destination[destination_path].append(block)
            found_routes.append(route_path)

    if not found_routes:
        remaining_routes = find_router_decorators_v1(settings_content)

        if remaining_routes:
            formatted_routes = "; ".join(
                f"linha {line_number}: {line_text}"
                for line_number, line_text in remaining_routes
            )
            raise RuntimeError(
                "Não encontrei as rotas esperadas para mover, mas ainda existem rotas: "
                + formatted_routes
            )

        print("INFO: nenhuma rota restante encontrada. Pode já ter sido movido.")
        write_text_v1(SETTINGS_HANDLERS_PATH, settings_content)
        return

    append_moved_blocks_v1(
        SIDEBAR_HANDLERS_PATH,
        moved_by_destination[SIDEBAR_HANDLERS_PATH],
        "SIDEBAR_SECTIONS",
    )

    append_moved_blocks_v1(
        MENU_CRUD_HANDLERS_PATH,
        moved_by_destination[MENU_CRUD_HANDLERS_PATH],
        "MENU_CRUD_ADMIN",
    )

    write_text_v1(SETTINGS_HANDLERS_PATH, settings_content)

    print("OK: rotas movidas: " + ", ".join(found_routes))


####################################################################################
# (4) GARANTIR IMPORTS NECESSÁRIOS NOS DESTINOS
####################################################################################

def patch_destination_imports_v1() -> None:
    sidebar_content = read_text_v1(SIDEBAR_HANDLERS_PATH)
    menu_crud_content = read_text_v1(MENU_CRUD_HANDLERS_PATH)

    sidebar_content = ensure_import_line_v1(
        sidebar_content,
        "from appverbo.menu_settings import *  # noqa: F403,F401",
    )

    menu_crud_content = ensure_import_line_v1(
        menu_crud_content,
        "from appverbo.menu_settings import *  # noqa: F403,F401",
    )

    write_text_v1(SIDEBAR_HANDLERS_PATH, sidebar_content)
    write_text_v1(MENU_CRUD_HANDLERS_PATH, menu_crud_content)


####################################################################################
# (5) GERAR AGREGADOR LIMPO
####################################################################################

def build_aggregator_content_v1() -> str:
    imports = [
        (
            "from appverbo.routes.profile.settings import "
            "sidebar_sections_handlers as sidebar_sections_handlers_v1  # noqa: F401"
        ),
        (
            "from appverbo.routes.profile.settings import "
            "menu_crud_handlers as menu_crud_handlers_v1  # noqa: F401"
        ),
        (
            "from appverbo.routes.profile.settings import "
            "additional_fields_handlers as additional_fields_handlers_v1  # noqa: F401"
        ),
        (
            "from appverbo.routes.profile.settings import "
            "process_fields_handlers as process_fields_handlers_v1  # noqa: F401"
        ),
        (
            "from appverbo.routes.profile.settings import "
            "process_lists_handlers as process_lists_handlers_v1  # noqa: F401"
        ),
        (
            "from appverbo.routes.profile.settings import "
            "process_quantity_handlers as process_quantity_handlers_v1  # noqa: F401"
        ),
        (
            "from appverbo.routes.profile.settings import "
            "subsequent_fields_handlers as subsequent_fields_handlers_v1  # noqa: F401"
        ),
    ]

    all_names = [
        "sidebar_sections_handlers_v1",
        "menu_crud_handlers_v1",
        "additional_fields_handlers_v1",
        "process_fields_handlers_v1",
        "process_lists_handlers_v1",
        "process_quantity_handlers_v1",
        "subsequent_fields_handlers_v1",
        "_build_settings_redirect_url",
        "_require_menu_settings_owner_v1",
    ]

    all_block = ",\n".join(f'    "{name}"' for name in all_names)

    return f'''from __future__ import annotations

{AGGREGATOR_START}

####################################################################################
# (1) AGREGADOR DOS SUBPROCESSOS DE CONFIGURAÇÕES DO MENU - V1
####################################################################################

# Este ficheiro mantém compatibilidade com os imports existentes do projeto.
# As rotas FastAPI são registadas ao importar os módulos de subprocesso abaixo.
# A lógica real de cada subprocesso fica em appverbo/routes/profile/settings/.

# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START
{chr(10).join(imports)}
# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_END

####################################################################################
# (2) ALIASES DE COMPATIBILIDADE
####################################################################################

from appverbo.routes.profile.settings.redirects import (  # noqa: E402
    build_settings_redirect_url_v1 as _build_settings_redirect_url,
)
from appverbo.routes.profile.settings.permissions import (  # noqa: E402
    require_menu_settings_owner_v1 as _require_menu_settings_owner_v1,
)

####################################################################################
# (3) EXPORTS
####################################################################################

__all__ = [
{all_block},
]

{AGGREGATOR_END}
'''


def cleanup_settings_handlers_v1() -> None:
    settings_content = read_text_v1(SETTINGS_HANDLERS_PATH)
    remaining_routes = find_router_decorators_v1(settings_content)

    if remaining_routes:
        formatted_routes = "; ".join(
            f"linha {line_number}: {line_text}"
            for line_number, line_text in remaining_routes
        )

        raise RuntimeError(
            "Ainda existem rotas diretamente no settings_handlers.py: "
            + formatted_routes
        )

    write_text_v1(SETTINGS_HANDLERS_PATH, build_aggregator_content_v1())


####################################################################################
# (6) VALIDAÇÃO FINAL
####################################################################################

def validate_v1() -> None:
    settings_content = read_text_v1(SETTINGS_HANDLERS_PATH)
    sidebar_content = read_text_v1(SIDEBAR_HANDLERS_PATH)
    menu_crud_content = read_text_v1(MENU_CRUD_HANDLERS_PATH)

    required_settings_markers = [
        "APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_START",
        "APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START",
        "sidebar_sections_handlers_v1",
        "menu_crud_handlers_v1",
        "additional_fields_handlers_v1",
        "process_fields_handlers_v1",
        "process_lists_handlers_v1",
        "process_quantity_handlers_v1",
        "subsequent_fields_handlers_v1",
        "_build_settings_redirect_url",
        "_require_menu_settings_owner_v1",
        "APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_END",
    ]

    missing_settings = [
        marker
        for marker in required_settings_markers
        if marker not in settings_content
    ]

    if missing_settings:
        raise RuntimeError(
            "Agregador incompleto. Marcadores ausentes: "
            + ", ".join(missing_settings)
        )

    remaining_routes = find_router_decorators_v1(settings_content)

    if remaining_routes:
        raise RuntimeError("settings_handlers.py ainda contém decorators @router.")

    if "/settings/menu/sidebar-section-delete-one" not in sidebar_content:
        raise RuntimeError("Rota sidebar-section-delete-one não encontrada em sidebar_sections_handlers.py.")

    for route in (
        "/settings/menu/admin-create",
        "/settings/menu/admin-move",
        "/settings/menu/admin-delete",
    ):
        if route not in menu_crud_content:
            raise RuntimeError(f"Rota {route} não encontrada em menu_crud_handlers.py.")

    print("OK: rotas restantes movidas para os módulos corretos.")
    print("OK: settings_handlers.py transformado em agregador limpo.")
    print("OK: nenhum decorator @router permaneceu no ficheiro antigo.")


####################################################################################
# (7) EXECUÇÃO
####################################################################################

def main() -> None:
    move_remaining_routes_v1()
    patch_destination_imports_v1()
    cleanup_settings_handlers_v1()
    validate_v1()


if __name__ == "__main__":
    main()
