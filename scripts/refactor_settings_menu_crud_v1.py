from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

SETTINGS_HANDLERS_PATH = Path("appverbo/routes/profile/settings_handlers.py")
SETTINGS_PACKAGE_DIR = Path("appverbo/routes/profile/settings")
MENU_CRUD_PATH = SETTINGS_PACKAGE_DIR / "menu_crud_handlers.py"

IMPORT_MARKER_START = "# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START"
IMPORT_MARKER_END = "# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_END"

MOVED_MARKER_START = "# APPVERBO_SETTINGS_HANDLERS_MENU_CRUD_MOVED_V1_START"
MOVED_MARKER_END = "# APPVERBO_SETTINGS_HANDLERS_MENU_CRUD_MOVED_V1_END"


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


def find_route_decorator_start_v1(content: str, route_path: str) -> int:
    patterns = [
        rf'(?m)^@router\.post\("{re.escape(route_path)}"',
        rf"(?m)^@router\.post\('{re.escape(route_path)}'",
        rf'(?m)^@router\.get\("{re.escape(route_path)}"',
        rf"(?m)^@router\.get\('{re.escape(route_path)}'",
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


####################################################################################
# (3) MÓDULO DO CRUD PRINCIPAL DO MENU
####################################################################################

def build_menu_crud_module_v1(blocks: list[str]) -> str:
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
# (4) REFATORAR CRUD PRINCIPAL DO MENU
####################################################################################

def patch_settings_handlers_v1() -> None:
    settings_content = read_text_v1(SETTINGS_HANDLERS_PATH)

    require_text_v1(
        settings_content,
        "APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START",
        SETTINGS_HANDLERS_PATH,
    )

    already_moved = "menu_crud_handlers_v1" in settings_content

    if already_moved:
        if not MENU_CRUD_PATH.exists():
            raise RuntimeError(
                "settings_handlers.py já importa menu_crud_handlers_v1, "
                "mas o ficheiro menu_crud_handlers.py não existe."
            )

        print("INFO: CRUD principal do Menu já estava importado.")
        return

    route_paths = [
        "/settings/menu/edit",
        "/settings/menu/create",
        "/settings/menu/delete",
        "/settings/menu/move",
        "/settings/menu/status",
        "/settings/menu/visibility",
    ]

    extracted_blocks: list[str] = []
    found_routes: list[str] = []

    for route_path in route_paths:
        block, settings_content, found = extract_endpoint_by_route_v1(
            settings_content,
            route_path,
        )

        if found:
            extracted_blocks.append(block)
            found_routes.append(route_path)

    if "/settings/menu/edit" not in found_routes:
        raise RuntimeError(
            "Endpoint principal /settings/menu/edit não encontrado no settings_handlers.py."
        )

    if not extracted_blocks:
        raise RuntimeError("Nenhum endpoint de CRUD do Menu foi encontrado para mover.")

    menu_crud_module = build_menu_crud_module_v1(extracted_blocks)
    write_text_v1(MENU_CRUD_PATH, menu_crud_module)

    import_block_pattern = re.compile(
        re.escape(IMPORT_MARKER_START) + r".*?" + re.escape(IMPORT_MARKER_END),
        flags=re.DOTALL,
    )

    import_match = import_block_pattern.search(settings_content)

    if not import_match:
        raise RuntimeError("Bloco de imports dos subprocessos não encontrado.")

    current_import_block = import_match.group(0)

    menu_crud_import_line = (
        "from appverbo.routes.profile.settings import "
        "menu_crud_handlers as menu_crud_handlers_v1  # noqa: F401"
    )

    if menu_crud_import_line not in current_import_block:
        updated_import_block = current_import_block.replace(
            IMPORT_MARKER_END,
            menu_crud_import_line + "\n" + IMPORT_MARKER_END,
        )

        settings_content = replace_marker_block_v1(
            settings_content,
            IMPORT_MARKER_START,
            IMPORT_MARKER_END,
            updated_import_block,
        )

    moved_note = f'''{MOVED_MARKER_START}
# O CRUD principal do Menu foi movido para:
# appverbo/routes/profile/settings/menu_crud_handlers.py
# Rotas movidas: {", ".join(found_routes)}
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
    menu_crud_content = read_text_v1(MENU_CRUD_PATH)

    required_settings_markers = [
        "APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START",
        "menu_crud_handlers_v1",
        "APPVERBO_SETTINGS_HANDLERS_MENU_CRUD_MOVED_V1_START",
    ]

    required_menu_crud_markers = [
        "@router.post(\"/settings/menu/edit\"",
        "edit_sidebar_menu_setting_handler_v1",
        "_build_settings_redirect_url = build_settings_redirect_url_v1",
        "_require_menu_settings_owner_v1 = require_menu_settings_owner_v1",
    ]

    missing_settings = [
        marker
        for marker in required_settings_markers
        if marker not in settings_content
    ]

    missing_menu_crud = [
        marker
        for marker in required_menu_crud_markers
        if marker not in menu_crud_content
    ]

    if missing_settings:
        raise RuntimeError(
            "Marcadores ausentes no settings_handlers.py: "
            + ", ".join(missing_settings)
        )

    if missing_menu_crud:
        raise RuntimeError(
            "Marcadores ausentes no menu_crud_handlers.py: "
            + ", ".join(missing_menu_crud)
        )

    if '@router.post("/settings/menu/edit"' in settings_content:
        raise RuntimeError(
            "A rota /settings/menu/edit ainda ficou duplicada no settings_handlers.py."
        )

    print("OK: CRUD principal do Menu movido para menu_crud_handlers.py.")
    print("OK: settings_handlers.py ficou apenas com import do CRUD principal do Menu.")
    print("OK: rota /settings/menu/edit permanece registada no router partilhado.")


####################################################################################
# (6) EXECUÇÃO
####################################################################################

def main() -> None:
    SETTINGS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    patch_settings_handlers_v1()
    validate_v1()


if __name__ == "__main__":
    main()
