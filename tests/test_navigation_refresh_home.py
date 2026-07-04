from __future__ import annotations

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD


####################################################################################
# (1) HELPERS
####################################################################################


def _build_chrome_driver_v1() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)


def _build_driver_v1():
    try:
        return _build_chrome_driver_v1()
    except WebDriverException as exc:
        pytest.skip(f"Selenium Chrome indisponivel neste ambiente: {exc}")


def _login_admin_v1(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    admin_email = str(ADMIN_LOGIN_EMAIL or "").strip()
    admin_password = str(ADMIN_LOGIN_PASSWORD or "").strip()
    if not admin_email or not admin_password:
        pytest.skip("ADMIN_LOGIN_EMAIL / ADMIN_LOGIN_PASSWORD nao definidos.")

    driver.get("http://127.0.0.1:8000/login")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(admin_email)
    driver.find_element(By.NAME, "password").send_keys(admin_password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/users/new"))


####################################################################################
# (2) REFRESH NORMAL VOLTA PARA HOME
####################################################################################


def test_browser_refresh_from_menu_returns_to_home() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        driver.get(
            "http://127.0.0.1:8000/users/new"
            "?menu=sessoes&admin_tab=contas&target=menu-subprocess-card-active"
            "#menu-subprocess-card-active"
        )
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")

        assert "menu=sessoes" in driver.current_url

        driver.refresh()
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
        wait.until(lambda drv: "menu=home" in drv.current_url)

        active_sidebar = [
            str(element.text or "").strip()
            for element in driver.find_elements(By.CSS_SELECTOR, ".menu-item.active")
        ]
        home_visible = driver.execute_script(
            """
            const card = document.getElementById('home-summary-card');
            return Boolean(card) && window.getComputedStyle(card).display !== 'none';
            """
        )

        assert driver.current_url == "http://127.0.0.1:8000/users/new?menu=home"
        assert "Home" in active_sidebar
        assert home_visible is True
    finally:
        driver.quit()


####################################################################################
# (3) LINK DIRETO DE EDICAO CONTINUA RESPEITADO NO REFRESH
####################################################################################


def test_browser_refresh_preserves_explicit_process_editor_link() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)

        editor_url = (
            "http://127.0.0.1:8000/users/new"
            "?menu=sessoes&admin_tab=contas&settings_action=edit"
            "&target=settings-menu-edit-card&settings_edit_key=calendario"
            "&settings_tab=campos-config#settings-menu-edit-card"
        )
        driver.get(editor_url)
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
        wait.until(
            lambda drv: drv.execute_script(
                """
                const card = document.getElementById('settings-menu-edit-card');
                return Boolean(card) && window.getComputedStyle(card).display !== 'none';
                """
            )
        )

        driver.refresh()
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
        wait.until(lambda drv: "settings_edit_key=calendario" in drv.current_url)

        editor_visible = driver.execute_script(
            """
            const card = document.getElementById('settings-menu-edit-card');
            return Boolean(card) && window.getComputedStyle(card).display !== 'none';
            """
        )

        assert "menu=home" not in driver.current_url
        assert "settings_edit_key=calendario" in driver.current_url
        assert editor_visible is True
    finally:
        driver.quit()
