import json

from jinja2.runtime import Undefined

from appgenesis.domains.meu_perfil.service import (
    build_meu_perfil_bootstrap_v1,
    build_meu_perfil_personal_sections_state_v1,
    build_meu_perfil_navigation_state_v1,
    normalize_meu_perfil_menu_key_v1,
    normalize_meu_perfil_tab_key_v1,
    resolve_meu_perfil_tab_target_v1,
)


def test_normalize_meu_perfil_menu_key_v1_maps_legacy_aliases() -> None:
    assert normalize_meu_perfil_menu_key_v1("meu_perfil") == "meu_perfil"
    assert normalize_meu_perfil_menu_key_v1("perfil") == "meu_perfil"
    assert normalize_meu_perfil_menu_key_v1("documentos") == "meu_perfil"


def test_normalize_meu_perfil_tab_key_v1_defaults_to_pessoal() -> None:
    assert normalize_meu_perfil_tab_key_v1("morada") == "morada"
    assert normalize_meu_perfil_tab_key_v1("treinamento") == "treinamento"
    assert normalize_meu_perfil_tab_key_v1("qualquer-coisa") == "pessoal"


def test_resolve_meu_perfil_tab_target_v1_returns_expected_cards() -> None:
    assert resolve_meu_perfil_tab_target_v1("pessoal") == "#perfil-pessoal-card"
    assert resolve_meu_perfil_tab_target_v1("morada") == "#perfil-morada-card"
    assert resolve_meu_perfil_tab_target_v1("treinamento") == "#dados-treinamento-card"


def test_build_meu_perfil_navigation_state_v1_preserves_section_and_target() -> None:
    state = build_meu_perfil_navigation_state_v1(
        menu_key="perfil",
        profile_tab="morada",
        profile_section="dados_pessoais",
        target="#perfil-morada-card",
    )

    assert state.menu_key == "meu_perfil"
    assert state.tab == "morada"
    assert state.target == "#perfil-morada-card"
    assert state.section == "dados_pessoais"


def test_build_meu_perfil_bootstrap_v1_exposes_tabs() -> None:
    bootstrap = build_meu_perfil_bootstrap_v1(
        profile_tab="treinamento",
        profile_section="treinos",
        profile_personal_sections=[{"key": "dados", "label": "Dados"}],
        profile_personal_visible_fields=["nome"],
        profile_personal_field_labels={"nome": "Nome"},
    )

    assert bootstrap["menuKey"] == "meu_perfil"
    assert [tab["key"] for tab in bootstrap["tabs"]] == ["pessoal", "morada", "treinamento"]
    assert bootstrap["activeTab"] == "treinamento"
    assert bootstrap["activeTarget"] == "#dados-treinamento-card"
    assert bootstrap["activeSection"] == "dados"
    assert bootstrap["personalSections"] == [{"key": "dados", "label": "Dados"}]


def test_build_meu_perfil_bootstrap_v1_sanitizes_undefined_values() -> None:
    bootstrap = build_meu_perfil_bootstrap_v1(
        profile_tab="pessoal",
        profile_section=Undefined(name="missing-section"),
        profile_personal_sections=[
            {
                "key": "dados",
                "label": Undefined(name="missing-label"),
            }
        ],
        profile_personal_visible_fields=[Undefined(name="missing-field")],
        profile_personal_field_labels={"nome": Undefined(name="missing-name")},
    )

    assert bootstrap["activeSection"] == "dados"
    assert bootstrap["activePersonalSection"] == "dados"
    assert bootstrap["personalSections"] == [{"key": "dados", "label": ""}]
    assert bootstrap["visibleFields"] == [""] 
    assert bootstrap["fieldLabels"] == {"nome": ""}
    json.dumps(bootstrap)


def test_build_meu_perfil_bootstrap_v1_falls_back_to_first_personal_section() -> None:
    bootstrap = build_meu_perfil_bootstrap_v1(
        profile_tab="pessoal",
        profile_section="seccao-inexistente",
        profile_personal_sections=[
            {"key": "dados", "label": "Dados"},
            {"key": "morada", "label": "Morada"},
        ],
    )

    assert bootstrap["activeSection"] == "dados"
    assert bootstrap["activePersonalSection"] == "dados"


def test_build_meu_perfil_personal_sections_state_v1_resolves_active_section() -> None:
    state = build_meu_perfil_personal_sections_state_v1(
        profile_personal_visible_fields=[
            "custom_dados_pessoais",
            "nome",
            "custom_morada",
            "telefone",
        ],
        profile_personal_field_labels={
            "custom_dados_pessoais": "Dados pessoais",
            "custom_morada": "Morada",
            "nome": "Nome",
            "telefone": "Telefone",
        },
        profile_personal_field_types={
            "custom_dados_pessoais": "header",
            "custom_morada": "header",
            "nome": "text",
            "telefone": "text",
        },
        profile_personal_field_header_map={
            "nome": "custom_dados_pessoais",
            "telefone": "custom_morada",
        },
        profile_personal_custom_field_meta={
            "custom_dados_pessoais": {"field_type": "header"},
            "custom_morada": {"field_type": "header"},
        },
        requested_profile_section="custom_morada",
    )

    assert [section["key"] for section in state["personalSections"]] == [
        "custom_dados_pessoais",
        "custom_morada",
    ]
    assert state["activePersonalSection"] == "custom_morada"
    assert state["defaultPersonalSection"] == "custom_dados_pessoais"
    assert state["personalFieldSectionMap"] == {
        "nome": "custom_dados_pessoais",
        "telefone": "custom_morada",
    }
