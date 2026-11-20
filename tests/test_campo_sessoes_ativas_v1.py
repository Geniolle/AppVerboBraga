from appgenesis.services.profile import resolve_field_list_options_v1


def test_active_sessions_list_source_returns_only_active_sidebar_sections():
    sidebar_menu_settings = [
        {
            "key": "administrativo",
            "menu_config": {
                "sidebar_sections": [
                    {"key": "igreja_ativa", "label": "Igreja Ativa", "status": "ativo"},
                    {"key": "campanha_inativa", "label": "Campanha Inativa", "status": "inativo"},
                ]
            },
        }
    ]
    field_definition = {
        "key": "sessao_origem",
        "label": "SESSÃO DA ORIGEM",
        "field_type": "list",
        "list_source_type": "active_sessions",
    }

    options = resolve_field_list_options_v1(
        current_menu_key="perfil_de_autorizacao",
        field_definition=field_definition,
        sidebar_menu_settings=sidebar_menu_settings,
    )
    labels = [option["label"].lower() for option in options]

    assert "igreja ativa" in labels
    assert "campanha inativa" not in labels


def test_active_sessions_is_accepted_by_normalizers():
    from appgenesis.services.process_settings.additional_field_service import (
        _normalize_additional_field_list_source_type_v1,
    )
    from appgenesis.services.process_tabs import _normalize_process_tab_list_source_type_v1

    assert _normalize_additional_field_list_source_type_v1("active_sessions") == "active_sessions"
    assert _normalize_process_tab_list_source_type_v1("active_sessions", {}) == "active_sessions"


def test_menu_options_carry_their_sidebar_section_for_dependent_filter():
    from appgenesis.services.profile import resolve_active_menu_options_v1

    options = resolve_active_menu_options_v1(
        [
            {"key": "empresa", "label": "Empresa", "is_active": True, "is_deleted": False, "sidebar_section_key": "dados_gerais"},
            {"key": "home", "label": "Home", "is_active": True, "is_deleted": False, "sidebar_section_key": "geral"},
        ]
    )
    by_value = {option["value"]: option["section"] for option in options}

    assert by_value == {"empresa": "dados_gerais", "home": "geral"}


def test_menu_origin_filter_script_is_wired_into_page():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    script = (root / "static" / "js" / "modules" / "auth_profile_menu_origin_filter_v1.js").read_text(encoding="utf-8")
    template = (root / "templates" / "new_user.html").read_text(encoding="utf-8")

    assert 'select[data-depends-on]' in script
    assert "auth_profile_menu_origin_filter_v1.js" in template
