import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.menu_settings import update_sidebar_menu_additional_fields_v1
from appgenesis.models import Base, Entity, SidebarMenuSetting


def _build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[Entity.__table__, SidebarMenuSetting.__table__],
    )
    return sessionmaker(bind=engine, future=True)


def _seed_menu(SessionLocal, *, menu_key, entity_id, menu_config):
    session = SessionLocal()
    row = SidebarMenuSetting(
        entity_id=entity_id,
        menu_key=menu_key,
        menu_label=menu_key,
        menu_config=json.dumps(menu_config),
    )
    session.add(row)
    session.commit()
    session.close()


def _load_config(SessionLocal, menu_key):
    session = SessionLocal()
    row = session.execute(
        select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == menu_key)
    ).scalar_one()
    config = json.loads(row.menu_config)
    entity_id = row.entity_id
    session.close()
    return config, entity_id


def test_update_additional_fields_ignores_entity_id_column_by_design():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=999,
        menu_config={"additional_fields": []},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[{"label": "Estado", "field_type": "text"}],
    )
    session.close()

    assert ok is True
    assert error == ""
    config, entity_id = _load_config(SessionLocal, "processo_teste_a")
    assert entity_id == 999
    assert config["additional_fields"][0]["key"] == "custom_estado"


def test_update_additional_fields_isolated_between_menu_keys():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"additional_fields": []},
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_b",
        entity_id=1,
        menu_config={
            "additional_fields": [
                {
                    "key": "custom_preexistente",
                    "label": "Preexistente",
                    "field_type": "text",
                    "is_required": False,
                }
            ]
        },
    )

    session = SessionLocal()
    update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[{"label": "Novo Campo", "field_type": "text"}],
    )
    session.close()

    config_a, _ = _load_config(SessionLocal, "processo_teste_a")
    config_b, _ = _load_config(SessionLocal, "processo_teste_b")

    assert [item["key"] for item in config_a["additional_fields"]] == ["custom_novo_campo"]
    assert [item["key"] for item in config_b["additional_fields"]] == ["custom_preexistente"]


def test_update_additional_fields_preserves_unrelated_menu_config_sections():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={
            "additional_fields": [],
            "process_lists": [{"key": "list_x", "label": "X"}],
            "subsequent_fields": [{"key": "subseq_x"}],
        },
    )

    session = SessionLocal()
    update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[{"label": "Estado", "field_type": "text"}],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_lists"] == [{"key": "list_x", "label": "X"}]
    assert config["subsequent_fields"] == [{"key": "subseq_x"}]


def test_update_additional_fields_persists_list_key_without_manual_items():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_lista",
        entity_id=1,
        menu_config={"additional_fields": [], "process_lists": [{"key": "list_opcoes", "label": "Opcoes"}]},
    )

    session = SessionLocal()
    update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_lista",
        fields=[
            {
                "label": "Estado",
                "field_type": "list",
                "list_key": "list_opcoes",
                "manual_list_key": "list_opcoes",
            }
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_lista")
    item = config["additional_fields"][0]
    assert item["list_key"] == "list_opcoes"
    assert item["manual_list_key"] == "list_opcoes"
    assert item["field_type"] == "list"
    assert item.get("manual_list_items_csv", "") == ""
    assert item.get("manual_list_items", []) == []


def test_update_additional_fields_dedup_identical_label_within_same_group():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"additional_fields": []},
    )

    session = SessionLocal()
    update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[
            {"label": "Motivo", "field_type": "text"},
            {"label": "Motivo", "field_type": "text"},
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert len(config["additional_fields"]) == 1


def test_update_additional_fields_rows_without_label_are_discarded():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"additional_fields": []},
    )

    session = SessionLocal()
    update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[
            {"label": "", "field_type": "text"},
            {"label": "   ", "field_type": "text"},
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["additional_fields"] == []


def test_update_additional_fields_protected_menu_key_home_is_blocked():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="home",
        entity_id=1,
        menu_config={"additional_fields": []},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_additional_fields_v1(
        session,
        "home",
        fields=[{"label": "Estado", "field_type": "text"}],
    )
    session.close()

    assert ok is False
    assert error == "Este processo nao permite campos adicionais."
    config, _ = _load_config(SessionLocal, "home")
    assert config["additional_fields"] == []


def test_update_additional_fields_menu_not_found_returns_error():
    SessionLocal = _build_session_factory()

    session = SessionLocal()
    ok, error = update_sidebar_menu_additional_fields_v1(
        session,
        "processo_inexistente",
        fields=[{"label": "Estado", "field_type": "text"}],
    )
    session.close()

    assert ok is False
    assert error == "Menu não encontrado."


def test_update_additional_fields_headers_are_reordered_before_regular_fields():
    """
    Comportamento existente: normalize_menu_process_additional_fields (geracao ativa,
    linha 4880) reordena a lista final colocando TODOS os headers primeiro, mesmo que
    tenham sido submetidos misturados com campos normais. Este teste trava o
    comportamento atual; nao uniformizar/alterar nesta fase.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"additional_fields": []},
    )

    session = SessionLocal()
    update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[
            {"label": "Campo A", "field_type": "text"},
            {"label": "Secao 1", "field_type": "header"},
            {"label": "Campo B", "field_type": "text"},
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    keys = [item["key"] for item in config["additional_fields"]]
    assert keys == ["custom_secao_1", "custom_campo_a", "custom_campo_b"]


def test_update_additional_fields_stable_key_preserved_when_key_resupplied():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"additional_fields": []},
    )

    session = SessionLocal()
    update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[{"label": "Estado", "field_type": "text"}],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    original_key = config["additional_fields"][0]["key"]

    session = SessionLocal()
    update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[{"key": original_key, "label": "Estado Civil", "field_type": "text"}],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["additional_fields"][0]["key"] == original_key
    # _normalize_additional_field_label aplica "sentence case" (so a primeira
    # letra da frase fica maiuscula); nao e' um simples passthrough do label.
    assert config["additional_fields"][0]["label"] == "Estado civil"


def test_update_additional_fields_automatic_list_source_is_persisted():
    """
    Protege a funcionalidade de "lista automatica" (list_source_type=automatic),
    ja suportada pela geracao ativa do normalizador. Risco documentado na Fase 0:
    esta funcionalidade poderia perder-se silenciosamente numa reversao acidental
    para uma geracao mais antiga do normalizador.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"additional_fields": []},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[
            {
                "label": "Categoria",
                "field_type": "list",
                "list_source_type": "automatic",
                "automatic_source_process_key": "estoque",
                "automatic_source_section_key": "produtos",
                "automatic_source_field_key": "categoria",
                "automatic_only_active": "on",
            }
        ],
    )
    session.close()

    assert ok is True
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    item = config["additional_fields"][0]
    assert item["list_source_type"] == "automatic"
    assert item["automatic_source_process_key"] == "estoque"
    assert item["automatic_source_section_key"] == "produtos"
    assert item["automatic_source_field_key"] == "categoria"
    assert item["automatic_only_active"] is True


def test_update_additional_fields_group_scoped_key_for_same_label_across_groups():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"additional_fields": []},
    )

    session = SessionLocal()
    update_sidebar_menu_additional_fields_v1(
        session,
        "processo_teste_a",
        fields=[
            {"label": "Dados", "field_type": "header"},
            {"label": "Dados", "field_type": "text"},
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    keys = [item["key"] for item in config["additional_fields"]]
    assert len(keys) == 2
    assert len(set(keys)) == 2
