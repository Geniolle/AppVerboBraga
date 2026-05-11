from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

SETTINGS_HANDLERS_PATH = Path("appverbo/routes/profile/settings_handlers.py")
SETTINGS_PACKAGE_DIR = Path("appverbo/routes/profile/settings")
PROCESS_QUANTITY_PATH = SETTINGS_PACKAGE_DIR / "process_quantity_handlers.py"

IMPORT_MARKER_START = "# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START"
IMPORT_MARKER_END = "# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_END"

MOVED_MARKER_START = "# APPVERBO_SETTINGS_HANDLERS_PROCESS_QUANTITY_MOVED_V1_START"
MOVED_MARKER_END = "# APPVERBO_SETTINGS_HANDLERS_PROCESS_QUANTITY_MOVED_V1_END"


####################################################################################
# (2) FUNÇÕES AUXILIARES
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def require_text_v1(content: str, marker: str, path: Path) -> None:
    if marker not in content:
        raise RuntimeError(f"Marcador obrigatório não encontrado em {path}: {marker}")


def replace_marker_block_v1(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )

    if not pattern.search(content):
        raise RuntimeError(f"Bloco não encontrado: {start_marker} ... {end_marker}")

    return pattern.sub(new_block.strip(), content, count=1)


def find_router_decorators_v1(content: str) -> list[re.Match[str]]:
    return list(
        re.finditer(
            r"(?m)^@router\.(?:get|post|put|patch|delete)\(",
            content,
        )
    )


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


def get_route_path_from_block_v1(block: str) -> str:
    match = re.search(
        r"""@router\.(?:get|post|put|patch|delete)\(\s*["']([^"']+)["']""",
        block,
    )

    if not match:
        return ""

    return match.group(1).strip()


def should_move_process_quantity_block_v1(block: str) -> bool:
    route_path = get_route_path_from_block_v1(block).lower()
    block_lower = block.lower()

    if "/settings/menu/" not in route_path:
        return False

    if "additional" in route_path:
        return False

    if "subsequent" in route_path:
        return False

    if "process-lists" in route_path or "process-list" in route_path:
        return False

    if "sidebar" in route_path or "section" in route_path:
        return False

    if "process-quantity" in route_path or "quantity-fields" in route_path or "quantity-field" in route_path:
        return True

    if "update_sidebar_menu_process_quantity_fields_v1" in block:
        return True

    if "update_sidebar_menu_process_quantity_fields" in block:
        return True

    if "process_quantity" in block_lower or "quantity_field" in block_lower or "quantity_fields" in block_lower:
        return True

    return False


def extract_selected_router_blocks_v1(content: str) -> tuple[list[str], str, list[str]]:
    decorators = find_router_decorators_v1(content)

    if not decorators:
        return [], content, []

    starts = [
        include_heading_before_decorator_v1(content, decorator.start())
        for decorator in decorators
    ]

    starts = sorted(set(starts))

    ranges: list[tuple[int, int]] = []

    for index, block_start in enumerate(starts):
        block_end = starts[index + 1] if index + 1 < len(starts) else len(content)
        ranges.append((block_start, block_end))

    selected_ranges: list[tuple[int, int]] = []
    selected_blocks: list[str] = []
    moved_routes: list[str] = []

    for block_start, block_end in ranges:
        block = content[block_start:block_end].strip()

        if not block:
            continue

        if should_move_process_quantity_block_v1(block):
            selected_ranges.append((block_start, block_end))
            selected_blocks.append(block)
            moved_routes.append(get_route_path_from_block_v1(block))

    updated_content = content

    for block_start, block_end in sorted(selected_ranges, reverse=True):
        updated_content = (
            updated_content[:block_start].rstrip()
            + "\n\n"
            + updated_content[block_end:].lstrip()
        )

    return selected_blocks, updated_content, moved_routes


####################################################################################
# (3) MÓDULO DE CAMPOS DE QUANTIDADE
####################################################################################

def build_process_quantity_module_v1(blocks: list[str]) -> str:
    module_header = '''from __future__ import annotations

import json

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import text
from starlette.requests import Request as RequestType
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER

from appverbo.core import SessionLocal
from appverbo.menu_settings import *  # noqa: F403,F401
from appverbo.routes.profile.router import router
from appverbo.routes.profile.settings.permissions import require_menu_settings_owner_v1
from appverbo.routes.profile.settings.redirects import build_settings_redirect_url_v1
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_current_user, get_session_entity_id


####################################################################################
# (1) ALIASES TEMPORÁRIOS PARA COMPATIBILIDADE COM O CÓDIGO MIGRADO
####################################################################################

_build_settings_redirect_url = build_settings_redirect_url_v1
_require_menu_settings_owner_v1 = require_menu_settings_owner_v1
'''

    return module_header.rstrip() + "\n\n\n" + "\n\n\n".join(blocks).strip() + "\n"


####################################################################################
# (4) REFATORAR CAMPOS DE QUANTIDADE
####################################################################################

def patch_settings_handlers_v1() -> None:
    settings_content = read_text_v1(SETTINGS_HANDLERS_PATH)

    require_text_v1(
        settings_content,
        "APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START",
        SETTINGS_HANDLERS_PATH,
    )

    already_moved = "process_quantity_handlers_v1" in settings_content

    if already_moved:
        if not PROCESS_QUANTITY_PATH.exists():
            raise RuntimeError(
                "settings_handlers.py já importa process_quantity_handlers_v1, "
                "mas o ficheiro process_quantity_handlers.py não existe."
            )

        print("INFO: Campos de Quantidade já estavam importados.")
        return

    extracted_blocks, settings_content, moved_routes = extract_selected_router_blocks_v1(
        settings_content
    )

    if not extracted_blocks:
        raise RuntimeError(
            "Nenhum endpoint de Campos de Quantidade foi encontrado para mover. "
            "Confirme se ainda existem rotas/handlers de process-quantity-fields em settings_handlers.py."
        )

    process_quantity_module = build_process_quantity_module_v1(extracted_blocks)
    write_text_v1(PROCESS_QUANTITY_PATH, process_quantity_module)

    import_block_pattern = re.compile(
        re.escape(IMPORT_MARKER_START) + r".*?" + re.escape(IMPORT_MARKER_END),
        flags=re.DOTALL,
    )

    import_match = import_block_pattern.search(settings_content)

    if not import_match:
        raise RuntimeError("Bloco de imports dos subprocessos não encontrado.")

    current_import_block = import_match.group(0)

    process_quantity_import_line = (
        "from appverbo.routes.profile.settings import "
        "process_quantity_handlers as process_quantity_handlers_v1  # noqa: F401"
    )

    if process_quantity_import_line not in current_import_block:
        updated_import_block = current_import_block.replace(
            IMPORT_MARKER_END,
            process_quantity_import_line + "\n" + IMPORT_MARKER_END,
        )

        settings_content = replace_marker_block_v1(
            settings_content,
            IMPORT_MARKER_START,
            IMPORT_MARKER_END,
            updated_import_block,
        )

    moved_note = f'''{MOVED_MARKER_START}
# Campos de Quantidade do Processo/Menu movidos para:
# appverbo/routes/profile/settings/process_quantity_handlers.py
# Rotas movidas: {", ".join(route for route in moved_routes if route)}
{MOVED_MARKER_END}
'''

    if MOVED_MARKER_START not in settings_content:
        settings_content = settings_content.rstrip() + "\n\n" + moved_note.strip() + "\n"

    write_text_v1(SETTINGS_HANDLERS_PATH, settings_content)


####################################################################################
# (5) VALIDAÇÃO DO PATCH
####################################################################################

def validate_v1() -> None:
    settings_content = read_text_v1(SETTINGS_HANDLERS_PATH)
    process_quantity_content = read_text_v1(PROCESS_QUANTITY_PATH)

    required_settings_markers = [
        "APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START",
        "process_quantity_handlers_v1",
        "APPVERBO_SETTINGS_HANDLERS_PROCESS_QUANTITY_MOVED_V1_START",
    ]

    required_process_quantity_markers = [
        "_build_settings_redirect_url = build_settings_redirect_url_v1",
        "_require_menu_settings_owner_v1 = require_menu_settings_owner_v1",
        "@router.",
    ]

    if (
        "update_sidebar_menu_process_quantity_fields_v1" not in process_quantity_content
        and "process-quantity" not in process_quantity_content.lower()
        and "quantity_field" not in process_quantity_content.lower()
    ):
        raise RuntimeError(
            "O ficheiro process_quantity_handlers.py não parece conter lógica de Campos de Quantidade."
        )

    missing_settings = [
        marker
        for marker in required_settings_markers
        if marker not in settings_content
    ]

    missing_process_quantity = [
        marker
        for marker in required_process_quantity_markers
        if marker not in process_quantity_content
    ]

    if missing_settings:
        raise RuntimeError(
            "Marcadores ausentes no settings_handlers.py: "
            + ", ".join(missing_settings)
        )

    if missing_process_quantity:
        raise RuntimeError(
            "Marcadores ausentes no process_quantity_handlers.py: "
            + ", ".join(missing_process_quantity)
        )

    duplicated_routes = []

    for route in re.findall(
        r"""@router\.(?:get|post|put|patch|delete)\(\s*["']([^"']*quantity[^"']*)["']""",
        settings_content,
        flags=re.IGNORECASE,
    ):
        duplicated_routes.append(route)

    if duplicated_routes:
        raise RuntimeError(
            "Rotas de Campos de Quantidade ainda ficaram duplicadas no settings_handlers.py: "
            + ", ".join(duplicated_routes)
        )

    print("OK: Campos de Quantidade do Processo/Menu movidos para process_quantity_handlers.py.")
    print("OK: settings_handlers.py ficou apenas com import do subprocesso Campos de Quantidade.")
    print("OK: rotas de Campos de Quantidade permanecem registadas no router partilhado.")


####################################################################################
# (6) EXECUÇÃO
####################################################################################

def main() -> None:
    SETTINGS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    patch_settings_handlers_v1()
    validate_v1()


if __name__ == "__main__":
    main()
