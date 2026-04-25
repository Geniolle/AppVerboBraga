from appverbo.menu_settings import (
    get_menu_process_default_visible_fields,
    get_menu_process_field_options,
    normalize_menu_process_additional_fields,
)


def test_configuracao_process_field_options_defaults() -> None:
    options = get_menu_process_field_options("configuracao")
    assert [item["key"] for item in options] == [
        "geral",
        "configuracao_campos",
        "campos_adicionais",
    ]


def test_configuracao_default_visible_fields() -> None:
    defaults = get_menu_process_default_visible_fields("configuracao")
    assert defaults == ["geral", "configuracao_campos", "campos_adicionais"]


def test_normalize_additional_fields_places_headers_first() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {"label": "Data Início", "field_type": "date"},
            {"label": "Departamento", "field_type": "header"},
            {"label": "Motivo", "field_type": "text"},
        ]
    )

    assert [item["field_type"] for item in normalized] == ["header", "date", "text"]
    assert [item["label"] for item in normalized] == ["Departamento", "Data início", "Motivo"]
