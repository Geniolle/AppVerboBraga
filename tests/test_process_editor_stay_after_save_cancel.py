from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD
from appgenesis.routes.profile.settings_handlers import (
    _build_settings_editor_stay_redirect_url_v1,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EDITOR_RETURN_URL = (
    "/users/new?menu=sessoes&admin_tab=contas&settings_action=edit"
    "&target=settings-menu-edit-card&settings_edit_key=perfil_de_autorizacao"
    "&settings_tab={settings_tab}#settings-menu-edit-card"
)


# ###################################################################################
# (1) GUARDAR PRESERVA O PROCESSO, O CARD E A ABA ATUAL EM TODOS OS HANDLERS DO EDITOR
# ###################################################################################


@pytest.mark.parametrize(
    "settings_tab",
    [
        "geral",
        "campos-config",
        "campos-adicionais",
        "campos-quantidade",
        "lista",
        "campos-subsequentes",
    ],
)
def test_save_redirect_stays_in_current_process_editor_tab(settings_tab: str) -> None:
    result = _build_settings_editor_stay_redirect_url_v1(
        success_message="ok",
        redirect_menu="sessoes",
        settings_edit_key="perfil_de_autorizacao",
        settings_tab=settings_tab,
        return_url=EDITOR_RETURN_URL.format(settings_tab=settings_tab),
    )

    parsed = urlsplit(result)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))

    assert parsed.fragment == "settings-menu-edit-card"
    assert params["menu"] == "sessoes"
    assert params["admin_tab"] == "contas"
    assert params["settings_action"] == "edit"
    assert params["settings_edit_key"] == "perfil_de_autorizacao"
    assert params["settings_tab"] == settings_tab
    assert params["target"] == "settings-menu-edit-card"
    assert params["target"] != "menu-subprocess-card-active"


# ###################################################################################
# (2) CANCELAR USA O MESMO RETURN_URL E O CANCELAMENTO DE COLUNAS CONTINUA LOCAL
# ###################################################################################


def test_cancel_buttons_stay_in_editor_and_list_column_cancel_is_local() -> None:
    html_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")
    controller_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "appgenesis_cancel_controller_v1.js"
    ).read_text(encoding="utf-8")

    # O cancelar do editor de processo devolve o utilizador a lista de origem (nunca
    # ao proprio card do editor) -- por isso o alvo/URL de retorno usam as variaveis
    # de saida resolvidas no template, nao mais o "settings-menu-edit-card" estatico.
    assert html_text.count(
        'data-appgenesis-cancel-return-target="#{{ settings_edit_exit_target }}"'
    ) == 7
    assert html_text.count(
        'data-appgenesis-cancel-return-url="{{ settings_edit_exit_url }}"'
    ) == 7
    assert '"[data-process-list-column-editor-cancel]"' in controller_text


def test_cancel_buttons_outside_editor_keep_their_own_targets() -> None:
    html_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    for target in (
        "dynamic-process-card",
        "perfil-pessoal-card",
        "edit-entity-card",
        "edit-user-card",
    ):
        assert f'data-appgenesis-cancel-target="{target}"' in html_text


# ###################################################################################
# (3) BROWSER REAL - GUARDAR, RECARREGAR, CANCELAR E LIMPAR A LISTA DE TESTE
# ###################################################################################


def _build_driver_v1():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    try:
        return webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Selenium Chrome indisponivel neste ambiente: {exc}")


def test_lists_save_and_cancel_stay_in_editor_in_browser() -> None:
    email = str(ADMIN_LOGIN_EMAIL or "").strip()
    password = str(ADMIN_LOGIN_PASSWORD or "").strip()
    if not email or not password:
        pytest.skip("ADMIN_LOGIN_EMAIL / ADMIN_LOGIN_PASSWORD nao definidos.")

    target_url = "http://127.0.0.1:8000" + EDITOR_RETURN_URL.format(settings_tab="lista")
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    def open_editor() -> None:
        driver.get(target_url)
        wait.until(EC.visibility_of_element_located((By.ID, "settings-menu-edit-card")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-process-list-editor-label]")))

    def remove_test_list() -> None:
        open_editor()
        removed = driver.execute_script(
            """
            const form = document.querySelector("form[data-process-lists-manager-v1='1']");
            const manager = form && form.processListsManagerV1;
            if (!manager) return false;
            const filtered = manager.getItems().filter((item) => item.label !== "Lista teste stay");
            if (filtered.length === manager.getItems().length) return false;
            manager.setItems(filtered);
            manager.syncHiddenInputs();
            return true;
            """
        )
        if removed:
            form = driver.find_element(By.CSS_SELECTOR, "form[data-process-lists-manager-v1='1']")
            driver.execute_script(
                "HTMLFormElement.prototype.submit.call("
                "document.querySelector(\"form[data-process-lists-manager-v1='1']\"));"
            )
            wait.until(EC.staleness_of(form))

    try:
        driver.get("http://127.0.0.1:8000/login")
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_contains("/users/new"))

        remove_test_list()
        open_editor()
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-label]").send_keys("Lista teste stay")
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-items]").send_keys("A, B, C")
        submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
        submit.click()
        wait.until(
            lambda drv: "Lista teste stay"
            in drv.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]").text
        )
        form = driver.find_element(By.CSS_SELECTOR, "form[data-process-lists-manager-v1='1']")
        driver.execute_script(
            "HTMLFormElement.prototype.submit.call("
            "document.querySelector(\"form[data-process-lists-manager-v1='1']\"));"
        )
        wait.until(EC.staleness_of(form))

        parsed = urlsplit(driver.current_url)
        params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        assert parsed.fragment == "settings-menu-edit-card"
        assert params["settings_edit_key"] == "perfil_de_autorizacao"
        assert params["settings_tab"] == "lista"
        assert params["target"] == "settings-menu-edit-card"

        driver.refresh()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-process-lists-table-body]")))
        assert "Lista teste stay" in driver.find_element(By.CSS_SELECTOR, "[data-process-lists-table-body]").text

        name_input = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-label]")
        name_input.send_keys("Cancelar")
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-cancel]").click()
        assert name_input.get_attribute("value") == ""
        assert driver.find_element(By.ID, "settings-menu-edit-card").is_displayed()
        assert "settings_tab=lista" in driver.current_url
    finally:
        try:
            remove_test_list()
        finally:
            try:
                driver.close()
            finally:
                driver.service.stop()
