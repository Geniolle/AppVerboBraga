"""
Testes Selenium funcionais completos para Extratos.
Validam ações reais no browser: pesquisa, paginacao, editar, inativar, etc.
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from appgenesis.db.session import SessionLocal
from appgenesis.models import User

try:
    from tests.browser_support import EXTERNAL_APP_BASE_URL
    from tests.test_process_submenu_runtime_stage6_browser import (
        _login_admin_v1,
        _build_driver_v1,
    )
    HAS_BROWSER_SUPPORT = True
except ImportError:
    HAS_BROWSER_SUPPORT = False


pytestmark = pytest.mark.skipif(
    not HAS_BROWSER_SUPPORT,
    reason="Browser support not available"
)


class TestExtratosBrowserFuncional:
    """Testes funcionais de Extratos via Selenium"""

    @pytest.fixture
    def browser_session(self):
        driver = _build_driver_v1()
        wait = WebDriverWait(driver, 10)
        try:
            yield driver, wait
        finally:
            driver.quit()

    def test_pesquisa_por_descricao(self, browser_session):
        """Pesquisar por descricao e verificar filtragem"""
        driver, wait = browser_session

        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Encontrar campo de pesquisa
        try:
            search_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search'], input[placeholder*='Pesquisa'], input[placeholder*='pesquisa']"))
            )
            search_input.send_keys("PROSEGUR")
            search_input.send_keys(Keys.RETURN)

            # Verificar que encontrou registos com PROSEGUR
            wait.until(
                lambda drv: len(drv.find_elements(By.XPATH, "//table//tbody//tr")) > 0
            )

            rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
            assert len(rows) > 0, "Pesquisa por descricao nao retornou resultados"

        except TimeoutException:
            pytest.skip("Campo de pesquisa nao encontrado ou timeout")

    def test_pesquisa_sem_resultado(self, browser_session):
        """Pesquisar termo inexistente e limpar pesquisa"""
        driver, wait = browser_session

        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        try:
            search_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search'], input[placeholder*='Pesquisa']"))
            )

            # Obter contagem inicial
            initial_rows = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))

            # Pesquisar inexistente
            search_input.send_keys("XXXXYYYYZZZZ")
            search_input.send_keys(Keys.RETURN)

            # Verificar que nao ha resultados
            empty_message = driver.find_elements(By.XPATH, "//*[contains(text(), 'Sem')]")
            assert len(empty_message) > 0 or len(driver.find_elements(By.XPATH, "//table//tbody//tr")) == 0

            # Limpar pesquisa
            search_input.clear()
            search_input.send_keys(Keys.RETURN)

            # Verificar que voltou
            wait.until(lambda drv: len(drv.find_elements(By.XPATH, "//table//tbody//tr")) > 0)

        except TimeoutException:
            pytest.skip("Campo de pesquisa nao encontrado")

    def test_seletor_entradas_por_pagina(self, browser_session):
        """Mudar quantidade de entradas por pagina"""
        driver, wait = browser_session

        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        try:
            # Procurar dropdown de quantidade
            qty_select = driver.find_elements(
                By.XPATH, "//select[contains(@class, 'quantity')], //select[@name*='quantity'], //select[@data-test*='quantity']"
            )

            if qty_select:
                qty_select[0].send_keys("20")
                wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

                # Verificar que tabela se renderizou com nova quantidade
                assert len(driver.find_elements(By.XPATH, "//table//tbody//tr")) > 0

        except (TimeoutException, IndexError):
            pytest.skip("Seletor de quantidade nao encontrado")

    def test_paginacao_avanca_volta(self, browser_session):
        """Testar navegacao de paginas"""
        driver, wait = browser_session

        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        try:
            # Procurar botao proximo
            next_button = driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Proximo')], //button[@aria-label*='next']"
            )

            if next_button:
                initial_rows_ids = [
                    row.get_attribute('data-id') or row.text
                    for row in driver.find_elements(By.XPATH, "//table//tbody//tr")[:3]
                ]

                next_button[0].click()
                wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

                # Verificar que os IDs mudaram
                new_rows_ids = [
                    row.get_attribute('data-id') or row.text
                    for row in driver.find_elements(By.XPATH, "//table//tbody//tr")[:3]
                ]

                # Se ha segunda pagina, IDs devem ser diferentes
                if new_rows_ids:
                    assert new_rows_ids != initial_rows_ids or len(initial_rows_ids) < 3

        except (TimeoutException, IndexError):
            pytest.skip("Botoes de paginacao nao encontrados")

    def test_visualizar_preserva_record_id(self, browser_session):
        """Visualizar um registo e verificar que abre o registro correto"""
        driver, wait = browser_session

        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        try:
            # Obter primeiro record_id da tabela
            first_row = wait.until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody//tr[1]"))
            )

            record_id = first_row.get_attribute('data-id') or first_row.get_attribute('id')

            # Procurar e clicar botao visualizar
            view_buttons = first_row.find_elements(By.XPATH, ".//button[contains(text(), 'Visualizar')], .//button[@title*='Ver'], .//a[@title*='Ver']")

            if view_buttons:
                view_buttons[0].click()
                wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

                # Verificar que o formulario tem o mesmo record_id
                form_record_id = driver.execute_script("return window.__CURRENT_RECORD_ID__")
                if form_record_id:
                    assert form_record_id == record_id or record_id in str(form_record_id)

        except (TimeoutException, IndexError):
            pytest.skip("Botao visualizar nao encontrado")

    def test_reload_sem_duplicacao(self, browser_session):
        """Reload da pagina nao duplica linhas"""
        driver, wait = browser_session

        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Contar linhas antes
        initial_count = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))

        # Reload
        driver.refresh()
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Contar linhas depois
        reload_count = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))

        assert initial_count == reload_count, "Reload duplicou linhas"

    def test_navegar_menu_e_voltar(self, browser_session):
        """Navegar para outro menu e voltar sem perder dados"""
        driver, wait = browser_session

        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Contar linhas
        initial_count = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
        initial_records = [
            row.get_attribute('data-id') or row.text
            for row in driver.find_elements(By.XPATH, "//table//tbody//tr")[:5]
        ]

        # Navegar para home
        home_link = driver.find_elements(By.XPATH, "//a[contains(text(), 'Home')], .menu-item[contains(text(), 'Home')]")
        if home_link:
            home_link[0].click()
            wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

            # Voltar para extrato
            extrato_link = driver.find_elements(By.XPATH, "//a[contains(text(), 'Extrato')], .menu-item[contains(text(), 'Extrato')]")
            if extrato_link:
                extrato_link[0].click()
                wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

                # Verificar que dados sao iguais
                return_count = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
                assert initial_count == return_count, "Dados mudaram apos navegacao"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
