import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD

TARGET_URL = (
    "http://127.0.0.1:8000/users/new?menu=sessoes&admin_tab=contas"
    "&settings_action=edit&target=settings-menu-edit-card"
    "&settings_edit_key=perfil_de_autorizacao&settings_tab=campos-adicionais"
    "#settings-menu-edit-card"
)


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


def _browser_console_errors_v1(driver: webdriver.Chrome) -> list[dict]:
    return [
        entry
        for entry in driver.get_log("browser")
        if str(entry.get("level") or "").upper() == "SEVERE"
        and "favicon.ico" not in str(entry.get("message") or "")
    ]


####################################################################################
# (2) DROPDOWN DE LISTAS DEVE SER ALIMENTADO PELO PAYLOAD DO TEMPLATE
####################################################################################


def test_additional_fields_list_dropdown_uses_process_lists_payload() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        driver.get(TARGET_URL)
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-process-lists]"))
        )

        raw_payload = driver.execute_script(
            "return document.querySelector('[data-process-lists]')?.dataset.processLists || '';"
        )
        assert raw_payload
        assert "Perfil" in raw_payload

        driver.execute_script(
            """
            const typeSelect = document.querySelector('[data-additional-field-editor-type]');
            if (!typeSelect) {
              return false;
            }
            typeSelect.value = 'list';
            typeSelect.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
            """
        )

        wait.until(
            lambda drv: drv.execute_script(
                """
                const listSelect = document.querySelector('[data-additional-field-editor-list-key]');
                return Boolean(listSelect && listSelect.options && listSelect.options.length > 0);
                """
            )
        )

        options = driver.execute_script(
            """
            const listSelect = document.querySelector('[data-additional-field-editor-list-key]');
            return {
              disabled: Boolean(listSelect && listSelect.disabled),
              options: Array.from(listSelect ? listSelect.options : []).map((option) => ({
                value: option.value,
                text: option.textContent.trim()
              }))
            };
            """
        )

        assert options["disabled"] is False
        option_texts = [option["text"] for option in options["options"]]
        assert "Selecione a lista" in option_texts
        assert "Perfil" in option_texts
        assert not _browser_console_errors_v1(driver), _browser_console_errors_v1(driver)
    finally:
        driver.quit()
