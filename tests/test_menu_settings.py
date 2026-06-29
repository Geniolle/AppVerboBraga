import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from appverbo.menu_settings import (
    get_menu_process_default_visible_fields,
    get_menu_process_field_options,
    get_menu_process_header_options,
    get_menu_process_selectable_field_options,
    get_sidebar_menu_settings,
    normalize_menu_process_additional_fields,
    normalize_menu_process_quantity_fields,
    normalize_sidebar_sections,
    update_sidebar_menu_process_quantity_fields_v1,
)
from appverbo.models import Base, SidebarMenuSetting
from appverbo.services.profile import resolve_field_list_options_v1
from appverbo.services.process_tabs import resolve_subprocess_section_fields_v1


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


def test_normalize_additional_fields_allows_same_label_across_groups() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {"label": "Perfil", "field_type": "header"},
            {"label": "Perfil", "field_type": "text"},
        ]
    )

    assert [item["field_type"] for item in normalized] == ["header", "text"]
    assert [item["key"] for item in normalized] == ["custom_header_perfil", "custom_field_perfil"]


def test_normalize_additional_fields_blocks_duplicate_inside_same_group() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {"label": "Perfil", "field_type": "text"},
            {"label": "Perfil", "field_type": "list", "list_key": "perfil"},
        ]
    )

    assert len(normalized) == 1
    assert normalized[0]["field_type"] == "text"
    assert normalized[0]["key"] == "custom_perfil"


def test_normalize_additional_fields_blocks_duplicate_inside_header_group() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {"label": "Perfil", "field_type": "header"},
            {"label": "Perfil", "field_type": "header"},
        ]
    )

    assert len(normalized) == 1
    assert normalized[0]["field_type"] == "header"
    assert normalized[0]["key"] == "custom_perfil"


def test_menu_process_field_options_keep_header_and_field_with_same_label() -> None:
    menu_config = {
        "additional_fields": [
            {"label": "Perfil", "field_type": "header"},
            {"label": "Perfil", "field_type": "text"},
        ]
    }

    options = get_menu_process_field_options("perfil_de_autorizacao", menu_config)
    selectable_options = get_menu_process_selectable_field_options("perfil_de_autorizacao", menu_config)
    header_options = get_menu_process_header_options("perfil_de_autorizacao", menu_config)

    assert [item["key"] for item in options] == ["custom_header_perfil", "custom_field_perfil"]
    assert [item["key"] for item in selectable_options] == ["custom_field_perfil"]
    assert [item["key"] for item in header_options] == ["custom_header_perfil"]


def test_normalize_additional_fields_list_legacy_defaults_to_manual() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {"label": "Perfil", "field_type": "list", "list_key": "perfil_manual"},
        ]
    )

    assert normalized == [
        {
            "key": "custom_perfil",
            "label": "Perfil",
            "field_type": "list",
            "is_required": False,
            "list_source_type": "manual",
            "manual_list_key": "perfil_manual",
            "list_key": "perfil_manual",
        }
    ]


def test_normalize_additional_fields_list_automatic_keeps_source_metadata() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {
                "label": "Nome do perfil",
                "field_type": "list",
                "list_source_type": "automatic",
                "automatic_source_process_key": "perfil_de_autorizacao",
                "automatic_source_section_key": "perfis",
                "automatic_source_field_key": "custom_nome_do_perfil",
                "automatic_only_active": "1",
            },
        ]
    )

    assert normalized == [
        {
            "key": "custom_nome_do_perfil",
            "label": "Nome do perfil",
            "field_type": "list",
            "is_required": False,
            "list_source_type": "automatic",
            "manual_list_key": "",
            "list_key": "",
            "automatic_source_process_key": "perfil_de_autorizacao",
            "automatic_source_section_key": "perfis",
            "automatic_source_field_key": "custom_nome_do_perfil",
            "automatic_only_active": True,
        }
    ]


def test_resolve_field_list_options_manual_uses_current_process_list() -> None:
    resolved = resolve_field_list_options_v1(
        current_menu_key="empresa",
        field_definition={
            "field_type": "list",
            "list_source_type": "manual",
            "manual_list_key": "perfil_manual",
        },
        sidebar_menu_settings=[
            {
                "key": "empresa",
                "process_lists": [
                    {"key": "perfil_manual", "items": ["Pastor", "Líder", "Colaborador"]},
                ],
            }
        ],
        visible_sidebar_menu_keys={"empresa"},
        menu_process_history_map={},
    )

    assert resolved == [
        {"value": "Pastor", "label": "Pastor", "status": "active"},
        {"value": "Líder", "label": "Líder", "status": "active"},
        {"value": "Colaborador", "label": "Colaborador", "status": "active"},
    ]


def test_resolve_field_list_options_automatic_filters_active_records() -> None:
    resolved = resolve_field_list_options_v1(
        current_menu_key="empresa",
        field_definition={
            "field_type": "list",
            "list_source_type": "automatic",
            "automatic_source_process_key": "perfil_de_autorizacao",
            "automatic_source_section_key": "perfis",
            "automatic_source_field_key": "custom_nome_do_perfil",
            "automatic_only_active": "1",
        },
        sidebar_menu_settings=[
            {"key": "empresa", "process_lists": []},
            {
                "key": "perfil_de_autorizacao",
                "process_record_status_field_key": "__estado",
                "process_field_options": [
                    {"key": "custom_nome_do_perfil", "field_type": "text"},
                ],
            },
        ],
        visible_sidebar_menu_keys={"empresa", "perfil_de_autorizacao"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "perfis",
                    "values": {
                        "custom_nome_do_perfil": "Extrato",
                        "__estado": "ativo",
                    },
                },
                {
                    "section_key": "perfis",
                    "values": {
                        "custom_nome_do_perfil": "Financeiro",
                        "__estado": "inativo",
                    },
                },
                {
                    "section_key": "perfis",
                    "values": {
                        "custom_nome_do_perfil": "Extrato",
                        "__estado": "ativo",
                    },
                },
            ]
        },
    )

    assert resolved == [
        {"value": "Extrato", "label": "Extrato", "status": "active"},
    ]


def test_resolve_field_list_options_automatic_honours_visible_source_process() -> None:
    resolved = resolve_field_list_options_v1(
        current_menu_key="empresa",
        field_definition={
            "field_type": "list",
            "list_source_type": "automatic",
            "automatic_source_process_key": "perfil_de_autorizacao",
            "automatic_source_section_key": "perfis",
            "automatic_source_field_key": "custom_nome_do_perfil",
        },
        sidebar_menu_settings=[
            {"key": "empresa", "process_lists": []},
            {
                "key": "perfil_de_autorizacao",
                "process_field_options": [
                    {"key": "custom_nome_do_perfil", "field_type": "text"},
                ],
            },
        ],
        visible_sidebar_menu_keys={"empresa"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "perfis",
                    "values": {"custom_nome_do_perfil": "Extrato"},
                },
            ]
        },
    )

    assert resolved == []


def test_resolve_subprocess_section_fields_enriches_list_metadata_and_input_type() -> None:
    resolved_fields = resolve_subprocess_section_fields_v1(
        "perfil_de_autorizacao",
        "custom_objeto_de_autorizacao",
        [
            {
                "key": "perfil_de_autorizacao",
                "process_additional_fields": [
                    {"key": "custom_objeto_de_autorizacao", "label": "Objeto de autorização", "field_type": "header"},
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "list",
                        "is_required": True,
                        "list_source_type": "manual",
                        "manual_list_key": "lista_processos",
                    },
                ],
                "process_field_options": [
                    {"key": "custom_objeto_de_autorizacao", "label": "Objeto de autorização", "field_type": "header"},
                    {"key": "custom_processo", "label": "Processo", "field_type": "text"},
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_processo",
                        "header_key": "custom_objeto_de_autorizacao",
                    }
                ],
                "process_lists": [
                    {"key": "lista_processos", "items": ["Financeiro", "Tesouraria"]},
                ],
            }
        ],
    )

    assert resolved_fields == [
        {
            "key": "custom_processo",
            "label": "Processo",
            "field_type": "list",
            "input_type": "select",
            "required": True,
            "size": None,
            "list_source_type": "manual",
            "manual_list_key": "lista_processos",
            "list_key": "lista_processos",
            "automatic_source_process_key": "",
            "automatic_source_section_key": "",
            "automatic_source_field_key": "",
            "automatic_only_active": False,
            "options": [
                {"value": "Financeiro", "label": "Financeiro", "status": "active"},
                {"value": "Tesouraria", "label": "Tesouraria", "status": "active"},
            ],
            "header_key": "custom_objeto_de_autorizacao",
            "header_label": "Objeto de autorização",
        }
    ]


def test_resolve_subprocess_section_fields_keeps_empty_lists_as_select() -> None:
    resolved_fields = resolve_subprocess_section_fields_v1(
        "perfil_de_autorizacao",
        "custom_objeto_de_autorizacao",
        [
            {
                "key": "perfil_de_autorizacao",
                "process_additional_fields": [
                    {"key": "custom_objeto_de_autorizacao", "label": "Objeto de autorização", "field_type": "header"},
                    {
                        "key": "custom_subprocesso",
                        "label": "Subprocesso",
                        "field_type": "list",
                        "list_source_type": "automatic",
                        "automatic_source_process_key": "perfil_de_autorizacao",
                        "automatic_source_section_key": "perfis",
                        "automatic_source_field_key": "custom_nome_do_perfil",
                    },
                ],
                "process_field_options": [
                    {"key": "custom_objeto_de_autorizacao", "label": "Objeto de autorização", "field_type": "header"},
                    {"key": "custom_subprocesso", "label": "Subprocesso", "field_type": "text"},
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_subprocesso",
                        "header_key": "custom_objeto_de_autorizacao",
                    }
                ],
            }
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao"},
        menu_process_history_map={},
    )

    assert resolved_fields == [
        {
            "key": "custom_subprocesso",
            "label": "Subprocesso",
            "field_type": "list",
            "input_type": "select",
            "required": False,
            "size": None,
            "list_source_type": "automatic",
            "manual_list_key": "",
            "list_key": "",
            "automatic_source_process_key": "perfil_de_autorizacao",
            "automatic_source_section_key": "perfis",
            "automatic_source_field_key": "custom_nome_do_perfil",
            "automatic_only_active": False,
            "options": [],
            "header_key": "custom_objeto_de_autorizacao",
            "header_label": "Objeto de autorização",
        }
    ]


def test_normalize_sidebar_sections_ensures_defaults() -> None:
    normalized = normalize_sidebar_sections([])
    keys = [item["key"] for item in normalized]
    assert "sistema" in keys
    assert "geral" in keys
    assert "igreja" in keys
    assert keys[0] == "sistema"
    for item in normalized:
        assert item["visibility_scope_mode"] == "all"


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
