"""Campos adicionais do tipo Lista: escolher uma lista da aba Listas (refaz o PR #40)."""

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from appgenesis.config.settings import settings


BASE_URL = "http://127.0.0.1:8000"
EDITOR_URL = (
    BASE_URL
    + "/users/new?menu=sessoes&admin_tab=contas&settings_action=edit"
    "&target=settings-menu-edit-card&settings_edit_key=calendario"
    "&settings_tab={tab}#settings-menu-edit-card"
)
LIST_LABEL = "Lista do seletor"  # ja em "sentence case", como a aba Listas grava
FIELD_LABEL = "Campo lista CI"
FIELD_KEY = "custom_campo_lista_ci"
MANAGER = "[data-process-additional-fields-manager-v3='1']"


def _build_driver_v1():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    try:
        return webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Selenium Chrome indisponivel neste ambiente: {exc}")


def _show_all_rows_js():
    # A tabela pagina (Mais/Menos); mostra tudo para encontrar a linha do campo.
    return f"""
        const root = document.querySelector("{MANAGER}");
        for (let i = 0; i < 10; i += 1) {{
          const more = Array.from(root.querySelectorAll("button"))
            .find((b) => b.innerText.trim() === "Mais" && b.offsetParent !== null);
          if (!more) break;
          more.click();
        }}
    """


def test_additional_list_field_uses_list_from_lists_tab() -> None:
    email = str(settings.ADMIN_LOGIN_EMAIL or "").strip()
    password = str(settings.ADMIN_LOGIN_PASSWORD or "").strip()
    if not email or not password:
        pytest.skip("ADMIN_LOGIN_EMAIL / ADMIN_LOGIN_PASSWORD nao definidos.")

    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    def open_tab(tab: str) -> None:
        driver.get(EDITOR_URL.format(tab=tab))
        wait.until(EC.visibility_of_element_located((By.ID, "settings-menu-edit-card")))

    def remove_test_field() -> None:
        open_tab("campos-adicionais")
        driver.execute_script(_show_all_rows_js())
        button = driver.execute_script(
            """
            const btn = document.querySelector(arguments[0]);
            if (!btn) return null;
            window.AppGenesisProcessShell.createConfirmDialogController = () => Promise.resolve(true);
            return btn;
            """,
            f'{MANAGER} [data-configurable-action="remove"][data-configurable-item-id="{FIELD_KEY}"]',
        )
        if button:
            driver.execute_script("arguments[0].click();", button)
            wait.until(EC.staleness_of(button))

    def remove_test_list() -> None:
        open_tab("lista")
        form = driver.find_element(By.CSS_SELECTOR, "form[data-process-lists-manager-v1='1']")
        removed = driver.execute_script(
            """
            const manager = arguments[0].processListsManagerV1;
            if (!manager) return false;
            const kept = manager.getItems().filter((item) => item.label !== arguments[1]);
            if (kept.length === manager.getItems().length) return false;
            manager.setItems(kept);
            manager.syncHiddenInputs();
            HTMLFormElement.prototype.submit.call(arguments[0]);
            return true;
            """,
            form,
            LIST_LABEL,
        )
        if removed:
            wait.until(EC.staleness_of(form))

    try:
        driver.get(BASE_URL + "/login")
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_contains("/users/new"))
        remove_test_field()
        remove_test_list()

        # 1) Criar a lista na aba Listas.
        open_tab("lista")
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-label]").send_keys(LIST_LABEL)
        driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-items]").send_keys("Um, Dois, Tres")
        submit = driver.find_element(By.CSS_SELECTOR, "[data-process-list-editor-submit]")
        submit.click()
        wait.until(EC.staleness_of(submit))

        # 2) Campo adicional do tipo Lista: escolher a lista pelo nome.
        open_tab("campos-adicionais")
        driver.find_element(
            By.CSS_SELECTOR, f"[data-configurable-create-trigger][data-configurable-manager-target=\"{MANAGER}\"]"
        ).click()
        root = driver.find_element(By.CSS_SELECTOR, MANAGER)
        wait.until(lambda d: root.find_element(By.CSS_SELECTOR, "[data-additional-field-editor-label]").is_displayed())
        root.find_element(By.CSS_SELECTOR, "[data-additional-field-editor-label]").send_keys(FIELD_LABEL)
        Select(root.find_element(By.CSS_SELECTOR, "[data-additional-field-editor-type]")).select_by_value("list")
        list_select = Select(root.find_element(By.CSS_SELECTOR, "[data-additional-field-editor-list-key]"))
        list_select.select_by_visible_text(LIST_LABEL)
        list_key = list_select.first_selected_option.get_attribute("value")
        assert list_key
        # Com uma lista escolhida, o texto livre da lista manual fica escondido.
        assert not root.find_element(By.CSS_SELECTOR, "[data-additional-field-list-wrap]").is_displayed()
        submit = root.find_element(By.CSS_SELECTOR, "[data-additional-field-editor-submit]")
        submit.click()
        wait.until(EC.staleness_of(submit))

        # 3) Gravado com a chave da lista e mostrado na tabela; ao reabrir, a lista vem selecionada.
        wait.until(EC.visibility_of_element_located((By.ID, "settings-menu-edit-card")))
        saved = driver.execute_script(
            f"""
            const rows = document.querySelectorAll("{MANAGER} [data-additional-fields-legacy-container] .process-additional-field-row");
            for (const row of rows) {{
              const key = row.querySelector("[name='additional_field_key']");
              if (key && key.value === "{FIELD_KEY}") {{
                return row.querySelector("[name='additional_field_manual_list_key']").value;
              }}
            }}
            return null;
            """
        )
        assert saved == list_key
        driver.execute_script(_show_all_rows_js())
        row = driver.find_element(By.CSS_SELECTOR, f"{MANAGER} tr[data-configurable-item-id='{FIELD_KEY}']")
        assert f"Lista: {LIST_LABEL}" in row.text
        edit_button = row.find_element(By.CSS_SELECTOR, "[data-configurable-action='edit']")
        driver.execute_script("arguments[0].click();", edit_button)
        reopened = driver.find_element(By.CSS_SELECTOR, f"{MANAGER} [data-additional-field-editor-list-key]")
        wait.until(lambda d: reopened.get_attribute("value") == list_key)
    finally:
        try:
            remove_test_field()
            remove_test_list()
        finally:
            try:
                driver.close()
            finally:
                driver.service.stop()
