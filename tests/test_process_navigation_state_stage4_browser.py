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
# (2) STAGE 4 URL VALIDATION
####################################################################################


@pytest.mark.parametrize(
    ("url", "expected_sidebar_menu", "expected_visible_card"),
    [
        ("/users/new", "home", "home-summary-card"),
        ("/users/new?menu=home", "home", "home-summary-card"),
        (
            "/users/new?menu=sessoes&admin_tab=contas&target=menu-subprocess-card-active#menu-subprocess-card-active",
            "sessoes",
            "menu-subprocess-card-active",
        ),
        pytest.param(
            "/users/new?menu=sessoes&admin_tab=sessoes",
            "sessoes",
            "admin-sidebar-sections-card",
            marks=pytest.mark.xfail(
                strict=False,
                reason="The sections card still follows the active submenu path during bootstrap.",
            ),
        ),
        pytest.param(
            "/users/new?menu=perfil_de_autorizacao&target=auth-profile-card#auth-profile-card",
            "perfil_de_autorizacao",
            "auth-profile-card",
            marks=pytest.mark.xfail(
                strict=False,
                reason="Authorization profile wrapper target remains backed by the active card path.",
            ),
        ),
    ],
)
def test_stage4_process_navigation_state_routes_keep_runtime_behavior(
    url: str,
    expected_sidebar_menu: str,
    expected_visible_card: str,
) -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        driver.get(f"http://127.0.0.1:8000{url}")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
        wait.until(lambda drv: expected_sidebar_menu in _active_sidebar_menu_keys_v1(drv))
        wait.until(lambda drv: _card_is_visible_v1(drv, expected_visible_card))

        assert expected_sidebar_menu in _active_sidebar_menu_keys_v1(driver)
        assert _card_is_visible_v1(driver, expected_visible_card)
        assert not _browser_console_errors_v1(driver), _browser_console_errors_v1(driver)
    finally:
        driver.quit()
