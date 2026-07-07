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
# (2) STAGE 7 MENU VALIDATION
####################################################################################


def test_stage7_process_menu_runtime_clicks_all_visible_menus() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        driver.get("http://127.0.0.1:8000/users/new")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        visible_menu_keys = driver.execute_script(
            """
            return Array.from(document.querySelectorAll(".menu-item[data-menu]"))
              .map((element) => String(element.getAttribute("data-menu") || "").trim().toLowerCase())
              .filter(Boolean);
            """
        )
        assert visible_menu_keys, "Nenhum menu principal visível foi encontrado."

        for menu_key in visible_menu_keys:
            _click_menu_v1(driver, menu_key)
            wait.until(lambda drv: menu_key in _active_sidebar_menu_keys_v1(drv))

            has_context = driver.execute_script(
                """
                const visibleCards = Array.from(document.querySelectorAll("[data-menu-scope]"))
                  .filter((element) => window.getComputedStyle(element).display !== "none");
                const submenuCount = document.querySelectorAll(".submenu-item").length;
                const dynamicVisible = (() => {
                  const el = document.getElementById("dynamic-process-card");
                  return !!el && window.getComputedStyle(el).display !== "none";
                })();
                return visibleCards.length > 0 || submenuCount > 0 || dynamicVisible;
                """
            )
            assert has_context, f"O menu '{menu_key}' ficou sem contexto visível."

        assert not _browser_console_errors_v1(driver), _browser_console_errors_v1(driver)
    finally:
        driver.quit()
