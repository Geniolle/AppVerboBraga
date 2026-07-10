from __future__ import annotations

import json
import time
from urllib.parse import urljoin

import httpx
import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.core import ADMIN_LOGIN_EMAIL, ADMIN_LOGIN_PASSWORD
from appgenesis.db.session import SessionLocal
from appgenesis.menu_settings import get_sidebar_menu_settings

BASE_URL = "http://127.0.0.1:8000"
TARGET_URL = (
    f"{BASE_URL}/users/new?menu=sessoes&admin_tab=contas"
    "&target=menu-subprocess-card-active#menu-subprocess-card-active"
)


# ###################################################################################
# (1) HELPERS
# ###################################################################################


def _build_chrome_driver_v1() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1400")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=options)


def _build_driver_v1():
    try:
        return _build_chrome_driver_v1()
    except WebDriverException as exc:
        pytest.skip(f"Selenium Chrome indisponível neste ambiente: {exc}")


def _require_admin_credentials_v1() -> tuple[str, str]:
    admin_email = str(ADMIN_LOGIN_EMAIL or "").strip()
    admin_password = str(ADMIN_LOGIN_PASSWORD or "").strip()
    if not admin_email or not admin_password:
        pytest.skip("ADMIN_LOGIN_EMAIL / ADMIN_LOGIN_PASSWORD não definidos.")
    return admin_email, admin_password


def _login_admin_v1(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    admin_email, admin_password = _require_admin_credentials_v1()
    driver.get(f"{BASE_URL}/login")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(
        admin_email
    )
    driver.find_element(By.NAME, "password").send_keys(admin_password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/users/new"))


def _open_target_page_v1(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    driver.get(TARGET_URL)
    wait.until(
        lambda drv: drv.execute_script(
            """
            const el = document.getElementById('menu-subprocess-card-active');
            return Boolean(el) && window.getComputedStyle(el).display === 'block';
            """
        )
    )
    wait.until(lambda drv: len(_get_visible_menu_labels_v1(drv)) >= 3)


def _get_visible_menu_labels_v1(driver: webdriver.Chrome) -> list[str]:
    return driver.execute_script(
        """
        const card = document.getElementById('menu-subprocess-card-active');
        if (!card) return [];
        return Array.from(card.querySelectorAll('tbody tr'))
          .filter((row) => window.getComputedStyle(row).display !== 'none')
          .map((row) => {
            const cell =
              row.querySelector('td[data-column-key="label"]') ||
              row.querySelector('td.admin-col-main-v1') ||
              row.querySelector('td');
            return cell ? String(cell.textContent || '').trim().replace(/\\s+/g, ' ') : '';
          })
          .filter(Boolean);
        """
    )


def _install_submit_probe_v1(driver: webdriver.Chrome) -> None:
    driver.execute_script(
        """
        window.__menuMoveDiagV1 = { clicks: [], submits: [] };
        document.addEventListener('click', function (event) {
          const actionEl = event.target && event.target.closest(
            '.appgenesis-row-actions-popup-v1 a, .appgenesis-row-actions-popup-v1 button'
          );
          if (!actionEl) {
            return;
          }
          window.__menuMoveDiagV1.clicks.push({
            text: String(
              actionEl.innerText || actionEl.value || actionEl.textContent || ''
            ).trim(),
            className: String(actionEl.className || ''),
            type: String(actionEl.getAttribute('type') || actionEl.tagName || '')
          });
        }, true);

        document.addEventListener('submit', function (event) {
          const form = event.target;
          if (!form || String(form.action || '').indexOf('/settings/menu/menu-move') === -1) {
            return;
          }
          const payload = {};
          const fd = new FormData(form);
          for (const pair of fd.entries()) {
            payload[pair[0]] = pair[1];
          }
          window.__menuMoveDiagV1.submits.push({
            action: String(form.action || ''),
            payload: payload,
            defaultPrevented: Boolean(event.defaultPrevented)
          });
        }, true);
        """
    )


def _get_submit_probe_v1(driver: webdriver.Chrome) -> dict[str, object]:
    return driver.execute_script(
        "return window.__menuMoveDiagV1 || { clicks: [], submits: [] };"
    )


def _get_menu_move_logs_v1(driver: webdriver.Chrome) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    move_request_ids: set[str] = set()
    for entry in driver.get_log("performance"):
        try:
            message = json.loads(entry["message"])["message"]
        except Exception:
            continue
        method = str(message.get("method") or "")
        params = message.get("params") or {}
        if method == "Network.requestWillBeSent":
            request = params.get("request") or {}
            url = str(request.get("url") or "")
            if "/settings/menu/menu-move" in url:
                request_id = str(params.get("requestId") or "")
                if request_id:
                    move_request_ids.add(request_id)
                filtered.append(
                    {
                        "kind": "request",
                        "requestId": request_id,
                        "url": url,
                        "method": request.get("method"),
                        "postData": request.get("postData"),
                    }
                )
        if method == "Network.responseReceived":
            response = params.get("response") or {}
            url = str(response.get("url") or "")
            if "/settings/menu/menu-move" in url:
                request_id = str(params.get("requestId") or "")
                if request_id:
                    move_request_ids.add(request_id)
                filtered.append(
                    {
                        "kind": "response",
                        "requestId": request_id,
                        "url": url,
                        "status": response.get("status"),
                        "statusText": response.get("statusText"),
                    }
                )
        if method == "Network.loadingFinished":
            request_id = str(params.get("requestId") or "")
            if request_id not in move_request_ids:
                continue
            filtered.append(
                {
                    "kind": "loadingFinished",
                    "requestId": request_id,
                }
            )
        if method == "Network.loadingFailed":
            request_id = str(params.get("requestId") or "")
            if request_id not in move_request_ids:
                continue
            filtered.append(
                {
                    "kind": "loadingFailed",
                    "requestId": request_id,
                    "errorText": params.get("errorText"),
                    "canceled": params.get("canceled"),
                }
            )
    return filtered


def _current_href_v1(driver: webdriver.Chrome) -> str:
    return str(driver.execute_script("return window.location.href;") or "")


def _collect_active_menu_orders_v1() -> tuple[list[str], dict[str, int | None]]:
    with SessionLocal() as session:
        settings = get_sidebar_menu_settings(session)
    active_rows = [
        row for row in settings if row.get("is_active") and not row.get("is_deleted")
    ]
    active_labels = [str(row.get("label") or "").strip() for row in active_rows]
    display_orders = {
        str(row.get("key") or "").strip().lower(): row.get("display_order")
        for row in active_rows
    }
    return active_labels, display_orders


def _login_http_session_v1() -> httpx.Client:
    admin_email, admin_password = _require_admin_credentials_v1()
    client = httpx.Client(base_url=BASE_URL, timeout=90.0, follow_redirects=False)
    login_response = client.post(
        "/login",
        data={
            "email": admin_email,
            "password": admin_password,
            "login_mode": "login",
        },
    )
    assert login_response.status_code in (302, 303), login_response.text
    return client


# ###################################################################################
# (2) DIAGNÓSTICO REAL DO BROWSER
# ###################################################################################


def test_menu_move_browser_diagnostic_v1() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        _open_target_page_v1(driver, wait)
        _install_submit_probe_v1(driver)
        _get_menu_move_logs_v1(driver)
        before_db_labels, before_db_orders = _collect_active_menu_orders_v1()

        before = _get_visible_menu_labels_v1(driver)
        target_index = len(before) // 2
        target_label = before[target_index]

        target_row = driver.find_element(
            By.XPATH,
            (
                "//section[@id='menu-subprocess-card-active']//tbody/tr"
                "[not(contains(@style,'display: none'))]"
                f"[.//td[contains(normalize-space(.), \"{target_label}\")]]"
            ),
        )
        trigger = target_row.find_element(
            By.CSS_SELECTOR, ".appgenesis-row-actions-trigger-v1"
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
        trigger.click()

        wait.until(
            lambda drv: len(
                drv.find_elements(
                    By.CSS_SELECTOR, ".appgenesis-row-actions-popup-v1:not([hidden])"
                )
            )
            >= 1
        )

        popup = driver.find_element(
            By.CSS_SELECTOR, ".appgenesis-row-actions-popup-v1:not([hidden])"
        )
        move_up_button = popup.find_element(
            By.XPATH, ".//button[contains(normalize-space(.), 'Subir')]"
        )
        move_form = move_up_button.find_element(By.XPATH, "./ancestor::form[1]")
        payload = driver.execute_script(
            """
            const form = arguments[0];
            const out = {};
            const fd = new FormData(form);
            for (const pair of fd.entries()) {
              out[pair[0]] = pair[1];
            }
            return out;
            """,
            move_form,
        )

        move_up_button.click()

        wait.until(lambda drv: _get_visible_menu_labels_v1(drv) != before)
        probe = _get_submit_probe_v1(driver)
        network_logs = _get_menu_move_logs_v1(driver)
        after = _get_visible_menu_labels_v1(driver)
        href_after_click = _current_href_v1(driver)
        inline_success_alerts = [
            str(el.text or "").strip()
            for el in driver.find_elements(By.CSS_SELECTOR, ".alert.ok")
            if str(el.text or "").strip()
        ]
        success_toasts: list[str] = []
        toast_viewports: list[dict[str, str]] = []
        toast_deadline = time.monotonic() + 3.0
        while time.monotonic() < toast_deadline:
            success_toasts = [
                str(el.text or "").strip()
                for el in driver.find_elements(
                    By.CSS_SELECTOR,
                    ".appgenesis-toast-success-v1 .appgenesis-toast-message-v1",
                )
                if str(el.text or "").strip()
            ]
            toast_viewports = [
                {
                    "className": str(el.get_attribute("class") or "").strip(),
                    "text": str(el.text or "").strip(),
                }
                for el in driver.find_elements(
                    By.CSS_SELECTOR,
                    ".appgenesis-toast-viewport-v1, .appgenesis-toast-v1",
                )
            ]
            if success_toasts or toast_viewports:
                break
            time.sleep(0.2)
        body_class_name = driver.execute_script(
            "return document.body ? String(document.body.className || '') : '';"
        )
        alerts = [
            str(el.text or "").strip()
            for el in driver.find_elements(By.CSS_SELECTOR, ".alert, .alert.ok, .alert.error")
            if str(el.text or "").strip()
        ]
        after_db_labels, after_db_orders = _collect_active_menu_orders_v1()

        driver.get(TARGET_URL)
        _open_target_page_v1(driver, wait)
        after_reload = _get_visible_menu_labels_v1(driver)

        result = {
            "before": before,
            "target_index": target_index,
            "target_label": target_label,
            "captured_form_payload": payload,
            "db_before": before_db_labels,
            "db_before_orders": before_db_orders,
            "probe": probe,
            "network_logs": network_logs,
            "alerts": alerts,
            "inline_success_alerts": inline_success_alerts,
            "success_toasts": success_toasts,
            "toast_viewports": toast_viewports,
            "body_class_name": body_class_name,
            "href_after_click": href_after_click,
            "after": after,
            "db_after": after_db_labels,
            "db_after_orders": after_db_orders,
            "after_reload": after_reload,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

        assert before, result
        assert not inline_success_alerts, result
    finally:
        driver.quit()


# ###################################################################################
# (3) DIAGNÓSTICO DIRETO DO BACKEND
# ###################################################################################


def test_menu_move_backend_post_diagnostic_v1() -> None:
    before_labels, before_orders = _collect_active_menu_orders_v1()
    assert len(before_labels) >= 3

    target_label = before_labels[len(before_labels) // 2]

    with SessionLocal() as session:
        settings = get_sidebar_menu_settings(session)
    target_row = next(
        row
        for row in settings
        if row.get("is_active")
        and not row.get("is_deleted")
        and str(row.get("label") or "").strip() == target_label
    )

    payload = {
        "menu_key": str(target_row.get("key") or "").strip().lower(),
        "direction": "up",
        "subprocess_return_url": (
            "/users/new?menu=sessoes&admin_tab=contas&target=menu-subprocess-card-active"
            "#menu-subprocess-card-active"
        ),
    }

    client = _login_http_session_v1()
    try:
        response = client.post("/settings/menu/menu-move", data=payload)
        after_labels, after_orders = _collect_active_menu_orders_v1()
        result = {
            "before": before_labels,
            "after": after_labels,
            "payload": payload,
            "status_code": response.status_code,
            "location": response.headers.get("location", ""),
            "display_order_before": before_orders,
            "display_order_after": after_orders,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

        assert response.status_code == 303, result
    finally:
        client.close()


# ###################################################################################
# (4) ERRO INLINE CONTINUA VISÍVEL NO FLUXO MENU
# ###################################################################################


def test_menu_flow_keeps_inline_error_visible_v1() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        driver.get(
            f"{BASE_URL}/users/new?menu=sessoes&admin_tab=contas"
            "&target=menu-subprocess-card-active&error=Erro%20de%20teste"
            "#menu-subprocess-card-active"
        )
        _open_target_page_v1(driver, wait)

        inline_errors = [
            str(el.text or "").strip()
            for el in driver.find_elements(By.CSS_SELECTOR, ".alert.error")
            if str(el.text or "").strip()
        ]
        error_toasts = [
            str(el.text or "").strip()
            for el in driver.find_elements(
                By.CSS_SELECTOR,
                ".appgenesis-toast-error-v1 .appgenesis-toast-message-v1",
            )
            if str(el.text or "").strip()
        ]

        result = {
            "inline_errors": inline_errors,
            "error_toasts": error_toasts,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

        assert inline_errors, result
    finally:
        driver.quit()


# ###################################################################################
# (5) RENDER SERVER-SIDE DO MENU: SUCCESS INLINE SUPRIMIDO, ERROR INLINE MANTIDO
# ###################################################################################


def test_menu_flow_server_render_feedback_contract_v1() -> None:
    client = _login_http_session_v1()
    try:
        success_response = client.get(
            "/users/new",
            params={
                "menu": "sessoes",
                "admin_tab": "contas",
                "target": "menu-subprocess-card-active",
                "success": "Sucesso de teste",
            },
        )
        error_response = client.get(
            "/users/new",
            params={
                "menu": "sessoes",
                "admin_tab": "contas",
                "target": "menu-subprocess-card-active",
                "error": "Erro de teste",
            },
        )

        result = {
            "success_status": success_response.status_code,
            "error_status": error_response.status_code,
            "success_has_inline_ok": '<div class="alert ok">Sucesso de teste</div>'
            in success_response.text,
            "error_has_inline_error": '<div class="alert error">Erro de teste</div>'
            in error_response.text,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

        assert success_response.status_code == 200, result
        assert error_response.status_code == 200, result
        assert result["success_has_inline_ok"] is False, result
        assert result["error_has_inline_error"] is True, result
    finally:
        client.close()
