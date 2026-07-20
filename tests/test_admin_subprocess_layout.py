from dataclasses import replace
from pathlib import Path

from appgenesis.admin_subprocesses.service import build_admin_subprocess_state
from appgenesis.admin_subprocesses.models import AdminSubprocessState
from appgenesis.admin_subprocesses.registry import (
    AUTHORIZATION_PROFILE_CONFIG,
    ENTIDADE_CONFIG,
    OBJETO_AUTORIZACAO_CONFIG,
    UTILIZADOR_CONFIG,
)
from appgenesis.admin_subprocesses.service import build_admin_subprocess_config_for_entity_context_v1
from appgenesis.admin_subprocesses.models import AdminFieldConfig


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

    assert OBJETO_AUTORIZACAO_CONFIG.form_grid_css_class == "admin-subprocess-grid-entity-context-v1"
    assert '.admin-subprocess-grid-entity-context-v1 {' in css_text


def test_objeto_autorizacao_create_and_edit_forms_both_get_dedicated_grid_variant() -> None:
    env = _build_admin_subprocess_jinja_env_v1()
    macro_module = env.get_template("macros/admin_subprocess.html").module

    create_html = macro_module.render_admin_subprocess_form(
        AdminSubprocessState(config=OBJETO_AUTORIZACAO_CONFIG, mode="create")
    )
    edit_html = macro_module.render_admin_subprocess_form(
        AdminSubprocessState(config=OBJETO_AUTORIZACAO_CONFIG, mode="edit", edit_data={"key": "x"})
    )

    assert "admin-subprocess-grid-v1 admin-subprocess-grid-entity-context-v1" in create_html
    assert "admin-subprocess-grid-v1 admin-subprocess-grid-entity-context-v1" in edit_html


def test_objeto_autorizacao_entity_context_builder_adds_entidade_next_to_estado_without_duplication() -> None:
    config = build_admin_subprocess_config_for_entity_context_v1(
        OBJETO_AUTORIZACAO_CONFIG,
        {"selected_entity_number": "1001"},
    )

    assert [field.key for field in config.fields][-2:] == ["status", "entity_number"]
    assert sum(1 for field in config.fields if field.key == "entity_number") == 1
    assert next(field for field in config.fields if field.key == "entity_number").field_type == "readonly"


def test_objeto_autorizacao_state_prefers_normalized_edit_values() -> None:
    state = build_admin_subprocess_state(
        config=OBJETO_AUTORIZACAO_CONFIG,
        rows=[
            {
                "key": "gestor-de-tesouraria",
                "label": "Gestor de Tesouraria",
                "is_active": True,
                "values": {
                    "objeto_de_autorizacao": "Gestor de Tesouraria",
                    "process_label": "extrato",
                    "authorization_label": "Todas autorizações",
                },
                "edit_values": {
                    "custom_nome_do_perfil": "Gestor de Tesouraria",
                    "custom_processo": "extrato",
                    "custom_subprocesso": "Todas autorizações",
                },
            }
        ],
        edit_key="gestor-de-tesouraria",
        sidebar_menu_settings=[
            {
                "key": "perfil_de_autorizacao",
                "label": "Perfil de autorização",
                "is_active": True,
                "is_deleted": False,
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_nome_do_perfil",
                        "header_key": "custom_objeto_de_autorizacao",
                    },
                    {
                        "field_key": "custom_processo",
                        "header_key": "custom_objeto_de_autorizacao",
                    },
                    {
                        "field_key": "custom_subprocesso",
                        "header_key": "custom_objeto_de_autorizacao",
                    },
                ],
                "process_field_options": [
                    {
                        "key": "custom_nome_do_perfil",
                        "label": "Nome do perfil",
                        "field_type": "list",
                        "list_source_type": "manual",
                        "manual_list_key": "list_perfil",
                        "list_key": "list_perfil",
                        "options": [
                            {"value": "Gestor de Tesouraria", "label": "Gestor de Tesouraria"}
                        ],
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "list",
                        "list_source_type": "profile_menu_tabs",
                        "automatic_source_field_key": "custom_nome_do_perfil",
                        "options": [
                            {"value": "extrato", "label": "extrato"}
                        ],
                    },
                    {
                        "key": "custom_subprocesso",
                        "label": "Autorização",
                        "field_type": "list",
                        "list_source_type": "profile_menu_tabs",
                        "automatic_source_field_key": "custom_processo",
                        "options": [
                            {"value": "Todas autorizações", "label": "Todas autorizações"}
                        ],
                    },
                ],
            }
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao"},
        menu_process_history_map={"perfil_de_autorizacao": []},
    )

    assert state.is_editing is True
    assert state.edit_values["custom_nome_do_perfil"] == "Gestor de Tesouraria"
    assert state.edit_values["custom_processo"] == "extrato"
    assert state.edit_values["custom_subprocesso"] == "Todas autorizações"


####################################################################################
# (2) LAYOUT ESPECIFICO DO PERFIL DE AUTORIZACAO (campo "Entidade" read-only)
####################################################################################


def test_auth_profile_config_sets_dedicated_grid_variant_pairing_entidade_with_estado() -> None:
    css_text = (PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v1.css").read_text(
        encoding="utf-8"
    )

    assert AUTHORIZATION_PROFILE_CONFIG.form_grid_css_class == "admin-subprocess-grid-entity-context-v1"
    assert '.admin-subprocess-grid-entity-context-v1 {' in css_text


def test_auth_profile_entity_number_field_is_readonly_and_not_client_editable() -> None:
    config = build_admin_subprocess_config_for_entity_context_v1(
        AUTHORIZATION_PROFILE_CONFIG,
        {"selected_entity_number": "1001"},
    )
    entity_number_field = next(field for field in config.fields if field.key == "entity_number")

    assert entity_number_field.label == "Entidade"
    assert entity_number_field.field_type == "readonly"
    assert entity_number_field.default_value == "1001"


def test_auth_profile_config_has_no_entity_scope_field() -> None:
    assert all(field.key != "entity_scope" for field in AUTHORIZATION_PROFILE_CONFIG.fields)
    assert all(
        field.input_name != "auth_profile_entity_scope"
        for field in AUTHORIZATION_PROFILE_CONFIG.fields
    )


def test_entity_context_builder_adds_entidade_next_to_estado_without_duplication() -> None:
    config = build_admin_subprocess_config_for_entity_context_v1(
        AUTHORIZATION_PROFILE_CONFIG,
        {"selected_entity_number": "1001"},
    )

    assert [field.key for field in config.fields][-2:] == ["status", "entity_number"]
    assert sum(1 for field in config.fields if field.key == "entity_number") == 1


def test_auth_profile_entity_number_renders_readonly_input_with_context_value() -> None:
    config = build_admin_subprocess_config_for_entity_context_v1(
        AUTHORIZATION_PROFILE_CONFIG,
        {"selected_entity_number": "1001"},
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
    assert 'name="perfil_de_autorizacao_entity_number_display"' in html
    # O campo "Escopo do perfil" foi removido: nao deve haver select nem opcoes
    # de "Entidade atual" / "Todo o sistema" para Perfil de autorizacao.
    assert "auth_profile_entity_scope" not in html
    assert "Escopo do perfil" not in html
    assert "Entidade atual" not in html
    assert "Todo o sistema" not in html


def test_admin_subprocess_readonly_field_type_not_used_by_unrelated_subprocesses() -> None:
    assert all(field.field_type != "readonly" for field in ENTIDADE_CONFIG.fields)


def test_generic_entity_scoped_config_gets_entity_context_fields_automatically() -> None:
    synthetic_config = replace(
        UTILIZADOR_CONFIG,
        key="processo_sintetico",
        uses_entity_context=True,
        fields=(
            AdminFieldConfig(
                key="status",
                label="Estado",
                input_name="processo_sintetico_status",
                field_type="select",
                required=True,
                options=(
                    ("ativo", "Ativo"),
                    ("inativo", "Inativo"),
                ),
            ),
        ),
        form_grid_css_class="",
    )

    config = build_admin_subprocess_config_for_entity_context_v1(
        synthetic_config,
        {"selected_entity_number": "1001"},
    )

    assert [field.key for field in config.fields] == ["status", "entity_number"]
    assert config.fields[-1].field_type == "readonly"
    assert config.fields[-1].default_value == "1001"
    assert config.form_grid_css_class == "admin-subprocess-grid-entity-context-v1"


def _build_admin_subprocess_jinja_env_v1():
    from jinja2 import Environment, FileSystemLoader

    return Environment(loader=FileSystemLoader(str(PROJECT_ROOT / "templates")))
