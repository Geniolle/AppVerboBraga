from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PAGE_HANDLER = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
PAGINA_DEFAULT = ROOT / "appverbo" / "page_state" / "pagina_default.py"
TEMPLATE = ROOT / "templates" / "new_user.html"
REFRESH_JS = ROOT / "static" / "js" / "modules" / "appverbo_page_state_refresh_home_v1.js"


def read_text(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"Ficheiro obrigatório não encontrado: {path}")
    return path.read_text(encoding="utf-8")


def assert_contains(content: str, expected: str, label: str) -> None:
    if expected not in content:
        raise AssertionError(f"Contrato inválido em {label}: falta {expected!r}")


def assert_not_contains(content: str, unexpected: str, label: str) -> None:
    if unexpected in content:
        raise AssertionError(f"Contrato inválido em {label}: ainda existe {unexpected!r}")


def main() -> None:
    page_handler = read_text(PAGE_HANDLER)
    pagina_default = read_text(PAGINA_DEFAULT)
    template = read_text(TEMPLATE)
    refresh_js = read_text(REFRESH_JS)

    assert_contains(
        page_handler,
        "from appverbo.page_state.pagina_default import resolver_pagina_default_v1",
        "page_handler.py",
    )
    assert_contains(
        page_handler,
        "page_state = resolver_pagina_default_v1(",
        "page_handler.py",
    )
    assert_contains(
        page_handler,
        '"page_state": page_state',
        "page_handler.py",
    )
    assert_not_contains(
        page_handler,
        "APPVERBO_PAGE_STATE_RESOLVER_V1_START",
        "page_handler.py",
    )
    assert_not_contains(
        page_handler,
        "def _resolve_appverbo_page_state_v1",
        "page_handler.py",
    )

    assert_contains(
        pagina_default,
        "APPVERBO_PAGINA_DEFAULT_PROTECTED_AREA_V1_START",
        "pagina_default.py",
    )
    assert_contains(
        pagina_default,
        "def resolver_pagina_default_v1(",
        "pagina_default.py",
    )
    assert_contains(
        pagina_default,
        '"refresh_home_url": "/users/new?menu=home"',
        "pagina_default.py",
    )
    assert_contains(
        pagina_default,
        '"refresh_home_target": "#home-summary-card"',
        "pagina_default.py",
    )
    assert_contains(
        pagina_default,
        '"preserve_on_browser_refresh": preservar_contexto_no_refresh',
        "pagina_default.py",
    )

    assert_contains(
        template,
        "APPVERBO_PAGINA_DEFAULT_REFRESH_HOME_V1_START",
        "new_user.html",
    )
    assert_contains(
        template,
        "appverbo_page_state_refresh_home_v1.js?v=20260513-pagina-default-refresh-home-v1",
        "new_user.html",
    )
    assert_not_contains(
        template,
        "APPVERBO_PAGE_STATE_REFRESH_HOME_V1_START",
        "new_user.html",
    )

    assert_contains(
        refresh_js,
        "APPVERBO_PAGINA_DEFAULT_REFRESH_HOME_PROTECTED_AREA_V1_START",
        "appverbo_page_state_refresh_home_v1.js",
    )
    assert_contains(
        refresh_js,
        'window.location.replace("/users/new?menu=home")',
        "appverbo_page_state_refresh_home_v1.js",
    )
    assert_contains(
        refresh_js,
        "appverbo_after_save",
        "appverbo_page_state_refresh_home_v1.js",
    )

    print("OK: contrato pagina_default validado com sucesso.")


if __name__ == "__main__":
    main()
