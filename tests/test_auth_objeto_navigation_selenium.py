from __future__ import annotations

from urllib.parse import parse_qs, urlparse

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


####################################################################################
# (2) FLUXO REAL DO BROWSER
####################################################################################


def test_auth_objeto_edit_keeps_objeto_tab_active_in_browser() -> None:
    admin_email = str(ADMIN_LOGIN_EMAIL or "").strip()
    admin_password = str(ADMIN_LOGIN_PASSWORD or "").strip()
    if not admin_email or not admin_password:
        pytest.skip("ADMIN_LOGIN_EMAIL / ADMIN_LOGIN_PASSWORD nao definidos.")

    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        driver.get("http://127.0.0.1:8000/login")
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(admin_email)
        driver.find_element(By.NAME, "password").send_keys(admin_password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_contains("/users/new"))

        driver.get(
            "http://127.0.0.1:8000/users/new"
            "?menu=perfil_de_autorizacao&target=auth-objeto-card#auth-objeto-card"
        )
        wait.until(lambda drv: len(drv.find_elements(By.CSS_SELECTOR, ".submenu-item")) >= 2)

        active_labels_before = [
            str(link.text or "").strip()
            for link in driver.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
        ]
        objeto_group_visible_before = driver.execute_script(
            """
            return [
              'auth-objeto-card',
              'auth-objeto-active-card',
              'auth-objeto-inactive-card',
            ].some((id) => {
              const card = document.getElementById(id);
              return Boolean(card) && window.getComputedStyle(card).display !== 'none';
            });
            """
        )
        assert "Objeto de autorização" in active_labels_before
        assert objeto_group_visible_before is True

        action_triggers = driver.find_elements(
            By.CSS_SELECTOR,
            (
                "#auth-objeto-card .appgenesis-row-actions-trigger-v1, "
                "#auth-objeto-active-card .appgenesis-row-actions-trigger-v1, "
                "#auth-objeto-inactive-card .appgenesis-row-actions-trigger-v1"
            ),
        )
        visible_action_trigger = next(
            (trigger for trigger in action_triggers if trigger.is_displayed()),
            None,
        )
        assert visible_action_trigger is not None

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            visible_action_trigger,
        )
        driver.execute_script("arguments[0].click();", visible_action_trigger)

        wait.until(
            lambda drv: len(
                drv.find_elements(
                    By.CSS_SELECTOR,
                    ".appgenesis-row-actions-popup-v1:not([hidden]) a.appgenesis-row-actions-item-edit-v1",
                )
            )
            >= 1
        )
        edit_links = driver.find_elements(
            By.CSS_SELECTOR,
            ".appgenesis-row-actions-popup-v1:not([hidden]) a.appgenesis-row-actions-item-edit-v1",
        )
        assert edit_links, {
            "current_url": driver.current_url,
            "active_labels_before": active_labels_before,
            "objeto_group_visible_before": objeto_group_visible_before,
            "page_source_has_edit_key": "auth_objeto_edit_key=" in driver.page_source,
        }

        edit_href = str(edit_links[0].get_attribute("href") or "")
        parsed_edit_href = urlparse(edit_href)
        edit_query = parse_qs(parsed_edit_href.query)

        assert edit_query.get("menu") == ["perfil_de_autorizacao"]
        assert edit_query.get("target") == ["auth-objeto-form-card"]
        assert edit_query.get("auth_objeto_edit_key")
        assert parsed_edit_href.fragment == "auth-objeto-form-card"

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_links[0])
        driver.execute_script("arguments[0].click();", edit_links[0])

        wait.until(lambda drv: "auth_objeto_edit_key=" in drv.current_url)
        wait.until(lambda drv: "#auth-objeto-form-card" in drv.current_url)

        active_labels = [
            str(link.text or "").strip()
            for link in driver.find_elements(By.CSS_SELECTOR, ".submenu-item.active")
        ]
        objeto_form_visible = driver.execute_script(
            """
            const card = document.getElementById('auth-objeto-form-card');
            return Boolean(card) && window.getComputedStyle(card).display !== 'none';
            """
        )
        perfil_form_visible = driver.execute_script(
            """
            const card = document.getElementById('auth-profile-form-card');
            return Boolean(card) && window.getComputedStyle(card).display !== 'none';
            """
        )
        objeto_form_header = driver.execute_script(
            """
            const header = document.querySelector('#auth-objeto-form-card h2');
            return header ? String(header.textContent || '').trim() : '';
            """
        )

        assert "Objeto de autorização" in active_labels
        assert "Perfis" not in active_labels
        assert objeto_form_visible is True
        assert perfil_form_visible is False
        assert "Editar objeto de autorização" == objeto_form_header
    finally:
        driver.quit()
