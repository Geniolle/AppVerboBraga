from __future__ import annotations

import json
from typing import Any

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD
from appgenesis.db.session import SessionLocal
from appgenesis.models import SidebarMenuSetting


TARGET_URL = (
    "http://127.0.0.1:8000/users/new?menu=perfil_de_autorizacao&target=auth-objeto-card"
    "#auth-objeto-card"
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


def _find_scenario_entity_v1() -> dict[str, Any]:
    with SessionLocal() as session:
        rows = (
            session.query(SidebarMenuSetting)
            .filter(
                SidebarMenuSetting.menu_key == "perfil_de_autorizacao",
                SidebarMenuSetting.is_deleted.is_(False),
                SidebarMenuSetting.is_active.is_(True),
            )
            .order_by(SidebarMenuSetting.entity_id.asc())
            .all()
        )

        for row in rows:
            try:
                menu_config = json.loads(row.menu_config or "{}")
            except json.JSONDecodeError:
                continue

            process_lists = [
                item
                for item in (menu_config.get("process_lists") or [])
                if isinstance(item, dict)
            ]
            additional_fields = [
                item
                for item in (
                    menu_config.get("process_additional_fields")
                    or menu_config.get("additional_fields")
                    or []
                )
                if isinstance(item, dict)
            ]

            process_list = next(
                (
                    item
                    for item in process_lists
                    if str(item.get("key") or "").strip() == "list_processo"
                ),
                None,
            )
            processo_field = next(
                (
                    item
                    for item in additional_fields
                    if str(item.get("key") or "").strip() == "custom_processo"
                ),
                None,
            )

            if not process_list or not processo_field:
                continue

            if str(process_list.get("field_type") or "").strip().lower() != "automatic":
                continue
            if str(process_list.get("source_session_key") or "").strip().lower() != "all_sessions":
                continue
            if str(processo_field.get("field_type") or "").strip().lower() != "list":
                continue
            if str(processo_field.get("manual_list_key") or processo_field.get("list_key") or "").strip() != "list_processo":
                continue

            return {
                "entity_id": int(row.entity_id),
                "menu_label": str(row.menu_label or "").strip() or "perfil_de_autorizacao",
                "process_list": process_list,
                "processo_field": processo_field,
            }

    pytest.skip(
        "Nao foi encontrada configuracao de diagnostico para Perfil de autorizacao "
        "com a lista reutilizavel L_processo."
    )


def _login_owner_for_entity_v1(driver: webdriver.Chrome, wait: WebDriverWait, entity_id: int) -> None:
    admin_email = str(ADMIN_LOGIN_EMAIL or "").strip()
    admin_password = str(ADMIN_LOGIN_PASSWORD or "").strip()
    if not admin_email or not admin_password:
        pytest.skip("ADMIN_LOGIN_EMAIL / ADMIN_LOGIN_PASSWORD nao definidos.")

    driver.get("http://127.0.0.1:8000/login")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(admin_email)
    driver.find_element(By.NAME, "password").send_keys(admin_password)
    driver.execute_script(
        """
        const form = document.querySelector("form[action='/login']");
        if (!form) {
          return false;
        }

        let modeInput = form.querySelector("input[name='login_mode']");
        if (!modeInput) {
          modeInput = document.createElement("input");
          modeInput.type = "hidden";
          modeInput.name = "login_mode";
          form.appendChild(modeInput);
        }
        modeInput.value = "admin";

        let entityInput = form.querySelector("input[name='entity_id']");
        if (!entityInput) {
          entityInput = document.createElement("input");
          entityInput.type = "hidden";
          entityInput.name = "entity_id";
          form.appendChild(entityInput);
        }
        entityInput.value = String(arguments[0] || "");
        return true;
        """,
        str(entity_id),
    )
    driver.find_element(By.CSS_SELECTOR, "form[action='/login'] button[type='submit']").click()
    wait.until(EC.url_contains("/users/new"))


def _browser_console_severe_errors_v1(driver: webdriver.Chrome) -> list[dict[str, Any]]:
    severe_errors: list[dict[str, Any]] = []
    for entry in driver.get_log("browser"):
        if str(entry.get("level") or "").upper() != "SEVERE":
            continue
        message = str(entry.get("message") or "")
        if "favicon.ico" in message:
            continue
        severe_errors.append(entry)
    return severe_errors


def _open_objeto_form_v1(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    driver.get(TARGET_URL)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#auth-objeto-card")))

    edit_links = driver.find_elements(
        By.XPATH,
        "//section[@id='auth-objeto-card']//a[contains(@href, 'auth_objeto_edit_key')]",
    )
    if edit_links:
        driver.execute_script("arguments[0].click();", edit_links[0])
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#auth-objeto-form-card")))
        return

    create_toggle = driver.find_elements(
        By.XPATH,
        "//section[@id='auth-objeto-card']//summary[contains(normalize-space(.), 'Criar objeto de autorização')]",
    )
    if not create_toggle:
        pytest.fail("Nao foi possivel abrir o formulario do Objeto de autorizacao.")

    driver.execute_script("arguments[0].click();", create_toggle[0])
    wait.until(
        lambda drv: bool(
            drv.find_elements(
                By.CSS_SELECTOR,
                "#auth-objeto-card [data-admin-subprocess-field-key='custom_processo'] select",
            )
        )
    )


def _collect_process_field_diagnostics_v1(driver: webdriver.Chrome) -> dict[str, Any]:
    return driver.execute_script(
        """
        const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};
        const select = document.querySelector(
          "#auth-objeto-card [data-admin-subprocess-field-key='custom_processo'] select, " +
          "#auth-objeto-form-card [data-admin-subprocess-field-key='custom_processo'] select"
        );
        const container = select ? (select.closest('.admin-subprocess-field-v1') || select.parentElement) : null;
        const options = Array.from(select ? select.options : []).map((option) => ({
          value: String(option.value || ''),
          text: String(option.textContent || '').trim(),
          selected: Boolean(option.selected)
        }));
        const severeErrors = (window.__processoFieldDiagSevereErrors || []);
        return {
          bootstrap: bootstrap,
          select: select ? {
            id: select.id || '',
            name: select.name || '',
            fieldKey: select.dataset.adminSubprocessFieldKey || '',
            value: select.value || '',
            selectedIndex: typeof select.selectedIndex === 'number' ? select.selectedIndex : -1,
            options: options,
            outerHTML: select.outerHTML || '',
          } : null,
          containerOuterHTML: container ? container.outerHTML || '' : '',
          severeErrors: severeErrors,
        };
        """
    )


####################################################################################
# (2) DIAGNOSTICO REAL DO CAMPO PROCESSO
####################################################################################


def test_processo_field_diagnostic_does_not_receive_automatic_list_options() -> None:
    scenario = _find_scenario_entity_v1()
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_owner_for_entity_v1(driver, wait, scenario["entity_id"])
        _open_objeto_form_v1(driver, wait)

        diagnostics = _collect_process_field_diagnostics_v1(driver)
        bootstrap = diagnostics.get("bootstrap") or {}
        select_info = diagnostics.get("select")

        print(
            json.dumps(
                {
                    "scenario": {
                        "entity_id": scenario["entity_id"],
                        "menu_label": scenario["menu_label"],
                        "process_list_key": scenario["process_list"].get("key"),
                        "process_list_label": scenario["process_list"].get("label"),
                        "process_list_field_type": scenario["process_list"].get("field_type"),
                        "process_list_source_session_key": scenario["process_list"].get("source_session_key"),
                        "processo_field_key": scenario["processo_field"].get("key"),
                        "processo_field_list_source_type": scenario["processo_field"].get("list_source_type"),
                        "processo_field_manual_list_key": scenario["processo_field"].get("manual_list_key"),
                        "processo_field_list_key": scenario["processo_field"].get("list_key"),
                    },
                    "bootstrap": {
                        "currentEntityId": bootstrap.get("currentEntityId"),
                        "initialMenu": bootstrap.get("initialMenu"),
                        "initialMenuTarget": bootstrap.get("initialMenuTarget"),
                        "processListAllSessionsKey": bootstrap.get("processListAllSessionsKey"),
                        "processListAllSessionsLabel": bootstrap.get("processListAllSessionsLabel"),
                        "processListSourceMenus": bootstrap.get("processListSourceMenus"),
                        "perfilDeAutorizacaoHistoryCount": len(
                            (bootstrap.get("menuProcessHistoryMap") or {}).get("perfil_de_autorizacao", [])
                        ),
                        "perfilDeAutorizacaoProcessLists": [
                            {
                                "key": item.get("key"),
                                "label": item.get("label"),
                                "field_type": item.get("field_type"),
                                "source_session_key": item.get("source_session_key"),
                                "source_menu_key": item.get("source_menu_key"),
                                "source_subprocess_key": item.get("source_subprocess_key"),
                            }
                            for item in (bootstrap.get("sidebarMenuSettings") or [])
                            if isinstance(item, dict) and str(item.get("key") or "").strip() == "perfil_de_autorizacao"
                            for item in (item.get("process_lists") or [])
                            if isinstance(item, dict)
                        ],
                    },
                    "select": select_info,
                    "containerOuterHTML": diagnostics.get("containerOuterHTML"),
                    "browserConsoleSevereErrors": _browser_console_severe_errors_v1(driver),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        assert int(bootstrap.get("currentEntityId") or 0) == int(scenario["entity_id"])
        assert select_info is not None, "Campo Processo não foi encontrado no formulário do Objeto de autorização."

        option_values = [str(option.get("value") or "") for option in select_info.get("options") or []]
        option_texts = [str(option.get("text") or "") for option in select_info.get("options") or []]

        assert option_texts and option_texts[0] == "Selecione", {
            "id": select_info.get("id"),
            "name": select_info.get("name"),
            "field_key": select_info.get("fieldKey"),
            "option_values": option_values,
            "option_texts": option_texts,
            "selected_value": select_info.get("value"),
            "outer_html": select_info.get("outerHTML"),
            "container_outer_html": diagnostics.get("containerOuterHTML"),
        }

        severe_errors = _browser_console_severe_errors_v1(driver)
        assert not severe_errors, severe_errors

        assert len([value for value in option_values if value]) > 0, (
            "Campo Processo não recebeu opções reais da lista automática L_processo."
        )
    finally:
        driver.quit()
