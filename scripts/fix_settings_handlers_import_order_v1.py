from __future__ import annotations

from pathlib import Path


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

SETTINGS_HANDLERS_PATH = Path("appverbo/routes/profile/settings_handlers.py")


####################################################################################
# (2) CONTEÚDO CORRIGIDO
####################################################################################

SETTINGS_HANDLERS_CONTENT = '''from __future__ import annotations

from appverbo.routes.profile.settings import (
    additional_fields_handlers as additional_fields_handlers_v1,
)
from appverbo.routes.profile.settings import menu_crud_handlers as menu_crud_handlers_v1
from appverbo.routes.profile.settings import (
    process_fields_handlers as process_fields_handlers_v1,
)
from appverbo.routes.profile.settings import (
    process_lists_handlers as process_lists_handlers_v1,
)
from appverbo.routes.profile.settings import (
    process_quantity_handlers as process_quantity_handlers_v1,
)
from appverbo.routes.profile.settings import (
    sidebar_sections_handlers as sidebar_sections_handlers_v1,
)
from appverbo.routes.profile.settings import (
    subsequent_fields_handlers as subsequent_fields_handlers_v1,
)
from appverbo.routes.profile.settings.permissions import (
    require_menu_settings_owner_v1 as _require_menu_settings_owner_v1,
)
from appverbo.routes.profile.settings.redirects import (
    build_settings_redirect_url_v1 as _build_settings_redirect_url,
)

# APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_START

####################################################################################
# (1) AGREGADOR DOS SUBPROCESSOS DE CONFIGURAÇÕES DO MENU - V1
####################################################################################

# Este ficheiro mantém compatibilidade com os imports existentes do projeto.
# As rotas FastAPI são registadas ao importar os módulos de subprocesso abaixo.
# A lógica real de cada subprocesso fica em appverbo/routes/profile/settings/.

# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_START
# APPVERBO_SETTINGS_SUBPROCESS_IMPORTS_V1_END

####################################################################################
# (2) EXPORTS
####################################################################################

__all__ = [
    "additional_fields_handlers_v1",
    "menu_crud_handlers_v1",
    "process_fields_handlers_v1",
    "process_lists_handlers_v1",
    "process_quantity_handlers_v1",
    "sidebar_sections_handlers_v1",
    "subsequent_fields_handlers_v1",
    "_build_settings_redirect_url",
    "_require_menu_settings_owner_v1",
]

# APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_END
'''


####################################################################################
# (3) EXECUÇÃO
####################################################################################

def main() -> None:
    SETTINGS_HANDLERS_PATH.write_text(SETTINGS_HANDLERS_CONTENT, encoding="utf-8")

    content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

    required_markers = [
        "APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_START",
        "additional_fields_handlers_v1",
        "menu_crud_handlers_v1",
        "process_fields_handlers_v1",
        "process_lists_handlers_v1",
        "process_quantity_handlers_v1",
        "sidebar_sections_handlers_v1",
        "subsequent_fields_handlers_v1",
        "_build_settings_redirect_url",
        "_require_menu_settings_owner_v1",
        "APPVERBO_SETTINGS_HANDLERS_AGGREGATOR_V1_END",
    ]

    missing = [marker for marker in required_markers if marker not in content]

    if missing:
        raise RuntimeError("Marcadores ausentes: " + ", ".join(missing))

    if "@router." in content:
        raise RuntimeError("settings_handlers.py voltou a conter rotas diretas.")

    print("OK: settings_handlers.py reformatado com imports ordenados para Ruff.")


if __name__ == "__main__":
    main()
