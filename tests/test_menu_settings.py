import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from appgenesis.menu_settings import (
    ADDITIONAL_FIELD_TYPES,
    SIDEBAR_MENU_DEFAULTS,
    delete_sidebar_section,
    get_menu_process_default_visible_fields,
    get_menu_process_field_options,
    get_menu_process_visible_field_header_map,
    get_menu_process_visible_field_rows,
    get_menu_process_header_options,
    get_menu_process_selectable_field_options,
    get_sidebar_menu_settings,
    move_sidebar_menu_setting,
    normalize_menu_process_additional_fields,
    normalize_menu_process_quantity_fields,
    resolve_menu_sidebar_section_key,
    normalize_sidebar_sections,
    update_sidebar_menu_process_quantity_fields_v1,
)
from appgenesis.admin_subprocesses.registry import SESSOES_CONFIG
from appgenesis.models import Base, Entity, SidebarMenuSetting
from appgenesis.services.profile import (
    build_profile_menu_tabs_dependency_map_v1,
    resolve_field_list_options_v1,
)
from appgenesis.services.process_tabs import resolve_subprocess_section_fields_v1


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


def test_additional_field_types_include_time_with_correct_label() -> None:
    types_by_key = {item["key"]: item["label"] for item in ADDITIONAL_FIELD_TYPES}

    assert types_by_key["time"] == "Horário"
    # Tipos existentes continuam disponiveis e inalterados.
    assert types_by_key["text"] == "Texto"
    assert types_by_key["number"] == "Número"
    assert types_by_key["email"] == "Email"
    assert types_by_key["phone"] == "Telefone"
    assert types_by_key["date"] == "Data"
    assert types_by_key["flag"] == "Flag"
    assert types_by_key["header"] == "Cabeçalho (aba)"
    assert types_by_key["list"] == "Lista"


def test_normalize_additional_fields_accepts_time_type_and_ignores_size() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {
                "label": "Hora de início",
                "field_type": "time",
                "size": "255",
                "is_required": True,
            },
        ]
    )

    assert len(normalized) == 1
    assert normalized[0]["field_type"] == "time"
    assert normalized[0]["is_required"] is True
    # "time" nao e um tipo textual: o tamanho maximo nao e persistido/exigido.
    assert "size" not in normalized[0]


def test_normalize_additional_fields_keeps_all_existing_types_working() -> None:
    raw_fields = [
        {"label": "Campo texto", "field_type": "text"},
        {"label": "Campo numero", "field_type": "number"},
        {"label": "Campo email", "field_type": "email"},
        {"label": "Campo telefone", "field_type": "phone"},
        {"label": "Campo data", "field_type": "date"},
        {"label": "Campo flag", "field_type": "flag"},
        {
            "label": "Campo lista",
            "field_type": "list",
            "manual_list_key": "lista_teste",
        },
        {"label": "Campo cabecalho", "field_type": "header"},
    ]

    normalized = normalize_menu_process_additional_fields(raw_fields)

    assert [item["field_type"] for item in normalized] == [
        "header",
        "text",
        "number",
        "email",
        "phone",
        "date",
        "flag",
        "list",
    ]


def test_normalize_additional_fields_allows_same_label_across_groups() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {"label": "Perfil", "field_type": "header"},
            {"label": "Perfil", "field_type": "text"},
        ]
    )

    assert [item["field_type"] for item in normalized] == ["header", "text"]
    assert [item["key"] for item in normalized] == [
        "custom_header_perfil",
        "custom_field_perfil",
    ]


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
    selectable_options = get_menu_process_selectable_field_options(
        "perfil_de_autorizacao", menu_config
    )
    header_options = get_menu_process_header_options(
        "perfil_de_autorizacao", menu_config
    )

    assert [item["key"] for item in options] == [
        "custom_header_perfil",
        "custom_field_perfil",
    ]
    assert [item["key"] for item in selectable_options] == ["custom_field_perfil"]
    assert [item["key"] for item in header_options] == ["custom_header_perfil"]


def test_get_menu_process_visible_field_header_map_prefers_process_rows_over_legacy_map() -> (
    None
):
    menu_config = {
        "additional_fields": [
            {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
            {
                "key": "custom_objeto_de_autorizacao",
                "label": "Objeto de autorização",
                "field_type": "header",
            },
            {
                "key": "custom_nome_do_perfil",
                "label": "Nome do perfil",
                "field_type": "text",
            },
            {"key": "custom_processo", "label": "Processo", "field_type": "text"},
            {"key": "custom_subprocesso", "label": "Subprocesso", "field_type": "text"},
            {"key": "custom_perfil_2", "label": "Perfil", "field_type": "text"},
        ],
        "visible_fields": [
            "custom_perfil",
            "custom_nome_do_perfil",
            "custom_processo",
            "custom_subprocesso",
            "custom_perfil_2",
        ],
        "visible_field_headers": {
            "custom_nome_do_perfil": "custom_perfil",
            "custom_processo": "custom_perfil",
            "custom_subprocesso": "custom_perfil",
            "custom_perfil_2": "custom_perfil",
        },
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
            {
                "field_key": "custom_perfil_2",
                "header_key": "custom_perfil",
            },
        ],
        "process_visible_field_header_map": {
            "custom_nome_do_perfil": "custom_objeto_de_autorizacao",
            "custom_processo": "custom_objeto_de_autorizacao",
            "custom_subprocesso": "custom_objeto_de_autorizacao",
            "custom_perfil_2": "custom_perfil",
        },
    }

    assert get_menu_process_visible_field_header_map(
        "perfil_de_autorizacao", menu_config
    ) == {
        "custom_nome_do_perfil": "custom_objeto_de_autorizacao",
        "custom_processo": "custom_objeto_de_autorizacao",
        "custom_subprocesso": "custom_objeto_de_autorizacao",
        "custom_perfil_2": "custom_perfil",
    }


def test_get_menu_process_visible_field_rows_prefers_process_rows_over_legacy_header_map() -> (
    None
):
    menu_config = {
        "additional_fields": [
            {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
            {
                "key": "custom_objeto_de_autorizacao",
                "label": "Objeto de autorização",
                "field_type": "header",
            },
            {
                "key": "custom_nome_do_perfil",
                "label": "Nome do perfil",
                "field_type": "text",
            },
            {"key": "custom_processo", "label": "Processo", "field_type": "text"},
            {"key": "custom_subprocesso", "label": "Subprocesso", "field_type": "text"},
            {"key": "custom_perfil_2", "label": "Perfil", "field_type": "text"},
        ],
        "visible_fields": [
            "custom_perfil",
            "custom_nome_do_perfil",
            "custom_processo",
            "custom_subprocesso",
            "custom_perfil_2",
        ],
        "visible_field_headers": {
            "custom_nome_do_perfil": "custom_perfil",
            "custom_processo": "custom_perfil",
            "custom_subprocesso": "custom_perfil",
            "custom_perfil_2": "custom_perfil",
        },
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
            {
                "field_key": "custom_perfil_2",
                "header_key": "custom_perfil",
            },
        ],
        "process_visible_field_header_map": {
            "custom_nome_do_perfil": "custom_objeto_de_autorizacao",
            "custom_processo": "custom_objeto_de_autorizacao",
            "custom_subprocesso": "custom_objeto_de_autorizacao",
            "custom_perfil_2": "custom_perfil",
        },
    }

    assert get_menu_process_visible_field_rows(
        "perfil_de_autorizacao", menu_config
    ) == [
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
        {
            "field_key": "custom_perfil_2",
            "header_key": "custom_perfil",
        },
    ]


def test_get_sidebar_menu_settings_repairs_profile_authorization_object_section() -> (
    None
):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    profile_menu_config = {
        "additional_fields": [
            {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
            {
                "key": "custom_objeto_de_autorizacao",
                "label": "Objeto de autorização",
                "field_type": "header",
            },
            {
                "key": "custom_nome_do_perfil",
                "label": "Nome do perfil",
                "field_type": "list",
                "list_source_type": "manual",
                "manual_list_key": "list_perfil",
                "list_key": "list_perfil",
            },
            {
                "key": "custom_field_perfil",
                "label": "Perfil",
                "field_type": "text",
            },
            {
                "key": "custom_objeto_de_autorizacao_1",
                "label": "Objeto de autorização 1",
                "field_type": "text",
            },
        ],
        "visible_fields": [
            "custom_perfil",
            "custom_nome_do_perfil",
            "custom_objeto_de_autorizacao",
            "custom_field_perfil",
            "custom_objeto_de_autorizacao_1",
        ],
        "visible_field_headers": {
            "custom_nome_do_perfil": "custom_perfil",
            "custom_field_perfil": "custom_objeto_de_autorizacao",
        },
        "process_visible_field_rows": [
            {
                "field_key": "custom_nome_do_perfil",
                "header_key": "custom_perfil",
            },
            {
                "field_key": "custom_field_perfil",
                "header_key": "custom_objeto_de_autorizacao",
            },
            {
                "field_key": "custom_objeto_de_autorizacao_1",
                "header_key": "",
            },
        ],
        "process_visible_field_header_map": {
            "custom_nome_do_perfil": "custom_perfil",
            "custom_field_perfil": "custom_objeto_de_autorizacao",
        },
    }

    with Session(engine) as session:
        session.add(
            Entity(
                entity_number=1,
                name="Igreja Teste",
                is_active=True,
            )
        )
        session.add(
            SidebarMenuSetting(
                entity_id=1,
                menu_key="perfil_de_autorizacao",
                menu_label="Perfil de autorização",
                is_active=True,
                is_deleted=False,
                menu_config=json.dumps(profile_menu_config, ensure_ascii=False),
            )
        )
        session.commit()

        settings = get_sidebar_menu_settings(session)
        profile_setting = next(
            item for item in settings if item["key"] == "perfil_de_autorizacao"
        )

        assert [row["field_key"] for row in profile_setting["process_visible_field_rows"]] == [
            "custom_field_perfil",
            "custom_nome_do_perfil",
            "custom_processo",
            "custom_subprocesso",
            "custom_objeto_de_autorizacao_1",
        ]
        assert profile_setting["process_visible_field_header_map"] == {
            "custom_field_perfil": "custom_perfil",
            "custom_nome_do_perfil": "custom_objeto_de_autorizacao",
            "custom_processo": "custom_objeto_de_autorizacao",
            "custom_subprocesso": "custom_objeto_de_autorizacao",
        }

        resolved_fields = resolve_subprocess_section_fields_v1(
            "perfil_de_autorizacao",
            "custom_objeto_de_autorizacao",
            settings,
            active_entity_id=1,
        )

        assert [item["key"] for item in resolved_fields] == [
            "custom_nome_do_perfil",
            "custom_processo",
            "custom_subprocesso",
        ]
        assert [item["label"] for item in resolved_fields] == [
            "Nome do perfil",
            "Processo",
            "Autorização",
        ]

        stored_row = session.scalar(
            select(SidebarMenuSetting).where(
                SidebarMenuSetting.menu_key == "perfil_de_autorizacao"
            )
        )
        assert stored_row is not None
        stored_config = json.loads(stored_row.menu_config or "{}")
        assert [row["field_key"] for row in stored_config["process_visible_field_rows"]] == [
            "custom_field_perfil",
            "custom_nome_do_perfil",
            "custom_processo",
            "custom_subprocesso",
            "custom_objeto_de_autorizacao_1",
        ]


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


def test_normalize_additional_fields_list_field_list_keeps_source_metadata() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {
                "label": "Processo",
                "field_type": "list",
                "list_source_type": "field_list",
                "automatic_source_process_key": "perfil_de_autorizacao",
                "automatic_source_section_key": "custom_perfil",
                "automatic_source_field_key": "custom_perfil",
            },
        ]
    )
    r = normalized[0]
    assert r["list_source_type"] == "field_list"
    assert r["automatic_source_process_key"] == "perfil_de_autorizacao"
    assert r["automatic_source_section_key"] == "custom_perfil"
    assert r["automatic_source_field_key"] == "custom_perfil"
    assert "automatic_only_active" not in r


def test_normalize_additional_fields_list_active_menus_keeps_source_type() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {
                "label": "Perfil",
                "field_type": "list",
                "list_source_type": "active_menus",
            },
        ]
    )

    assert normalized == [
        {
            "key": "custom_perfil",
            "label": "Perfil",
            "field_type": "list",
            "is_required": False,
            "list_source_type": "active_menus",
            "manual_list_key": "",
            "list_key": "",
        }
    ]


def test_normalize_additional_fields_list_profile_menu_tabs_keeps_source_type() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {
                "label": "Processo",
                "field_type": "list",
                "list_source_type": "profile_menu_tabs",
                "automatic_source_field_key": "custom_nome_do_perfil",
            },
        ]
    )

    assert normalized == [
        {
            "key": "custom_processo",
            "label": "Processo",
            "field_type": "list",
            "is_required": False,
            "list_source_type": "profile_menu_tabs",
            "manual_list_key": "",
            "list_key": "",
            "automatic_source_process_key": "",
            "automatic_source_section_key": "",
            "automatic_source_field_key": "custom_nome_do_perfil",
        }
    ]


def test_resolve_field_list_options_field_list_inherits_source_field_options() -> None:
    sidebar_menu_settings = [
        {
            "key": "perfil_de_autorizacao",
            "label": "Perfil de autorização",
            "process_field_options": [
                {
                    "key": "custom_perfil",
                    "label": "Perfil",
                    "field_type": "list",
                    "list_source_type": "manual",
                    "manual_list_key": "list_perfil",
                },
            ],
            "process_lists": [
                {
                    "key": "list_perfil",
                    "label": "Perfil",
                    "items": ["Perfil A", "Perfil B"],
                },
            ],
        },
        {
            "key": "objeto_de_autorizacao",
            "label": "Objeto",
            "process_field_options": [
                {
                    "key": "custom_processo",
                    "label": "Processo",
                    "field_type": "list",
                    "list_source_type": "field_list",
                    "automatic_source_process_key": "perfil_de_autorizacao",
                    "automatic_source_section_key": "custom_perfil",
                    "automatic_source_field_key": "custom_perfil",
                },
            ],
        },
    ]
    resolved = resolve_field_list_options_v1(
        current_menu_key="objeto_de_autorizacao",
        field_definition={
            "key": "custom_processo",
            "field_type": "list",
            "list_source_type": "field_list",
            "automatic_source_process_key": "perfil_de_autorizacao",
            "automatic_source_section_key": "custom_perfil",
            "automatic_source_field_key": "custom_perfil",
        },
        sidebar_menu_settings=sidebar_menu_settings,
    )
    assert [opt["value"] for opt in resolved] == ["Perfil A", "Perfil B"]


def test_resolve_field_list_options_manual_delegates_to_automatic_list_with_all_sessions_source_returns_active_menus() -> (
    None
):
    sidebar_menu_settings = [
        {"key": "home", "label": "Home", "is_active": True, "is_deleted": False},
        {
            "key": "perfil_de_autorizacao",
            "label": "Perfil de autorização",
            "is_active": True,
            "is_deleted": False,
            "process_field_options": [
                {
                    "key": "custom_processo",
                    "label": "Processo",
                    "field_type": "list",
                    "list_source_type": "manual",
                    "manual_list_key": "list_processo",
                },
            ],
            "process_lists": [
                {
                    "key": "list_processo",
                    "label": "L_processo",
                    "field_type": "automatic",
                    "source_session_key": "all_sessions",
                    "source_menu_key": "",
                    "source_subprocess_key": "",
                    "items": [],
                },
            ],
        },
    ]

    resolved = resolve_field_list_options_v1(
        current_menu_key="perfil_de_autorizacao",
        field_definition={
            "key": "custom_processo",
            "field_type": "list",
            "list_source_type": "manual",
            "manual_list_key": "list_processo",
        },
        sidebar_menu_settings=sidebar_menu_settings,
        visible_sidebar_menu_keys={"home", "perfil_de_autorizacao"},
    )

    assert resolved == [
        {"value": "home", "label": "Home", "status": "active"},
        {
            "value": "perfil_de_autorizacao",
            "label": "Perfil de autorização",
            "status": "active",
        },
    ]


def test_resolve_field_list_options_field_list_cycle_returns_empty() -> None:
    sidebar_menu_settings = [
        {
            "key": "processo_x",
            "process_field_options": [
                {
                    "key": "campo_a",
                    "field_type": "list",
                    "list_source_type": "field_list",
                    "automatic_source_process_key": "processo_x",
                    "automatic_source_section_key": "",
                    "automatic_source_field_key": "campo_b",
                },
                {
                    "key": "campo_b",
                    "field_type": "list",
                    "list_source_type": "field_list",
                    "automatic_source_process_key": "processo_x",
                    "automatic_source_section_key": "",
                    "automatic_source_field_key": "campo_a",
                },
            ],
            "process_lists": [],
        },
    ]
    resolved = resolve_field_list_options_v1(
        current_menu_key="processo_x",
        field_definition={
            "key": "campo_a",
            "field_type": "list",
            "list_source_type": "field_list",
            "automatic_source_process_key": "processo_x",
            "automatic_source_section_key": "",
            "automatic_source_field_key": "campo_b",
        },
        sidebar_menu_settings=sidebar_menu_settings,
    )
    assert resolved == []


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
                    {
                        "key": "perfil_manual",
                        "items": ["Pastor", "Líder", "Colaborador"],
                    },
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


def test_resolve_field_list_options_active_menus_filters_visibility_and_state() -> None:
    resolved = resolve_field_list_options_v1(
        current_menu_key="perfil_de_autorizacao",
        field_definition={
            "field_type": "list",
            "list_source_type": "active_menus",
        },
        sidebar_menu_settings=[
            {"key": "home", "label": "Home", "is_active": True, "is_deleted": False},
            {
                "key": "sessoes",
                "label": "Estruturas",
                "is_active": True,
                "is_deleted": False,
            },
            {
                "key": "departamentos",
                "label": "Departamentos",
                "is_active": False,
                "is_deleted": False,
            },
            {
                "key": "musicas",
                "label": "Músicas",
                "is_active": True,
                "is_deleted": True,
            },
            {
                "key": "perfil_de_autorizacao",
                "label": "Perfil de autorização",
                "is_active": True,
                "is_deleted": False,
            },
        ],
        visible_sidebar_menu_keys={"home", "sessoes", "perfil_de_autorizacao"},
        menu_process_history_map={},
    )

    assert resolved == [
        {"value": "home", "label": "Home", "status": "active"},
        {"value": "sessoes", "label": "Estruturas", "status": "active"},
        {
            "value": "perfil_de_autorizacao",
            "label": "Perfil de autorização",
            "status": "active",
        },
    ]


def test_resolve_field_list_options_profile_menu_tabs_returns_tabs_from_selected_profile_menu() -> (
    None
):
    resolved = resolve_field_list_options_v1(
        current_menu_key="perfil_de_autorizacao",
        field_definition={
            "key": "custom_processo",
            "field_type": "list",
            "list_source_type": "profile_menu_tabs",
            "automatic_source_field_key": "custom_nome_do_perfil",
        },
        sidebar_menu_settings=[
            {
                "key": "perfil_de_autorizacao",
                "label": "Perfil de autorização",
                "is_active": True,
                "is_deleted": False,
                "process_field_options": [
                    {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
                    {
                        "key": "custom_nome_do_perfil",
                        "label": "Nome do perfil",
                        "field_type": "text",
                    },
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "list",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_nome_do_perfil",
                        "header_key": "custom_perfil",
                    },
                    {
                        "field_key": "custom_processo",
                        "header_key": "custom_objeto_de_autorizacao",
                    },
                ],
            },
            {
                "key": "extrato",
                "label": "Extrato",
                "is_active": True,
                "is_deleted": False,
                "is_list_process": True,
                "process_field_options": [
                    {
                        "key": "custom_extrato_header",
                        "label": "Extratos bancários",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_descricao",
                        "label": "Descrição",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_descricao",
                        "header_key": "custom_extrato_header",
                    },
                ],
            },
            {
                "key": "tesouraria",
                "label": "Tesouraria",
                "is_active": True,
                "is_deleted": False,
                "is_list_process": True,
                "process_field_options": [
                    {
                        "key": "custom_tes_header",
                        "label": "Movimentos",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_referencia",
                        "label": "Referência",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_referencia",
                        "header_key": "custom_tes_header",
                    },
                ],
            },
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao", "extrato", "tesouraria"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "__menu_key": "extrato",
                        "custom_perfil": "Extrato",
                        "custom_nome_do_perfil": "Extrato",
                        "__estado": "ativo",
                    },
                },
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "__menu_key": "tesouraria",
                        "custom_perfil": "Tesouraria",
                        "custom_nome_do_perfil": "Tesouraria",
                        "__estado": "ativo",
                    },
                },
            ]
        },
        current_field_values={"custom_nome_do_perfil": "Extrato"},
    )

    assert resolved == [
        {
            "value": "custom_extrato_header",
            "label": "Extratos bancários",
            "status": "active",
        },
    ]


def test_resolve_field_list_options_profile_menu_tabs_objeto_autorizacao_prioritizes_custom_processo() -> (
    None
):
    resolved = resolve_field_list_options_v1(
        current_menu_key="perfil_de_autorizacao",
        field_definition={
            "key": "custom_subprocesso",
            "field_type": "list",
            "header_key": "custom_objeto_de_autorizacao",
            "list_source_type": "profile_menu_tabs",
            "automatic_source_field_key": "custom_nome_do_perfil",
        },
        sidebar_menu_settings=[
            {
                "key": "perfil_de_autorizacao",
                "label": "Perfil de autorização",
                "is_active": True,
                "is_deleted": False,
            },
            {
                "key": "extrato",
                "label": "Extrato",
                "is_active": True,
                "is_deleted": False,
                "is_list_process": True,
                "process_field_options": [
                    {
                        "key": "custom_extrato_header",
                        "label": "Extratos bancários",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_descricao",
                        "label": "Descrição",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_descricao",
                        "header_key": "custom_extrato_header",
                    },
                ],
            },
            {
                "key": "tesouraria",
                "label": "Tesouraria",
                "is_active": True,
                "is_deleted": False,
                "is_list_process": True,
                "process_field_options": [
                    {
                        "key": "custom_tes_header",
                        "label": "Movimentos",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_referencia",
                        "label": "Referência",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_referencia",
                        "header_key": "custom_tes_header",
                    },
                ],
            },
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao", "extrato", "tesouraria"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "__menu_key": "extrato",
                        "custom_perfil": "Extrato",
                        "custom_nome_do_perfil": "Extrato",
                        "__estado": "ativo",
                    },
                },
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "__menu_key": "tesouraria",
                        "custom_perfil": "Tesouraria",
                        "custom_nome_do_perfil": "Tesouraria",
                        "__estado": "ativo",
                    },
                },
            ]
        },
        current_field_values={
            "custom_processo": "extrato",
            "custom_nome_do_perfil": "Tesouraria",
        },
    )

    assert resolved == [
        {
            "value": "custom_extrato_header",
            "label": "Extratos bancários",
            "status": "active",
        },
    ]


def test_build_profile_menu_tabs_dependency_map_supports_menu_key_and_label_aliases() -> (
    None
):
    dependency_map = build_profile_menu_tabs_dependency_map_v1(
        sidebar_menu_settings=[
            {
                "key": "perfil_de_autorizacao",
                "label": "Perfil de autorização",
                "is_active": True,
                "is_deleted": False,
            },
            {
                "key": "extrato",
                "label": "Extratos bancários",
                "is_active": True,
                "is_deleted": False,
                "is_list_process": True,
                "process_field_options": [
                    {
                        "key": "custom_extrato_header",
                        "label": "Extratos bancários",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_descricao",
                        "label": "Descrição",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_descricao",
                        "header_key": "custom_extrato_header",
                    },
                ],
            },
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao", "extrato"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "__menu_key": "extrato",
                        "custom_perfil": "Extrato",
                        "custom_nome_do_perfil": "Extrato",
                        "__estado": "ativo",
                    },
                }
            ]
        },
    )

    expected_options = [
        {
            "value": "custom_extrato_header",
            "label": "Extratos bancários",
            "status": "active",
        },
    ]

    assert dependency_map["extrato"] == expected_options
    assert dependency_map["Extrato"] == expected_options
    assert dependency_map["Extratos bancários"] == expected_options


def test_resolve_field_list_options_profile_menu_tabs_accepts_legacy_profile_without_menu_key() -> (
    None
):
    resolved = resolve_field_list_options_v1(
        current_menu_key="perfil_de_autorizacao",
        field_definition={
            "key": "custom_processo",
            "field_type": "list",
            "list_source_type": "profile_menu_tabs",
            "automatic_source_field_key": "custom_nome_do_perfil",
        },
        sidebar_menu_settings=[
            {
                "key": "perfil_de_autorizacao",
                "label": "Perfil de autorização",
                "is_active": True,
                "is_deleted": False,
            },
            {
                "key": "extrato",
                "label": "Extrato",
                "is_active": True,
                "is_deleted": False,
                "is_list_process": True,
                "process_field_options": [
                    {
                        "key": "custom_extrato_header",
                        "label": "Extratos bancários",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_descricao",
                        "label": "Descrição",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_descricao",
                        "header_key": "custom_extrato_header",
                    },
                ],
            },
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao", "extrato"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "custom_perfil": "Extrato",
                        "custom_nome_do_perfil": "Extrato",
                        "__estado": "ativo",
                    },
                }
            ]
        },
        current_field_values={"custom_nome_do_perfil": "Extrato"},
    )

    assert resolved == [
        {
            "value": "custom_extrato_header",
            "label": "Extratos bancários",
            "status": "active",
        },
    ]


def test_resolve_field_list_options_profile_menu_tabs_returns_empty_when_menu_has_no_tabs() -> (
    None
):
    resolved = resolve_field_list_options_v1(
        current_menu_key="perfil_de_autorizacao",
        field_definition={
            "key": "custom_processo",
            "field_type": "list",
            "list_source_type": "profile_menu_tabs",
            "automatic_source_field_key": "custom_nome_do_perfil",
        },
        sidebar_menu_settings=[
            {
                "key": "perfil_de_autorizacao",
                "label": "Perfil de autorização",
                "is_active": True,
                "is_deleted": False,
            },
            {
                "key": "menu_sem_abas",
                "label": "Sem abas",
                "is_active": True,
                "is_deleted": False,
            },
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao", "menu_sem_abas"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "__menu_key": "menu_sem_abas",
                        "custom_perfil": "Sem abas",
                        "custom_nome_do_perfil": "Sem abas",
                    },
                }
            ]
        },
        current_field_values={"custom_nome_do_perfil": "Sem abas"},
    )

    assert resolved == []


def test_resolve_field_list_options_legacy_auth_profile_processo_config_uses_profile_menu_tabs() -> (
    None
):
    resolved = resolve_field_list_options_v1(
        current_menu_key="perfil_de_autorizacao",
        field_definition={
            "key": "custom_processo",
            "field_type": "list",
            "list_source_type": "automatic",
            "automatic_source_process_key": "perfil_de_autorizacao",
            "automatic_source_section_key": "custom_perfil",
            "automatic_source_field_key": "custom_perfil",
        },
        sidebar_menu_settings=[
            {
                "key": "perfil_de_autorizacao",
                "label": "Perfil de autorização",
                "is_active": True,
                "is_deleted": False,
            },
            {
                "key": "extrato",
                "label": "Extrato",
                "is_active": True,
                "is_deleted": False,
                "is_list_process": True,
                "process_field_options": [
                    {
                        "key": "custom_extrato_header",
                        "label": "Extratos bancários",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_descricao",
                        "label": "Descrição",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_descricao",
                        "header_key": "custom_extrato_header",
                    },
                ],
            },
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao", "extrato"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "__menu_key": "extrato",
                        "custom_perfil": "Extrato",
                        "custom_nome_do_perfil": "Extrato",
                    },
                }
            ]
        },
        current_field_values={"custom_nome_do_perfil": "Extrato"},
    )

    assert resolved == [
        {
            "value": "custom_extrato_header",
            "label": "Extratos bancários",
            "status": "active",
        },
    ]


def test_resolve_field_list_options_profile_menu_tabs_works_outside_perfil_de_autorizacao_menu() -> (
    None
):
    """A fonte 'profile_menu_tabs' (label visivel: Abas do processo selecionado) deve
    funcionar para qualquer processo/menu que hospede os campos, nao apenas perfil_de_autorizacao,
    e sem depender de historico do menu perfil_de_autorizacao."""
    resolved = resolve_field_list_options_v1(
        current_menu_key="empresa",
        field_definition={
            "key": "custom_subprocesso",
            "field_type": "list",
            "list_source_type": "profile_menu_tabs",
            "automatic_source_field_key": "custom_processo",
        },
        sidebar_menu_settings=[
            {
                "key": "empresa",
                "label": "Empresa",
                "is_active": True,
                "is_deleted": False,
            },
            {
                "key": "extrato",
                "label": "Extrato",
                "is_active": True,
                "is_deleted": False,
                "process_field_options": [
                    {"key": "custom_saldo", "label": "Saldo", "field_type": "header"},
                    {
                        "key": "custom_movimentos",
                        "label": "Movimentos",
                        "field_type": "header",
                    },
                ],
                "process_visible_field_rows": [
                    {"field_key": "custom_valor", "header_key": "custom_saldo"},
                    {"field_key": "custom_data", "header_key": "custom_movimentos"},
                ],
            },
        ],
        visible_sidebar_menu_keys={"empresa", "extrato"},
        menu_process_history_map=None,
        current_field_values={"custom_processo": "extrato"},
    )

    assert resolved == [
        {"value": "custom_saldo", "label": "Saldo", "status": "active"},
        {"value": "custom_movimentos", "label": "Movimentos", "status": "active"},
    ]


def test_resolve_field_list_options_profile_menu_tabs_empresa_target_without_tabs_is_empty() -> (
    None
):
    """Se o processo escolhido em 'Processo' nao tiver abas/subprocessos resolviveis,
    o campo dependente deve ficar vazio, sem erro."""
    resolved = resolve_field_list_options_v1(
        current_menu_key="empresa",
        field_definition={
            "key": "custom_subprocesso",
            "field_type": "list",
            "list_source_type": "profile_menu_tabs",
            "automatic_source_field_key": "custom_processo",
        },
        sidebar_menu_settings=[
            {
                "key": "empresa",
                "label": "Empresa",
                "is_active": True,
                "is_deleted": False,
            },
        ],
        visible_sidebar_menu_keys={"empresa"},
        current_field_values={"custom_processo": "empresa"},
    )

    assert resolved == []


def test_resolve_subprocess_section_fields_profile_menu_tabs_generic_process_infers_processo_sibling_by_label() -> (
    None
):
    """Sem automatic_source_field_key configurado explicitamente, o resolver deve encontrar
    genericamente o campo irmao rotulado 'Processo' em qualquer processo/menu (nao apenas
    perfil_de_autorizacao) e usar o processo escolhido para montar as opcoes iniciais."""
    resolved_fields = resolve_subprocess_section_fields_v1(
        "empresa",
        "custom_dados_gerais",
        [
            {
                "key": "empresa",
                "process_additional_fields": [
                    {
                        "key": "custom_dados_gerais",
                        "label": "Dados gerais",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "list",
                        "list_source_type": "active_menus",
                    },
                    {
                        "key": "custom_subprocesso",
                        "label": "Subprocesso",
                        "field_type": "list",
                        "list_source_type": "profile_menu_tabs",
                    },
                ],
                "process_field_options": [
                    {
                        "key": "custom_dados_gerais",
                        "label": "Dados gerais",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "text",
                    },
                    {
                        "key": "custom_subprocesso",
                        "label": "Subprocesso",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_processo",
                        "header_key": "custom_dados_gerais",
                    },
                    {
                        "field_key": "custom_subprocesso",
                        "header_key": "custom_dados_gerais",
                    },
                ],
            },
            {
                "key": "extrato",
                "label": "Extrato",
                "is_active": True,
                "is_deleted": False,
                "process_field_options": [
                    {"key": "custom_saldo", "label": "Saldo", "field_type": "header"},
                    {
                        "key": "custom_movimentos",
                        "label": "Movimentos",
                        "field_type": "header",
                    },
                ],
                "process_visible_field_rows": [
                    {"field_key": "custom_valor", "header_key": "custom_saldo"},
                    {"field_key": "custom_data", "header_key": "custom_movimentos"},
                ],
            },
        ],
        visible_sidebar_menu_keys={"empresa", "extrato"},
        current_field_values={"custom_processo": "extrato"},
    )

    dependent_field = next(
        item for item in resolved_fields if item["key"] == "custom_subprocesso"
    )

    assert dependent_field["dependent_field_key"] == "custom_processo"
    assert dependent_field["automatic_source_field_key"] == "custom_processo"
    assert dependent_field["options"] == [
        {"value": "custom_saldo", "label": "Saldo", "status": "active"},
        {"value": "custom_movimentos", "label": "Movimentos", "status": "active"},
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


def test_resolve_field_list_options_automatic_accepts_legacy_auth_profile_aliases() -> (
    None
):
    resolved = resolve_field_list_options_v1(
        current_menu_key="objeto_de_autorizacao",
        field_definition={
            "field_type": "list",
            "list_source_type": "automatic",
            "automatic_source_process_key": "perfil_de_autorizacao",
            "automatic_source_section_key": "custom_perfil",
            "automatic_source_field_key": "custom_perfil_2",
            "automatic_only_active": "1",
        },
        sidebar_menu_settings=[
            {"key": "objeto_de_autorizacao", "process_lists": []},
            {
                "key": "perfil_de_autorizacao",
                "process_record_status_field_key": "__estado",
                "process_field_options": [
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
                    {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
                    {
                        "key": "custom_nome_do_perfil",
                        "label": "Nome do perfil",
                        "field_type": "text",
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "list",
                    },
                    {
                        "key": "custom_subprocesso",
                        "label": "Subprocesso",
                        "field_type": "text",
                    },
                    {"key": "custom_perfil_2", "label": "Perfil", "field_type": "text"},
                ],
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
                    {"field_key": "custom_perfil_2", "header_key": "custom_perfil"},
                ],
            },
        ],
        visible_sidebar_menu_keys={"objeto_de_autorizacao", "perfil_de_autorizacao"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "custom_perfil": "Extrato",
                        "custom_nome_do_perfil": "Extrato",
                        "__estado": "ativo",
                    },
                },
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "custom_perfil": "Input bancário",
                        "custom_nome_do_perfil": "Input bancário",
                        "__estado": "ativo",
                    },
                },
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "custom_perfil": "Arquivo",
                        "custom_nome_do_perfil": "Arquivo",
                        "__estado": "inativo",
                    },
                },
            ]
        },
    )

    assert resolved == [
        {"value": "Extrato", "label": "Extrato", "status": "active"},
        {"value": "Input bancário", "label": "Input bancário", "status": "active"},
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


def test_resolve_subprocess_section_fields_enriches_list_metadata_and_input_type() -> (
    None
):
    resolved_fields = resolve_subprocess_section_fields_v1(
        "perfil_de_autorizacao",
        "custom_objeto_de_autorizacao",
        [
            {
                "key": "perfil_de_autorizacao",
                "process_additional_fields": [
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
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
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "text",
                    },
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
            "manual_list_items": [],
            "manual_list_items_csv": "",
            "options": [
                {"value": "Financeiro", "label": "Financeiro", "status": "active"},
                {"value": "Tesouraria", "label": "Tesouraria", "status": "active"},
            ],
            "header_key": "custom_objeto_de_autorizacao",
            "header_label": "Objeto de autorização",
        }
    ]


def test_resolve_subprocess_section_fields_renders_time_field_as_time_input() -> None:
    resolved_fields = resolve_subprocess_section_fields_v1(
        "calendario",
        "custom_horario",
        [
            {
                "key": "calendario",
                "process_additional_fields": [
                    {
                        "key": "custom_hora_de_inicio",
                        "label": "Hora de início",
                        "field_type": "time",
                        "is_required": True,
                        "size": "255",
                        "header_key": "custom_horario",
                    },
                ],
                "process_field_options": [
                    {
                        "key": "custom_horario",
                        "label": "Horário",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_hora_de_inicio",
                        "label": "Hora de início",
                        "field_type": "time",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_hora_de_inicio",
                        "header_key": "custom_horario",
                    }
                ],
            }
        ],
    )

    assert len(resolved_fields) == 1
    resolved_field = resolved_fields[0]
    assert resolved_field["field_type"] == "time"
    assert resolved_field["input_type"] == "time"
    assert resolved_field["required"] is True
    # "time" nao e textual: o tamanho maximo enviado e ignorado na renderizacao.
    assert resolved_field["size"] is None


def test_resolve_subprocess_section_fields_keeps_empty_lists_as_select() -> None:
    resolved_fields = resolve_subprocess_section_fields_v1(
        "perfil_de_autorizacao",
        "custom_objeto_de_autorizacao",
        [
            {
                "key": "perfil_de_autorizacao",
                "process_additional_fields": [
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
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
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_subprocesso",
                        "label": "Subprocesso",
                        "field_type": "text",
                    },
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
            "manual_list_items": [],
            "manual_list_items_csv": "",
            "options": [],
            "header_key": "custom_objeto_de_autorizacao",
            "header_label": "Objeto de autorização",
        }
    ]


def test_resolve_subprocess_section_fields_profile_menu_tabs_uses_custom_processo_dependency_in_objeto_autorizacao() -> (
    None
):
    resolved_fields = resolve_subprocess_section_fields_v1(
        "perfil_de_autorizacao",
        "custom_objeto_de_autorizacao",
        [
            {
                "key": "perfil_de_autorizacao",
                "process_additional_fields": [
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "list",
                        "list_source_type": "manual",
                    },
                    {
                        "key": "custom_subprocesso",
                        "label": "Subprocesso",
                        "field_type": "list",
                        "list_source_type": "profile_menu_tabs",
                        "automatic_source_field_key": "custom_nome_do_perfil",
                    },
                ],
                "process_field_options": [
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "text",
                    },
                    {
                        "key": "custom_subprocesso",
                        "label": "Subprocesso",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_processo",
                        "header_key": "custom_objeto_de_autorizacao",
                    },
                    {
                        "field_key": "custom_subprocesso",
                        "header_key": "custom_objeto_de_autorizacao",
                    },
                ],
            }
        ],
    )

    dependent_field = next(
        item for item in resolved_fields if item["key"] == "custom_subprocesso"
    )

    assert dependent_field["dependent_field_key"] == "custom_processo"


def test_resolve_subprocess_section_fields_active_menus_controller_does_not_depend_on_itself() -> (
    None
):
    resolved_fields = resolve_subprocess_section_fields_v1(
        "perfil_de_autorizacao",
        "custom_objeto_de_autorizacao",
        [
            {
                "key": "perfil_de_autorizacao",
                "process_additional_fields": [
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "list",
                        "list_source_type": "active_menus",
                    },
                ],
                "process_field_options": [
                    {
                        "key": "custom_objeto_de_autorizacao",
                        "label": "Objeto de autorização",
                        "field_type": "header",
                    },
                    {
                        "key": "custom_processo",
                        "label": "Processo",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_processo",
                        "header_key": "custom_objeto_de_autorizacao",
                    },
                ],
            },
            {
                "key": "extrato",
                "label": "Extrato",
                "is_active": True,
                "is_deleted": False,
            },
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao", "extrato"},
    )

    controller_field = next(
        item for item in resolved_fields if item["key"] == "custom_processo"
    )

    assert controller_field["list_source_type"] == "active_menus"
    assert "dependent_field_key" not in controller_field


def test_resolve_subprocess_section_fields_profile_menu_tabs_keeps_legacy_profile_dependency_outside_objeto_autorizacao() -> (
    None
):
    resolved_fields = resolve_subprocess_section_fields_v1(
        "perfil_de_autorizacao",
        "custom_perfil",
        [
            {
                "key": "perfil_de_autorizacao",
                "process_additional_fields": [
                    {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
                    {
                        "key": "custom_nome_do_perfil",
                        "label": "Nome do perfil",
                        "field_type": "text",
                    },
                    {
                        "key": "custom_subprocesso",
                        "label": "Subprocesso",
                        "field_type": "list",
                        "list_source_type": "profile_menu_tabs",
                        "automatic_source_field_key": "custom_nome_do_perfil",
                    },
                ],
                "process_field_options": [
                    {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
                    {
                        "key": "custom_nome_do_perfil",
                        "label": "Nome do perfil",
                        "field_type": "text",
                    },
                    {
                        "key": "custom_subprocesso",
                        "label": "Subprocesso",
                        "field_type": "text",
                    },
                ],
                "process_visible_field_rows": [
                    {
                        "field_key": "custom_nome_do_perfil",
                        "header_key": "custom_perfil",
                    },
                    {"field_key": "custom_subprocesso", "header_key": "custom_perfil"},
                ],
            }
        ],
    )

    dependent_field = next(
        item for item in resolved_fields if item["key"] == "custom_subprocesso"
    )

    assert dependent_field["dependent_field_key"] == "custom_nome_do_perfil"


def test_resolve_subprocess_section_fields_active_menus_keeps_select_options() -> None:
    resolved_fields = resolve_subprocess_section_fields_v1(
        "perfil_de_autorizacao",
        "custom_perfil",
        [
            {
                "key": "perfil_de_autorizacao",
                "label": "Perfil de autorização",
                "is_active": True,
                "is_deleted": False,
                "process_additional_fields": [
                    {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
                    {
                        "key": "custom_perfil_2",
                        "label": "Perfil",
                        "field_type": "list",
                        "list_source_type": "active_menus",
                    },
                ],
                "process_field_options": [
                    {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
                    {"key": "custom_perfil_2", "label": "Perfil", "field_type": "list"},
                ],
                "process_visible_field_rows": [
                    {"field_key": "custom_perfil_2", "header_key": "custom_perfil"},
                ],
            },
            {
                "key": "sessoes",
                "label": "Estruturas",
                "is_active": True,
                "is_deleted": False,
            },
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao", "sessoes"},
        menu_process_history_map={},
    )

    assert resolved_fields == [
        {
            "key": "custom_perfil_2",
            "label": "Perfil",
            "field_type": "list",
            "input_type": "select",
            "required": False,
            "size": None,
            "list_source_type": "active_menus",
            "manual_list_key": "",
            "list_key": "",
            "automatic_source_process_key": "",
            "automatic_source_section_key": "",
            "automatic_source_field_key": "",
            "automatic_only_active": False,
            "manual_list_items": [],
            "manual_list_items_csv": "",
            "options": [
                {
                    "value": "perfil_de_autorizacao",
                    "label": "Perfil de autorização",
                    "status": "active",
                },
                {"value": "sessoes", "label": "Estruturas", "status": "active"},
            ],
            "header_key": "custom_perfil",
            "header_label": "Perfil",
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


def test_normalize_sidebar_sections_exposes_can_delete_only_for_non_default_sections() -> (
    None
):
    normalized = normalize_sidebar_sections(
        [
            {
                "key": "arquivo",
                "label": "Arquivo",
                "visibility_scope_mode": "owner",
                "status": "inativo",
            }
        ]
    )

    sistema_item = next(item for item in normalized if item["key"] == "sistema")
    arquivo_item = next(item for item in normalized if item["key"] == "arquivo")

    assert sistema_item["can_delete"] is False
    assert arquivo_item["can_delete"] is True


def test_resolve_menu_sidebar_section_key_keeps_perfil_de_autorizacao_em_sistema() -> (
    None
):
    resolved_key = resolve_menu_sidebar_section_key(
        "perfil_de_autorizacao",
        {},
        {"sistema", "igreja"},
        ["sistema", "igreja"],
    )

    assert resolved_key == "sistema"


def test_sessoes_config_exposes_delete_action_for_inactive_rows() -> None:
    assert SESSOES_CONFIG.delete_endpoint == "/settings/menu/sidebar-section-delete"

    delete_action = next(
        action for action in SESSOES_CONFIG.actions if action.key == "delete"
    )

    assert delete_action.visible_when == ("inativo",)
    assert delete_action.condition_field == "can_delete"


def test_move_sidebar_menu_setting_respects_active_menu_ordering() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        default_rows = [
            SidebarMenuSetting(
                entity_id=1,
                menu_key=item["key"],
                menu_label=str(item["label"]),
                is_active=(item["key"] == "home"),
                is_deleted=False,
                menu_config=json.dumps(
                    {"display_order": index},
                    ensure_ascii=False,
                ),
            )
            for index, item in enumerate(SIDEBAR_MENU_DEFAULTS)
        ]
        session.add_all(
            [
                *default_rows,
                SidebarMenuSetting(
                    entity_id=1,
                    menu_key="sistema",
                    menu_label="Sistema",
                    is_active=False,
                    is_deleted=False,
                    menu_config=json.dumps(
                        {"display_order": len(SIDEBAR_MENU_DEFAULTS)},
                        ensure_ascii=False,
                    ),
                ),
                SidebarMenuSetting(
                    entity_id=1,
                    menu_key="agenda",
                    menu_label="Agenda",
                    is_active=True,
                    is_deleted=False,
                    menu_config=json.dumps(
                        {"display_order": len(SIDEBAR_MENU_DEFAULTS) + 1},
                        ensure_ascii=False,
                    ),
                ),
                SidebarMenuSetting(
                    entity_id=1,
                    menu_key="contatos",
                    menu_label="Contatos",
                    is_active=True,
                    is_deleted=False,
                    menu_config=json.dumps(
                        {"display_order": len(SIDEBAR_MENU_DEFAULTS) + 2},
                        ensure_ascii=False,
                    ),
                ),
            ]
        )
        session.commit()

        ok, error_message = move_sidebar_menu_setting(session, "contatos", "up")

        assert ok is True
        assert error_message == ""

        settings = get_sidebar_menu_settings(session)
        active_keys = [
            item["key"]
            for item in settings
            if item.get("is_active") and not item.get("is_deleted")
        ]

        assert active_keys == ["home", "contatos", "agenda"]


def test_get_sidebar_menu_settings_limits_moves_to_visible_active_menus() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        default_rows = [
            SidebarMenuSetting(
                entity_id=1,
                menu_key=item["key"],
                menu_label=str(item["label"]),
                is_active=(item["key"] == "home"),
                is_deleted=False,
                menu_config=json.dumps(
                    {"display_order": index},
                    ensure_ascii=False,
                ),
            )
            for index, item in enumerate(SIDEBAR_MENU_DEFAULTS)
        ]
        session.add_all(
            [
                *default_rows,
                SidebarMenuSetting(
                    entity_id=1,
                    menu_key="sistema",
                    menu_label="Sistema",
                    is_active=False,
                    is_deleted=False,
                    menu_config=json.dumps(
                        {"display_order": len(SIDEBAR_MENU_DEFAULTS)},
                        ensure_ascii=False,
                    ),
                ),
                SidebarMenuSetting(
                    entity_id=1,
                    menu_key="agenda",
                    menu_label="Agenda",
                    is_active=True,
                    is_deleted=False,
                    menu_config=json.dumps(
                        {"display_order": len(SIDEBAR_MENU_DEFAULTS) + 1},
                        ensure_ascii=False,
                    ),
                ),
                SidebarMenuSetting(
                    entity_id=1,
                    menu_key="contatos",
                    menu_label="Contatos",
                    is_active=True,
                    is_deleted=False,
                    menu_config=json.dumps(
                        {"display_order": len(SIDEBAR_MENU_DEFAULTS) + 2},
                        ensure_ascii=False,
                    ),
                ),
                SidebarMenuSetting(
                    entity_id=1,
                    menu_key="arquivo",
                    menu_label="Arquivo",
                    is_active=False,
                    is_deleted=True,
                    menu_config=json.dumps(
                        {"display_order": len(SIDEBAR_MENU_DEFAULTS) + 3},
                        ensure_ascii=False,
                    ),
                ),
            ]
        )
        session.commit()

        settings = get_sidebar_menu_settings(session)
        active_rows = [
            item
            for item in settings
            if item.get("is_active") and not item.get("is_deleted")
        ]

        assert [item["key"] for item in active_rows] == ["home", "agenda", "contatos"]
        assert active_rows[0]["can_move_up"] is False
        assert active_rows[0]["can_move_down"] is True
        assert active_rows[1]["can_move_up"] is True
        assert active_rows[1]["can_move_down"] is True
        assert active_rows[2]["can_move_up"] is True
        assert active_rows[2]["can_move_down"] is False

        ok, error_message = move_sidebar_menu_setting(session, "home", "up")
        assert ok is False
        assert error_message == "Esta pasta já está no topo."

        ok, error_message = move_sidebar_menu_setting(session, "contatos", "down")
        assert ok is False
        assert error_message == "Esta pasta já está no fim."


def test_delete_sidebar_section_removes_only_target_inactive_custom_section() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        admin_config = {
            "sidebar_sections": [
                {
                    "key": "sistema",
                    "label": "Sistema",
                    "visibility_scope_mode": "all",
                    "status": "ativo",
                },
                {
                    "key": "arquivo",
                    "label": "Arquivo",
                    "visibility_scope_mode": "owner",
                    "status": "inativo",
                },
                {
                    "key": "agenda",
                    "label": "Agenda",
                    "visibility_scope_mode": "owner",
                    "status": "ativo",
                },
            ]
        }
        session.add(
            SidebarMenuSetting(
                entity_id=1,
                menu_key="administrativo",
                menu_label="Administrativo",
                is_active=True,
                is_deleted=False,
                menu_config=json.dumps(admin_config, ensure_ascii=False),
            )
        )
        session.commit()

        ok, error_message = delete_sidebar_section(session, "arquivo")

        assert ok is True
        assert error_message == ""

        stored_admin = session.scalar(
            select(SidebarMenuSetting).where(
                SidebarMenuSetting.menu_key == "administrativo"
            )
        )
        assert stored_admin is not None

        stored_config = json.loads(stored_admin.menu_config or "{}")
        stored_sections = stored_config.get("sidebar_sections") or []
        stored_keys = [item["key"] for item in stored_sections]

        assert "arquivo" not in stored_keys
        assert "agenda" in stored_keys
        assert (
            next(item for item in stored_sections if item["key"] == "agenda")["status"]
            == "ativo"
        )


def test_delete_sidebar_section_rejects_active_or_protected_rows() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        admin_config = {
            "sidebar_sections": [
                {
                    "key": "sistema",
                    "label": "Sistema",
                    "visibility_scope_mode": "all",
                    "status": "inativo",
                },
                {
                    "key": "agenda",
                    "label": "Agenda",
                    "visibility_scope_mode": "owner",
                    "status": "ativo",
                },
            ]
        }
        session.add(
            SidebarMenuSetting(
                entity_id=1,
                menu_key="administrativo",
                menu_label="Administrativo",
                is_active=True,
                is_deleted=False,
                menu_config=json.dumps(admin_config, ensure_ascii=False),
            )
        )
        session.commit()

        ok_active, error_active = delete_sidebar_section(session, "agenda")
        ok_protected, error_protected = delete_sidebar_section(session, "sistema")

        assert ok_active is False
        assert error_active == "A sessão deve estar inativa antes de ser eliminada."
        assert ok_protected is False
        assert error_protected == "Não é permitido eliminar esta sessão."


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
            Entity(
                entity_number=1,
                name="Igreja Teste",
                is_active=True,
            )
        )
        session.add(
            SidebarMenuSetting(
                entity_id=1,
                menu_key="empresa",
                menu_label="Empresa",
                is_active=True,
                is_deleted=False,
                menu_config=json.dumps(
                    {
                        "created_from": "administrativo_menu",
                        "settings_tabs_enabled": True,
                        "additional_fields": [
                            {
                                "key": "custom_dados_agregados",
                                "label": "Dados agregados",
                                "field_type": "header",
                            },
                            {
                                "key": "custom_quantos_filhos_tens",
                                "label": "Quantos filhos tens?",
                                "field_type": "number",
                            },
                            {
                                "key": "custom_nome_do_agregado",
                                "label": "Nome do agregado",
                                "field_type": "text",
                                "size": 80,
                            },
                            {
                                "key": "custom_data_nascimento_do_agregado",
                                "label": "Data de nascimento do agregado",
                                "field_type": "date",
                            },
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
                        [
                            "custom_nome_do_agregado",
                            "custom_data_nascimento_do_agregado",
                        ]
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
        empresa_setting = next(
            item for item in sidebar_settings if item["key"] == "empresa"
        )
        assert (
            empresa_setting["process_quantity_fields"]
            == saved_config["process_quantity_fields"]
        )


def test_normalize_additional_fields_manual_list_inline_csv() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {
                "label": "Permissões",
                "field_type": "list",
                "list_source_type": "manual",
                "manual_list_items": "Criar, Editar, Eliminar, Visualizar",
            }
        ]
    )

    assert len(normalized) == 1
    field = normalized[0]
    assert field["field_type"] == "list"
    assert field["list_source_type"] == "manual"
    assert field["manual_list_items"] == ["Criar", "Editar", "Eliminar", "Visualizar"]
    assert field["manual_list_items_csv"] == "Criar, Editar, Eliminar, Visualizar"


def test_normalize_additional_fields_manual_list_inline_deduplicates() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {
                "label": "Estado",
                "field_type": "list",
                "list_source_type": "manual",
                "manual_list_items": "Criar, Editar, Criar",
            }
        ]
    )

    assert len(normalized) == 1
    field = normalized[0]
    assert field["manual_list_items"] == ["Criar", "Editar"]
    assert field["manual_list_items_csv"] == "Criar, Editar"


def test_normalize_additional_fields_manual_list_inline_trims_whitespace() -> None:
    normalized = normalize_menu_process_additional_fields(
        [
            {
                "label": "Tipo",
                "field_type": "list",
                "list_source_type": "manual",
                "manual_list_items": "  Ativo  ,  Inativo  ,   ",
            }
        ]
    )

    assert len(normalized) == 1
    field = normalized[0]
    assert field["manual_list_items"] == ["Ativo", "Inativo"]


def test_resolve_field_list_options_manual_inline_items() -> None:
    resolved = resolve_field_list_options_v1(
        current_menu_key="empresa",
        field_definition={
            "field_type": "list",
            "list_source_type": "manual",
            "manual_list_items": ["Criar", "Editar", "Eliminar", "Visualizar"],
        },
        sidebar_menu_settings=[{"key": "empresa"}],
        visible_sidebar_menu_keys={"empresa"},
        menu_process_history_map={},
    )

    assert resolved == [
        {"value": "Criar", "label": "Criar", "status": "active"},
        {"value": "Editar", "label": "Editar", "status": "active"},
        {"value": "Eliminar", "label": "Eliminar", "status": "active"},
        {"value": "Visualizar", "label": "Visualizar", "status": "active"},
    ]


def test_resolve_field_list_options_manual_inline_csv_string() -> None:
    resolved = resolve_field_list_options_v1(
        current_menu_key="empresa",
        field_definition={
            "field_type": "list",
            "list_source_type": "manual",
            "manual_list_items_csv": "Criar, Editar, Eliminar",
        },
        sidebar_menu_settings=[{"key": "empresa"}],
        visible_sidebar_menu_keys={"empresa"},
        menu_process_history_map={},
    )

    assert resolved == [
        {"value": "Criar", "label": "Criar", "status": "active"},
        {"value": "Editar", "label": "Editar", "status": "active"},
        {"value": "Eliminar", "label": "Eliminar", "status": "active"},
    ]


def test_resolve_field_list_options_manual_inline_takes_precedence_over_list_key() -> (
    None
):
    resolved = resolve_field_list_options_v1(
        current_menu_key="empresa",
        field_definition={
            "field_type": "list",
            "list_source_type": "manual",
            "manual_list_items": ["Inline A", "Inline B"],
            "manual_list_key": "lista_antiga",
        },
        sidebar_menu_settings=[
            {
                "key": "empresa",
                "process_lists": [
                    {"key": "lista_antiga", "items": ["Antigo 1", "Antigo 2"]},
                ],
            }
        ],
        visible_sidebar_menu_keys={"empresa"},
        menu_process_history_map={},
    )

    assert resolved == [
        {"value": "Inline A", "label": "Inline A", "status": "active"},
        {"value": "Inline B", "label": "Inline B", "status": "active"},
    ]


def test_resolve_field_list_options_manual_legacy_list_key_still_works() -> None:
    resolved = resolve_field_list_options_v1(
        current_menu_key="empresa",
        field_definition={
            "field_type": "list",
            "list_source_type": "manual",
            "manual_list_key": "list_perfil",
        },
        sidebar_menu_settings=[
            {
                "key": "empresa",
                "process_lists": [
                    {"key": "list_perfil", "items": ["Pastor", "Líder"]},
                ],
            }
        ],
        visible_sidebar_menu_keys={"empresa"},
        menu_process_history_map={},
    )

    assert resolved == [
        {"value": "Pastor", "label": "Pastor", "status": "active"},
        {"value": "Líder", "label": "Líder", "status": "active"},
    ]


def test_resolve_field_list_options_manual_reference_uses_automatic_process_list_history() -> (
    None
):
    resolved = resolve_field_list_options_v1(
        current_menu_key="perfil_de_autorizacao",
        field_definition={
            "key": "custom_nome_do_perfil",
            "field_type": "list",
            "list_source_type": "manual",
            "manual_list_key": "list_perfil",
            "list_key": "list_perfil",
        },
        sidebar_menu_settings=[
            {
                "key": "perfil_de_autorizacao",
                "process_lists": [
                    {
                        "key": "list_perfil",
                        "label": "Perfil",
                        "field_type": "automatic",
                        "source_menu_key": "perfil_de_autorizacao",
                        "source_subprocess_key": "perfis",
                        "automatic_only_active": True,
                        "items": [],
                    }
                ],
                "process_field_options": [
                    {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
                    {
                        "key": "custom_nome_do_perfil",
                        "label": "Nome do perfil",
                        "field_type": "list",
                    },
                ],
            }
        ],
        visible_sidebar_menu_keys={"perfil_de_autorizacao"},
        menu_process_history_map={
            "perfil_de_autorizacao": [
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "custom_nome_do_perfil": "Gestor de Tesouraria",
                        "__estado": "ativo",
                    },
                },
                {
                    "section_key": "custom_perfil",
                    "values": {
                        "custom_nome_do_perfil": "Calendário Geral",
                        "__estado": "active",
                    },
                },
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "custom_nome_do_perfil": "Gestor de sistema",
                        "__estado": "ativo",
                    },
                },
                {
                    "section_key": "outra_secao",
                    "values": {
                        "custom_nome_do_perfil": "Não entra",
                        "__estado": "active",
                    },
                },
                {
                    "section_key": "custom_perfil_header",
                    "values": {
                        "custom_nome_do_perfil": "Gestor de Tesouraria",
                        "__estado": "inactive",
                    },
                },
            ]
        },
    )

    assert resolved == [
        {"value": "Gestor de Tesouraria", "label": "Gestor de Tesouraria", "status": "active"},
        {"value": "Calendário Geral", "label": "Calendário Geral", "status": "active"},
        {"value": "Gestor de sistema", "label": "Gestor de sistema", "status": "active"},
    ]
