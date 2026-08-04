import json

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD
from appgenesis.db.session import SessionLocal
from appgenesis.models import Entity, SidebarMenuSetting


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


def _seed_process_list_delete_test_rows_v1() -> tuple[str, str]:
    test_label = "Lista teste eliminação"
    test_key = "list_lista_teste_eliminacao"

    with SessionLocal() as session:
        entity_ids = [
            row[0]
            for row in session.query(Entity.id).all()
        ]

        for entity_id in entity_ids:
            row = (
                session.query(SidebarMenuSetting)
                .filter(
                    SidebarMenuSetting.entity_id == entity_id,
                    SidebarMenuSetting.menu_key == "perfil_de_autorizacao",
                )
                .one_or_none()
            )
            if row is None:
                continue

            config = json.loads(row.menu_config or "{}")
            process_lists = list(config.get("process_lists") or [])
            if any(str(item.get("key") or "").strip() == test_key for item in process_lists):
                continue

            process_lists.append(
                {
                    "key": test_key,
                    "label": test_label,
                    "field_type": "manual",
                    "items": ["1"],
                    "status": "inativo",
                }
            )
            config["process_lists"] = process_lists
            row.menu_config = json.dumps(config, ensure_ascii=False)

        session.commit()

    return test_label, test_key


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
                "?v=20260717-process-lists-responsive-partition-v3" in url
            for url in stylesheet_urls
        )
    finally:
        driver.quit()


def test_process_lists_responsive_layout_and_independent_pagination() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    try:
        _login_owner_v1(driver, wait)
        _open_lists_editor_v1(driver, wait)

        seeded = driver.execute_script(
            """
            const form = document.querySelector("form[data-process-lists-manager-v1='1']");
            const manager = form && form.processListsManagerV1;
            if (!manager) return false;
            const items = [];
            for (let index = 1; index <= 22; index += 1) {
              items.push({
                key: `ativo_${index}`,
                label: `Ativo ${index}`,
                field_type: "manual",
                itemsCsv: `Conteudo ativo ${index}`,
                status: "ativo"
              });
            }
            for (let index = 1; index <= 13; index += 1) {
              items.push({
                key: `inativo_${index}`,
                label: `Inativo ${index}`,
                field_type: "manual",
                itemsCsv: `Conteudo inativo ${index}`,
                status: "inativo"
              });
            }
            manager.setItems(items);
            return true;
            """
        )
        assert seeded is True

        active_body = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]")
        inactive_body = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body]")
        active_page_size = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-page-size]")
        inactive_page_size = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-inactive-page-size]")
        active_pagination = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-pagination]")
        inactive_pagination = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-inactive-pagination]")

        assert len(active_body.find_elements(By.TAG_NAME, "tr")) == 5
        assert len(inactive_body.find_elements(By.TAG_NAME, "tr")) == 5
        assert "5 / 22" in active_pagination.text
        assert "5 / 13" in inactive_pagination.text

        driver.execute_script(
            "arguments[0].value='10'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            active_page_size,
        )
        wait.until(
            lambda current: len(
                current.find_elements(By.CSS_SELECTOR, "[data-process-lists-table-body] tr")
            ) == 10
        )
        assert len(inactive_body.find_elements(By.TAG_NAME, "tr")) == 5

        driver.execute_script(
            "arguments[0].value='10'; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            inactive_page_size,
        )
        wait.until(
            lambda current: len(
                current.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")
            ) == 10
        )
        assert len(active_body.find_elements(By.TAG_NAME, "tr")) == 10

        active_more = active_pagination.find_element(By.CSS_SELECTOR, ".appgenesis-load-more-btn-v1")
        active_more.click()
        wait.until(
            lambda current: len(
                current.find_elements(By.CSS_SELECTOR, "[data-process-lists-table-body] tr")
            ) == 20
        )
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")) == 10

        inactive_more = inactive_pagination.find_element(By.CSS_SELECTOR, ".appgenesis-load-more-btn-v1")
        inactive_more.click()
        wait.until(
            lambda current: len(
                current.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")
            ) == 20
        )
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-process-lists-table-body] tr")) == 20

        actions_info_after_rerender = driver.execute_script(
            """
            const inspectRow = (row) => {
              if (!row) {
                return { hasTrigger: false, popupHidden: false, directDelete: false };
              }
              const trigger = row.querySelector(".appgenesis-row-actions-trigger-v1");
              const popup = row.querySelector(".appgenesis-row-actions-popup-v1");
              const directDelete = Array.from(row.querySelectorAll("button[title='Eliminar']"))
                .some((button) => !button.closest(".appgenesis-row-actions-popup-v1"));
              return {
                hasTrigger: Boolean(trigger),
                popupHidden: Boolean(popup && popup.hidden),
                directDelete
              };
            };
            return {
              active: inspectRow(document.querySelector("[data-process-lists-table-body] tr")),
              inactive: inspectRow(document.querySelector("[data-process-lists-inactive-table-body] tr"))
            };
            """
        )
        assert actions_info_after_rerender["active"]["hasTrigger"] is True
        assert actions_info_after_rerender["inactive"]["hasTrigger"] is True
        assert actions_info_after_rerender["active"]["popupHidden"] is True
        assert actions_info_after_rerender["inactive"]["popupHidden"] is True
        assert actions_info_after_rerender["active"]["directDelete"] is False
        assert actions_info_after_rerender["inactive"]["directDelete"] is False

        visible_counts = []
        for width in (1440, 1200, 992, 768, 480, 360):
            driver.set_window_size(width, 1200)
            driver.execute_async_script(
                """
                const done = arguments[arguments.length - 1];
                requestAnimationFrame(() => requestAnimationFrame(done));
                """
            )
            metrics = driver.execute_script(
                """
                const activeWrap = document.querySelector("[data-process-lists-table]").closest(".configurable-items-table-wrap-v1");
                const inactiveWrap = document.querySelector("[data-process-lists-inactive-table]").closest(".configurable-items-table-wrap-v1");
                const activeVisible = document.querySelectorAll("[data-process-lists-table] thead th:not(.configurable-items-responsive-hidden-v1)").length;
                const inactiveVisible = document.querySelectorAll("[data-process-lists-inactive-table] thead th:not(.configurable-items-responsive-hidden-v1)").length;
                return {
                  activeVisible,
                  inactiveVisible,
                  activeOk: activeWrap ? activeWrap.scrollWidth <= activeWrap.clientWidth : true,
                  inactiveOk: inactiveWrap ? inactiveWrap.scrollWidth <= inactiveWrap.clientWidth : true,
                  docOk: document.documentElement.scrollWidth <= document.documentElement.clientWidth
                };
                """
            )
            assert metrics["docOk"], (width, metrics)
            assert metrics["activeOk"], (width, metrics)
            assert metrics["inactiveOk"], (width, metrics)
            visible_counts.append(metrics["activeVisible"])

        assert visible_counts == sorted(visible_counts, reverse=True)
        assert visible_counts[-1] <= 4
        assert visible_counts[-1] >= 3
    finally:
        driver.quit()


def test_process_lists_real_dom_separates_active_and_inactive_rows() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    try:
        _login_owner_v1(driver, wait)
        _open_lists_editor_v1(driver, wait)
        for selector in ("[data-process-lists-page-size]", "[data-process-lists-inactive-page-size]"):
            driver.execute_script(
                """
                const select = document.querySelector(arguments[0]);
                if (select) {
                  select.value = '5';
                  select.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                selector,
            )

        actions_info = driver.execute_script(
            """
            const activeRow = document.querySelector("[data-process-lists-table-body] tr");
            const inactiveRow = document.querySelector("[data-process-lists-inactive-table-body] tr");
            const inspectRow = (row) => {
              if (!row) {
                return { hasTrigger: false, popupHidden: false, directDelete: false };
              }
              const trigger = row.querySelector(".appgenesis-row-actions-trigger-v1");
              const popup = row.querySelector(".appgenesis-row-actions-popup-v1");
              const directDelete = Array.from(row.querySelectorAll("button[title='Eliminar']"))
                .some((button) => !button.closest(".appgenesis-row-actions-popup-v1"));
              return {
                hasTrigger: Boolean(trigger),
                popupHidden: Boolean(popup && popup.hidden),
                directDelete
              };
            };
            return {
              active: inspectRow(activeRow),
              inactive: inspectRow(inactiveRow)
            };
            """
        )
        assert actions_info["active"]["hasTrigger"] is True
        assert actions_info["inactive"]["hasTrigger"] is True
        assert actions_info["active"]["popupHidden"] is True
        assert actions_info["inactive"]["popupHidden"] is True
        assert actions_info["active"]["directDelete"] is False
        assert actions_info["inactive"]["directDelete"] is False

        stats = driver.execute_script(
            """
            const normalizeStatus = (item) => {
              const rawStatus = item && item.status !== undefined ? item.status : "";
              const rawIsActive = item && item.is_active !== undefined ? item.is_active : "";
              const cleanStatus = String(rawStatus || "")
                .trim()
                .toLowerCase()
                .normalize("NFD")
                .replace(/[\\u0300-\\u036f]/g, "")
                .replace(/[^a-z0-9_]+/g, "_")
                .replace(/_+/g, "_")
                .replace(/^_|_$/g, "");
              const cleanIsActive = String(rawIsActive || "").trim().toLowerCase();

              if (rawStatus === false || cleanStatus === "false" || cleanIsActive === "false" || cleanIsActive === "0") {
                return "inativo";
              }

              if (rawStatus === true || cleanStatus === "true" || cleanIsActive === "true" || cleanIsActive === "1") {
                return "ativo";
              }

              if (cleanStatus === "inactive" || cleanStatus === "inativo" || cleanStatus === "inativa") {
                return "inativo";
              }

              if (cleanStatus === "active" || cleanStatus === "ativo" || cleanStatus === "ativa") {
                return "ativo";
              }

              return "ativo";
            };

            const form = document.querySelector("form[data-process-lists-manager-v1='1']");
            const manager = form && form.processListsManagerV1;
            const items = manager ? manager.getItems() : [];
            const activeTotal = items.filter((item) => normalizeStatus(item) !== "inativo").length;
            const inactiveTotal = items.filter((item) => normalizeStatus(item) === "inativo").length;
            const activeBody = document.querySelector("[data-process-lists-table-body]");
            const inactiveBody = document.querySelector("[data-process-lists-inactive-table-body]");
            const activeRows = Array.from(activeBody ? activeBody.querySelectorAll("tr") : []);
            const inactiveRows = Array.from(inactiveBody ? inactiveBody.querySelectorAll("tr") : []);
            const activeFlags = activeRows.map((row) => Boolean(row.querySelector(".entity-status-active")));
            const inactiveFlags = inactiveRows.map((row) => Boolean(row.querySelector(".entity-status-inactive")));
            const activeCounter = document.querySelector("[data-process-lists-pagination]")?.textContent || "";
            const inactiveCounter = document.querySelector("[data-process-lists-inactive-pagination]")?.textContent || "";
            return {
              activeTotal,
              inactiveTotal,
              activeRows: activeRows.length,
              inactiveRows: inactiveRows.length,
              activeFlags,
              inactiveFlags,
              activeCounter,
              inactiveCounter
            };
            """
        )

        assert stats["activeTotal"] > 0, stats
        assert stats["inactiveTotal"] > 0, stats
        assert stats["activeRows"] == min(5, stats["activeTotal"]), stats
        assert stats["inactiveRows"] == min(5, stats["inactiveTotal"]), stats
        assert all(stats["activeFlags"]), stats
        assert all(stats["inactiveFlags"]), stats
        assert f"{stats['activeRows']} / {stats['activeTotal']}" in stats["activeCounter"], stats
        assert f"{stats['inactiveRows']} / {stats['inactiveTotal']}" in stats["inactiveCounter"], stats
    finally:
        driver.quit()


def test_process_lists_inactive_delete_requires_confirm_and_persists_after_refresh() -> None:
    test_label, test_key = _seed_process_list_delete_test_rows_v1()
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_owner_v1(driver, wait)
        _open_lists_editor_v1(driver, wait)

        search = driver.find_element(By.CSS_SELECTOR, "[data-configurable-search]")
        search.clear()
        search.send_keys(test_label)

        wait.until(
            lambda drv: any(
                test_label.lower() in row.text.lower()
                for row in drv.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")
            )
        )

        inactive_row = next(
            row
            for row in driver.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")
            if test_label.lower() in row.text.lower()
        )
        before_count = len(
            driver.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")
        )

        trigger = inactive_row.find_element(By.CSS_SELECTOR, ".appgenesis-row-actions-trigger-v1")
        trigger.click()
        delete_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".appgenesis-row-actions-popup-v1:not([hidden]) button[title='Eliminar']")
            )
        )
        delete_button.click()

        cancel_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".appgenesis-confirm-cancel-v1"))
        )
        cancel_button.click()

        wait.until(
            lambda drv: any(
                test_label.lower() in row.text.lower()
                for row in drv.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")
            )
        )

        inactive_row = next(
            row
            for row in driver.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")
            if test_label.lower() in row.text.lower()
        )
        trigger = inactive_row.find_element(By.CSS_SELECTOR, ".appgenesis-row-actions-trigger-v1")
        trigger.click()
        delete_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".appgenesis-row-actions-popup-v1:not([hidden]) button[title='Eliminar']")
            )
        )
        delete_button.click()

        confirm_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".appgenesis-confirm-action-v1"))
        )
        confirm_button.click()

        wait.until(
            lambda drv: not any(
                test_label.lower() in row.text.lower()
                for row in drv.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")
            )
        )

        after_count = len(
            driver.find_elements(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body] tr")
        )
        assert after_count == before_count - 1

        driver.refresh()
        wait.until(
            lambda drv: test_label.lower()
            not in drv.find_element(By.CSS_SELECTOR, "[data-process-lists-inactive-table-body]").text.lower()
        )

        with SessionLocal() as session:
            menu_row = (
                session.query(SidebarMenuSetting)
                .filter(SidebarMenuSetting.menu_key == "perfil_de_autorizacao")
                .first()
            )
            assert menu_row is not None
            config = json.loads(menu_row.menu_config or "{}")
            process_lists = config.get("process_lists") or []
            assert all(str(item.get("key") or "") != test_key for item in process_lists)
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
