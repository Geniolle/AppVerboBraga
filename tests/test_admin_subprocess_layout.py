from pathlib import Path

from appgenesis.admin_subprocesses.models import AdminSubprocessState
from appgenesis.admin_subprocesses.registry import (
    AUTHORIZATION_PROFILE_CONFIG,
    ENTIDADE_CONFIG,
    OBJETO_AUTORIZACAO_CONFIG,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) MECANISMO GENERICO form_grid_css_class (reutilizavel por qualquer subprocesso)
####################################################################################


def test_admin_subprocess_form_grid_uses_generic_config_class_not_hardcoded_key() -> None:
    template_text = (PROJECT_ROOT / "templates" / "macros" / "admin_subprocess.html").read_text(
        encoding="utf-8"
    )

    assert 'data-admin-subprocess-field-key="{{ field.key }}"' in template_text
    assert "state.config.form_grid_css_class" in template_text
    assert "state.config.key == 'objeto_de_autorizacao'" not in template_text
    # A classe generica deve ser aplicada tanto na grelha de edicao como na de criacao,
    # corrigindo a inconsistencia em que so' o formulario de edicao a recebia.
    assert template_text.count("state.config.form_grid_css_class") >= 2


def test_objeto_autorizacao_config_sets_dedicated_grid_variant() -> None:
    css_text = (PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v1.css").read_text(
        encoding="utf-8"
    )

    assert OBJETO_AUTORIZACAO_CONFIG.form_grid_css_class == "admin-subprocess-grid-objeto-autorizacao-v1"
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"custom_nome_do_perfil\"]' in css_text
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"custom_processo\"]' in css_text
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"custom_subprocesso\"]' in css_text
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"visibility_scope_mode\"]' in css_text
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"status\"]' in css_text


def test_objeto_autorizacao_create_and_edit_forms_both_get_dedicated_grid_variant() -> None:
    env = _build_admin_subprocess_jinja_env_v1()
    macro_module = env.get_template("macros/admin_subprocess.html").module

    create_html = macro_module.render_admin_subprocess_form(
        AdminSubprocessState(config=OBJETO_AUTORIZACAO_CONFIG, mode="create")
    )
    edit_html = macro_module.render_admin_subprocess_form(
        AdminSubprocessState(config=OBJETO_AUTORIZACAO_CONFIG, mode="edit", edit_data={"key": "x"})
    )

    assert "admin-subprocess-grid-v1 admin-subprocess-grid-objeto-autorizacao-v1" in create_html
    assert "admin-subprocess-grid-v1 admin-subprocess-grid-objeto-autorizacao-v1" in edit_html


####################################################################################
# (2) LAYOUT ESPECIFICO DO PERFIL DE AUTORIZACAO (campo "Entidade" read-only)
####################################################################################


def test_auth_profile_config_sets_dedicated_grid_variant_pairing_entidade_with_estado() -> None:
    css_text = (PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v1.css").read_text(
        encoding="utf-8"
    )

    assert AUTHORIZATION_PROFILE_CONFIG.form_grid_css_class == "admin-subprocess-grid-auth-profile-v1"
    assert '.admin-subprocess-grid-auth-profile-v1 > [data-admin-subprocess-field-key=\"status\"]' in css_text
    assert '.admin-subprocess-grid-auth-profile-v1 > [data-admin-subprocess-field-key=\"entity_number\"]' in css_text
    # O campo "Escopo do perfil" (entity_scope) foi removido do processo.
    assert '[data-admin-subprocess-field-key=\"entity_scope\"]' not in css_text


def test_auth_profile_entity_number_field_is_readonly_and_not_client_editable() -> None:
    entity_number_field = next(
        field for field in AUTHORIZATION_PROFILE_CONFIG.fields if field.key == "entity_number"
    )

    assert entity_number_field.label == "Entidade"
    assert entity_number_field.field_type == "readonly"


def test_auth_profile_config_has_no_entity_scope_field() -> None:
    assert all(field.key != "entity_scope" for field in AUTHORIZATION_PROFILE_CONFIG.fields)
    assert all(
        field.input_name != "auth_profile_entity_scope"
        for field in AUTHORIZATION_PROFILE_CONFIG.fields
    )


def test_auth_profile_entity_number_renders_readonly_input_with_context_value() -> None:
    from appgenesis.services.auth_profile_entity_scope import build_auth_profile_config_for_context_v1

    entity_context = {
        "selected_entity_number": "1001",
    }
    config = build_auth_profile_config_for_context_v1(
        AUTHORIZATION_PROFILE_CONFIG, entity_context
    )

    env = _build_admin_subprocess_jinja_env_v1()
    macro_module = env.get_template("macros/admin_subprocess.html").module

    html = macro_module.render_admin_subprocess_form(
        AdminSubprocessState(config=config, mode="create")
    )

    assert 'data-admin-subprocess-field-key="entity_number"' in html
    assert 'value="1001"' in html
    assert "readonly" in html
    # O payload submetido nao deve poder controlar o numero de entidade guardado;
    # o input existe apenas como espelho do contexto do servidor.
    assert 'name="auth_profile_entity_number_display"' in html
    # O campo "Escopo do perfil" foi removido: nao deve haver select nem opcoes
    # de "Entidade atual" / "Todo o sistema" para Perfil de autorizacao.
    assert "auth_profile_entity_scope" not in html
    assert "Escopo do perfil" not in html
    assert "Entidade atual" not in html
    assert "Todo o sistema" not in html


def test_admin_subprocess_readonly_field_type_not_used_by_unrelated_subprocesses() -> None:
    assert all(field.field_type != "readonly" for field in ENTIDADE_CONFIG.fields)


def _build_admin_subprocess_jinja_env_v1():
    from jinja2 import Environment, FileSystemLoader

    return Environment(loader=FileSystemLoader(str(PROJECT_ROOT / "templates")))
