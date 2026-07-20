from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from urllib.parse import quote

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
)


# ###################################################################################
# (1) HELPERS
# ###################################################################################


def _create_owner_user_on_entity_v1(entity_id: int) -> tuple[str, str, int]:
    email = f"qa_meu_perfil_entidade8_{uuid4().hex[:10]}@example.com"
    password = "SenhaUtilizador123!"

    session = SessionLocal()
    try:
        entity = session.get(Entity, entity_id)
        if entity is None or not entity.is_active:
            raise RuntimeError(f"Entidade {entity_id} indisponivel para o teste browser.")

        member = Member(
            full_name="QA Meu Perfil Entidade 8",
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
        return email, password, int(member.id)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _delete_owner_user_on_entity_v1(email: str, member_id: int) -> None:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.login_email == email).one_or_none()
        if user is None:
            return
        session.query(MemberEntity).filter(MemberEntity.member_id == member_id).delete()
        session.query(User).filter(User.id == user.id).delete()
        session.query(Member).filter(Member.id == member_id).delete()
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _login_owner_v1(driver, wait: WebDriverWait, email: str, password: str) -> None:
    driver.get("http://127.0.0.1:8000/login")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/users/new"))


def _wait_for_meu_perfil_page_v1(driver, wait: WebDriverWait) -> None:
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


def _click_sidebar_menu_v1(driver, menu_key: str) -> None:
    driver.find_element(By.CSS_SELECTOR, f"button.menu-item[data-menu='{menu_key}']").click()


def _count_visible_v1(driver, selector: str) -> int:
    return int(
        driver.execute_script(
            """
            const selector = arguments[0];
            return Array.from(document.querySelectorAll(selector)).filter((el) => {
              const style = getComputedStyle(el);
              return style.display !== "none" && style.visibility !== "hidden" && !el.hidden;
            }).length;
            """,
            selector,
        )
    )


def _count_profile_metrics_v1(driver) -> dict[str, object]:
    return driver.execute_script(
        """
        const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};
        const meuPerfil = bootstrap.meuPerfil || {};
        const entityNameEl = document.querySelector(".sidebar-product-name-v1");
        const activeMenu = Array.from(document.querySelectorAll(".menu-item.active")).map((el) => {
          return String(el.getAttribute("data-menu") || "");
        });
        const visibleCount = (selector) => Array.from(document.querySelectorAll(selector)).filter((el) => {
          const style = getComputedStyle(el);
          return style.display !== "none" && style.visibility !== "hidden" && !el.hidden;
        }).length;

        return {
          url: location.href,
          entityName: entityNameEl ? String(entityNameEl.textContent || "").trim() : "",
          activeMenu,
          activeTab: Array.from(document.querySelectorAll(".submenu-item.active")).map((el) => String(el.textContent || "").trim()).filter(Boolean),
          bootstrap: {
            activeMenuKey: String(bootstrap.initialMenu || ""),
            meuPerfilMenuKey: String(meuPerfil.menuKey || ""),
            activePersonalSection: String(meuPerfil.activePersonalSection || ""),
            activeTabKey: String(meuPerfil.activeTab || ""),
            selectedSectionInput: String((document.querySelector("[data-meu-perfil-section-input]") || {}).value || "")
          },
          counts: {
            readonly: document.querySelectorAll("#perfil-pessoal-card .profile-readonly .personal-item").length,
            form: document.querySelectorAll("#perfil-pessoal-card .profile-edit-form .field").length,
            panes: document.querySelectorAll("#perfil-pessoal-card [data-profile-section-pane]").length,
            fieldKeys: document.querySelectorAll("#perfil-pessoal-card [data-profile-field-key]").length
          },
          visibleCounts: {
            readonly: visibleCount("#perfil-pessoal-card .profile-readonly .personal-item"),
            form: visibleCount("#perfil-pessoal-card .profile-edit-form .field"),
            panes: visibleCount("#perfil-pessoal-card [data-profile-section-pane]"),
            fieldKeys: visibleCount("#perfil-pessoal-card [data-profile-field-key]")
          }
        };
        """
    )


def _collect_meu_perfil_section_state_v1(driver) -> dict[str, object]:
    return driver.execute_script(
        """
        const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};
        const meuPerfil = bootstrap.meuPerfil || {};
        const personalCard = document.getElementById("perfil-pessoal-card");
        const sectionNodes = Array.from(
          personalCard ? personalCard.querySelectorAll("[data-profile-section-pane]") : []
        );
        const sectionKeys = Array.from(
          new Set(
            sectionNodes
              .map((el) => String(el.dataset.profileSectionPane || "").trim())
              .filter(Boolean)
          )
        );
        const isVisible = (el) => {
          if (!el) {
            return false;
          }
          const style = getComputedStyle(el);
          return style.display !== "none" && style.visibility !== "hidden" && !el.hidden;
        };
        const visibleCountBySection = {};
        sectionKeys.forEach((sectionKey) => {
          const selector = `#perfil-pessoal-card [data-profile-section-pane="${sectionKey.replace(/"/g, '\\"')}"]`;
          visibleCountBySection[sectionKey] = Array.from(document.querySelectorAll(selector)).filter(isVisible).length;
        });
        return {
          hiddenMeuPerfilSectionKeys: Array.isArray(meuPerfil.hiddenPersonalSectionKeys)
            ? meuPerfil.hiddenPersonalSectionKeys
            : [],
          personalSections: Array.isArray(meuPerfil.personalSections)
            ? meuPerfil.personalSections.map((section) => String(section.key || "").trim()).filter(Boolean)
            : [],
          activePersonalSection: String(meuPerfil.activePersonalSection || ""),
          selectedSectionInput: String((document.querySelector("[data-meu-perfil-section-input]") || {}).value || ""),
          visibleCountBySection,
          totalVisibleSectionPanes: sectionNodes.filter(isVisible).length
        };
        """
    )


def _assert_meu_perfil_ready_v1(driver) -> None:
    metrics = _count_profile_metrics_v1(driver)
    assert metrics["entityName"] == "Deixa Estar Tech"
    assert "meu_perfil" in metrics["activeMenu"] or metrics["bootstrap"]["meuPerfilMenuKey"] == "meu_perfil"
    assert metrics["counts"]["readonly"] > 0
    assert metrics["counts"]["form"] > 0
    assert metrics["counts"]["panes"] > 0
    assert metrics["visibleCounts"]["readonly"] > 0
    assert metrics["visibleCounts"]["form"] > 0
    assert metrics["visibleCounts"]["panes"] > 0
    assert metrics["visibleCounts"]["fieldKeys"] > 0
    assert driver.find_element(By.ID, "perfil-pessoal-card").is_displayed()
    assert not driver.find_element(By.ID, "perfil-morada-card").is_displayed()
    assert not driver.find_element(By.ID, "dados-treinamento-card").is_displayed()


def _assert_meu_perfil_edit_mode_v1(driver) -> None:
    readonly = driver.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card .profile-readonly")
    edit_form = driver.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card .profile-edit-form")
    assert readonly.is_displayed()
    assert edit_form.is_displayed()


def _assert_meu_perfil_cancelled_v1(driver) -> None:
    readonly = driver.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card .profile-readonly")
    edit_form = driver.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card .profile-edit-form")
    assert readonly.is_displayed()
    assert not edit_form.is_displayed()


def _ensure_artifacts_dir_v1() -> None:
    Path("tests/_artifacts").mkdir(parents=True, exist_ok=True)


# ###################################################################################
# (2) TESTE BROWSER
# ###################################################################################


def test_meu_perfil_fields_browser_navigation_and_visibility_v1() -> None:
    driver = _build_driver_v1()
    wait = WebDriverWait(driver, 30)
    email = ""
    member_id = 0

    try:
        email, password, member_id = _create_owner_user_on_entity_v1(8)
        _login_owner_v1(driver, wait, email, password)

        scenarios = [
            {
                "name": "home",
                "url": "http://127.0.0.1:8000/users/new?menu=home",
                "needs_click": True,
                "before_artifact": "tests/_artifacts/meu_perfil_from_home_before.png",
                "after_artifact": "tests/_artifacts/meu_perfil_from_home_after.png",
            },
            {
                "name": "auth",
                "url": "http://127.0.0.1:8000/users/new?menu=perfil_de_autorizacao&target=%23auth-objeto-form-card#auth-objeto-form-card",
                "needs_click": True,
                "after_artifact": "tests/_artifacts/meu_perfil_from_auth_after.png",
            },
            {
                "name": "contactos",
                "url": "http://127.0.0.1:8000/users/new?menu=contactos",
                "needs_click": True,
                "after_artifact": "tests/_artifacts/meu_perfil_from_contacts_after.png",
            },
            {
                "name": "direct",
                "url": "http://127.0.0.1:8000/users/new?menu=meu_perfil",
                "needs_click": False,
                "after_artifact": "tests/_artifacts/meu_perfil_direct_after.png",
            },
        ]

        _ensure_artifacts_dir_v1()

        for run_index in range(2):
            for scenario in scenarios:
                driver.get(scenario["url"])
                _wait_for_meu_perfil_page_v1(driver, wait)

                if scenario.get("name") == "home" and scenario.get("before_artifact"):
                    before_metrics = _count_profile_metrics_v1(driver)
                    before_section_state = _collect_meu_perfil_section_state_v1(driver)
                    driver.save_screenshot(scenario["before_artifact"])
                    assert before_metrics["url"].endswith("/users/new?menu=home")
                    assert "home" in before_metrics["activeMenu"]
                    assert "meu_perfil" not in before_metrics["activeMenu"]
                    assert before_metrics["entityName"] == "Deixa Estar Tech"
                    assert driver.find_element(By.CSS_SELECTOR, "button.menu-item[data-menu='home']").get_attribute("class").find("active") >= 0
                    assert driver.find_element(By.CSS_SELECTOR, "button.menu-item[data-menu='meu_perfil']").get_attribute("class").find("active") < 0
                    assert before_section_state["personalSections"]
                    assert before_section_state["activePersonalSection"]
                    assert before_section_state["selectedSectionInput"]

                if scenario["needs_click"]:
                    _click_sidebar_menu_v1(driver, "meu_perfil")

                wait.until(lambda drv: "menu=meu_perfil" in drv.current_url)
                wait.until(lambda drv: "menu=home" not in drv.current_url)
                wait.until(lambda drv: drv.find_element(By.CSS_SELECTOR, "button.menu-item[data-menu='meu_perfil']").get_attribute("class").find("active") >= 0)
                wait.until(lambda drv: drv.find_element(By.ID, "perfil-pessoal-card").is_displayed())

                after_metrics = _count_profile_metrics_v1(driver)
                after_section_state = _collect_meu_perfil_section_state_v1(driver)
                driver.save_screenshot(scenario["after_artifact"])

                assert after_metrics["entityName"] == "Deixa Estar Tech"
                assert "meu_perfil" in after_metrics["activeMenu"]
                assert after_metrics["bootstrap"]["meuPerfilMenuKey"] == "meu_perfil"
                assert after_section_state["personalSections"]
                assert after_section_state["activePersonalSection"]
                assert after_section_state["selectedSectionInput"]
                assert after_section_state["totalVisibleSectionPanes"] > 0
                assert any(
                    visible_count > 0
                    for visible_count in after_section_state["visibleCountBySection"].values()
                )
                assert after_metrics["counts"]["readonly"] > 0
                assert after_metrics["counts"]["form"] > 0
                assert after_metrics["counts"]["panes"] > 0
                assert after_metrics["visibleCounts"]["readonly"] > 0
                assert after_metrics["visibleCounts"]["form"] > 0
                assert after_metrics["visibleCounts"]["panes"] > 0
                assert after_metrics["visibleCounts"]["fieldKeys"] > 0

                assert driver.find_element(By.ID, "perfil-pessoal-card").is_displayed()
                assert not driver.find_element(By.ID, "perfil-morada-card").is_displayed()
                assert not driver.find_element(By.ID, "dados-treinamento-card").is_displayed()

                if scenario["name"] in {"home", "direct"}:
                    edit_button = driver.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card .profile-edit-toggle")
                    edit_button.click()
                    wait.until(lambda drv: drv.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card").get_attribute("class").find("editing") >= 0)
                    driver.save_screenshot("tests/_artifacts/meu_perfil_edit_form.png")
                    _assert_meu_perfil_edit_mode_v1(driver)
                    assert _count_visible_v1(driver, "#perfil-pessoal-card .profile-edit-form input, #perfil-pessoal-card .profile-edit-form select, #perfil-pessoal-card .profile-edit-form textarea") > 0

                    cancel_button = driver.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card [data-appgenesis-cancel='1']")
                    cancel_button.click()
                    wait.until(lambda drv: drv.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card").get_attribute("class").find("editing") < 0)
                    _assert_meu_perfil_cancelled_v1(driver)

                assert not _browser_console_errors_v1(driver)
                if scenario["name"] == "home":
                    assert after_metrics["bootstrap"]["selectedSectionInput"]

        assert not _browser_console_errors_v1(driver)
    finally:
        try:
            if email and member_id:
                _delete_owner_user_on_entity_v1(email, member_id)
        finally:
            driver.quit()
