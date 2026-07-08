import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD


####################################################################################
# (1) HELPERS
####################################################################################


def _build_chrome_driver_v1() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
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


def _card_is_visible_v1(driver: webdriver.Chrome, card_id: str) -> bool:
    return bool(
        driver.execute_script(
            """
            const el = document.getElementById(arguments[0]);
            if (!el) return false;
            return window.getComputedStyle(el).display !== "none";
            """,
            card_id,
        )
    )


def _click_menu_v1(driver: webdriver.Chrome, menu_key: str) -> None:
    clicked = driver.execute_script(
        """
        const menuKey = arguments[0];
        const button = document.querySelector(`.menu-item[data-menu="${menuKey}"]`);
        if (!button) return false;
        button.click();
        return true;
        """,
        menu_key,
    )
    assert clicked, f"Menu '{menu_key}' nao encontrado."


def _click_submenu_v1(driver: webdriver.Chrome, label: str) -> None:
    clicked = driver.execute_script(
        """
        const expected = String(arguments[0] || "").trim();
        const links = Array.from(document.querySelectorAll(".submenu-item"));
        const link = links.find((item) => String(item.textContent || "").trim() === expected);
        if (!link) return false;
        link.click();
        return true;
        """,
        label,
    )
    assert clicked, f"Submenu '{label}' nao encontrado."


def _active_sidebar_menu_keys_v1(driver: webdriver.Chrome) -> list[str]:
    return driver.execute_script(
        """
        return Array.from(document.querySelectorAll(".menu-item.active"))
          .map((element) => String(element.getAttribute("data-menu") || "").trim().toLowerCase())
          .filter(Boolean);
        """
    )


def _browser_console_errors_v1(driver: webdriver.Chrome) -> list[dict]:
    return [
        entry
        for entry in driver.get_log("browser")
        if str(entry.get("level") or "").upper() == "SEVERE"
        and "favicon.ico" not in str(entry.get("message") or "")
    ]


####################################################################################
# (2) STAGE 5 CLICK VALIDATION
####################################################################################


def test_stage5_process_cards_visibility_click_flow_keeps_runtime_behavior() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        driver.get("http://127.0.0.1:8000/users/new")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        _click_menu_v1(driver, "administrativo")
        wait.until(lambda drv: "administrativo" in _active_sidebar_menu_keys_v1(drv))
        wait.until(lambda drv: _card_is_visible_v1(drv, "create-entity-card"))

        _click_submenu_v1(driver, "Utilizador")
        wait.until(lambda drv: _card_is_visible_v1(drv, "admin-users-created-card"))

        _click_menu_v1(driver, "sessoes")
        wait.until(lambda drv: "sessoes" in _active_sidebar_menu_keys_v1(drv))
        _click_submenu_v1(driver, "Sessões")
        wait.until(lambda drv: _card_is_visible_v1(drv, "admin-sidebar-sections-card-active"))

        _click_submenu_v1(driver, "Menu")
        wait.until(lambda drv: _card_is_visible_v1(drv, "menu-subprocess-card-active"))

        _click_menu_v1(driver, "perfil_de_autorizacao")
        wait.until(lambda drv: "perfil_de_autorizacao" in _active_sidebar_menu_keys_v1(drv))
        _click_submenu_v1(driver, "Perfis")
        wait.until(lambda drv: _card_is_visible_v1(drv, "auth-profile-active-card"))

        _click_submenu_v1(driver, "Objeto de autorização")
        wait.until(lambda drv: _card_is_visible_v1(drv, "auth-objeto-active-card"))

        candidate_menu_keys = driver.execute_script(
            """
            const fixedKeys = new Set([
              "home",
              "perfil",
              "links",
              "contato",
              "tutorial",
              "administrativo",
              "meu_perfil",
              "sessoes",
              "empresa",
              "perfil_de_autorizacao",
              "funcionarios",
              "financeiro",
              "relatorios"
            ]);
            return Array.from(document.querySelectorAll(".menu-item[data-menu]"))
              .map((element) => String(element.getAttribute("data-menu") || "").trim().toLowerCase())
              .filter((menuKey) => menuKey && !fixedKeys.has(menuKey));
            """
        )
        assert candidate_menu_keys, "Nenhum processo dinâmico visível foi encontrado no sidebar."

        matched_menu_key = ""
        for menu_key in candidate_menu_keys:
            _click_menu_v1(driver, menu_key)
            wait.until(lambda drv: menu_key in _active_sidebar_menu_keys_v1(drv))
            if _card_is_visible_v1(driver, "dynamic-process-card"):
                matched_menu_key = menu_key
                break

        assert matched_menu_key, f"Nenhum dos processos {candidate_menu_keys!r} abriu o card dinâmico."
        assert _card_is_visible_v1(driver, "dynamic-process-card")
        assert not _browser_console_errors_v1(driver), _browser_console_errors_v1(driver)
    finally:
        driver.quit()
