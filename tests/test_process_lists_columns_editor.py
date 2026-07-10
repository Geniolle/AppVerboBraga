import json

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD
from appgenesis.menu_settings import update_sidebar_menu_process_lists


####################################################################################
# (1) PERSISTENCIA COMPATIVEL DE LISTAS E COLUNAS
####################################################################################


class _RecordingSessionV1:
    def __init__(self) -> None:
        self.params = None
        self.committed = False

    def execute(self, _statement, params):
        self.params = params

    def commit(self) -> None:
        self.committed = True


def test_process_lists_save_preserves_reusable_lists_and_columns(monkeypatch) -> None:
    session = _RecordingSessionV1()
    menu_config = {
        "additional_fields": [
            {"key": "perfil", "label": "Perfil", "field_type": "text"},
            {
                "key": "nome_do_perfil",
                "label": "Nome do perfil",
                "field_type": "text",
            },
        ],
        "process_list_config": {"columns": []},
    }
    monkeypatch.setattr("appgenesis.menu_settings._menu_exists", lambda *_args: True)
    monkeypatch.setattr(
        "appgenesis.menu_settings._load_menu_config",
        lambda *_args: dict(menu_config),
    )
    monkeypatch.setattr(
        "appgenesis.menu_settings.get_menu_process_selectable_field_options",
        lambda *_args: [
            {"key": "perfil", "label": "Perfil"},
            {"key": "nome_do_perfil", "label": "Nome do perfil"},
        ],
    )

    ok, error = update_sidebar_menu_process_lists(
        session=session,
        menu_key="perfil_de_autorizacao",
        raw_lists=[
            {"key": "estados", "label": "Estados", "items_csv": "Ativo,Inativo"}
        ],
        raw_columns=[
            {
                "key": "perfil",
                "label": "Perfil",
                "field_key": "perfil",
                "source_kind": "field",
                "always_visible": "1",
                "responsive_priority": "2",
            }
        ],
    )

    assert ok is True
    assert error == ""
    assert session.committed is True
    stored = json.loads(session.params["menu_config"])
    assert stored["process_lists"][0]["label"] == "Estados"
    assert stored["process_list_columns"] == stored["process_list_config"]["columns"]
    assert stored["process_list_columns"][0] == {
        "key": "perfil",
        "label": "Perfil",
        "source_kind": "field",
        "field_key": "perfil",
        "always_visible": True,
        "responsive_priority": 2,
    }


def test_legacy_process_lists_client_does_not_erase_existing_columns(monkeypatch) -> None:
    session = _RecordingSessionV1()
    existing_columns = [
        {
            "key": "perfil",
            "label": "Perfil",
            "source_kind": "field",
            "field_key": "perfil",
            "always_visible": True,
            "responsive_priority": 1,
        }
    ]
    monkeypatch.setattr("appgenesis.menu_settings._menu_exists", lambda *_args: True)
    monkeypatch.setattr(
        "appgenesis.menu_settings._load_menu_config",
        lambda *_args: {"process_list_columns": existing_columns},
    )

    ok, _error = update_sidebar_menu_process_lists(
        session=session,
        menu_key="perfil_de_autorizacao",
        raw_lists=[{"key": "estados", "label": "Estados", "items_csv": "Ativo"}],
    )

    assert ok is True
    stored = json.loads(session.params["menu_config"])
    assert stored["process_list_columns"] == existing_columns


####################################################################################
# (2) BROWSER REAL: DROPDOWN E CAMPOS CONFIGURADOS
####################################################################################


def _build_driver_v1():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    try:
        return webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Selenium Chrome indisponivel neste ambiente: {exc}")


def test_process_lists_columns_editor_browser_owner() -> None:
    admin_email = str(ADMIN_LOGIN_EMAIL or "").strip()
    admin_password = str(ADMIN_LOGIN_PASSWORD or "").strip()
    if not admin_email or not admin_password:
        pytest.skip("ADMIN_LOGIN_EMAIL / ADMIN_LOGIN_PASSWORD nao definidos.")

    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    try:
        driver.get("http://127.0.0.1:8000/login")
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(
            admin_email
        )
        driver.find_element(By.NAME, "password").send_keys(admin_password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_contains("/users/new"))

        driver.get(
            "http://127.0.0.1:8000/users/new?menu=sessoes&admin_tab=contas"
            "&settings_action=edit&target=settings-menu-edit-card"
            "&settings_edit_key=perfil_de_autorizacao&settings_tab=lista"
            "#settings-menu-edit-card"
        )
        field_select = wait.until(
            EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "#settings-tab-lista [data-process-list-column-editor-field]",
                    )
            )
        )
        option_labels = [
            option.text.strip()
            for option in field_select.find_elements(By.TAG_NAME, "option")
            if option.get_attribute("value")
        ]

        assert option_labels
        assert "Perfil" in option_labels or "Nome do perfil" in option_labels
        assert driver.find_element(
            By.CSS_SELECTOR, "#settings-tab-lista [data-process-list-editor-label]"
        ).is_displayed()
        assert driver.find_element(
            By.CSS_SELECTOR, "#settings-tab-lista [data-process-list-editor-items]"
        ).is_displayed()
        assert not [
            entry
            for entry in driver.get_log("browser")
            if entry.get("level") == "SEVERE"
            and "favicon.ico" not in entry.get("message", "")
        ]
    finally:
        driver.quit()
