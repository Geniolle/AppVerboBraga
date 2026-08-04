from uuid import uuid4
from urllib.parse import parse_qs, quote, urlsplit

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from appgenesis.db.session import SessionLocal
from appgenesis.models import Entity, Member, MemberEntity, User
from appgenesis.models.enums import MemberEntityStatus, MemberStatus, UserAccountStatus
from appgenesis.services.passwords import hash_password

from tests.test_process_submenu_runtime_stage6_browser import (
    _browser_console_errors_v1,
    _build_driver_v1,
    _login_admin_v1,
)


def _wait_for_meu_perfil_page_v1(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
    wait.until(EC.presence_of_element_located((By.ID, "perfil-pessoal-card")))
    wait.until(
        lambda drv: drv.execute_script(
            """
            return Boolean(
              window.__APPGENESIS_BOOTSTRAP__ &&
              window.__APPGENESIS_BOOTSTRAP__.meuPerfil &&
              window.__APPGENESIS_BOOTSTRAP__.meuPerfil.menuKey === "meu_perfil"
            );
            """
        )
    )


def _active_sidebar_menu_key_v1(driver: webdriver.Chrome) -> str:
    active_menu = driver.find_elements(By.CSS_SELECTOR, ".menu-item.active")
    if not active_menu:
        return ""
    return str(active_menu[0].get_attribute("data-menu") or "").strip().lower()


def _create_regular_user_for_meu_perfil_v1() -> tuple[str, str]:
    email = f"qa_meu_perfil_{uuid4().hex[:10]}@example.com"
    password = "SenhaUtilizador123!"

    session = SessionLocal()
    try:
        entity = (
            session.query(Entity)
            .filter(Entity.is_active.is_(True))
            .order_by(Entity.id.asc())
            .first()
        )
        if entity is None:
            raise RuntimeError("Nao existe entidade ativa para testar o utilizador comum.")

        member = Member(
            full_name="QA Meu Perfil",
            primary_phone="910000000",
            email=email,
            member_status=MemberStatus.ACTIVE.value,
        )
        session.add(member)
        session.flush()

        user = User(
            member_id=member.id,
            login_email=email,
            password_hash=hash_password(password),
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="owner",
        )
        session.add(user)
        session.flush()

        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=entity.id,
                status=MemberEntityStatus.ACTIVE.value,
            )
        )
        session.commit()
        return email, password
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _delete_regular_user_for_meu_perfil_v1(email: str) -> None:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.login_email == email).one_or_none()
        if user is None:
            return
        session.query(MemberEntity).filter(MemberEntity.member_id == user.member_id).delete()
        session.query(User).filter(User.id == user.id).delete()
        session.query(Member).filter(Member.id == user.member_id).delete()
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _login_regular_user_v1(driver: webdriver.Chrome, wait: WebDriverWait) -> str:
    regular_email, regular_password = _create_regular_user_for_meu_perfil_v1()
    try:
        driver.get("http://127.0.0.1:8000/login")
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(regular_email)
        driver.find_element(By.NAME, "password").send_keys(regular_password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_contains("/users/new"))
        return regular_email
    except Exception:
        _delete_regular_user_for_meu_perfil_v1(regular_email)
        raise


def test_meu_perfil_browser_navigation_uses_canonical_bootstrap_and_tabs_v1() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        for tab_key, expected_card_id in [
            ("pessoal", "perfil-pessoal-card"),
            ("morada", "perfil-morada-card"),
            ("treinamento", "dados-treinamento-card"),
        ]:
            target = f"#{expected_card_id}"
            driver.get(
                "http://127.0.0.1:8000/users/new"
                f"?menu=perfil&profile_tab={tab_key}&target={quote(target)}{target}"
            )
            _wait_for_meu_perfil_page_v1(driver, wait)

            bootstrap = driver.execute_script(
                """
                return window.__APPGENESIS_BOOTSTRAP__.meuPerfil;
                """
            )
            assert bootstrap["menuKey"] == "meu_perfil"
            assert bootstrap["activeTab"] == tab_key
            assert bootstrap["activeTarget"] == f"#{expected_card_id}"
            assert [tab["key"] for tab in bootstrap["tabs"]] == ["pessoal", "morada", "treinamento"]

            assert driver.execute_script(
                """
                return Boolean(document.getElementById(arguments[0]));
                """,
                expected_card_id,
            )
            active_section = driver.execute_script(
                """
                const input = document.querySelector("[data-meu-perfil-section-input]");
                return input ? String(input.value || "") : "";
                """
            )
            assert isinstance(active_section, str)

        assert not _browser_console_errors_v1(driver)
    finally:
        driver.quit()


def test_meu_perfil_browser_navigation_includes_quantity_only_section_v1() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        driver.get("http://127.0.0.1:8000/users/new?menu=meu_perfil")
        _wait_for_meu_perfil_page_v1(driver, wait)

        bootstrap = driver.execute_script(
            """
            return window.__APPGENESIS_BOOTSTRAP__.meuPerfil;
            """
        )
        submenu_items = driver.execute_script(
            """
            return Array.from(document.querySelectorAll('#submenu-items .submenu-item')).map((el) => ({
              label: String(el.textContent || '').trim(),
              profileSection: String(el.dataset.profileSection || '').trim(),
              target: String(el.getAttribute('href') || '').trim()
            }));
            """
        )
        breadcrumb_before = driver.execute_script(
            """
            return {
              section: String(document.getElementById('process-shell-breadcrumb-section-v1')?.textContent || '').trim(),
              current: String(document.getElementById('process-shell-breadcrumb-current-v1')?.textContent || '').trim(),
              tab: String(document.getElementById('process-shell-breadcrumb-tab-v1')?.textContent || '').trim()
            };
            """
        )

        bootstrap_sections = [
            str(section.get("key") or "").strip()
            for section in bootstrap.get("personalSections", [])
            if str(section.get("key") or "").strip()
        ]
        submenu_sections = [str(item.get("profileSection") or "").strip() for item in submenu_items]
        submenu_labels = [str(item.get("label") or "").strip() for item in submenu_items]

        assert len(submenu_items) == len(bootstrap_sections)
        assert submenu_sections == bootstrap_sections
        assert submenu_labels == [
            str(section.get("label") or "").strip()
            for section in bootstrap.get("personalSections", [])
            if str(section.get("key") or "").strip()
        ]
        for expected_label in [
            "Dados pessoais",
            "Dados de morada",
            "Dados de agregados",
        ]:
            assert expected_label in submenu_labels
        assert "custom_canais_de_comunicacao_instantanea" not in submenu_labels
        assert "custom_nome_do_conjuge" not in submenu_labels
        assert "custom_morada" not in submenu_labels
        assert "custom_" not in breadcrumb_before["section"]
        assert "custom_" not in breadcrumb_before["current"]
        assert "custom_" not in breadcrumb_before["tab"]

        def _visible_labels_v1() -> list[str]:
            return driver.execute_script(
                """
                const card = document.getElementById('perfil-pessoal-card');
                return Array.from(card.querySelectorAll('.personal-item, .field'))
                  .filter((el) => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && style.visibility !== 'hidden' && !el.hidden;
                  })
                  .map((el) => String(el.querySelector('.personal-label')?.textContent || el.querySelector('label')?.textContent || '').trim())
                  .filter(Boolean);
                """
            )

        def _visible_quantity_hosts_v1() -> list[str]:
            return driver.execute_script(
                """
                const card = document.getElementById('perfil-pessoal-card');
                return Array.from(card.querySelectorAll('[data-profile-quantity-rule-key]'))
                  .filter((el) => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && style.visibility !== 'hidden' && !el.hidden;
                  })
                  .map((el) => String(el.getAttribute('data-profile-quantity-rule-key') || '').trim())
                  .filter(Boolean);
                """
            )

        def _visible_quantity_controls_v1() -> list[str]:
            return driver.execute_script(
                """
                const card = document.getElementById('perfil-pessoal-card');
                return Array.from(card.querySelectorAll("[name='custom_field__custom_quantos_filhos_tens']"))
                  .filter((el) => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && style.visibility !== 'hidden' && !el.hidden;
                  })
                  .map((el) => String(el.getAttribute('name') || '').trim())
                  .filter(Boolean);
                """
            )

        personal_link = driver.find_element(By.CSS_SELECTOR, ".submenu-item[data-profile-section='custom_dados_pessoais']")
        morada_link = driver.find_element(By.CSS_SELECTOR, ".submenu-item[data-profile-section='custom_dados_de_morada']")
        agregados_link = driver.find_element(By.CSS_SELECTOR, ".submenu-item[data-profile-section='custom_dados_de_agregados']")

        personal_link.click()
        wait.until(
            lambda drv: drv.execute_script(
                """
                return String(document.querySelector('[data-meu-perfil-section-input]')?.value || '').trim();
                """
            )
            == "custom_dados_pessoais"
        )
        personal_visible = _visible_labels_v1()
        assert "Nome" in personal_visible
        assert "Email" in personal_visible
        assert "Telefone" in personal_visible
        assert "País" in personal_visible
        assert "Estado civil" in personal_visible
        assert "Tem filhos" in personal_visible
        assert "Canais de comunicação instantânea" in personal_visible

        morada_link.click()
        wait.until(
            lambda drv: drv.execute_script(
                """
                return String(document.querySelector('[data-meu-perfil-section-input]')?.value || '').trim();
                """
            )
            == "custom_dados_de_morada"
        )
        morada_visible = _visible_labels_v1()
        assert "Nome" not in morada_visible
        assert "Email" not in morada_visible
        assert "Telefone" not in morada_visible
        assert "País" not in morada_visible
        assert "Morada" in morada_visible
        assert "Código postal" in morada_visible

        driver.execute_script(
            """
            const estadoCivil = document.querySelector("[name='custom_estado_civil']");
            const temFilhos = document.querySelector("[name='custom_tem_filhos']");
            const quantidadeFilhos = document.querySelector("[name='custom_field__custom_quantos_filhos_tens']");
            if (estadoCivil) {
              estadoCivil.value = "Casado";
              estadoCivil.dispatchEvent(new Event("input", { bubbles: true }));
              estadoCivil.dispatchEvent(new Event("change", { bubbles: true }));
            }
            if (temFilhos) {
              temFilhos.value = "Sim";
              temFilhos.dispatchEvent(new Event("input", { bubbles: true }));
              temFilhos.dispatchEvent(new Event("change", { bubbles: true }));
            }
            if (quantidadeFilhos) {
              quantidadeFilhos.value = "2";
              quantidadeFilhos.dispatchEvent(new Event("input", { bubbles: true }));
              quantidadeFilhos.dispatchEvent(new Event("change", { bubbles: true }));
            }
            if (typeof window.applyMeuPerfilProcessSubsequentVisibility === "function") {
              window.applyMeuPerfilProcessSubsequentVisibility();
            }
            """
        )
        wait.until(
            lambda drv: drv.execute_script(
                """
                const link = document.querySelector(".submenu-item[data-profile-section='custom_dados_de_agregados']");
                if (!link) {
                  return false;
                }
                const style = window.getComputedStyle(link);
                return style.display !== 'none' && style.visibility !== 'hidden';
                """
            )
        )
        agregados_link.click()
        wait.until(
            lambda drv: drv.execute_script(
                """
                return String(document.querySelector('[data-meu-perfil-section-input]')?.value || '').trim();
                """
            )
            == "custom_dados_de_agregados"
        )
        agregados_visible = _visible_labels_v1()
        quantity_hosts = _visible_quantity_hosts_v1()
        quantity_controls = _visible_quantity_controls_v1()
        assert "Nome" not in agregados_visible
        assert "Email" not in agregados_visible
        assert "Telefone" not in agregados_visible
        assert "País" not in agregados_visible
        assert quantity_controls == ["custom_field__custom_quantos_filhos_tens"]

        personal_link.click()
        wait.until(
            lambda drv: drv.execute_script(
                """
                return String(document.querySelector('[data-meu-perfil-section-input]')?.value || '').trim();
                """
            )
            == "custom_dados_pessoais"
        )
        personal_visible_again = _visible_labels_v1()
        assert "Nome" in personal_visible_again
        assert "Email" in personal_visible_again
        assert not _browser_console_errors_v1(driver)
    finally:
        driver.quit()


def test_meu_perfil_sidebar_navigation_updates_url_and_clears_previous_target_v1() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)

    try:
        _login_admin_v1(driver, wait)
        driver.get(
            "http://127.0.0.1:8000/users/new"
            "?menu=perfil_de_autorizacao&target=%23auth-objeto-form-card#auth-objeto-form-card"
        )
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
        wait.until(lambda drv: _active_sidebar_menu_key_v1(drv) == "perfil_de_autorizacao")
        assert "perfil_de_autorizacao" in driver.current_url
        assert "auth-objeto-form-card" in driver.current_url

        for menu_key in ["administrativo", "meu_perfil", "contactos", "meu_perfil", "perfil_de_autorizacao"]:
            driver.find_element(By.CSS_SELECTOR, f".menu-item[data-menu='{menu_key}']").click()
            wait.until(lambda drv, expected=menu_key: _active_sidebar_menu_key_v1(drv) == expected)

            parsed_url = urlsplit(driver.current_url)
            parsed_query = parse_qs(parsed_url.query)
            assert parsed_query.get("menu") == [menu_key]
            if menu_key == "meu_perfil":
                wait.until(EC.visibility_of_element_located((By.ID, "perfil-pessoal-card")))
                assert driver.find_element(By.ID, "perfil-pessoal-card").is_displayed()
                assert not driver.find_element(By.ID, "perfil-morada-card").is_displayed()
                assert not driver.find_element(By.ID, "dados-treinamento-card").is_displayed()
            else:
                assert not driver.find_element(By.ID, "perfil-pessoal-card").is_displayed()

            assert "target=%23auth-objeto-form-card" not in driver.current_url
            assert "#auth-objeto-form-card" not in driver.current_url
            assert "profile_tab=" not in driver.current_url
            assert "profile_section=" not in driver.current_url
            assert parsed_url.fragment == ""

        assert not _browser_console_errors_v1(driver)
    finally:
        driver.quit()


def test_meu_perfil_sidebar_navigation_updates_url_and_clears_previous_target_regular_user_v1() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)
    regular_email = ""

    try:
        regular_email = _login_regular_user_v1(driver, wait)
        driver.get("http://127.0.0.1:8000/users/new")
        wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")
        sidebar_keys = [
            str(element.get_attribute("data-menu") or "").strip().lower()
            for element in driver.find_elements(By.CSS_SELECTOR, ".menu-item[data-menu]")
        ]
        source_menu_key = next(
            (menu_key for menu_key in sidebar_keys if menu_key and menu_key != "meu_perfil"),
            "meu_perfil",
        )
        if source_menu_key != _active_sidebar_menu_key_v1(driver):
            driver.find_element(By.CSS_SELECTOR, f".menu-item[data-menu='{source_menu_key}']").click()
            wait.until(lambda drv, expected=source_menu_key: _active_sidebar_menu_key_v1(drv) == expected)

        driver.find_element(By.CSS_SELECTOR, ".menu-item[data-menu='meu_perfil']").click()
        wait.until(lambda drv: _active_sidebar_menu_key_v1(drv) == "meu_perfil")
        wait.until(EC.visibility_of_element_located((By.ID, "perfil-pessoal-card")))

        assert "menu=meu_perfil" in driver.current_url
        assert "target=" not in driver.current_url
        assert "#auth-objeto-form-card" not in driver.current_url
        assert not _browser_console_errors_v1(driver)
    finally:
        try:
            if regular_email:
                _delete_regular_user_for_meu_perfil_v1(regular_email)
        except Exception:
            pass
        driver.quit()
