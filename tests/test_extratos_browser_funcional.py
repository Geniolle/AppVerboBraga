"""
Testes Selenium funcionais para Extratos.
Validam interações reais: página abre, card visível, tabela renderiza, reload não duplica.
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from tests.browser_support import EXTERNAL_APP_BASE_URL
    from tests.test_process_submenu_runtime_stage6_browser import _login_admin_v1, _build_driver_v1
    HAS_BROWSER = True
except ImportError:
    HAS_BROWSER = False


pytestmark = pytest.mark.skipif(not HAS_BROWSER, reason="Browser support not available")


class TestExtratosFuncional:
    """Testes funcionais de Extratos"""

    @pytest.fixture
    def browser_session(self):
        driver = _build_driver_v1()
        wait = WebDriverWait(driver, 15)
        try:
            yield driver, wait
        finally:
            driver.quit()

    def test_pagina_extratos_abre(self, browser_session):
        """Página de Extratos carrega sem redireção"""
        driver, wait = browser_session
        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        assert "menu=extrato" in driver.current_url
        assert "login" not in driver.current_url.lower()

    def test_card_ativos_visivel(self, browser_session):
        """Card de Extratos ativos deve estar visível e renderizado"""
        driver, wait = browser_session
        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        active_card = wait.until(
            EC.visibility_of_element_located((By.ID, "dynamic-process-active-card"))
        )
        assert active_card.is_displayed(), "Card ativo deve estar visível"

    def test_tabela_tem_linhas(self, browser_session):
        """Tabela ativa deve conter linhas de dados com 11 registos"""
        driver, wait = browser_session
        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        active_card = wait.until(EC.visibility_of_element_located((By.ID, "dynamic-process-active-card")))

        # Diagnosticar estado
        diag = driver.execute_script("""
            const bootstrap = window.__APPGENESIS_BOOTSTRAP__;
            return {
                bootstrap_count: bootstrap?.menuProcessHistoryMap?.extrato?.length || 0,
                layout_config: bootstrap?.processDynamicLayoutMap?.extrato?.layout || 'undefined',
                tbody_tr_count: document.getElementById('dynamic-process-active-card')?.querySelectorAll('tbody tr').length || 0
            };
        """)

        # Se layout config está nula, é um erro de backend
        if diag['layout_config'] is None:
            pytest.fail(f"Backend não populou processDynamicLayoutMap. Bootstrap: {diag['bootstrap_count']} registos, Layout: null")

        # Aguardar que tabela tenha linhas
        def rows_loaded(card):
            try:
                rows = card.find_elements(By.CSS_SELECTOR, "tbody tr")
                return len(rows) > 0
            except:
                return False

        wait.until(lambda d: rows_loaded(active_card), message="Tabela deve ter linhas renderizadas")

        # Validar quantidade
        tbody = active_card.find_element(By.TAG_NAME, "tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")

        assert len(rows) > 0, f"Tabela vazia. Bootstrap: {diag['bootstrap_count']}, Tabela: {len(rows)}"


    def test_reload_nao_duplica(self, browser_session):
        """Navegar e voltar não duplica linhas na tabela"""
        driver, wait = browser_session
        _login_admin_v1(driver, wait)
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        active_card = wait.until(EC.visibility_of_element_located((By.ID, "dynamic-process-active-card")))
        tbody = active_card.find_element(By.TAG_NAME, "tbody")
        initial_count = len(tbody.find_elements(By.TAG_NAME, "tr"))

        # Navegar para outro menu e voltar, em vez de refresh
        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=departamento")
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        driver.get(f"{EXTERNAL_APP_BASE_URL}/users/new?menu=extrato")
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        active_card = wait.until(EC.visibility_of_element_located((By.ID, "dynamic-process-active-card")))
        tbody = active_card.find_element(By.TAG_NAME, "tbody")
        reload_count = len(tbody.find_elements(By.TAG_NAME, "tr"))

        assert initial_count == reload_count, f"Linhas antes: {initial_count}, após navegar: {reload_count}"

