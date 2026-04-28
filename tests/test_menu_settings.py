from appverbo.menu_settings import (
    get_menu_process_default_visible_fields,
    get_menu_process_field_options,
    normalize_menu_process_additional_fields,
    normalize_sidebar_sections,
)


def test_administrativo_process_field_options_defaults() -> None:
    options = get_menu_process_field_options("administrativo")
    assert [item["key"] for item in options] == [
        "entidade",
        "utilizador",
        "definicoes",
    ]


def test_administrativo_default_visible_fields() -> None:
    defaults = get_menu_process_default_visible_fields("administrativo")
    assert defaults == ["entidade", "utilizador", "definicoes"]


def test_legacy_configuracao_alias_maps_to_administrativo_fields() -> None:
    defaults = get_menu_process_default_visible_fields("configuracao")
    assert defaults == ["entidade", "utilizador", "definicoes"]


def test_normalize_additional_fields_places_headers_first() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {"label": "Data Inicio", "field_type": "date"},
            {"label": "Departamento", "field_type": "header"},
            {"label": "Motivo", "field_type": "text"},
        ]
    )

    assert [item["field_type"] for item in normalized] == ["header", "date", "text"]
    assert normalized[0]["label"] == "Departamento"
    assert normalized[1]["label"].lower().startswith("data")
    assert normalized[2]["label"] == "Motivo"


def test_normalize_sidebar_sections_ensures_defaults() -> None:
    normalized = normalize_sidebar_sections([])
    assert [item["key"] for item in normalized][:2] == ["geral", "igreja"]
    assert normalized[0]["visibility_scope_mode"] == "all"
    assert normalized[1]["visibility_scope_mode"] == "all"


def test_normalize_sidebar_sections_from_string() -> None:
    normalized = normalize_sidebar_sections("Administrativo, Ministerios")
    keys = [item["key"] for item in normalized]
    assert "administrativo" in keys
    assert "ministerios" in keys
    assert "geral" in keys
    assert "igreja" in keys


def test_normalize_sidebar_sections_preserves_scope_mode() -> None:
    normalized = normalize_sidebar_sections(
        [
            {
                "key": "treino",
                "label": "Dados de treino",
                "visibility_scope_mode": "owner",
            }
        ]
    )
    treino_item = next(item for item in normalized if item["key"] == "treino")
    assert treino_item["visibility_scope_mode"] == "owner"
    assert treino_item["visibility_scopes"] == ["owner"]
