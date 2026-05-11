from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

SETTINGS_HANDLERS_PATH = Path("appverbo/routes/profile/settings_handlers.py")
SETTINGS_PACKAGE_DIR = Path("appverbo/routes/profile/settings")

INIT_PATH = SETTINGS_PACKAGE_DIR / "__init__.py"
COMMON_PATH = SETTINGS_PACKAGE_DIR / "common.py"
NORMALIZERS_PATH = SETTINGS_PACKAGE_DIR / "normalizers.py"
REDIRECTS_PATH = SETTINGS_PACKAGE_DIR / "redirects.py"
PERMISSIONS_PATH = SETTINGS_PACKAGE_DIR / "permissions.py"
SIDEBAR_SECTIONS_PATH = SETTINGS_PACKAGE_DIR / "sidebar_sections_handlers.py"

IMPORT_MARKER_START = "# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START"
IMPORT_MARKER_END = "# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_END"

MOVED_MARKER_START = "# APPVERBO_SETTINGS_HANDLERS_SESSOES_MOVED_V1_START"
MOVED_MARKER_END = "# APPVERBO_SETTINGS_HANDLERS_SESSOES_MOVED_V1_END"


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


def extract_marker_block_v1(content: str, start_marker: str, end_marker: str) -> tuple[str, str]:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )

    match = pattern.search(content)

    if not match:
        raise RuntimeError(f"Bloco não encontrado: {start_marker} ... {end_marker}")

    block = match.group(0).strip()
    updated_content = pattern.sub("", content, count=1)

    return block, updated_content


def replace_marker_block_v1(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )

    if pattern.search(content):
        return pattern.sub(new_block.strip(), content, count=1)

    return content.rstrip() + "\n\n" + new_block.strip() + "\n"


def insert_after_marker_v1(content: str, marker: str, insertion: str) -> str:
    if insertion.strip() in content:
        return content

    marker_index = content.find(marker)

    if marker_index < 0:
        raise RuntimeError(f"Marcador de inserção não encontrado: {marker}")

    line_end = content.find("\n", marker_index)

    if line_end < 0:
        line_end = len(content)

    return content[: line_end + 1] + insertion.strip() + "\n" + content[line_end + 1 :]


####################################################################################
# (3) CONTEÚDO DOS FICHEIROS REUTILIZÁVEIS
####################################################################################

INIT_CONTENT = '''from __future__ import annotations

# Pacote de subprocessos das configurações do Menu.
'''

COMMON_CONTENT = '''from __future__ import annotations

import re
import unicodedata


####################################################################################
# (1) NORMALIZAÇÃO GERAL
####################################################################################

def normalize_settings_text_v1(value: object) -> str:
    return str(value or "").strip()


def normalize_settings_lookup_text_v1(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.strip().lower()
    return " ".join(normalized.split())


def slugify_settings_key_v1(value: object, fallback: str = "novo_item") -> str:
    raw_value = normalize_settings_text_v1(value).lower()
    raw_value = unicodedata.normalize("NFD", raw_value)
    raw_value = "".join(char for char in raw_value if unicodedata.category(char) != "Mn")
    raw_value = re.sub(r"[^a-z0-9]+", "_", raw_value)
    raw_value = re.sub(r"_+", "_", raw_value).strip("_")

    if raw_value and raw_value[0].isdigit():
        raw_value = f"item_{raw_value}"

    return raw_value or fallback


def normalize_settings_status_v1(value: object) -> str:
    clean_value = normalize_settings_text_v1(value).lower()

    if clean_value in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def settings_status_label_v1(value: object) -> str:
    return "Inativo" if normalize_settings_status_v1(value) == "inativo" else "Ativo"


####################################################################################
# (2) VISIBILIDADE
####################################################################################

def normalize_settings_visibility_scope_v1(value: object) -> str:
    clean_value = normalize_settings_text_v1(value).lower()

    if clean_value in {"owner", "legado"}:
        return clean_value

    return "all"


def settings_visibility_scope_to_scopes_v1(value: object) -> list[str]:
    clean_value = normalize_settings_visibility_scope_v1(value)

    if clean_value in {"owner", "legado"}:
        return [clean_value]

    return ["owner", "legado"]


def settings_visibility_scope_label_v1(value: object) -> str:
    clean_value = normalize_settings_visibility_scope_v1(value)

    if clean_value == "owner":
        return "Owner"

    if clean_value == "legado":
        return "Legado"

    return "Owner e Legado"
'''

NORMALIZERS_CONTENT = '''from __future__ import annotations

from appverbo.routes.profile.settings.common import (
    normalize_settings_lookup_text_v1,
    normalize_settings_status_v1,
    normalize_settings_text_v1,
    normalize_settings_visibility_scope_v1,
    settings_status_label_v1,
    settings_visibility_scope_label_v1,
    settings_visibility_scope_to_scopes_v1,
    slugify_settings_key_v1,
)

__all__ = [
    "normalize_settings_lookup_text_v1",
    "normalize_settings_status_v1",
    "normalize_settings_text_v1",
    "normalize_settings_visibility_scope_v1",
    "settings_status_label_v1",
    "settings_visibility_scope_label_v1",
    "settings_visibility_scope_to_scopes_v1",
    "slugify_settings_key_v1",
]
'''

REDIRECTS_CONTENT = '''from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


####################################################################################
# (1) URL DE RETORNO PADRÃO DAS CONFIGURAÇÕES DO MENU
####################################################################################

def build_settings_redirect_url_v1(
    error_message: str = "",
    success_message: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#admin-account-status-card",
    settings_edit_key: str = "",
    settings_action: str = "",
    settings_tab: str = "",
) -> str:
    params: list[tuple[str, str]] = []

    if error_message:
        params.append(("error", error_message))

    if success_message:
        params.append(("success", success_message))

    if redirect_menu:
        params.append(("menu", redirect_menu))

    if redirect_target:
        params.append(("target", redirect_target.lstrip("#")))

    if settings_edit_key:
        params.append(("settings_edit_key", settings_edit_key))

    if settings_action:
        params.append(("settings_action", settings_action))

    if settings_tab:
        params.append(("settings_tab", settings_tab))

    return f"/users/new?{urlencode(params)}"


####################################################################################
# (2) MENSAGENS EM RETURN_URL
####################################################################################

def append_settings_message_to_url_v1(return_url: str, message_key: str, message: str) -> str:
    parts = urlsplit(str(return_url or "").strip() or "/users/new?menu=administrativo")
    params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {"success", "error"}
    ]

    if message_key and message:
        params.append((message_key, message))

    return urlunsplit((
        "",
        "",
        parts.path or "/users/new",
        urlencode(params),
        parts.fragment,
    ))
'''

PERMISSIONS_CONTENT = '''from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import RedirectResponse

from appverbo.routes.profile.settings.redirects import build_settings_redirect_url_v1
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_current_user, get_session_entity_id


####################################################################################
# (1) PERMISSÃO REUTILIZÁVEL PARA CONFIGURAÇÕES DO MENU
####################################################################################

def require_menu_settings_owner_v1(
    session,
    request: Request,
    redirect_menu: str = "administrativo",
    redirect_target: str = "#settings-menu-edit-card",
    settings_edit_key: str = "",
    settings_action: str = "edit",
    settings_tab: str = "geral",
) -> RedirectResponse | None:
    current_user = get_current_user(request, session)

    if current_user is None:
        return RedirectResponse(
            url="/login?error=Efetue login para continuar.",
            status_code=status.HTTP_302_FOUND,
        )

    if not is_admin_user(session, current_user["id"], current_user["login_email"]):
        return RedirectResponse(
            url=build_settings_redirect_url_v1(
                error_message="Apenas administradores podem alterar definições do menu.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=settings_edit_key,
                settings_action=settings_action,
                settings_tab=settings_tab,
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    selected_entity_id = get_session_entity_id(request)
    permissions = get_user_entity_permissions(
        session,
        current_user["id"],
        current_user["login_email"],
        selected_entity_id,
    )

    if not permissions["can_manage_all_entities"]:
        return RedirectResponse(
            url=build_settings_redirect_url_v1(
                error_message="Apenas Owner pode alterar definições do menu.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=settings_edit_key,
                settings_action=settings_action,
                settings_tab=settings_tab,
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return None
'''


####################################################################################
# (4) REFATORAR SUBPROCESSO SESSÕES
####################################################################################

def build_sidebar_sections_module_v1(blocks: list[str]) -> str:
    module_header = '''from __future__ import annotations

import json

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import text

from appverbo.core import SessionLocal
from appverbo.menu_settings import (
    get_sidebar_global_refresh_version_v1,
    update_sidebar_sections_v2,
)
from appverbo.routes.profile.router import router
from appverbo.routes.profile.settings.redirects import build_settings_redirect_url_v1
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_current_user, get_session_entity_id


####################################################################################
# (1) ALIAS TEMPORÁRIO PARA COMPATIBILIDADE COM O CÓDIGO MIGRADO
####################################################################################

_build_settings_redirect_url = build_settings_redirect_url_v1
'''

    return module_header.rstrip() + "\n\n\n" + "\n\n\n".join(blocks).strip() + "\n"


def patch_settings_handlers_v1() -> None:
    SETTINGS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    settings_content = read_text_v1(SETTINGS_HANDLERS_PATH)

    if "appverbo.routes.profile.settings import sidebar_sections_handlers" in settings_content:
        print("INFO: import do subprocesso Sessões já existe no settings_handlers.py.")
        already_moved = True
    else:
        already_moved = False

    marker_pairs = [
        (
            "# APPVERBO_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_START",
            "# APPVERBO_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_END",
        ),
        (
            "# APPVERBO_SIDEBAR_SECTIONS_DATA_ENDPOINT_V6_START",
            "# APPVERBO_SIDEBAR_SECTIONS_DATA_ENDPOINT_V6_END",
        ),
        (
            "# APPVERBO_SESSOES_RETURN_URL_V17_START",
            "# APPVERBO_SESSOES_RETURN_URL_V17_END",
        ),
        (
            "# APPVERBO_SESSOES_SAVE_ONE_V19_START",
            "# APPVERBO_SESSOES_SAVE_ONE_V19_END",
        ),
        (
            "# APPVERBO_SESSOES_SERVER_MOVE_ONE_V25_START",
            "# APPVERBO_SESSOES_SERVER_MOVE_ONE_V25_END",
        ),
        (
            "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START",
            "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_END",
        ),
    ]

    extracted_blocks: list[str] = []

    if not already_moved:
        for start_marker, end_marker in marker_pairs:
            block, settings_content = extract_marker_block_v1(
                settings_content,
                start_marker,
                end_marker,
            )
            extracted_blocks.append(block)

        sidebar_module = build_sidebar_sections_module_v1(extracted_blocks)
        write_text_v1(SIDEBAR_SECTIONS_PATH, sidebar_module)

        import_block = f'''{IMPORT_MARKER_START}
# Subprocesso Sessões/Menu movido para ficheiro próprio.
# A importação regista as rotas FastAPI no router partilhado.
from appverbo.routes.profile.settings import sidebar_sections_handlers as sidebar_sections_handlers_v1  # noqa: F401
{IMPORT_MARKER_END}
'''

        if IMPORT_MARKER_START in settings_content:
            settings_content = replace_marker_block_v1(
                settings_content,
                IMPORT_MARKER_START,
                IMPORT_MARKER_END,
                import_block,
            )
        else:
            settings_content = insert_after_marker_v1(
                settings_content,
                "from appverbo.routes.profile.router import router",
                "\n" + import_block,
            )

        moved_note = f'''{MOVED_MARKER_START}
# O subprocesso Sessões/Menu foi movido para:
# appverbo/routes/profile/settings/sidebar_sections_handlers.py
{MOVED_MARKER_END}
'''

        if MOVED_MARKER_START not in settings_content:
            settings_content = settings_content.rstrip() + "\n\n" + moved_note.strip() + "\n"

        write_text_v1(SETTINGS_HANDLERS_PATH, settings_content)
    else:
        if not SIDEBAR_SECTIONS_PATH.exists():
            raise RuntimeError(
                "O settings_handlers.py já importa sidebar_sections_handlers, "
                "mas o ficheiro destino não existe."
            )

    write_text_v1(INIT_PATH, INIT_CONTENT)
    write_text_v1(COMMON_PATH, COMMON_CONTENT)
    write_text_v1(NORMALIZERS_PATH, NORMALIZERS_CONTENT)
    write_text_v1(REDIRECTS_PATH, REDIRECTS_CONTENT)
    write_text_v1(PERMISSIONS_PATH, PERMISSIONS_CONTENT)


####################################################################################
# (5) VALIDAÇÃO DO PATCH
####################################################################################

def validate_v1() -> None:
    settings_content = read_text_v1(SETTINGS_HANDLERS_PATH)
    sidebar_content = read_text_v1(SIDEBAR_SECTIONS_PATH)

    required_settings_markers = [
        "APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START",
        "sidebar_sections_handlers_v1",
        "APPVERBO_SETTINGS_HANDLERS_SESSOES_MOVED_V1_START",
    ]

    required_sidebar_markers = [
        "APPVERBO_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_START",
        "APPVERBO_SIDEBAR_SECTIONS_DATA_ENDPOINT_V6_START",
        "APPVERBO_SESSOES_SAVE_ONE_V19_START",
        "APPVERBO_SESSOES_SERVER_MOVE_ONE_V25_START",
        "APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START",
        "@router.post(\"/settings/menu/sidebar-section-save\"",
        "@router.post(\"/settings/menu/sidebar-section-move-one\"",
        "@router.post(\"/settings/menu/sidebar-sections\"",
    ]

    required_common_files = [
        COMMON_PATH,
        NORMALIZERS_PATH,
        REDIRECTS_PATH,
        PERMISSIONS_PATH,
        INIT_PATH,
    ]

    missing_settings = [
        marker
        for marker in required_settings_markers
        if marker not in settings_content
    ]

    missing_sidebar = [
        marker
        for marker in required_sidebar_markers
        if marker not in sidebar_content
    ]

    missing_files = [
        str(path)
        for path in required_common_files
        if not path.exists()
    ]

    if missing_settings:
        raise RuntimeError(
            "Marcadores ausentes no settings_handlers.py: "
            + ", ".join(missing_settings)
        )

    if missing_sidebar:
        raise RuntimeError(
            "Marcadores ausentes no sidebar_sections_handlers.py: "
            + ", ".join(missing_sidebar)
        )

    if missing_files:
        raise RuntimeError(
            "Ficheiros reutilizáveis ausentes: "
            + ", ".join(missing_files)
        )

    old_sidebar_blocks = [
        "APPVERBO_SESSOES_SAVE_ONE_V19_START",
        "APPVERBO_SESSOES_SERVER_MOVE_ONE_V25_START",
        "APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START",
    ]

    duplicated_blocks = [
        marker
        for marker in old_sidebar_blocks
        if marker in settings_content
    ]

    if duplicated_blocks:
        raise RuntimeError(
            "Blocos ainda ficaram duplicados no settings_handlers.py: "
            + ", ".join(duplicated_blocks)
        )

    print("OK: subprocesso Sessões/Menu movido para sidebar_sections_handlers.py.")
    print("OK: settings_handlers.py ficou apenas com import do subprocesso.")
    print("OK: ficheiros reutilizáveis criados em appverbo/routes/profile/settings/.")


####################################################################################
# (6) EXECUÇÃO
####################################################################################

def main() -> None:
    require_text_v1(
        read_text_v1(SETTINGS_HANDLERS_PATH),
        "from appverbo.routes.profile.router import router",
        SETTINGS_HANDLERS_PATH,
    )

    patch_settings_handlers_v1()
    validate_v1()


if __name__ == "__main__":
    main()
