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
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
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
            (
                By.CSS_SELECTOR,
                "[data-process-list-reusable-manager] [data-configurable-create-trigger]",
            )
        )
    ).click()
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
                "?v=20260713-shared-list-card-header-v1" in url
            for url in stylesheet_urls
        )
    finally:
        driver.quit()


def test_process_lists_entity_field_shows_only_entity_number_in_real_browser() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    try:
        _login_owner_v1(driver, wait)
        for width in (1920, 1366, 1024, 768):
            driver.set_window_size(width, 1200)
            _open_lists_editor_v1(driver, wait)

            entity_input = driver.find_element(By.ID, "process-list-editor-entity")
            entity_value = entity_input.get_attribute("value").strip()

            assert entity_value != ""
            assert entity_value.isdigit(), (width, entity_value)

            assert not driver.find_elements(
                By.CSS_SELECTOR, "[data-process-list-columns-manager]"
            )
            assert "Colunas da listagem do processo" not in driver.page_source
    finally:
        driver.quit()


def _remove_test_list_v1(driver, wait) -> None:
    _remove_process_list_by_label_v1(driver, wait, "Lista teste")


def _remove_process_list_by_label_v1(driver, wait, label: str) -> None:
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
        if (filtered.length === manager.getItems().length) return false;
        manager.setItems(filtered);
        manager.syncHiddenInputs();
        return true;
        """,
        label,
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
            return {
              managerAbsent: document.querySelector("[data-process-list-columns-manager]") === null,
              sectionTitleAbsent: !document.body.innerHTML.includes("Colunas da listagem do processo"),
              managerNotInitialized: !form || form.processListColumnsManagerV2 === undefined
            };
            """
        )
        assert column_diagnostics == {
            "managerAbsent": True,
            "sectionTitleAbsent": True,
            "managerNotInitialized": True,
        }
        assert not [
            entry
            for entry in driver.get_log("browser")
            if entry.get("level") == "SEVERE"
            and "favicon.ico" not in entry.get("message", "")
        ]

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
        table_body = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]")
        assert "Lista teste" in table_body.text
        row = next(row for row in table_body.find_elements(By.TAG_NAME, "tr") if "Lista teste" in row.text)
        entity_cell_value = driver.execute_script(
            """
            const form = document.querySelector("form[data-process-lists-manager-v1='1']");
            return form ? form.querySelector("[data-process-list-reusable-manager]").dataset.entityNumber : null;
            """
        )
        assert entity_cell_value.isdigit()
        assert entity_cell_value in row.text
    finally:
        try:
            _remove_test_list_v1(driver, wait)
            _open_lists_editor_v1(driver, wait)
            assert "Lista teste" not in driver.find_element(
                By.CSS_SELECTOR, "[data-process-lists-table-body]"
            ).text
        finally:
            driver.quit()


def test_process_lists_editor_redirects_to_list_tab_after_status_toggle() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    label = f"Lista status {__import__('time').time_ns()}"
    try:
        _login_owner_v1(driver, wait)
        _remove_process_list_by_label_v1(driver, wait, label)

        _open_lists_editor_v1(driver, wait)
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-label]").send_keys(label)
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-items]").send_keys("A")
        submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
        submit.click()
        wait.until(EC.staleness_of(submit))

        _open_lists_editor_v1(driver, wait)
        table_body = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]")
        row = next(
            row for row in table_body.find_elements(By.TAG_NAME, "tr")
            if label.lower() in row.text.lower()
        )
        edit_button = row.find_element(By.CSS_SELECTOR, "[data-configurable-action='edit']")
        driver.execute_script("arguments[0].click()", edit_button)

        status_select = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-status]")
        driver.execute_script(
            "arguments[0].value='inativo'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            status_select,
        )
        submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
        submit.click()
        wait.until(EC.staleness_of(submit))

        assert "settings_tab=lista" in driver.current_url
        assert "settings_action=edit" in driver.current_url
        assert "settings_edit_key=perfil_de_autorizacao" in driver.current_url

        _open_lists_editor_v1(driver, wait)
        inactive_table_body = driver.find_element(
            By.CSS_SELECTOR, "[data-process-lists-inactive-table-body]"
        )
        assert label.lower() in inactive_table_body.text.lower()

        inactive_row = next(
            row for row in inactive_table_body.find_elements(By.TAG_NAME, "tr")
            if label.lower() in row.text.lower()
        )
        edit_button = inactive_row.find_element(By.CSS_SELECTOR, "[data-configurable-action='edit']")
        driver.execute_script("arguments[0].click()", edit_button)
        status_select = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-status]")
        driver.execute_script(
            "arguments[0].value='ativo'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            status_select,
        )
        submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
        submit.click()
        wait.until(EC.staleness_of(submit))

        assert "settings_tab=lista" in driver.current_url
        assert "settings_action=edit" in driver.current_url
        assert "settings_edit_key=perfil_de_autorizacao" in driver.current_url

        _open_lists_editor_v1(driver, wait)
        active_table_body = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]")
        assert label.lower() in active_table_body.text.lower()
    finally:
        try:
            _remove_process_list_by_label_v1(driver, wait, label)
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
        assert driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-subprocess-wrapper]").is_displayed() is False

        session = driver.find_element(By.ID, "process-list-editor-source-session")
        session_options = [
            (option.get_attribute("value"), option.get_attribute("textContent").strip())
            for option in session.find_elements(By.TAG_NAME, "option")
        ]
        assert ("", "Selecione a sessão") in session_options
        assert ("sistema", "Sistema") in session_options
        assert ("geral", "Geral") in session_options
        assert ("tesouraria", "Tesouraria") in session_options
        assert ("dados_gerais", "Dados gerais") in session_options

        driver.execute_script(
            "arguments[0].value='sistema'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            session,
        )
        menu_options_after_session = [
            (option.get_attribute("value"), option.get_attribute("textContent").strip())
            for option in menu.find_elements(By.TAG_NAME, "option")
        ]
        assert ("perfil_de_autorizacao", "Perfil de autorização") in menu_options_after_session

        driver.execute_script(
            "arguments[0].value='perfil_de_autorizacao'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            menu,
        )
        subprocess = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-subprocess]")
        assert driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-subprocess-wrapper]").is_displayed()
        subprocess_options = [
            (option.get_attribute("value"), option.text)
            for option in subprocess.find_elements(By.TAG_NAME, "option")
        ]
        assert subprocess_options[0] == ("", "Todos os subprocessos")
        assert ("perfis", "Perfis") in subprocess_options
        assert ("objeto_de_autorizacao", "Objeto de autorização") in subprocess_options
        driver.execute_script("arguments[0].value='perfis'", subprocess)
        assert subprocess.get_attribute("value") == "perfis"
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-label]").send_keys(label)
        submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
        submit.click()
        wait.until(EC.staleness_of(submit))

        _open_lists_editor_v1(driver, wait)
        assert "settings_tab=lista" in driver.current_url
        table_body = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]")
        assert label.lower() in table_body.text.lower()
        assert "Perfil de autorização" in table_body.text
        assert "Perfis" in table_body.text
        row = next(row for row in table_body.find_elements(By.TAG_NAME, "tr") if label.lower() in row.text.lower())
        edit_button = row.find_element(By.CSS_SELECTOR, "[data-configurable-action='edit']")
        driver.execute_script("arguments[0].click()", edit_button)
        menu = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-menu]")
        session = driver.find_element(By.ID, "process-list-editor-source-session")
        assert menu.is_displayed()
        assert session.is_displayed()
        assert session.get_attribute("value") == "sistema"
        assert menu.get_attribute("value") == "perfil_de_autorizacao"
        subprocess = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-subprocess]")
        assert subprocess.get_attribute("value") == "perfis"

        field_type = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-field-type]")
        driver.execute_script(
            "arguments[0].value='manual'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            field_type,
        )
        assert driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-items-wrapper]").is_displayed()
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-cancel]").click()
        wait.until(lambda current: current.find_element(By.CSS_SELECTOR, "[data-process-list-editor-field-type]").get_attribute("value") == "manual")
        assert driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-menu]").get_attribute("value") == ""
        assert driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-subprocess]").get_attribute("value") == ""
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


def test_automatic_list_all_sessions_flow_restores_without_extra_click() -> None:
    label = "Lista automática Todas as Sessões Selenium"
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
        session = driver.find_element(By.ID, "process-list-editor-source-session")
        menu = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-menu]")

        driver.execute_script(
            "arguments[0].value='automatic'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            field_type,
        )

        session_options = [
            (option.get_attribute("value"), option.text)
            for option in session.find_elements(By.TAG_NAME, "option")
        ]
        assert session_options[:6] == [
            ("", "Selecione a sessão"),
            ("all_sessions", "Todas as sessões"),
            ("sistema", "Sistema"),
            ("geral", "Geral"),
            ("tesouraria", "Tesouraria"),
            ("dados_gerais", "Dados gerais"),
        ]

        driver.execute_script(
            "arguments[0].value='all_sessions'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            session,
        )

        menu_wrapper = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-menu-wrapper]")
        submenu = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-subprocess]")
        submenu_wrapper = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-subprocess-wrapper]")

        assert menu.get_attribute("value") == ""
        assert submenu.get_attribute("value") == ""
        assert not menu.is_displayed()
        assert not submenu.is_displayed()
        assert menu_wrapper.get_attribute("hidden") is not None
        assert submenu_wrapper.get_attribute("hidden") is not None
        assert menu.find_elements(By.TAG_NAME, "option") == []
        assert submenu.find_elements(By.TAG_NAME, "option") == []
        assert "Menu indisponível" not in menu.text
        assert "Subprocesso indisponível" not in submenu.text

        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-label]").send_keys(label)
        submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
        submit.click()
        wait.until(EC.staleness_of(submit))
        wait.until(
            lambda current_driver: (
                "settings_tab=lista" in current_driver.current_url
                and "target=settings-menu-edit-card" in current_driver.current_url
            )
        )
        table_body_after_save = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]")
        assert label.lower() in table_body_after_save.text.lower()

        _open_lists_editor_v1(driver, wait)
        table_body = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]")
        row = next(
            row
            for row in table_body.find_elements(By.TAG_NAME, "tr")
            if label.lower() in row.text.lower()
        )
        edit_button = row.find_element(By.CSS_SELECTOR, "[data-configurable-action='edit']")
        driver.execute_script("arguments[0].click()", edit_button)

        session = driver.find_element(By.ID, "process-list-editor-source-session")
        menu = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-menu]")
        submenu = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-subprocess]")
        menu_wrapper = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-menu-wrapper]")
        submenu_wrapper = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-subprocess-wrapper]")

        assert session.get_attribute("value") == "all_sessions"
        assert menu.get_attribute("value") == ""
        assert submenu.get_attribute("value") == ""
        assert not menu.is_displayed()
        assert not submenu.is_displayed()
        assert menu_wrapper.get_attribute("hidden") is not None
        assert submenu_wrapper.get_attribute("hidden") is not None
        assert "Sessão indisponível" not in session.text
        assert "Menu indisponível" not in menu.text

        driver.execute_script(
            "arguments[0].value='sistema'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            session,
        )

        assert menu.is_displayed()
        assert not submenu.is_displayed()
        assert menu.find_elements(By.TAG_NAME, "option")
        assert menu.get_attribute("value") == ""
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


def test_legacy_perfil_list_editor_restores_source_controls_without_extra_click() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    try:
        _login_owner_v1(driver, wait)
        _open_lists_editor_v1(driver, wait)

        table_body = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]")
        row = next(
            (
                candidate
                for candidate in table_body.find_elements(By.TAG_NAME, "tr")
                if "Perfil" in candidate.text
            ),
            None,
        )
        assert row is not None, "A lista legada 'Perfil' não foi encontrada."

        edit_button = row.find_element(By.CSS_SELECTOR, "[data-configurable-action='edit']")
        driver.execute_script("arguments[0].click()", edit_button)

        session = driver.find_element(By.ID, "process-list-editor-source-session")
        menu = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-menu]")
        subprocess = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-source-subprocess]")

        assert session.get_attribute("value") == "sistema"
        assert menu.get_attribute("value") == "perfil_de_autorizacao"
        assert subprocess.get_attribute("value") == "perfis"
        assert "Sessão indisponível" not in session.text
        assert "Menu indisponível" not in menu.text
    finally:
        driver.quit()
