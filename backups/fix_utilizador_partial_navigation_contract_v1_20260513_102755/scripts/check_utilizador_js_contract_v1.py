from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) HELPERS
####################################################################################

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


####################################################################################
# (2) CONTRATO DO JAVASCRIPT DO SUBPROCESSO UTILIZADOR
####################################################################################

def main() -> None:
    table_js = read("static/js/modules/admin_user_shadow_table_v1.js")
    navigation_js = read("static/js/modules/admin_user_action_navigation_v1.js")
    partial = read("templates/partials/admin_user_shadow_readonly_v1.html")

    assert_true(
        "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1" in navigation_js,
        "Módulo de navegação do Utilizador deve identificar APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1.",
    )

    assert_true(
        "navegarParaAcaoUtilizador_v1" in navigation_js,
        "Módulo de navegação deve conter navegarParaAcaoUtilizador_v1.",
    )

    assert_true(
        "document.addEventListener(\"click\", navegarParaAcaoUtilizador_v1, true)" in navigation_js,
        "Módulo de navegação deve ligar clique em capture phase.",
    )

    forbidden_table_patterns = (
        "APPVERBO_UTILIZADOR_ACTION_ICON_CLICK",
        "APPVERBO_UTILIZADOR_ACTION_CLICK_BRIDGE",
        "navigatetoUserAction",
        "navigateToUserAction",
        "navegarParaAcaoUtilizador",
        "window.location.assign(href)",
        "window.location.href = href",
    )

    for pattern in forbidden_table_patterns:
        assert_true(
            pattern not in table_js,
            f"admin_user_shadow_table_v1.js não deve conter lógica de navegação: {pattern}",
        )

    assert_true(
        "admin_user_shadow_table_v1.js" in partial,
        "Partial deve carregar módulo de tabela do Utilizador.",
    )

    assert_true(
        "admin_user_action_navigation_v1.js" in partial,
        "Partial deve carregar módulo isolado de navegação do Utilizador.",
    )

    table_script_index = partial.find("admin_user_shadow_table_v1.js")
    navigation_script_index = partial.find("admin_user_action_navigation_v1.js")

    assert_true(
        table_script_index >= 0 and navigation_script_index >= 0,
        "Scripts de tabela e navegação devem existir no partial.",
    )

    assert_true(
        table_script_index < navigation_script_index,
        "Módulo de tabela deve carregar antes do módulo de navegação.",
    )

    assert_true(
        re.search(r'row\.get\(["\']view_url["\']\)', partial) is not None,
        "Partial deve usar view_url vindo do repository.",
    )

    assert_true(
        re.search(r'row\.get\(["\']edit_url["\']\)', partial) is not None,
        "Partial deve usar edit_url vindo do repository.",
    )

    print("OK: contrato JS do subprocesso Utilizador validado com sucesso.")


if __name__ == "__main__":
    main()
