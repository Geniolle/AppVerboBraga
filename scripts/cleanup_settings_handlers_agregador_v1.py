from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

SETTINGS_HANDLERS_PATH = Path("appverbo/routes/profile/settings_handlers.py")
SETTINGS_PACKAGE_DIR = Path("appverbo/routes/profile/settings")

EXPECTED_MODULES = [
    "sidebar_sections_handlers",
    "menu_crud_handlers",
    "additional_fields_handlers",
    "process_fields_handlers",
    "process_lists_handlers",
    "process_quantity_handlers",
    "subsequent_fields_handlers",
]

EXPECTED_SUPPORT_FILES = [
    "common.py",
    "normalizers.py",
    "redirects.py",
    "permissions.py",
    "__init__.py",
]

AGGREGATOR_START = "# APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_START"
AGGREGATOR_END = "# APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_END"


####################################################################################
# (2) FUNÇÕES AUXILIARES
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def find_router_decorators_v1(content: str) -> list[tuple[int, str]]:
    matches = []

    for match in re.finditer(
        r"(?m)^\s*@router\.(?:get|post|put|patch|delete)\(",
        content,
    ):
        line_number = content.count("\n", 0, match.start()) + 1
        line_text = content.splitlines()[line_number - 1].strip()
        matches.append((line_number, line_text))

    return matches


def validate_required_files_v1() -> None:
    if not SETTINGS_HANDLERS_PATH.exists():
        raise RuntimeError(f"Ficheiro não encontrado: {SETTINGS_HANDLERS_PATH}")

    if not SETTINGS_PACKAGE_DIR.exists():
        raise RuntimeError(f"Pasta não encontrada: {SETTINGS_PACKAGE_DIR}")

    missing_modules = []

    for module_name in EXPECTED_MODULES:
        module_path = SETTINGS_PACKAGE_DIR / f"{module_name}.py"

        if not module_path.exists():
            missing_modules.append(str(module_path))

    for support_file in EXPECTED_SUPPORT_FILES:
        support_path = SETTINGS_PACKAGE_DIR / support_file

        if not support_path.exists():
            missing_modules.append(str(support_path))

    if missing_modules:
        raise RuntimeError(
            "Ficheiros obrigatórios ausentes: "
            + ", ".join(missing_modules)
        )


####################################################################################
# (3) GERAR settings_handlers.py COMO AGREGADOR
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


####################################################################################
# (4) APLICAR LIMPEZA
####################################################################################

def cleanup_settings_handlers_v1() -> None:
    validate_required_files_v1()

    original_content = read_text_v1(SETTINGS_HANDLERS_PATH)

    remaining_routes = find_router_decorators_v1(original_content)

    if remaining_routes:
        formatted_routes = "; ".join(
            f"linha {line_number}: {line_text}"
            for line_number, line_text in remaining_routes
        )

        raise RuntimeError(
            "Ainda existem rotas diretamente no settings_handlers.py. "
            "Mova essas rotas antes de transformar o ficheiro em agregador. "
            f"Rotas encontradas: {formatted_routes}"
        )

    aggregator_content = build_aggregator_content_v1()

    write_text_v1(SETTINGS_HANDLERS_PATH, aggregator_content)


####################################################################################
# (5) VALIDAÇÃO FINAL
####################################################################################

def validate_aggregator_v1() -> None:
    content = read_text_v1(SETTINGS_HANDLERS_PATH)

    required_markers = [
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

    missing_markers = [
        marker
        for marker in required_markers
        if marker not in content
    ]

    if missing_markers:
        raise RuntimeError(
            "settings_handlers.py agregador incompleto. Marcadores ausentes: "
            + ", ".join(missing_markers)
        )

    remaining_routes = find_router_decorators_v1(content)

    if remaining_routes:
        raise RuntimeError(
            "O agregador ainda contém decorators @router, o que não deveria acontecer."
        )

    print("OK: settings_handlers.py transformado em agregador limpo.")
    print("OK: nenhum decorator @router permaneceu no ficheiro antigo.")
    print("OK: aliases de compatibilidade preservados.")


####################################################################################
# (6) EXECUÇÃO
####################################################################################

def main() -> None:
    cleanup_settings_handlers_v1()
    validate_aggregator_v1()


if __name__ == "__main__":
    main()
