import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.menu_settings import (
    create_sidebar_menu_setting,
    delete_sidebar_menu_setting,
    move_sidebar_menu_setting,
    resolve_menu_key_alias,
    set_sidebar_menu_visibility,
    update_sidebar_menu_label,
)
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


def _seed_menu(SessionLocal, *, menu_key, entity_id=1, menu_label=None, menu_config=None, is_active=True, is_deleted=False):
    session = SessionLocal()
    row = SidebarMenuSetting(
        entity_id=entity_id,
        menu_key=menu_key,
        menu_label=menu_label if menu_label is not None else menu_key,
        menu_config=json.dumps(menu_config if menu_config is not None else {}),
        is_active=is_active,
        is_deleted=is_deleted,
    )
    session.add(row)
    session.commit()
    session.close()


def _load_row(SessionLocal, menu_key):
    session = SessionLocal()
    row = session.execute(
        select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == menu_key)
    ).scalar_one_or_none()
    if row is None:
        session.close()
        return None
    config = json.loads(row.menu_config) if row.menu_config else {}
    data = {
        "entity_id": row.entity_id,
        "menu_label": row.menu_label,
        "is_active": row.is_active,
        "is_deleted": row.is_deleted,
        "config": config,
    }
    session.close()
    return data


####################################################################################
# (1) GERACAO UNICA: apos a consolidacao estrutural desta fase, menu_settings.py
# define uma unica funcao "create_sidebar_menu_setting" (antigo corpo da v2). A
# v1 morta e o alias de modulo "create_sidebar_menu_setting = create_sidebar_menu_setting_v2"
# foram removidos. entity_id passou a ser o segundo parametro posicional,
# obrigatorio, resolvido pelo caller a partir da entidade ativa da sessao.
####################################################################################

####################################################################################
# (1B) CORRECAO CONFIRMADA: o INSERT de criacao genuina agora inclui entity_id,
# eliminando o IntegrityError anteriormente documentado. A unicidade de menu_key
# e menu_label permanece GLOBAL (nao filtrada por entity_id) nesta fase -- uma
# segunda entidade NAO pode criar/reativar uma pasta com a mesma chave/rotulo ja'
# usada por outra entidade. Migrar para isolamento por entity_id + menu_key em
# todas as leituras/escritas e' uma fase estrutural separada, ainda nao iniciada
# (ver secao (2)/ISOLAMENTO abaixo, que continua valida para
# update/move/delete/set_visibility).
####################################################################################

def test_create_sidebar_menu_setting_persists_entity_id_on_genuine_creation():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    session.add(Entity(id=1, name="Entidade Teste"))
    session.commit()

    ok, error, menu_key = create_sidebar_menu_setting(session, 1, "Processo Novo")
    session.close()

    assert ok is True
    assert error == ""
    assert menu_key == "processo_novo"
    row = _load_row(SessionLocal, "processo_novo")
    assert row["entity_id"] == 1
    assert row["is_active"] is True
    assert row["is_deleted"] is False


def test_create_sidebar_menu_setting_validates_label_before_insert():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    session.add(Entity(id=1, name="Entidade Teste"))
    session.commit()

    ok, error, menu_key = create_sidebar_menu_setting(session, 1, "   ")
    session.close()

    assert ok is False
    assert error == "Informe o nome da pasta."
    assert menu_key == ""


def test_create_sidebar_menu_setting_rejects_duplicate_active_key_globally():
    """
    A unicidade permanece global: uma segunda entidade nao pode criar uma pasta
    com a mesma menu_key/label ja' ativa em outra entidade. Duas entidades com a
    mesma menu_key NAO sao permitidas nesta fase -- isso exigiria migrar todas as
    leituras/escritas para filtrar por entity_id, fora de escopo aqui.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_existente", entity_id=1, menu_label="Processo Existente")

    session = SessionLocal()
    session.add(Entity(id=2, name="Entidade B"))
    session.commit()

    ok, error, menu_key = create_sidebar_menu_setting(session, 2, "Processo Existente")
    session.close()

    assert ok is False
    assert error == "Ja existe uma pasta com este nome."
    assert menu_key == "processo_existente"

    row = _load_row(SessionLocal, "processo_existente")
    assert row["entity_id"] == 1


def test_create_sidebar_menu_setting_does_not_create_ambiguous_rows_across_entities():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_existente", entity_id=1, menu_label="Processo Existente")

    session = SessionLocal()
    session.add(Entity(id=2, name="Entidade B"))
    session.commit()
    create_sidebar_menu_setting(session, 2, "Processo Existente")
    session.close()

    session = SessionLocal()
    matching_rows = (
        session.execute(
            select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == "processo_existente")
        )
        .scalars()
        .all()
    )
    session.close()

    assert len(matching_rows) == 1


def test_create_sidebar_menu_setting_bumps_administrativo_refresh_version_on_success():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="administrativo", menu_label="Administrativo")

    session = SessionLocal()
    session.add(Entity(id=1, name="Entidade Teste"))
    session.commit()
    create_sidebar_menu_setting(session, 1, "Processo Novo")
    session.close()

    administrativo_row = _load_row(SessionLocal, "administrativo")
    assert "sidebar_global_refresh_version" in administrativo_row["config"]


####################################################################################
# (3) COMPORTAMENTO PRESERVADO: create_sidebar_menu_setting REATIVA uma pasta
# soft-deleted quando a chave OU o rotulo coincidem -- reconstruindo o
# menu_config via _build_menu_config_v2 (preservando campos existentes como
# additional_fields) e marcando is_active=True/is_deleted=False. A busca de
# reativacao permanece GLOBAL (nao filtrada por entity_id), coerente com a
# unicidade global mantida nesta fase.
####################################################################################

def test_create_sidebar_menu_setting_reactivates_soft_deleted_menu_matching_key():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_a",
        menu_label="Processo A",
        menu_config={"additional_fields": [{"key": "custom_x", "label": "X"}]},
        is_active=False,
        is_deleted=True,
    )

    session = SessionLocal()
    ok, error, menu_key = create_sidebar_menu_setting(session, 1, "Processo A")
    session.close()

    assert ok is True
    assert error == ""
    assert menu_key == "processo_a"
    row = _load_row(SessionLocal, "processo_a")
    assert row["is_active"] is True
    assert row["is_deleted"] is False
    assert row["config"]["additional_fields"] == [{"key": "custom_x", "label": "X"}]


def test_create_sidebar_menu_setting_reactivates_soft_deleted_menu_matching_label_only():
    """
    Comportamento preservado: a busca por registo existente usa
    "menu_key = :menu_key OR menu_label = :menu_label", portanto um rotulo
    identico com uma chave historica diferente da que seria gerada agora tambem
    aciona a reativacao (com a chave historica preservada), em vez de criar uma
    segunda linha.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="chave_historica_antiga",
        menu_label="Processo A",
        is_active=False,
        is_deleted=True,
    )

    session = SessionLocal()
    ok, error, menu_key = create_sidebar_menu_setting(session, 1, "Processo A")
    session.close()

    assert ok is True
    assert error == ""
    assert menu_key == "chave_historica_antiga"
    row = _load_row(SessionLocal, "chave_historica_antiga")
    assert row["is_active"] is True
    assert row["is_deleted"] is False


def test_create_sidebar_menu_setting_purges_legacy_menu_section_on_reactivation():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_a",
        menu_label="Processo A",
        menu_config={"menu_section": "financeiro"},
        is_active=False,
        is_deleted=True,
    )

    session = SessionLocal()
    create_sidebar_menu_setting(session, 1, "Processo A")
    session.close()

    row = _load_row(SessionLocal, "processo_a")
    assert "menu_section" not in row["config"]
    assert "sidebar_section" in row["config"]


def test_create_sidebar_menu_setting_bumps_administrativo_refresh_version_on_reactivation():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="administrativo", menu_label="Administrativo")
    _seed_menu(
        SessionLocal,
        menu_key="processo_a",
        menu_label="Processo A",
        is_active=False,
        is_deleted=True,
    )

    session = SessionLocal()
    create_sidebar_menu_setting(session, 1, "Processo A")
    session.close()

    administrativo_row = _load_row(SessionLocal, "administrativo")
    assert "sidebar_global_refresh_version" in administrativo_row["config"]


####################################################################################
# (2) ISOLAMENTO: entity_id nao filtra nenhuma consulta em menu_settings.py; o
# isolamento e' exclusivamente por menu_key (lower/trim), por design, em todas as
# funcoes de escrita da aba Geral. Nao alterar este modelo nesta fase.
####################################################################################

def test_update_sidebar_menu_label_ignores_entity_id_column_by_design():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", entity_id=999, menu_label="Processo A")

    session = SessionLocal()
    ok, error = update_sidebar_menu_label(session, "processo_a", "Processo A Editado")
    session.close()

    assert ok is True
    assert error == ""
    row = _load_row(SessionLocal, "processo_a")
    assert row["entity_id"] == 999
    assert row["menu_label"] == "Processo A Editado"


def test_update_sidebar_menu_label_isolated_between_distinct_menu_keys():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")
    _seed_menu(SessionLocal, menu_key="processo_b", menu_label="Processo B")

    session = SessionLocal()
    update_sidebar_menu_label(session, "processo_a", "Processo A Editado")
    session.close()

    row_a = _load_row(SessionLocal, "processo_a")
    row_b = _load_row(SessionLocal, "processo_b")
    assert row_a["menu_label"] == "Processo A Editado"
    assert row_b["menu_label"] == "Processo B"


####################################################################################
# (3) VALIDACAO / MENSAGENS DE ERRO EXATAS (update_sidebar_menu_label)
####################################################################################

def test_update_sidebar_menu_label_rejects_nonexistent_menu():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    ok, error = update_sidebar_menu_label(session, "processo_inexistente", "Novo Nome")
    session.close()

    assert ok is False
    assert error == "Menu inválido."


def test_update_sidebar_menu_label_rejects_empty_label():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    session = SessionLocal()
    ok, error = update_sidebar_menu_label(session, "processo_a", "   ")
    session.close()

    assert ok is False
    assert error == "Nome do menu é obrigatório."


def test_update_sidebar_menu_label_rejects_invalid_visibility_scope():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    session = SessionLocal()
    ok, error = update_sidebar_menu_label(
        session, "processo_a", "Processo A", visibility_scope_mode="modo_invalido"
    )
    session.close()

    assert ok is False
    assert error == "Escopo de exibição inválido."


def test_update_sidebar_menu_label_rejects_invalid_sidebar_section():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    session = SessionLocal()
    ok, error = update_sidebar_menu_label(
        session, "processo_a", "Processo A", sidebar_section_key="secao_inexistente"
    )
    session.close()

    assert ok is False
    assert error == "Sessão inválida."


####################################################################################
# (4) COMPORTAMENTO ESTRANHO: menu_section (chave legado) e' sempre purgada do
# menu_config em toda edicao bem-sucedida, mesmo quando nao fornecida.
####################################################################################

def test_update_sidebar_menu_label_purges_legacy_menu_section_key():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_a",
        menu_label="Processo A",
        menu_config={"menu_section": "financeiro", "additional_fields": []},
    )

    session = SessionLocal()
    ok, _ = update_sidebar_menu_label(session, "processo_a", "Processo A")
    session.close()

    assert ok is True
    row = _load_row(SessionLocal, "processo_a")
    assert "menu_section" not in row["config"]
    assert row["config"]["additional_fields"] == []


####################################################################################
# (5) COMPORTAMENTO ESTRANHO CONFIRMADO: sidebar_global_refresh_version e'
# atualizado na row "administrativo" em TODA edicao bem-sucedida de qualquer menu
# (inline quando o proprio administrativo e' editado; via segundo UPDATE separado
# quando qualquer outra chave e' editada). create_sidebar_menu_setting NAO produz
# este efeito (nem chega a executar, dado o bug de entity_id).
####################################################################################

def test_update_sidebar_menu_label_bumps_administrativo_refresh_version_when_editing_other_key():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    session = SessionLocal()
    update_sidebar_menu_label(session, "processo_a", "Processo A")
    session.close()

    administrativo_row = _load_row(SessionLocal, "administrativo")
    assert "sidebar_global_refresh_version" in administrativo_row["config"]


def test_update_sidebar_menu_label_bumps_own_refresh_version_when_editing_administrativo_itself():
    SessionLocal = _build_session_factory()

    session = SessionLocal()
    ok, _ = update_sidebar_menu_label(session, "administrativo", "Administrativo")
    session.close()

    assert ok is True
    administrativo_row = _load_row(SessionLocal, "administrativo")
    assert "sidebar_global_refresh_version" in administrativo_row["config"]


####################################################################################
# (6) COMPORTAMENTO ESTRANHO CONFIRMADO: set_sidebar_menu_visibility forca
# is_deleted=False INCONDICIONALMENTE, mesmo quando make_visible=False. Isto
# permite reativar (undelete) um menu soft-deleted atraves do toggle de
# visibilidade usado pelo handler de edicao, e produz um estado inconsistente
# (is_active=False, is_deleted=False) quando make_visible=False e' aplicado a um
# menu ja' soft-deleted.
####################################################################################

def test_set_sidebar_menu_visibility_unconditionally_clears_is_deleted_on_hide():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_a",
        menu_label="Processo A",
        is_active=False,
        is_deleted=True,
    )

    session = SessionLocal()
    ok, error = set_sidebar_menu_visibility(session, "processo_a", False)
    session.close()

    assert ok is True
    assert error == ""
    row = _load_row(SessionLocal, "processo_a")
    assert row["is_active"] is False
    assert row["is_deleted"] is False


def test_set_sidebar_menu_visibility_reactivates_a_soft_deleted_menu():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_a",
        menu_label="Processo A",
        is_active=False,
        is_deleted=True,
    )

    session = SessionLocal()
    ok, error = set_sidebar_menu_visibility(session, "processo_a", True)
    session.close()

    assert ok is True
    assert error == ""
    row = _load_row(SessionLocal, "processo_a")
    assert row["is_active"] is True
    assert row["is_deleted"] is False


def test_set_sidebar_menu_visibility_rejects_hiding_protected_key():
    SessionLocal = _build_session_factory()

    session = SessionLocal()
    ok, error = set_sidebar_menu_visibility(session, "administrativo", False)
    session.close()

    assert ok is False
    assert error == "Não é permitido ocultar este menu."


def test_set_sidebar_menu_visibility_rejects_nonexistent_menu():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    ok, error = set_sidebar_menu_visibility(session, "processo_inexistente", True)
    session.close()

    assert ok is False
    assert error == "Menu inválido."


####################################################################################
# (7) EXCLUSAO: protecao por chave (home/administrativo) e protecao por rotulo
# ("Configuração"/"Configuracao") independente da chave.
####################################################################################

def test_delete_sidebar_menu_setting_rejects_protected_key():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    ok, error = delete_sidebar_menu_setting(session, "administrativo")
    session.close()

    assert ok is False
    assert error == "Não é permitido excluir este menu."


def test_delete_sidebar_menu_setting_rejects_label_based_protection_regardless_of_key():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_configuracao", menu_label="Configuração")

    session = SessionLocal()
    ok, error = delete_sidebar_menu_setting(session, "processo_configuracao")
    session.close()

    assert ok is False
    assert error == "Não é permitido excluir este menu."


def test_delete_sidebar_menu_setting_soft_deletes_a_regular_process():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    session = SessionLocal()
    ok, error = delete_sidebar_menu_setting(session, "processo_a")
    session.close()

    assert ok is True
    assert error == ""
    row = _load_row(SessionLocal, "processo_a")
    assert row["is_active"] is False
    assert row["is_deleted"] is True


def test_delete_sidebar_menu_setting_rejects_nonexistent_menu():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    ok, error = delete_sidebar_menu_setting(session, "processo_inexistente")
    session.close()

    assert ok is False
    assert error == "Menu inválido."


####################################################################################
# (8) COMPORTAMENTO ESTRANHO: _menu_exists e _load_menu_config nao filtram
# is_deleted -- um menu soft-deleted continua "existindo" para update/delete/move,
# permitindo, por exemplo, editar o rotulo de um processo ja' eliminado.
####################################################################################

def test_update_sidebar_menu_label_succeeds_on_a_soft_deleted_menu():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_a",
        menu_label="Processo A",
        is_active=False,
        is_deleted=True,
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_label(session, "processo_a", "Processo A Editado")
    session.close()

    assert ok is True
    assert error == ""
    row = _load_row(SessionLocal, "processo_a")
    assert row["menu_label"] == "Processo A Editado"
    assert row["is_deleted"] is True


def test_delete_sidebar_menu_setting_is_idempotent_on_an_already_deleted_menu():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_a",
        menu_label="Processo A",
        is_active=False,
        is_deleted=True,
    )

    session = SessionLocal()
    ok, error = delete_sidebar_menu_setting(session, "processo_a")
    session.close()

    assert ok is True
    assert error == ""


####################################################################################
# (9) ALIAS DE CHAVES LEGADAS
####################################################################################

@pytest.mark.parametrize(
    "legacy_key,canonical_key",
    [
        ("configuracao", "administrativo"),
        ("estruturas", "sessoes"),
        ("documentos", "meu_perfil"),
    ],
)
def test_resolve_menu_key_alias_resolves_all_legacy_aliases(legacy_key, canonical_key):
    assert resolve_menu_key_alias(legacy_key) == canonical_key


def test_resolve_menu_key_alias_is_pass_through_for_unknown_keys():
    assert resolve_menu_key_alias("processo_qualquer") == "processo_qualquer"


def test_update_sidebar_menu_label_accepts_legacy_alias_key():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    ok, error = update_sidebar_menu_label(session, "configuracao", "Administrativo")
    session.close()

    assert ok is True
    assert error == ""


####################################################################################
# (10) MOVER: limites de topo/fim entre menus ativos e nao-eliminados.
####################################################################################

def test_move_sidebar_menu_setting_rejects_invalid_direction():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    ok, error = move_sidebar_menu_setting(session, "administrativo", "sideways")
    session.close()

    assert ok is False
    assert error == "Direção inválida."


def test_move_sidebar_menu_setting_rejects_nonexistent_menu():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    ok, error = move_sidebar_menu_setting(session, "processo_inexistente", "up")
    session.close()

    assert ok is False
    assert error == "Menu inválido."


def test_move_sidebar_menu_setting_blocks_moving_first_active_item_up():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    ok, error = move_sidebar_menu_setting(session, "home", "up")
    session.close()

    assert ok is False
    assert error == "Esta pasta já está no topo."


def test_move_sidebar_menu_setting_blocks_moving_last_active_item_down():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    ok, error = move_sidebar_menu_setting(session, "tutorial", "down")
    session.close()

    assert ok is False
    assert error == "Esta pasta já está no fim."
