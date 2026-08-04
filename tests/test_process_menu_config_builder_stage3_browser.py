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


def _active_submenu_labels_v1(driver: webdriver.Chrome) -> list[str]:
    return [
        element.text.strip()
        for element in driver.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
        if element.text.strip()
    ]


def _browser_console_errors_v1(driver: webdriver.Chrome) -> list[dict]:
    return [
        entry
        for entry in driver.get_log("browser")
        if str(entry.get("level") or "").upper() == "SEVERE"
        and "favicon.ico" not in str(entry.get("message") or "")
    ]


####################################################################################
# (2) STAGE 3 URL VALIDATION
####################################################################################


@pytest.mark.parametrize(
    ("url", "expected_sidebar_menu", "expected_visible_card", "expected_submenu"),
    [
        ("/users/new", "home", "home-summary-card", None),
        ("/users/new?menu=documentos", "meu_perfil", "perfil-pessoal-card", None),
        ("/users/new?menu=administrativo&admin_tab=entidade", "administrativo", "recent-entities-card", "Entidade"),
        (
            "/users/new?menu=sessoes&admin_tab=contas&target=menu-subprocess-card-active#menu-subprocess-card-active",
            "sessoes",
            "menu-subprocess-card-active",
            "Menu",
        ),
        pytest.param(
            "/users/new?menu=perfil_de_autorizacao&target=auth-profile-card#auth-profile-card",
            "perfil_de_autorizacao",
            "auth-profile-active-card",
            "Perfis",
        ),
        pytest.param(
            "/users/new?menu=perfil_de_autorizacao&target=auth-objeto-card#auth-objeto-card",
            "perfil_de_autorizacao",
            "auth-objeto-active-card",
            "Objeto de autorização",
        ),
    ],
)
def test_stage3_process_menu_config_builder_routes_keep_runtime_behavior(
    url: str,
    expected_sidebar_menu: str,
    expected_visible_card: str,
    expected_submenu: str | None,
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

        if expected_submenu:
            wait.until(lambda drv: expected_submenu in _active_submenu_labels_v1(drv))
            assert expected_submenu in _active_submenu_labels_v1(driver)

        assert not _browser_console_errors_v1(driver), _browser_console_errors_v1(driver)
    finally:
        driver.quit()


def test_stage3_process_menu_config_builder_finds_at_least_one_dynamic_process() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        driver.get("http://127.0.0.1:8000/users/new")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

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
            driver.get(f"http://127.0.0.1:8000/users/new?menu={menu_key}")
            wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
            wait.until(lambda drv: menu_key in _active_sidebar_menu_keys_v1(drv))
            if _card_is_visible_v1(driver, "dynamic-process-card"):
                matched_menu_key = menu_key
                break

        assert matched_menu_key, f"Nenhum dos processos {candidate_menu_keys!r} abriu o card dinâmico."
        assert matched_menu_key in _active_sidebar_menu_keys_v1(driver)
        assert _card_is_visible_v1(driver, "dynamic-process-card")
        assert not _browser_console_errors_v1(driver), _browser_console_errors_v1(driver)
    finally:
        driver.quit()
