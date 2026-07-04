from __future__ import annotations

from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appverbo.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD

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
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(admin_email)
    driver.find_element(By.NAME, "password").send_keys(admin_password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/users/new"))


####################################################################################
# (2) REFRESH NORMAL DO BROWSER DEVE SEMPRE VOLTAR PARA HOME, A PARTIR DE QUALQUER
# MENU CLICADO CLIENT-SIDE (Estruturas>Menu, Calendario, Perfil de autorizacao,
# Extrato) -- nao deve restaurar Menu/Estruturas/Sessoes/ultimo processo.
####################################################################################


@pytest.mark.parametrize("data_menu", ["sessoes", "calendario", "perfil_de_autorizacao", "extrato"])
def test_reload_from_any_menu_normalizes_to_home(data_menu: str) -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        menu_item = driver.find_elements(By.CSS_SELECTOR, f".menu-item[data-menu='{data_menu}']")
        if not menu_item:
            pytest.skip(f"menu-item '{data_menu}' nao existe no sidebar deste ambiente")
        menu_item[0].click()
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        driver.refresh()
        wait.until(EC.url_contains("/users/new"))
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        assert "menu=home" in driver.current_url, (
            f"Refresh a partir de '{data_menu}' nao normalizou para Home: {driver.current_url}"
        )
    finally:
        driver.quit()


####################################################################################
# (3) UM MARCADOR DE SUCESSO/ERRO PERSISTENTE NA URL NAO DEVE BLOQUEAR A NORMALIZACAO
# PARA HOME NUM REFRESH NORMAL (gap identificado: clearPostSaveFeedbackMarkersFromUrlV3
# so limpava "appverbo_after_save", nao outros marcadores "*_success"/"*_error").
####################################################################################


def test_reload_with_persistent_success_marker_still_normalizes_to_home() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        driver.get("http://127.0.0.1:8000/users/new?menu=sessoes&admin_tab=contas&settings_success=1")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        driver.refresh()
        wait.until(EC.url_contains("/users/new"))
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        assert "menu=home" in driver.current_url, driver.current_url
    finally:
        driver.quit()


####################################################################################
# (4) CONTEXTO DE EDICAO EM CURSO (protegido) NAO DEVE SER EXPULSO PARA HOME NUM
# REFRESH -- perder esse estado significaria perder trabalho nao guardado.
####################################################################################


def test_reload_in_protected_edit_context_is_not_redirected_to_home() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        protected_url = (
            "http://127.0.0.1:8000/users/new?menu=sessoes&admin_tab=contas"
            "&settings_edit_key=some-key&target=%23settings-menu-edit-card"
        )
        driver.get(protected_url)
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        driver.refresh()
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        assert "menu=home" not in driver.current_url, driver.current_url
        assert "settings_edit_key" in driver.current_url, driver.current_url
    finally:
        driver.quit()


####################################################################################
# (5) LOADER GLOBAL: markup existe com role=status/aria-live=polite, comeca escondido,
# e aparece/desaparece durante navegacao client-side (clique na sidebar).
####################################################################################


def test_global_loading_overlay_exists_and_toggles_on_sidebar_click() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        overlay = wait.until(EC.presence_of_element_located((By.ID, "appverbo-global-loading-overlay")))
        assert overlay.get_attribute("role") == "status"
        assert overlay.get_attribute("aria-live") == "polite"
        assert overlay.get_attribute("aria-hidden") == "true"

        driver.find_element(By.CSS_SELECTOR, ".menu-item[data-menu='sessoes']").click()

        wait.until(lambda drv: "true" == drv.execute_script(
            "return document.getElementById('appverbo-global-loading-overlay')"
            ".classList.contains('appverbo-global-loading-overlay--visible') ? 'true' : 'false'"
        ) or "false" == drv.execute_script(
            "return document.getElementById('appverbo-global-loading-overlay')"
            ".getAttribute('aria-hidden')"
        ))

        wait.until(lambda drv: drv.execute_script(
            "return document.getElementById('appverbo-global-loading-overlay')"
            ".getAttribute('aria-hidden')"
        ) == "true")

        final_state = driver.execute_script(
            "return document.getElementById('appverbo-global-loading-overlay')"
            ".classList.contains('appverbo-global-loading-overlay--visible')"
        )
        assert final_state is False, "Loader global ficou preso visivel apos a navegacao terminar"
    finally:
        driver.quit()


####################################################################################
# (6) FONTE: showGlobalLoadingOverlayV1/hideGlobalLoadingOverlayV1 expostos
# globalmente, com timeout de seguranca, e disparados no beforeunload (cobre
# refresh/navegacao real e submits que navegam).
####################################################################################


def test_global_loading_overlay_module_exposes_expected_api() -> None:
    js_text = (PROJECT_ROOT / "static" / "js" / "modules" / "global_loading_overlay_v1.js").read_text(
        encoding="utf-8"
    )

    assert "window.showGlobalLoadingOverlayV1 = showGlobalLoadingOverlayV1;" in js_text
    assert "window.hideGlobalLoadingOverlayV1 = hideGlobalLoadingOverlayV1;" in js_text
    assert 'addEventListener("beforeunload"' in js_text
    assert 'addEventListener("pageshow"' in js_text
    assert "SAFETY_TIMEOUT_MS = 10000" in js_text


def test_base_template_wires_global_loading_overlay_markup() -> None:
    html_text = (PROJECT_ROOT / "templates" / "base.html").read_text(encoding="utf-8")

    assert 'id="appverbo-global-loading-overlay"' in html_text
    assert 'role="status"' in html_text
    assert 'aria-live="polite"' in html_text
    assert "global_loading_overlay_v1.js" in html_text
    assert "global_loading_overlay_v1.css" in html_text


####################################################################################
# (7) FONTE: reload->Home nao fica bloqueado por marcadores de feedback pos-save --
# a condicao "!isPostSaveFeedbackUrl" foi removida do gatilho de normalizacao.
####################################################################################


def test_reload_guard_normalizes_regardless_of_feedback_markers() -> None:
    js_text = (PROJECT_ROOT / "static" / "js" / "modules" / "navigation_reload_guard_v1.js").read_text(
        encoding="utf-8"
    )

    assert "function isBrowserReloadNavigationV1()" in js_text
    assert "function normalizeReloadToHomeV1()" in js_text
    assert "if (hasProtectedReloadContext) {" in js_text
    assert "!isPostSaveFeedbackUrl &&" not in js_text


####################################################################################
# (8) FONTE: o post-save usa o sinal autoritativo de menu ativo e a URL de retorno
# fornecida pela propria config do subprocesso (*_return_url), em vez de tentar
# adivinhar pela URL do browser (que nao muda em navegacao client-side).
####################################################################################


def test_post_save_uses_authoritative_menu_and_config_return_url() -> None:
    js_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "function resolveAuthoritativeActiveMenuKeyForPostSaveV1()" in js_text
    assert "function findConfigProvidedReturnUrlV1(form)" in js_text
    assert "window.__appverboGetActiveMenuKeyV1()" in js_text
