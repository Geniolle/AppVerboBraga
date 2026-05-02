import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from appverbo.menu_settings import (
    get_menu_process_default_visible_fields,
    get_menu_process_field_options,
    get_sidebar_menu_settings,
    normalize_menu_process_additional_fields,
    normalize_menu_process_quantity_fields,
    normalize_sidebar_sections,
    update_sidebar_menu_process_quantity_fields_v1,
)
from appverbo.models import Base, SidebarMenuSetting


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


def test_normalize_menu_process_quantity_fields() -> None:
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "label": "Agregados",
                "quantity_field_key": "custom_quantos_filhos_tens",
                "repeated_field_keys": [
                    "custom_nome_do_agregado",
                    "custom_data_nascimento_do_agregado",
                    "custom_nome_do_agregado",
                ],
                "header_key": "custom_dados_de_agregados",
                "max_items": "10",
                "item_label": "Agregado",
            }
        ]
    )

    assert normalized == [
        {
            "key": "qty_agregados",
            "label": "Agregados",
            "quantity_field_key": "custom_quantos_filhos_tens",
            "repeated_field_keys": [
                "custom_nome_do_agregado",
                "custom_data_nascimento_do_agregado",
            ],
            "header_key": "custom_dados_de_agregados",
            "max_items": 10,
            "item_label": "Agregado",
        }
    ]


def test_update_sidebar_menu_process_quantity_fields_persists_per_menu() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            SidebarMenuSetting(
                menu_key="empresa",
                menu_label="Empresa",
                is_active=True,
                is_deleted=False,
                menu_config=json.dumps(
                    {
                        "created_from": "administrativo_menu",
                        "settings_tabs_enabled": True,
                        "additional_fields": [
                            {"key": "custom_dados_agregados", "label": "Dados agregados", "field_type": "header"},
                            {"key": "custom_quantos_filhos_tens", "label": "Quantos filhos tens?", "field_type": "number"},
                            {"key": "custom_nome_do_agregado", "label": "Nome do agregado", "field_type": "text", "size": 80},
                            {"key": "custom_data_nascimento_do_agregado", "label": "Data de nascimento do agregado", "field_type": "date"},
                        ],
                    },
                    ensure_ascii=False,
                ),
            )
        )
        session.commit()

        ok, error_message = update_sidebar_menu_process_quantity_fields_v1(
            session,
            "empresa",
            [
                {
                    "label": "Agregados",
                    "quantity_field_key": "custom_quantos_filhos_tens",
                    "repeated_field_keys": json.dumps(
                        ["custom_nome_do_agregado", "custom_data_nascimento_do_agregado"]
                    ),
                    "header_key": "custom_dados_agregados",
                    "max_items": "10",
                    "item_label": "Agregado",
                }
            ],
        )

        assert ok is True
        assert error_message == ""

        saved_row = session.scalar(
            select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == "empresa")
        )
        assert saved_row is not None

        saved_config = json.loads(saved_row.menu_config or "{}")
        assert saved_config["process_quantity_fields"] == [
            {
                "key": "qty_agregados",
                "label": "Agregados",
                "quantity_field_key": "custom_quantos_filhos_tens",
                "repeated_field_keys": [
                    "custom_nome_do_agregado",
                    "custom_data_nascimento_do_agregado",
                ],
                "header_key": "custom_dados_agregados",
                "max_items": 10,
                "item_label": "Agregado",
            }
        ]

        sidebar_settings = get_sidebar_menu_settings(session)
        empresa_setting = next(item for item in sidebar_settings if item["key"] == "empresa")
        assert empresa_setting["process_quantity_fields"] == saved_config["process_quantity_fields"]
