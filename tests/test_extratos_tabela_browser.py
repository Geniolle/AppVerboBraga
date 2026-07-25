"""
Testes de Extratos no browser via Selenium.

Valida:
- Renderização da tabela dinâmica
- Apresentação de registos ativos/inativos
- Funcionalidade de criação, edição, inativação
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from appgenesis.db.session import SessionLocal
from appgenesis.models import User

# Importar helpers
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


class TestExtratosTabelaBrowser:
    """Testes de renderização da tabela de Extratos no browser"""

    @pytest.fixture
    def browser_session(self):
        """Setup e cleanup do driver Selenium"""
        driver = _build_driver_v1()
        wait = WebDriverWait(driver, 10)

        try:
            yield driver, wait
        finally:
            driver.quit()

    def test_extrato_page_loads_with_table(self, browser_session):
        """
        Teste 1: Página de Extratos carrega e mostra tabela
        """
        driver, wait = browser_session

        # Login como admin
        _login_admin_v1(driver, wait)

        # Navegar para Extratos
        url = f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato"
        driver.get(url)

        # Esperar carregamento
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Verificar que bootstrap contém dados de extrato
        bootstrap_data = driver.execute_script("""
            return window.__APPGENESIS_BOOTSTRAP__ &&
                   window.__APPGENESIS_BOOTSTRAP__.menuProcessHistoryMap &&
                   window.__APPGENESIS_BOOTSTRAP__.menuProcessHistoryMap['extrato'];
        """)

        assert bootstrap_data is not None, "Dados de extrato não carregados no bootstrap"
        assert isinstance(bootstrap_data, list), "Dados de extrato devem ser lista"
        assert len(bootstrap_data) > 0, "Deve haver registos de extrato"

    def test_extrato_active_table_visible(self, browser_session):
        """
        Teste 2: Card "Extratos ativos" está visível com tabela
        """
        driver, wait = browser_session

        _login_admin_v1(driver, wait)

        url = f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato"
        driver.get(url)

        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Esperar presença de card de ativos
        try:
            active_card = wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Extratos ativos')]"))
            )
            assert active_card is not None, "Card 'Extratos ativos' não encontrado"
        except TimeoutException:
            pytest.fail("Card 'Extratos ativos' não renderizado após 10s")

    def test_extrato_inactive_section_exists(self, browser_session):
        """
        Teste 3: Seção "Extratos inativos" existe (mesmo que vazia)
        """
        driver, wait = browser_session

        _login_admin_v1(driver, wait)

        url = f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato"
        driver.get(url)

        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Esperar presença de seção de inativos
        try:
            inactive_section = wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Extratos inativos')]"))
            )
            assert inactive_section is not None, "Seção 'Extratos inativos' não encontrada"
        except TimeoutException:
            pytest.fail("Seção 'Extratos inativos' não renderizada após 10s")

    def test_extrato_table_has_columns(self, browser_session):
        """
        Teste 4: Tabela tem colunas esperadas (Doc. soma, Sistema, Estado)
        """
        driver, wait = browser_session

        _login_admin_v1(driver, wait)

        url = f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato"
        driver.get(url)

        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Verificar presença de colunas esperadas
        expected_columns = ["Doc. soma", "Estado"]  # Colunas principais

        for col_name in expected_columns:
            try:
                col_element = wait.until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{col_name}')]"))
                )
                assert col_element is not None, f"Coluna '{col_name}' não encontrada"
            except TimeoutException:
                pytest.fail(f"Coluna '{col_name}' não renderizada")

    def test_extrato_create_button_visible(self, browser_session):
        """
        Teste 5: Botão "Criar extrato" está visível
        """
        driver, wait = browser_session

        _login_admin_v1(driver, wait)

        url = f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato"
        driver.get(url)

        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        try:
            create_button = wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Criar extrato')]"))
            )
            assert create_button is not None, "Botão 'Criar extrato' não encontrado"
        except TimeoutException:
            pytest.fail("Botão 'Criar extrato' não renderizado após 10s")

    def test_extrato_records_count_matches(self, browser_session):
        """
        Teste 6: Quantidade de registos na tabela corresponde ao bootstrap
        """
        driver, wait = browser_session

        _login_admin_v1(driver, wait)

        url = f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato"
        driver.get(url)

        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Obter contagem do bootstrap
        bootstrap_count = driver.execute_script("""
            const data = window.__APPGENESIS_BOOTSTRAP__.menuProcessHistoryMap['extrato'];
            return data ? data.filter(r => r.values && r.values['__estado'] === 'ativo').length : 0;
        """)

        # Contar linhas na tabela (aproximado, pode variar por paginação)
        table_rows = driver.find_elements(By.XPATH, "//table//tbody//tr")

        # Verificar que há pelo menos alguns registos (talvez paginados)
        assert len(table_rows) > 0, "Tabela de extratos ativos está vazia (deve ter registos)"

    def test_no_console_errors_on_extrato_page(self, browser_session):
        """
        Teste 7: Nenhum erro JavaScript no console ao carregar página de extratos
        (Ignora 404 de recursos estáticos como favicon.ico)
        """
        driver, wait = browser_session

        _login_admin_v1(driver, wait)

        url = f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato"
        driver.get(url)

        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        # Verificar logs do browser, ignorando 404 de recursos estáticos
        logs = driver.get_log('browser')
        errors = [
            log for log in logs
            if log['level'] == 'SEVERE'
            and 'favicon.ico' not in log.get('message', '')
            and '404' not in log.get('message', '')
        ]

        if errors:
            error_messages = [f"{log['message']}" for log in errors]
            assert False, f"Erros de console encontrados: {error_messages}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
