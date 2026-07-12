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


####################################################################################
# (2) GRID RESPONSIVO DO EDITOR DE LISTAS
####################################################################################


def test_process_lists_editor_uses_expected_computed_grid_by_viewport() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    try:
        _login_owner_v1(driver, wait)
        _open_lists_editor_v1(driver, wait)

        expected_columns = ((1920, 3), (1366, 3), (1024, 2), (768, 1))
        for width, expected_count in expected_columns:
            driver.set_window_size(width, 1200)
            columns = driver.execute_script(
                """
                const editor = document.querySelector(
                  "[data-process-list-reusable-manager] " +
                  "[data-process-list-reusable-editor-block].process-lists-editor-grid-v1"
                );
                return editor ? getComputedStyle(editor).gridTemplateColumns : "";
                """
            )
            assert len(columns.split()) == expected_count, (width, columns)

        stylesheet_urls = driver.execute_script(
            "return Array.from(document.styleSheets, (sheet) => sheet.href || '');"
        )
        assert any(
                "configurable_items_manager_v1.css"
                "?v=20260712-process-lists-source-menu-v1" in url
            for url in stylesheet_urls
        )
    finally:
        driver.quit()


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


####################################################################################
# (3) LISTA AUTOMÁTICA COM MENU DE ORIGEM
####################################################################################


def test_automatic_list_source_menu_real_flow() -> None:
    label = "Lista automática Selenium"
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    try:
        _login_owner_v1(driver, wait)
        _open_lists_editor_v1(driver, wait)
        removed_before = driver.execute_script(
            """
            const form = document.querySelector("form[data-process-lists-manager-v1='1']");
            const manager = form && form.processListsManagerV1;
            const expected = String(arguments[0] || '').toLowerCase();
            if (!manager) return false;
            const filtered = manager.getItems().filter(
              (item) => String(item.label || '').toLowerCase() !== expected
            );
            if (filtered.length === manager.getItems().length) return false;
            manager.setItems(filtered);
            manager.syncHiddenInputs();
            return true;
            """,
            label,
        )
        if removed_before:
            submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
            submit.click()
            wait.until(EC.staleness_of(submit))
            _open_lists_editor_v1(driver, wait)
        field_type = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-field-type]")
        items = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-items]")
        menu = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-menu]")

        assert field_type.get_attribute("value") == "manual"
        assert items.is_displayed()
        assert not menu.is_displayed()

        items.send_keys("Rascunho manual")
        driver.execute_script(
            "arguments[0].value='automatic'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            field_type,
        )
        assert not items.is_displayed()
        assert menu.is_displayed()
        source_options = [option for option in menu.find_elements(By.TAG_NAME, "option") if option.get_attribute("value")]
        assert source_options
        source_key = source_options[0].get_attribute("value")
        source_label = source_options[0].text
        driver.execute_script("arguments[0].value=arguments[1]", menu, source_key)
        assert menu.get_attribute("value") == source_key
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-label]").send_keys(label)
        submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
        submit.click()
        wait.until(EC.staleness_of(submit))

        _open_lists_editor_v1(driver, wait)
        assert "settings_tab=lista" in driver.current_url
        table_body = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]")
        assert label.lower() in table_body.text.lower()
        assert source_label in table_body.text
        row = next(row for row in table_body.find_elements(By.TAG_NAME, "tr") if label.lower() in row.text.lower())
        edit_button = row.find_element(By.CSS_SELECTOR, "[data-configurable-action='edit']")
        driver.execute_script("arguments[0].click()", edit_button)
        menu = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-menu]")
        assert menu.is_displayed()
        assert menu.get_attribute("value") == source_key

        field_type = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-field-type]")
        driver.execute_script(
            "arguments[0].value='manual'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            field_type,
        )
        assert driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-items]").is_displayed()
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-cancel]").click()
        wait.until(lambda current: current.find_element(By.CSS_SELECTOR, "[data-process-list-editor-field-type]").get_attribute("value") == "manual")
        assert driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-menu]").get_attribute("value") == ""
    finally:
        try:
            _open_lists_editor_v1(driver, wait)
            removed = driver.execute_script(
                """
                const form = document.querySelector("form[data-process-lists-manager-v1='1']");
                const manager = form && form.processListsManagerV1;
                if (!manager) return false;
                const expected = String(arguments[0] || '').toLowerCase();
                const filtered = manager.getItems().filter(
                  (item) => String(item.label || '').toLowerCase() !== expected
                );
                manager.setItems(filtered);
                manager.syncHiddenInputs();
                return true;
                """,
                label,
            )
            if removed:
                submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
                submit.click()
                wait.until(EC.staleness_of(submit))
        finally:
            driver.quit()
