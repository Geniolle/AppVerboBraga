import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.dynamic_process_layout import resolve_dynamic_process_layout_config
from appgenesis.menu_settings import (
    get_menu_process_selectable_field_options,
    update_sidebar_menu_process_fields,
)
from appgenesis.models import Base, Entity, SidebarMenuSetting


CUSTOM_ADDITIONAL_FIELDS = [
    {
        "key": "custom_secao_dados",
        "label": "Dados",
        "field_type": "header",
        "is_required": False,
    },
    {
        "key": "custom_nome",
        "label": "Nome",
        "field_type": "text",
        "is_required": False,
    },
    {
        "key": "custom_estado",
        "label": "Estado",
        "field_type": "text",
        "is_required": False,
    },
]


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


def _seed_custom_process(SessionLocal, *, menu_key="processo_teste_a", entity_id=1, extra=None):
    menu_config = {"additional_fields": CUSTOM_ADDITIONAL_FIELDS}
    if extra:
        menu_config.update(extra)
    _seed_menu(SessionLocal, menu_key=menu_key, entity_id=entity_id, menu_config=menu_config)


####################################################################################
# (1) ISOLAMENTO: entity_id ignorado por design (mesmo padrao das 3 abas ja
# protegidas) e isolamento entre menu_keys distintos.
####################################################################################

def test_update_process_fields_ignores_entity_id_column_by_design():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal, entity_id=999)

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome"],
        visible_headers=[""],
    )
    session.close()

    assert ok is True
    assert error == ""
    config, entity_id = _load_config(SessionLocal, "processo_teste_a")
    assert entity_id == 999
    assert config["process_visible_fields"] == ["custom_nome"]


def test_update_process_fields_isolated_between_menu_keys():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal, menu_key="processo_teste_a", entity_id=1)
    _seed_custom_process(SessionLocal, menu_key="processo_teste_b", entity_id=1)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome"],
        visible_headers=[""],
    )
    session.close()

    config_a, _ = _load_config(SessionLocal, "processo_teste_a")
    config_b, _ = _load_config(SessionLocal, "processo_teste_b")

    assert config_a["process_visible_fields"] == ["custom_nome"]
    assert config_b.get("process_visible_fields") is None


def test_update_process_fields_preserves_unrelated_menu_config_sections():
    SessionLocal = _build_session_factory()
    _seed_custom_process(
        SessionLocal,
        extra={
            "process_lists": [{"key": "list_x", "label": "X"}],
            "subsequent_fields": [{"key": "subseq_x"}],
        },
    )

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome"],
        visible_headers=[""],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_lists"] == [{"key": "list_x", "label": "X"}]
    assert config["subsequent_fields"] == [{"key": "subseq_x"}]
    # additional_fields (fonte das opcoes configuraveis) tambem deve permanecer intacta.
    assert config["additional_fields"] == CUSTOM_ADDITIONAL_FIELDS


####################################################################################
# (2) FILTRAGEM E DEDUPLICACAO: linhas sem chave, chaves nao configuraveis, e
# repeticoes sao descartadas via "seen_fields"/"selectable_keys".
####################################################################################

def test_update_process_fields_dedup_repeated_field_key():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    ok, _ = update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome", "custom_nome"],
        visible_headers=["", ""],
    )
    session.close()

    assert ok is True
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_visible_fields"] == ["custom_nome"]


def test_update_process_fields_rows_without_field_key_are_discarded():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["", "  ", "custom_nome"],
        visible_headers=["", "", ""],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_visible_fields"] == ["custom_nome"]


def test_update_process_fields_keys_not_in_selectable_options_are_discarded():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome", "chave_inexistente"],
        visible_headers=["", ""],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_visible_fields"] == ["custom_nome"]


def test_update_process_fields_header_key_not_in_header_options_is_dropped():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome"],
        visible_headers=["chave_de_header_inexistente"],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_visible_field_header_map"] == {}
    assert config["process_visible_field_rows"][0]["header_key"] == ""


####################################################################################
# (3) AUSENCIA DE CAMPOS CONFIGURAVEIS E MENU INEXISTENTE.
####################################################################################

def test_update_process_fields_no_configurable_fields_returns_error():
    """
    Achado desta fase: para um processo custom SEM nenhum campo em
    additional_fields, MENU_PROCESS_FIELD_OPTIONS_BY_KEY.get(...) tambem devolve
    tupla vazia -- logo nao ha nenhuma chave selecionavel nem de header, e a
    persistencia falha de forma explicita. Esta aba depende inteiramente dos dados
    de Campos Adicionais para ser utilizavel num processo custom.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_sem_campos",
        entity_id=1,
        menu_config={"additional_fields": []},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_fields(
        session,
        "processo_sem_campos",
        visible_fields=["qualquer_coisa"],
        visible_headers=[""],
    )
    session.close()

    assert ok is False
    assert error == "Este processo não possui campos configuráveis."
    config, _ = _load_config(SessionLocal, "processo_sem_campos")
    assert "process_visible_fields" not in config


def test_update_process_fields_menu_not_found_returns_error():
    SessionLocal = _build_session_factory()

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_fields(
        session,
        "processo_inexistente",
        visible_fields=["x"],
        visible_headers=[""],
    )
    session.close()

    assert ok is False
    assert error == "Menu não encontrado."


####################################################################################
# (4) ORDEM E DEPENDENCIA POR INDICE: process_visible_fields preserva a ordem
# submetida (sem reordenar headers, ao contrario de Campos Adicionais). A
# associacao campo->header dentro de _v4 e' feita por indice de array
# (raw_visible_headers[row_index]) -- um risco real de desalinhamento se as duas
# listas tiverem tamanhos diferentes.
####################################################################################

def test_update_process_fields_order_is_preserved_as_submitted():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_estado", "custom_nome"],
        visible_headers=["", ""],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    # Ao contrario de Campos Adicionais (que reordena headers para o inicio), esta
    # aba mantem a ordem exata submetida.
    assert config["process_visible_fields"] == ["custom_estado", "custom_nome"]


def test_update_process_fields_index_based_header_association_when_lists_same_length():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome", "custom_estado"],
        visible_headers=["custom_secao_dados", ""],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    rows_by_field = {row["field_key"]: row["header_key"] for row in config["process_visible_field_rows"]}
    assert rows_by_field["custom_nome"] == "custom_secao_dados"
    assert rows_by_field["custom_estado"] == ""


def test_update_process_fields_header_list_shorter_than_fields_list_defaults_missing_to_empty():
    """
    Comportamento estranho documentado, nao corrigido (regra 10): quando
    visible_headers tem MENOS elementos que visible_fields, a associacao por
    indice (raw_visible_headers[row_index] if row_index < len(...) else "") faz com
    que os campos "sobrantes" fiquem silenciosamente sem header, em vez de gerar
    erro. Este e' o risco real de "dependencia por indice ou ordem" desta aba.
    """
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome", "custom_estado"],
        visible_headers=["custom_secao_dados"],
    )
    session.close()

    assert ok is True
    assert error == ""
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    rows_by_field = {row["field_key"]: row["header_key"] for row in config["process_visible_field_rows"]}
    assert rows_by_field["custom_nome"] == "custom_secao_dados"
    # "custom_estado" nao tinha entrada correspondente na lista de headers --
    # ficou sem header, silenciosamente, em vez de reaproveitar por engano o header
    # de outro campo ou de gerar um erro de validacao.
    assert rows_by_field["custom_estado"] == ""


####################################################################################
# (5) PRESERVACAO DE HEADER EM RESUBMISSAO EM BRANCO: quando a submissao nao traz
# NENHUM header e ja existe um mapa de headers persistido (em qualquer uma das 3
# fontes possiveis), os headers sao restaurados silenciosamente em vez de limpos.
####################################################################################

def test_update_process_fields_headers_preserved_on_blank_resubmit():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome"],
        visible_headers=["custom_secao_dados"],
    )
    session.close()

    # Resubmissao sem NENHUM header (ex.: refresh de pagina com formulario legado).
    session = SessionLocal()
    ok, _ = update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome"],
        visible_headers=[""],
    )
    session.close()

    assert ok is True
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    rows_by_field = {row["field_key"]: row["header_key"] for row in config["process_visible_field_rows"]}
    assert rows_by_field["custom_nome"] == "custom_secao_dados"


def test_update_process_fields_headers_not_preserved_when_incoming_has_any_header():
    """
    A preservacao so' ocorre quando NENHUM header e' submetido. Se pelo menos um
    header vier preenchido (mesmo que outros venham em branco), a submissao e'
    tratada como autoritativa e o mapa de headers e' recalculado do zero.
    """
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome", "custom_estado"],
        visible_headers=["custom_secao_dados", "custom_secao_dados"],
    )
    session.close()

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome", "custom_estado"],
        # Apenas o segundo header vem preenchido -- ja e' suficiente para
        # incoming_has_any_header ser True, desativando a preservacao.
        visible_headers=["", "custom_secao_dados"],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    rows_by_field = {row["field_key"]: row["header_key"] for row in config["process_visible_field_rows"]}
    assert rows_by_field["custom_nome"] == ""
    assert rows_by_field["custom_estado"] == "custom_secao_dados"


def test_update_process_fields_legacy_visible_field_headers_format_is_source_for_preservation():
    """
    Compatibilidade com dados antigos: o mapa de preservacao tambem le a partir do
    formato legado "visible_field_headers" (sem passar por process_visible_field_rows
    nem por process_visible_field_header_map), simulando um registo migrado de uma
    versao anterior do sistema que nunca gravou o formato novo.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_legado",
        entity_id=1,
        menu_config={
            "additional_fields": CUSTOM_ADDITIONAL_FIELDS,
            "visible_field_headers": {"custom_nome": "custom_secao_dados"},
        },
    )

    session = SessionLocal()
    ok, _ = update_sidebar_menu_process_fields(
        session,
        "processo_legado",
        visible_fields=["custom_nome"],
        visible_headers=[""],
    )
    session.close()

    assert ok is True
    config, _ = _load_config(SessionLocal, "processo_legado")
    rows_by_field = {row["field_key"]: row["header_key"] for row in config["process_visible_field_rows"]}
    assert rows_by_field["custom_nome"] == "custom_secao_dados"


####################################################################################
# (6) FORMATO LEGADO ESCRITO EM PARALELO: legacy_visible_fields interleava headers
# e campos na ordem em que o header e' encontrado; visible_fields/visible_field_headers
# sao sempre escritos ao lado do formato novo.
####################################################################################

def test_update_process_fields_legacy_visible_fields_interleaves_headers_and_fields():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome", "custom_estado"],
        visible_headers=["custom_secao_dados", "custom_secao_dados"],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    # O header e' emitido uma unica vez, antes do primeiro campo do grupo.
    assert config["visible_fields"] == [
        "custom_secao_dados",
        "custom_nome",
        "custom_estado",
    ]


def test_update_process_fields_writes_new_and_legacy_format_keys_simultaneously():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome"],
        visible_headers=["custom_secao_dados"],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    for key in (
        "process_visible_fields",
        "process_visible_field_header_map",
        "process_visible_field_rows",
        "process_visible_fields_configured",
        "process_visible_fields_refresh_version",
        "visible_fields",
        "visible_field_headers",
        "sidebar_global_refresh_version",
    ):
        assert key in config, f"chave {key} nao foi escrita"
    assert config["process_visible_fields_configured"] is True


def test_update_process_fields_refresh_version_changes_on_each_save():
    SessionLocal = _build_session_factory()
    _seed_custom_process(SessionLocal)

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session, "processo_teste_a", visible_fields=["custom_nome"], visible_headers=[""]
    )
    session.close()
    config_1, _ = _load_config(SessionLocal, "processo_teste_a")

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session, "processo_teste_a", visible_fields=["custom_estado"], visible_headers=[""]
    )
    session.close()
    config_2, _ = _load_config(SessionLocal, "processo_teste_a")

    assert (
        config_1["process_visible_fields_refresh_version"]
        != config_2["process_visible_fields_refresh_version"]
    )
    assert (
        config_1["sidebar_global_refresh_version"]
        != config_2["sidebar_global_refresh_version"]
    )


####################################################################################
# (7) COMPATIBILIDADE COM MENU BUILT-IN (sem additional_fields): confirma que as
# opcoes estaticas de MENU_PROCESS_FIELD_OPTIONS_BY_KEY continuam a funcionar para
# menus do sistema, independentemente de Campos Adicionais.
####################################################################################

def test_update_process_fields_built_in_menu_key_uses_static_options_without_additional_fields():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="financeiro",
        entity_id=1,
        menu_config={},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_fields(
        session,
        "financeiro",
        visible_fields=["nome", "estado"],
        visible_headers=["", ""],
    )
    session.close()

    assert ok is True
    assert error == ""
    config, _ = _load_config(SessionLocal, "financeiro")
    assert config["process_visible_fields"] == ["nome", "estado"]
    # Menus built-in nao tem nenhuma opcao do tipo "header" (os dicts em
    # MENU_PROCESS_FIELD_OPTIONS_BY_KEY nao definem "field_type").
    assert config["process_visible_field_header_map"] == {}


####################################################################################
# (8) IMPACTO NO RUNTIME OPERACIONAL: os dados persistidos por esta aba alimentam
# diretamente resolve_dynamic_process_layout_config, consumido pelo bootstrap do
# menu lateral e pela pagina de listagem do processo.
####################################################################################

def test_update_process_fields_runtime_layout_config_consumes_saved_rows_without_error():
    SessionLocal = _build_session_factory()
    _seed_custom_process(
        SessionLocal,
        extra={"process_list_config": {"layout": "lista"}},
    )

    session = SessionLocal()
    update_sidebar_menu_process_fields(
        session,
        "processo_teste_a",
        visible_fields=["custom_nome", "custom_estado"],
        visible_headers=["custom_secao_dados", ""],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    field_options = get_menu_process_selectable_field_options("processo_teste_a", config)

    layout_config = resolve_dynamic_process_layout_config(
        "processo_teste_a",
        "Processo Teste A",
        config,
        visible_field_rows=config["process_visible_field_rows"],
        field_options=field_options,
    )

    assert layout_config["is_list_process"] is True
    assert layout_config["list_columns"]
    assert layout_config["list_columns"][0]["field_key"] == "custom_nome"
