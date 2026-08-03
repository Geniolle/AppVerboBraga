import pytest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD


####################################################################################
# (1) CENARIOS A-E DO RODAPE DE PAGINACAO REUTILIZAVEL (renderPagination_v1)
#
# A aba Listas expoe form.processListsManagerV1 para diagnostico (unica das 5 abas
# que ja tinha este ganho); usamo-lo para semear itens via manager.setItems(), que e
# puramente client-side (nao envia nada ao servidor), tornando este teste seguro para
# correr repetidamente sem deixar dados de teste na base de dados. Como as 5 abas
# partilham a MESMA renderPagination_v1 do core (ver test_configurable_items_actions_order.py
# e test_configurable_items_pagination_core_v1.py), validar o comportamento aqui cobre
# o contrato de todas elas; as outras 4 abas sao cobertas por testes estruturais que
# confirmam que usam exatamente esta mesma funcao central.
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
            (By.CSS_SELECTOR, "[data-process-list-editor-label]")
        )
    )


def _seed_items_v1(driver, labels):
    driver.execute_script(
        """
        const form = document.querySelector("form[data-process-lists-manager-v1='1']");
        const manager = form && form.processListsManagerV1;
        if (!manager) { return false; }
        manager.setItems(arguments[0].map((label) => ({ label, field_type: "manual", itemsCsv: "A" })));
        return true;
        """,
        labels,
    )


def _counter_text_v1(driver):
    try:
        return driver.find_element(
            By.CSS_SELECTOR, "[data-process-lists-pagination] .appgenesis-load-more-counter-v1"
        ).text
    except NoSuchElementException:
        return None


def _mais_button_v1(driver):
    return driver.find_elements(
        By.CSS_SELECTOR, "[data-process-lists-pagination] .appgenesis-load-more-btn-v1"
    )


def _menos_button_v1(driver):
    return driver.find_elements(
        By.CSS_SELECTOR, ".configurable-items-less-v1 .appgenesis-load-more-btn-v1"
    )


def test_configurable_items_pagination_scenarios_a_to_e_real_browser() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 20)
    try:
        _login_owner_v1(driver, wait)
        _open_lists_editor_v1(driver, wait)

        ####################################################################
        # CENARIO A: 1 registo -> contador visivel, sem Mais, sem Menos.
        ####################################################################
        _seed_items_v1(driver, ["Seed A1"])
        assert _counter_text_v1(driver) == "[ 1 / 1 ]"
        assert len(_mais_button_v1(driver)) == 0
        assert len(_menos_button_v1(driver)) == 0

        ####################################################################
        # CENARIO B: 5 registos (== pageSize default) -> contador visivel,
        # sem Mais (tudo ja visivel), sem Menos (visibleCount == pageSize).
        ####################################################################
        five_labels = [f"Seed B{i}" for i in range(1, 6)]
        _seed_items_v1(driver, five_labels)
        assert _counter_text_v1(driver) == "[ 5 / 5 ]"
        assert len(_mais_button_v1(driver)) == 0
        assert len(_menos_button_v1(driver)) == 0

        ####################################################################
        # CENARIO C: 6 registos -> Mais aparece; clicar Mais mostra tudo e
        # troca para Menos; clicar Menos volta ao estado paginado.
        ####################################################################
        six_labels = [f"Seed C{i}" for i in range(1, 7)]
        _seed_items_v1(driver, six_labels)
        assert _counter_text_v1(driver) == "[ 5 / 6 ]"
        mais_buttons = _mais_button_v1(driver)
        assert len(mais_buttons) == 1
        assert len(_menos_button_v1(driver)) == 0

        mais_buttons[0].click()
        wait.until(lambda d: _counter_text_v1(d) == "[ 6 / 6 ]")
        assert len(_mais_button_v1(driver)) == 0
        menos_buttons = _menos_button_v1(driver)
        assert len(menos_buttons) == 1

        menos_buttons[0].click()
        wait.until(lambda d: _counter_text_v1(d) == "[ 5 / 6 ]")
        assert len(_mais_button_v1(driver)) == 1
        assert len(_menos_button_v1(driver)) == 0

        ####################################################################
        # CENARIO D: mudar o tamanho de pagina para 10 com 6 registos ->
        # visibleCount recalculado, contador atualizado, sem Mais/Menos.
        ####################################################################
        page_size_select = driver.find_element(By.CSS_SELECTOR, "[data-process-lists-page-size]")
        driver.execute_script(
            """
            arguments[0].value = '10';
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """,
            page_size_select,
        )
        wait.until(lambda d: _counter_text_v1(d) == "[ 6 / 6 ]")
        assert len(_mais_button_v1(driver)) == 0
        assert len(_menos_button_v1(driver)) == 0

        ####################################################################
        # CENARIO E: pesquisa filtra os itens visiveis e recalcula o
        # contador/Mais/Menos sobre o subconjunto filtrado; limpar a
        # pesquisa restaura o estado sobre o conjunto completo.
        ####################################################################
        search_input = driver.find_element(
            By.CSS_SELECTOR, "[data-process-list-reusable-manager] [data-configurable-search]"
        )
        search_input.clear()
        search_input.send_keys("Seed C1")
        wait.until(lambda d: _counter_text_v1(d) == "[ 1 / 1 ]")
        assert len(_mais_button_v1(driver)) == 0
        assert len(_menos_button_v1(driver)) == 0

        driver.execute_script(
            """
            arguments[0].value = '';
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            """,
            search_input,
        )
        wait.until(lambda d: _counter_text_v1(d) == "[ 6 / 6 ]")
        assert len(_mais_button_v1(driver)) == 0
        assert len(_menos_button_v1(driver)) == 0

        assert not [
            entry
            for entry in driver.get_log("browser")
            if entry.get("level") == "SEVERE"
            and "favicon.ico" not in entry.get("message", "")
        ]
    finally:
        driver.quit()
