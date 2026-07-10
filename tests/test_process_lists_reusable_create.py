import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD


####################################################################################
# (1) BROWSER REAL - CRIAR LISTA REUTILIZAVEL
####################################################################################


TARGET_URL = (
    "http://127.0.0.1:8000/users/new?menu=sessoes&admin_tab=contas"
    "&settings_action=edit&target=settings-menu-edit-card"
    "&settings_edit_key=perfil_de_autorizacao&settings_tab=lista"
    "#settings-menu-edit-card"
)


def _build_driver_v1():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    try:
        return webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Selenium Chrome indisponivel neste ambiente: {exc}")


def _login_owner_v1(driver, wait) -> None:
    email = str(ADMIN_LOGIN_EMAIL or "").strip()
    password = str(ADMIN_LOGIN_PASSWORD or "").strip()
    if not email or not password:
        pytest.skip("ADMIN_LOGIN_EMAIL / ADMIN_LOGIN_PASSWORD nao definidos.")
    driver.get("http://127.0.0.1:8000/login")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/users/new"))


def _open_lists_editor_v1(driver, wait) -> None:
    driver.get(TARGET_URL)
    wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "[data-process-list-editor-label]")
        )
    )


def _remove_test_list_v1(driver, wait) -> None:
    _open_lists_editor_v1(driver, wait)
    removed = driver.execute_script(
        """
        const form = document.querySelector("form[data-process-lists-manager-v1='1']");
        const manager = form && form.processListsManagerV1;
        if (!manager) return false;
        const filtered = manager.getItems().filter((item) => item.label !== "Lista teste");
        if (filtered.length === manager.getItems().length) return false;
        manager.setItems(filtered);
        manager.syncHiddenInputs();
        return true;
        """
    )
    if removed:
        submit_button = driver.find_element(
            By.CSS_SELECTOR, "[data-process-list-editor-submit]"
        )
        submit_button.click()
        wait.until(EC.staleness_of(submit_button))


def test_create_reusable_list_reads_visible_editor_values() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    try:
        _login_owner_v1(driver, wait)
        _remove_test_list_v1(driver, wait)
        _open_lists_editor_v1(driver, wait)
        name_input = driver.find_element(
            By.CSS_SELECTOR, "[data-process-list-editor-label]"
        )
        items_input = driver.find_element(
            By.CSS_SELECTOR, "[data-process-list-editor-items]"
        )
        name_input.clear()
        name_input.send_keys("Lista teste")
        items_input.clear()
        items_input.send_keys("A, B, C")

        diagnostics = driver.execute_script(
            """
            const form = document.querySelector("form[data-process-lists-manager-v1='1']");
            const visible = document.querySelector("[data-process-list-editor-label]");
            const managerLabel = form && form.processListsManagerV1 &&
              form.processListsManagerV1.elements.editorLabel;
            return {
              visibleValue: visible ? visible.value : null,
              managerValue: managerLabel ? managerLabel.value : null,
              labelCount: document.querySelectorAll("[data-process-list-editor-label]").length,
              submitCount: document.querySelectorAll("[data-process-list-editor-submit]").length
            };
            """
        )
        print(f"process-lists diagnostics before validation: {diagnostics}")
        assert diagnostics == {
            "visibleValue": "Lista teste",
            "managerValue": "Lista teste",
            "labelCount": 1,
            "submitCount": 1,
        }

        column_diagnostics = driver.execute_script(
            """
            const form = document.querySelector("form[data-process-lists-manager-v1='1']");
            const manager = form && form.processListColumnsManagerV2;
            return {
              fieldCount: document.querySelectorAll("[data-process-list-column-editor-field]").length,
              labelCount: document.querySelectorAll("[data-process-list-column-editor-label]").length,
              submitCount: document.querySelectorAll("[data-process-list-column-editor-submit]").length,
              managerFieldReady: Boolean(manager && manager.elements.editorField),
              managerLabelReady: Boolean(manager && manager.elements.editorLabel)
            };
            """
        )
        assert column_diagnostics == {
            "fieldCount": 1,
            "labelCount": 1,
            "submitCount": 1,
            "managerFieldReady": True,
            "managerLabelReady": True,
        }

        submit_button = driver.find_element(
            By.CSS_SELECTOR, "[data-process-list-editor-submit]"
        )
        submit_button.click()

        wait.until(EC.staleness_of(submit_button))
        messages = [
            element.text
            for element in driver.find_elements(
                By.CSS_SELECTOR, ".appgenesis-alert-message-v1"
            )
        ]

        assert "Informe o nome da lista." not in messages
        _open_lists_editor_v1(driver, wait)
        assert "Lista teste" in driver.find_element(
            By.CSS_SELECTOR, "[data-process-lists-table-body]"
        ).text
    finally:
        try:
            _remove_test_list_v1(driver, wait)
            _open_lists_editor_v1(driver, wait)
            assert "Lista teste" not in driver.find_element(
                By.CSS_SELECTOR, "[data-process-lists-table-body]"
            ).text
        finally:
            driver.quit()
