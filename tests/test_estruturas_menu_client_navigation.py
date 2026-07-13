from __future__ import annotations

from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD

PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) HELPERS
####################################################################################


def _build_chrome_driver_v1() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)


def _build_driver_v1():
    try:
        return _build_chrome_driver_v1()
    except WebDriverException as exc:
        pytest.skip(f"Selenium Chrome indisponivel neste ambiente: {exc}")


def _login_admin_v1(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    admin_email = str(ADMIN_LOGIN_EMAIL or "").strip()
    admin_password = str(ADMIN_LOGIN_PASSWORD or "").strip()
    if not admin_email or not admin_password:
        pytest.skip("ADMIN_LOGIN_EMAIL / ADMIN_LOGIN_PASSWORD nao definidos.")

    driver.get("http://127.0.0.1:8000/login")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(
        admin_email
    )
    driver.find_element(By.NAME, "password").send_keys(admin_password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/users/new"))


def _card_state(driver: webdriver.Chrome, card_id: str) -> dict:
    return driver.execute_script(
        """
        const el = document.getElementById(arguments[0]);
        if (!el) return {exists: false};
        const cs = getComputedStyle(el);
        return {
          exists: true,
          computedDisplay: cs.display,
          rowCount: el.querySelectorAll('tbody tr').length
        };
        """,
        card_id,
    )


def _current_href_v1(driver: webdriver.Chrome) -> str:
    # driver.current_url pode devolver um valor desatualizado logo apos uma navegacao
    # completa na mesma aba (observado com esta combinacao chromedriver/chrome); ler
    # window.location.href via JS reflete o estado real do documento carregado.
    return driver.execute_script("return window.location.href;")


####################################################################################
# (2) NAVEGACAO POR CLIQUE PARA ESTRUTURAS > MENU MOSTRA OS DADOS SEM REFRESH
####################################################################################


def test_client_navigation_to_estruturas_menu_shows_tables_without_refresh() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        driver.find_element(By.CSS_SELECTOR, ".menu-item[data-menu='sessoes']").click()
        wait.until(
            lambda drv: (
                "Sessões"
                in [
                    e.text.strip()
                    for e in drv.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
                ]
            )
        )

        menu_tab = None
        for el in driver.find_elements(By.CSS_SELECTOR, ".submenu-item"):
            if el.text.strip() == "Menu":
                menu_tab = el
                break
        assert menu_tab is not None, "Aba 'Menu' nao encontrada"
        menu_tab.click()

        wait.until(
            lambda drv: (
                _card_state(drv, "menu-subprocess-card-active").get("computedDisplay")
                == "block"
            )
        )

        state = _card_state(driver, "menu-subprocess-card-active")
        assert state["computedDisplay"] == "block"
        assert state["rowCount"] > 0, (
            "Tabela Menus ativos sem linhas apos navegacao por clique"
        )

        active_submenu = [
            e.text.strip()
            for e in driver.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
        ]
        assert active_submenu == ["Menu"]
    finally:
        driver.quit()


####################################################################################
# (3) REENTRAR EM ESTRUTURAS DEPOIS DE VISITAR OUTRO MENU MANTEM ABA E CONTEUDO
# SINCRONIZADOS (bug original: aba ficava presa em "Menu" enquanto o conteudo mudava
# para "Sessoes", ou vice-versa, ate um refresh).
####################################################################################


def test_reentering_estruturas_keeps_active_tab_and_content_in_sync() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        driver.find_element(By.CSS_SELECTOR, ".menu-item[data-menu='sessoes']").click()
        wait.until(
            lambda drv: (
                "Sessões"
                in [
                    e.text.strip()
                    for e in drv.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
                ]
            )
        )
        for el in driver.find_elements(By.CSS_SELECTOR, ".submenu-item"):
            if el.text.strip() == "Menu":
                el.click()
                break
        wait.until(
            lambda drv: (
                _card_state(drv, "menu-subprocess-card-active").get("computedDisplay")
                == "block"
            )
        )

        driver.find_element(By.CSS_SELECTOR, ".menu-item[data-menu='home']").click()
        wait.until(EC.presence_of_element_located((By.ID, "home-summary-card")))

        driver.find_element(By.CSS_SELECTOR, ".menu-item[data-menu='sessoes']").click()
        wait.until(
            lambda drv: bool(
                [
                    e.text.strip()
                    for e in drv.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
                ]
            )
        )

        active_submenu = [
            e.text.strip()
            for e in driver.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
        ]

        if active_submenu == ["Menu"]:
            state = _card_state(driver, "menu-subprocess-card-active")
        else:
            state = _card_state(driver, "admin-sidebar-sections-card-active")

        assert state["computedDisplay"] == "block", (
            f"Aba ativa ({active_submenu}) nao corresponde ao card visivel: {state}"
        )
    finally:
        driver.quit()


####################################################################################
# (4) REGRESSAO: NAVEGACAO POR URL LIMPO NO ADMINISTRATIVO (ENTIDADE/UTILIZADOR)
# CONTINUA A MARCAR A ABA CERTA -- ISTO E O CASO DE USO ORIGINAL DE top_menu_active_v1.js
####################################################################################


def test_administrativo_clean_url_tab_still_activates_correct_tab() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        driver.get(
            "http://127.0.0.1:8000/users/new?menu=administrativo&admin_tab=entidade"
        )
        wait.until(
            lambda drv: bool(
                [
                    e.text.strip()
                    for e in drv.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
                ]
            )
        )

        active_submenu = [
            e.text.strip().lower()
            for e in driver.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
        ]
        assert "entidade" in active_submenu, active_submenu
    finally:
        driver.quit()


####################################################################################
# (5) FONTE: reagirMudancaAbas_v4 so reaplica o rotulo memorizado quando o menu
# realmente ativo na SPA e' "administrativo" -- caso contrario, o rotulo e limpo.
####################################################################################


def test_top_menu_active_scopes_sticky_label_to_administrativo() -> None:
    js_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js"
    ).read_text(encoding="utf-8")

    reagir_index = js_text.index("function reagirMudancaAbas_v4()")
    reagir_body_end = js_text.index("function observarAbasDinamicas_v4")
    reagir_body = js_text[reagir_index:reagir_body_end]

    assert "estaNoAdministrativo_v4()" in reagir_body
    assert 'activeTabLabelV4 = "";' in reagir_body

    estar_index = js_text.index("function estaNoAdministrativo_v4()")
    estar_body_end = js_text.index("function temContextoDeEdicaoMenu_v4")
    estar_body = js_text[estar_index:estar_body_end]

    assert "window.__appgenesisGetActiveMenuKeyV1" in estar_body


def test_new_user_js_exposes_active_menu_key_signal() -> None:
    js_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(
        encoding="utf-8"
    )

    assert "window.__appgenesisGetActiveMenuKeyV1 = function () {" in js_text
    assert "return activeMenuKey;" in js_text


def test_breadcrumb_markup_has_active_tab_slot() -> None:
    template_text = (
        PROJECT_ROOT
        / "templates"
        / "partials"
        / "app_shell"
        / "process_header_v1.html"
    ).read_text(encoding="utf-8")

    assert 'id="process-shell-breadcrumb-tab-group-v1"' in template_text
    assert 'id="process-shell-breadcrumb-tab-v1"' in template_text


####################################################################################
# (6) NAVEGACAO POR CLIQUE PARA ESTRUTURAS > MENU MOSTRA TAMBEM "MENUS INATIVOS"
# (nao apenas "Menus ativos") SEM REFRESH -- cobre explicitamente o par
# ativo+inativo pedido pelo usuario, nao so o card de ativos.
####################################################################################


def test_client_navigation_to_estruturas_menu_shows_inactive_card_without_refresh() -> (
    None
):
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        driver.find_element(By.CSS_SELECTOR, ".menu-item[data-menu='sessoes']").click()
        wait.until(
            lambda drv: (
                "Sessões"
                in [
                    e.text.strip()
                    for e in drv.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
                ]
            )
        )

        menu_tab = None
        for el in driver.find_elements(By.CSS_SELECTOR, ".submenu-item"):
            if el.text.strip() == "Menu":
                menu_tab = el
                break
        assert menu_tab is not None, "Aba 'Menu' nao encontrada"
        menu_tab.click()

        wait.until(
            lambda drv: (
                _card_state(drv, "menu-subprocess-card-inactive").get("computedDisplay")
                == "block"
            )
        )

        state = _card_state(driver, "menu-subprocess-card-inactive")
        assert state["exists"], (
            "Card 'Menus inativos' nao existe no DOM apos navegacao por clique"
        )
        assert state["computedDisplay"] == "block", (
            f"Card 'Menus inativos' nao esta visivel apos navegacao por clique: {state}"
        )
    finally:
        driver.quit()


####################################################################################
# (7) FONTE: activateSubprocessCardsV1 -- rotina unica reutilizavel (alias exposto
# em window) que ativa card de acao + listas ativos/inativos em conjunto, com o
# parametro "source" propagado pelos pontos de entrada de navegacao (boot, clique
# na sidebar, clique nas abas do submenu) para permitir depuracao/telemetria.
####################################################################################


####################################################################################
# (8) BUG GLOBAL DO EDITOR DE PROCESSO: Cancelar/Guardar tem de SEMPRE devolver o
# utilizador a lista de origem (nunca deixar #settings-menu-edit-card preso), em
# QUALQUER aba -- fluxo generico, reutilizado por todas as abas do editor.
####################################################################################


def _open_estruturas_menu_list_v1(
    driver: webdriver.Chrome, wait: WebDriverWait
) -> None:
    driver.find_element(By.CSS_SELECTOR, ".menu-item[data-menu='sessoes']").click()
    wait.until(
        lambda drv: (
            "Sessões"
            in [
                e.text.strip()
                for e in drv.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
            ]
        )
    )

    menu_tab = None
    for el in driver.find_elements(By.CSS_SELECTOR, ".submenu-item"):
        if el.text.strip() == "Menu":
            menu_tab = el
            break
    assert menu_tab is not None, "Aba 'Menu' nao encontrada"
    menu_tab.click()

    wait.until(
        lambda drv: (
            _card_state(drv, "menu-subprocess-card-active").get("computedDisplay")
            == "block"
        )
    )
    wait.until(
        lambda drv: (
            _card_state(drv, "menu-subprocess-card-active").get("rowCount", 0) > 0
        )
    )


def _open_process_editor_from_list_v1(
    driver: webdriver.Chrome, wait: WebDriverWait
) -> None:
    # As acoes de linha ficam atras de um menu "kebab" (botao com aria-haspopup): o link de
    # "Editar" so existe dentro do popup, que e' reposicionado para document.body ao abrir
    # (portal), por isso capturamos as referencias ANTES de clicar no gatilho.
    active_card = driver.find_element(By.ID, "menu-subprocess-card-active")
    actions_menu = active_card.find_element(
        By.CSS_SELECTOR,
        "tbody tr:not([style*='display: none']) .appgenesis-row-actions-menu-v1",
    )
    trigger = actions_menu.find_element(
        By.CSS_SELECTOR, ".appgenesis-row-actions-trigger-v1"
    )
    edit_link = actions_menu.find_element(
        By.CSS_SELECTOR, ".appgenesis-row-actions-item-edit-v1"
    )

    trigger.click()
    wait.until(EC.visibility_of(edit_link))
    edit_link.click()

    wait.until(EC.visibility_of_element_located((By.ID, "settings-menu-edit-card")))
    wait.until(lambda drv: "settings_edit_key" in _current_href_v1(drv))


def _editor_card_closed_v1(driver: webdriver.Chrome) -> bool:
    # O editor pode fechar de duas formas legitimas: escondido via JS (Cancelar, sem reload)
    # ou ausente do DOM porque o backend so renderiza a section quando settings_edit_data
    # existe (Guardar, com reload completo apos o redirect). Ambas contam como "fechado".
    state = _card_state(driver, "settings-menu-edit-card")
    return not state.get("exists") or state.get("computedDisplay") == "none"


def _assert_editor_closed_and_list_visible_v1(
    driver: webdriver.Chrome, wait: WebDriverWait
) -> None:
    wait.until(_editor_card_closed_v1)
    wait.until(
        lambda drv: (
            _card_state(drv, "menu-subprocess-card-active").get("computedDisplay")
            == "block"
        )
    )
    current_href = _current_href_v1(driver)
    assert "settings_edit_key" not in current_href, current_href


def test_process_editor_cancel_returns_to_origin_list_on_multiple_tabs() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        _open_estruturas_menu_list_v1(driver, wait)

        # (a) Cancelar na aba "Geral" (aba ativa por omissao).
        _open_process_editor_from_list_v1(driver, wait)
        driver.find_element(
            By.CSS_SELECTOR, ".process-edit-pane.active .action-btn-cancel"
        ).click()
        _assert_editor_closed_and_list_visible_v1(driver, wait)

        # (b) Reabrir e cancelar numa segunda aba ("Configuração dos campos"), provando que
        # a saida do editor e generica e nao depende da aba especifica.
        _open_process_editor_from_list_v1(driver, wait)
        driver.find_element(
            By.CSS_SELECTOR, "[data-process-edit-tab='campos-config']"
        ).click()
        wait.until(
            lambda drv: (
                "campos-config"
                in (
                    drv.find_element(
                        By.CSS_SELECTOR, ".process-edit-pane.active"
                    ).get_attribute("data-process-edit-pane")
                )
            )
        )
        driver.find_element(
            By.CSS_SELECTOR, ".process-edit-pane.active .action-btn-cancel"
        ).click()
        _assert_editor_closed_and_list_visible_v1(driver, wait)
    finally:
        driver.quit()


def test_process_editor_save_returns_to_origin_list_without_manual_refresh() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        _open_estruturas_menu_list_v1(driver, wait)

        _open_process_editor_from_list_v1(driver, wait)

        # Guarda na aba "Geral" sem tocar em nenhum campo -- reenvia os mesmos valores ja
        # carregados no formulario, cobrindo "Guardar" sem alterar dados criticos.
        driver.find_element(
            By.CSS_SELECTOR, ".process-edit-pane.active .action-btn[type='submit']"
        ).click()

        wait.until(lambda drv: "settings_edit_key" not in _current_href_v1(drv))
        _assert_editor_closed_and_list_visible_v1(driver, wait)
        # No subprocesso "Sessoes > Menu" o alerta inline ".alert.ok" e' deliberadamente
        # suprimido (ver _suppress_inline_success_feedback em macros/admin_subprocess.html) --
        # o feedback de sucesso desse fluxo e' promovido a um toast global lido do query
        # param "success" pelo runtime (enhanceFeedbackToasts), por isso a confirmacao aqui
        # verifica o toast, nao o alerta inline.
        success_toast = wait.until(
            lambda drv: drv.find_element(
                By.CSS_SELECTOR, ".appgenesis-toast-v1.appgenesis-toast-success-v1"
            )
        )
        assert "sucesso" in success_toast.text.strip().lower(), success_toast.text
    finally:
        driver.quit()


def test_new_user_js_exposes_activate_subprocess_cards_alias_and_source_tracking() -> (
    None
):
    js_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(
        encoding="utf-8"
    )
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_cards_visibility_v1.js"
    ).read_text(encoding="utf-8")
    menu_runtime_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_menu_runtime_v1.js"
    ).read_text(encoding="utf-8")

    assert (
        "window.activateSubprocessCardsV1 = function (menuKey, targetSelector, source) {"
        in js_text
    )
    assert (
        'function applyContentForMenuTarget(menuKey, targetSelector, source = "unspecified") {'
        in js_text
    )
    assert (
        "return applyContentForMenuTarget(menuKey, targetSelector, source);" in js_text
    )
    assert '"activateSubprocessCardsV1:resolve"' in module_text
    assert '"activateSubprocessCardsV1:applied"' in module_text

    assert 'source: "boot"' in js_text
    assert '"click:sidebar"' in menu_runtime_text
    assert '"click:submenu-tab"' in (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_submenu_runtime_v1.js"
    ).read_text(encoding="utf-8")
