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
