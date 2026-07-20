from urllib.parse import parse_qs, quote, urlsplit

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tests.test_process_submenu_runtime_stage6_browser import (
    _browser_console_errors_v1,
    _build_driver_v1,
    _login_admin_v1,
)


def _wait_for_meu_perfil_page_v1(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
    wait.until(EC.presence_of_element_located((By.ID, "perfil-pessoal-card")))
    wait.until(
        lambda drv: drv.execute_script(
            """
            return Boolean(
              window.__APPGENESIS_BOOTSTRAP__ &&
              window.__APPGENESIS_BOOTSTRAP__.meuPerfil &&
              window.__APPGENESIS_BOOTSTRAP__.meuPerfil.menuKey === "meu_perfil"
            );
            """
        )
    )


def _active_sidebar_menu_key_v1(driver: webdriver.Chrome) -> str:
    active_menu = driver.find_elements(By.CSS_SELECTOR, ".menu-item.active")
    if not active_menu:
        return ""
    return str(active_menu[0].get_attribute("data-menu") or "").strip().lower()


def test_meu_perfil_browser_navigation_uses_canonical_bootstrap_and_tabs_v1() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        for tab_key, expected_card_id in [
            ("pessoal", "perfil-pessoal-card"),
            ("morada", "perfil-morada-card"),
            ("treinamento", "dados-treinamento-card"),
        ]:
            target = f"#{expected_card_id}"
            driver.get(
                "http://127.0.0.1:8000/users/new"
                f"?menu=perfil&profile_tab={tab_key}&target={quote(target)}{target}"
            )
            _wait_for_meu_perfil_page_v1(driver, wait)

            bootstrap = driver.execute_script(
                """
                return window.__APPGENESIS_BOOTSTRAP__.meuPerfil;
                """
            )
            assert bootstrap["menuKey"] == "meu_perfil"
            assert bootstrap["activeTab"] == tab_key
            assert bootstrap["activeTarget"] == f"#{expected_card_id}"
            assert [tab["key"] for tab in bootstrap["tabs"]] == ["pessoal", "morada", "treinamento"]

            assert driver.execute_script(
                """
                return Boolean(document.getElementById(arguments[0]));
                """,
                expected_card_id,
            )
            active_section = driver.execute_script(
                """
                const input = document.querySelector("[data-meu-perfil-section-input]");
                return input ? String(input.value || "") : "";
                """
            )
            assert isinstance(active_section, str)

        assert not _browser_console_errors_v1(driver)
    finally:
        driver.quit()


def test_meu_perfil_sidebar_navigation_updates_url_and_clears_previous_target_v1() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        driver.get(
            "http://127.0.0.1:8000/users/new"
            "?menu=perfil_de_autorizacao&target=%23auth-objeto-form-card#auth-objeto-form-card"
        )
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
        wait.until(lambda drv: _active_sidebar_menu_key_v1(drv) == "perfil_de_autorizacao")
        assert "perfil_de_autorizacao" in driver.current_url
        assert "auth-objeto-form-card" in driver.current_url

        for menu_key in ["administrativo", "meu_perfil", "contactos", "meu_perfil", "perfil_de_autorizacao"]:
            driver.find_element(By.CSS_SELECTOR, f".menu-item[data-menu='{menu_key}']").click()
            wait.until(lambda drv, expected=menu_key: _active_sidebar_menu_key_v1(drv) == expected)

            parsed_url = urlsplit(driver.current_url)
            parsed_query = parse_qs(parsed_url.query)
            assert parsed_query.get("menu") == [menu_key]
            if menu_key == "meu_perfil":
                wait.until(EC.visibility_of_element_located((By.ID, "perfil-pessoal-card")))
                assert driver.find_element(By.ID, "perfil-pessoal-card").is_displayed()
                assert not driver.find_element(By.ID, "perfil-morada-card").is_displayed()
                assert not driver.find_element(By.ID, "dados-treinamento-card").is_displayed()
            else:
                assert not driver.find_element(By.ID, "perfil-pessoal-card").is_displayed()

            assert "target=%23auth-objeto-form-card" not in driver.current_url
            assert "#auth-objeto-form-card" not in driver.current_url
            assert "profile_tab=" not in driver.current_url
            assert "profile_section=" not in driver.current_url
            assert parsed_url.fragment == ""

        assert not _browser_console_errors_v1(driver)
    finally:
        driver.quit()
