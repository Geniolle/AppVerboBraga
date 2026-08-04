import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.menu_settings import (
    normalize_menu_process_quantity_fields,
    update_sidebar_menu_process_quantity_fields_v1,
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


ADDITIONAL_FIELDS_BASE = [
    {
        "key": "custom_dados",
        "label": "Dados",
        "field_type": "header",
    },
    {
        "key": "custom_quantidade_filhos",
        "label": "Quantidade de filhos",
        "field_type": "number",
    },
    {
        "key": "custom_nome_filho",
        "label": "Nome do filho",
        "field_type": "text",
    },
    {
        "key": "custom_data_nascimento_filho",
        "label": "Data de nascimento do filho",
        "field_type": "date",
    },
    {
        "key": "custom_outro_texto",
        "label": "Outro texto",
        "field_type": "text",
    },
]


def _seed_menu(SessionLocal, *, menu_key, entity_id=1, additional_fields=None, process_quantity_fields=None):
    session = SessionLocal()
    menu_config = {
        "additional_fields": additional_fields
        if additional_fields is not None
        else ADDITIONAL_FIELDS_BASE,
    }
    if process_quantity_fields is not None:
        menu_config["process_quantity_fields"] = process_quantity_fields
    row = SidebarMenuSetting(
        entity_id=entity_id,
        menu_key=menu_key,
        menu_label=menu_key,
        menu_config=json.dumps(menu_config),
    )
    session.add(row)
    session.commit()
    session.close()


def _load_config(SessionLocal, menu_key, entity_id=1):
    session = SessionLocal()
    row = session.execute(
        select(SidebarMenuSetting).where(
            SidebarMenuSetting.menu_key == menu_key,
            SidebarMenuSetting.entity_id == entity_id,
        )
    ).scalar_one()
    config = json.loads(row.menu_config)
    entity_id = row.entity_id
    session.close()
    return config, entity_id


BASE_RULE = {
    "label": "Filhos",
    "quantity_field_key": "custom_quantidade_filhos",
    "repeated_field_keys": ["custom_nome_filho", "custom_data_nascimento_filho"],
}


####################################################################################
# (1) ISOLAMENTO MULTI-TENANT: a atualizacao de Campos Quantidade nao pode afetar
# outra entidade com o mesmo menu_key.
####################################################################################

def test_update_quantity_fields_isolated_between_entities_with_same_menu_key():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        process_quantity_fields=[
            {
                "key": "qty_existente",
                "label": "Existente",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_nome_filho"],
                "header_key": "",
                "max_items": 3,
                "item_label": "Item",
            }
        ],
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=2,
        process_quantity_fields=[
            {
                "key": "qty_outra_entidade",
                "label": "Outra entidade",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_nome_filho"],
                "header_key": "",
                "max_items": 7,
                "item_label": "Item",
            }
        ],
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [dict(BASE_RULE)],
        entity_id=1,
    )
    session.close()

    assert ok is True
    assert error == ""
    config, entity_id = _load_config(SessionLocal, "processo_teste_a", entity_id=1)
    assert entity_id == 1
    assert config["process_quantity_fields"][0]["key"] == "qty_filhos"

    other_config, other_entity_id = _load_config(
        SessionLocal,
        "processo_teste_a",
        entity_id=2,
    )
    assert other_entity_id == 2
    assert [item["key"] for item in other_config["process_quantity_fields"]] == [
        "qty_outra_entidade"
    ]


def test_update_quantity_fields_isolated_between_menu_keys():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_b",
        process_quantity_fields=[
            {
                "key": "qty_preexistente",
                "label": "Preexistente",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_nome_filho"],
                "header_key": "",
                "max_items": 10,
                "item_label": "Item",
            }
        ],
    )

    session = SessionLocal()
    update_sidebar_menu_process_quantity_fields_v1(
        session, "processo_teste_a", [dict(BASE_RULE)]
    )
    session.close()

    config_a, _ = _load_config(SessionLocal, "processo_teste_a")
    config_b, _ = _load_config(SessionLocal, "processo_teste_b")

    assert [item["key"] for item in config_a["process_quantity_fields"]] == ["qty_filhos"]
    assert [item["key"] for item in config_b["process_quantity_fields"]] == ["qty_preexistente"]


def test_update_quantity_fields_preserves_unrelated_menu_config_sections():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    row = SidebarMenuSetting(
        entity_id=1,
        menu_key="processo_teste_a",
        menu_label="processo_teste_a",
        menu_config=json.dumps(
            {
                "additional_fields": ADDITIONAL_FIELDS_BASE,
                "process_lists": [{"key": "list_x", "label": "X"}],
                "subsequent_fields": [{"key": "subseq_x"}],
            }
        ),
    )
    session.add(row)
    session.commit()
    session.close()

    session = SessionLocal()
    update_sidebar_menu_process_quantity_fields_v1(
        session, "processo_teste_a", [dict(BASE_RULE)]
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_lists"] == [{"key": "list_x", "label": "X"}]
    assert config["subsequent_fields"] == [{"key": "subseq_x"}]
    assert config["additional_fields"] == ADDITIONAL_FIELDS_BASE


####################################################################################
# (2) CARREGAMENTO / CRIACAO / EDICAO / REMOCAO / PERSISTENCIA
####################################################################################

def test_update_quantity_fields_creates_new_rule():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session, "processo_teste_a", [dict(BASE_RULE)]
    )
    session.close()

    assert ok is True
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_quantity_fields"] == [
        {
            "key": "qty_filhos",
            "label": "Filhos",
            "quantity_field_key": "custom_quantidade_filhos",
            "repeated_field_keys": ["custom_nome_filho", "custom_data_nascimento_filho"],
            "header_key": "",
            "max_items": 1,
            "item_label": "Item",
        }
    ]


def test_update_quantity_fields_edit_preserves_stable_key_when_key_resupplied():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    update_sidebar_menu_process_quantity_fields_v1(
        session, "processo_teste_a", [dict(BASE_RULE)]
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    original_key = config["process_quantity_fields"][0]["key"]

    session = SessionLocal()
    update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [{**BASE_RULE, "key": original_key, "label": "Filhos e enteados"}],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_quantity_fields"][0]["key"] == original_key
    assert config["process_quantity_fields"][0]["label"] == "Filhos e enteados"


def test_update_quantity_fields_removal_via_empty_list_clears_all_rules():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        process_quantity_fields=[
            {
                "key": "qty_filhos",
                "label": "Filhos",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_nome_filho"],
                "header_key": "",
                "max_items": 5,
                "item_label": "Item",
            }
        ],
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(session, "processo_teste_a", [])
    session.close()

    assert ok is True
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_quantity_fields"] == []


def test_update_quantity_fields_removal_via_omitting_row_drops_it():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            dict(BASE_RULE),
            {
                "label": "Outra regra",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_outro_texto"],
            },
        ],
    )
    session.close()
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert len(config["process_quantity_fields"]) == 2

    session = SessionLocal()
    update_sidebar_menu_process_quantity_fields_v1(
        session, "processo_teste_a", [dict(BASE_RULE)]
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert [item["key"] for item in config["process_quantity_fields"]] == ["qty_filhos"]


####################################################################################
# (3) MULTIPLAS REGRAS / MULTIPLOS CAMPOS DE QUANTIDADE NO MESMO PROCESSO
####################################################################################

def test_update_quantity_fields_supports_multiple_rules_same_process():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            dict(BASE_RULE),
            {
                "label": "Outra regra",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_outro_texto"],
            },
        ],
    )
    session.close()

    assert ok is True
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert [item["key"] for item in config["process_quantity_fields"]] == [
        "qty_filhos",
        "qty_outra regra",
    ]


def test_update_quantity_fields_allows_duplicate_quantity_field_key_across_rules():
    """
    Comportamento existente, nao corrigido: nao ha verificacao de unicidade de
    quantity_field_key entre regras distintas -- duas regras diferentes podem
    apontar para o mesmo campo numerico de origem.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            {
                "label": "Regra A",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_nome_filho"],
            },
            {
                "label": "Regra B",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_outro_texto"],
            },
        ],
    )
    session.close()

    assert ok is True
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert [item["quantity_field_key"] for item in config["process_quantity_fields"]] == [
        "custom_quantidade_filhos",
        "custom_quantidade_filhos",
    ]


def test_normalize_quantity_fields_auto_generated_rule_key_is_not_sanitized_like_other_keys():
    """
    Comportamento estranho documentado (nao corrigido, regra 10): a rule_key
    auto-gerada usa _normalize_menu_key (apenas strip + lower), NAO
    _normalize_custom_field_key (que sanitiza para [a-z0-9_] e prefixa "custom_").
    Por isso, uma chave auto-gerada pode conter espacos e outros caracteres que
    quantity_field_key/repeated_field_keys/header_key jamais teriam.
    """
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "label": "Filhos & Enteados!",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_nome_filho"],
            }
        ]
    )
    assert normalized[0]["key"] == "qty_filhos & enteados!"


####################################################################################
# (4) DEDUPLICACAO / DESCARTE DE LINHAS VAZIAS OU INCOMPLETAS (na normalizacao)
####################################################################################

def test_normalize_quantity_fields_dedup_same_label_without_explicit_key():
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "label": "Filhos",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_nome_filho"],
            },
            {
                "label": "Filhos",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_outro_texto"],
            },
        ]
    )
    assert len(normalized) == 1
    assert normalized[0]["repeated_field_keys"] == ["custom_nome_filho"]


def test_normalize_quantity_fields_discards_row_without_label():
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "label": "",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_nome_filho"],
            }
        ]
    )
    assert normalized == []


def test_normalize_quantity_fields_discards_row_without_quantity_field_key():
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "label": "Filhos",
                "repeated_field_keys": ["custom_nome_filho"],
            }
        ]
    )
    assert normalized == []


def test_normalize_quantity_fields_discards_row_without_repeated_field_keys():
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "label": "Filhos",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": [],
            }
        ]
    )
    assert normalized == []


def test_normalize_quantity_fields_deduplicates_repeated_field_keys_within_same_rule():
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "label": "Filhos",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_nome_filho", "custom_nome_filho"],
            }
        ]
    )
    assert normalized[0]["repeated_field_keys"] == ["custom_nome_filho"]


####################################################################################
# (5) VALIDACOES DE CHAVES CONTRA CAMPOS ADICIONAIS (regra da aba)
####################################################################################

def test_update_quantity_fields_row_without_label_is_silently_dropped_not_rejected():
    """
    Comportamento estranho documentado (nao corrigido, regra 10): a validacao
    "Informe o nome da regra na linha ..." em update_sidebar_menu_process_quantity_fields_v1
    (menu_settings.py) e' CODIGO MORTO/INALCANCAVEL. raw_fields passa primeiro por
    normalize_menu_process_quantity_fields, que ja descarta silenciosamente qualquer
    linha sem rule_label (linha "if not rule_label ... continue") ANTES de chegar ao
    loop de validacao. Por isso, submeter uma linha sem label nao produz erro -- a
    linha e' simplesmente omitida do resultado, e a gravacao e' bem sucedida.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [{"key": "qty_x", "label": "", "quantity_field_key": "custom_quantidade_filhos", "repeated_field_keys": ["custom_nome_filho"]}],
    )
    session.close()
    assert ok is True
    assert error == ""
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_quantity_fields"] == []


def test_update_quantity_fields_duplicate_explicit_rule_key_silently_keeps_first_row():
    """
    Comportamento estranho documentado (nao corrigido, regra 10): a validacao
    "Ja existe uma regra com a chave ..." em update_sidebar_menu_process_quantity_fields_v1
    tambem e' CODIGO MORTO/INALCANCAVEL para chaves explicitas duplicadas. A
    deduplicacao por rule_key ja acontece dentro de normalize_menu_process_quantity_fields
    (via "seen_rule_keys"), que descarta silenciosamente a segunda linha com a mesma
    chave ANTES do loop de validacao em update_sidebar_menu_process_quantity_fields_v1.
    Resultado: nenhum erro e' devolvido -- apenas a primeira regra e' persistida.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            {"key": "qty_dup", "label": "Regra A", "quantity_field_key": "custom_quantidade_filhos", "repeated_field_keys": ["custom_nome_filho"]},
            {"key": "qty_dup", "label": "Regra B", "quantity_field_key": "custom_quantidade_filhos", "repeated_field_keys": ["custom_outro_texto"]},
        ],
    )
    session.close()
    assert ok is True
    assert error == ""
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert len(config["process_quantity_fields"]) == 1
    assert config["process_quantity_fields"][0]["label"] == "Regra a"
    assert config["process_quantity_fields"][0]["repeated_field_keys"] == ["custom_nome_filho"]


def test_normalize_and_update_have_dead_validation_branches_for_label_key_and_repeated_keys():
    """
    Documenta explicitamente, via inspecao de codigo, que as ramificacoes de erro
    "Informe o nome da regra", "Regra invalida" e "Selecione os campos repetidos"
    dentro de update_sidebar_menu_process_quantity_fields_v1 sao inalcancaveis a
    partir do fluxo real de update, porque normalize_menu_process_quantity_fields
    (chamada em primeiro lugar) ja garante rule_label, quantity_field_key,
    repeated_field_keys nao vazios e rule_key sempre preenchido (com fallback
    "qty_regra_N") em qualquer linha que sobreviva ao normalize.
    """
    import inspect

    from appgenesis.menu_settings import update_sidebar_menu_process_quantity_fields_v1 as fn

    source = inspect.getsource(fn)
    assert "normalized_fields = normalize_menu_process_quantity_fields(raw_fields)" in source
    assert 'f"Informe o nome da regra na linha {row_index + 1}."' in source
    assert 'f"Regra inválida na linha {row_index + 1}."' in source
    assert "f\"Selecione os campos repetidos da regra '{rule_label}'.\"" in source


def test_update_quantity_fields_quantity_field_must_exist_in_additional_fields():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            {
                "label": "Filhos",
                "quantity_field_key": "custom_campo_inexistente",
                "repeated_field_keys": ["custom_nome_filho"],
            }
        ],
    )
    session.close()
    assert ok is False
    assert "deve existir em Campos adicionais" in error


def test_update_quantity_fields_quantity_field_must_be_number_type():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            {
                "label": "Filhos",
                "quantity_field_key": "custom_nome_filho",
                "repeated_field_keys": ["custom_outro_texto"],
            }
        ],
    )
    session.close()
    assert ok is False
    assert "deve ser numérico" in error


def test_update_quantity_fields_repeated_field_must_exist_in_additional_fields():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            {
                "label": "Filhos",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_campo_inexistente"],
            }
        ],
    )
    session.close()
    assert ok is False
    assert "devem existir em Campos adicionais" in error


def test_update_quantity_fields_repeated_field_cannot_be_header():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            {
                "label": "Filhos",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_dados"],
            }
        ],
    )
    session.close()
    assert ok is False
    assert "não pode repetir cabeçalhos" in error


def test_update_quantity_fields_repeated_field_cannot_equal_quantity_field():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            {
                "label": "Filhos",
                "quantity_field_key": "custom_quantidade_filhos",
                "repeated_field_keys": ["custom_quantidade_filhos"],
            }
        ],
    )
    session.close()
    assert ok is False
    assert "não pode repetir o próprio campo de quantidade" in error


def test_update_quantity_fields_header_key_must_exist_among_headers():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [
            {
                **BASE_RULE,
                "header_key": "custom_header_inexistente",
            }
        ],
    )
    session.close()
    assert ok is False
    assert "cabeçalho da regra" in error


def test_update_quantity_fields_valid_header_key_is_persisted():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_teste_a")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session,
        "processo_teste_a",
        [{**BASE_RULE, "header_key": "custom_dados"}],
    )
    session.close()
    assert ok is True
    config, _ = _load_config(SessionLocal, "processo_teste_a")
    assert config["process_quantity_fields"][0]["header_key"] == "custom_dados"


####################################################################################
# (6) PROTEGIDOS / MENU INEXISTENTE
####################################################################################

def test_update_quantity_fields_protected_menu_key_home_is_blocked():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="home")

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session, "home", [dict(BASE_RULE)]
    )
    session.close()
    assert ok is False
    assert error == "Este processo não permite Campos Quantidade."
    config, _ = _load_config(SessionLocal, "home")
    assert "process_quantity_fields" not in config


def test_update_quantity_fields_menu_not_found_returns_error():
    SessionLocal = _build_session_factory()

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_quantity_fields_v1(
        session, "processo_inexistente", [dict(BASE_RULE)]
    )
    session.close()
    assert ok is False
    assert error == "Menu não encontrado."


####################################################################################
# (7) VALIDACOES NUMERICAS DE max_items (unico valor numerico real desta aba)
####################################################################################

def test_normalize_quantity_fields_max_items_integer_is_preserved():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "7"}]
    )
    assert normalized[0]["max_items"] == 7


def test_normalize_quantity_fields_max_items_decimal_string_falls_back_to_one():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "10.5"}]
    )
    assert normalized[0]["max_items"] == 1


def test_normalize_quantity_fields_max_items_zero_string_is_clamped_to_one():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "0"}]
    )
    assert normalized[0]["max_items"] == 1


def test_normalize_quantity_fields_max_items_negative_is_clamped_to_one():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "-5"}]
    )
    assert normalized[0]["max_items"] == 1


def test_normalize_quantity_fields_max_items_above_fifty_is_clamped_to_fifty():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "9999999999999999"}]
    )
    assert normalized[0]["max_items"] == 50


def test_normalize_quantity_fields_max_items_empty_string_falls_back_to_one():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": ""}]
    )
    assert normalized[0]["max_items"] == 1


def test_normalize_quantity_fields_max_items_whitespace_only_falls_back_to_one():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "   "}]
    )
    assert normalized[0]["max_items"] == 1


def test_normalize_quantity_fields_max_items_non_numeric_string_falls_back_to_one():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "abc"}]
    )
    assert normalized[0]["max_items"] == 1


def test_normalize_quantity_fields_max_items_surrounding_whitespace_is_stripped():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "  15  "}]
    )
    assert normalized[0]["max_items"] == 15


def test_normalize_quantity_fields_max_items_missing_defaults_to_one():
    normalized = normalize_menu_process_quantity_fields([dict(BASE_RULE)])
    assert normalized[0]["max_items"] == 1


def test_normalize_quantity_fields_max_items_raw_int_zero_falsy_trap_still_clamps_to_one():
    """
    Comportamento estranho documentado (nao corrigido): _normalize_process_quantity_max_items_v1
    usa "raw_value or ''", uma armadilha de zero falsy. Um max_items literal int(0) cai no
    mesmo ramo que string vazia, mas o resultado final observavel e' identico ao de "0"
    (string): ambos colapsam para 1 devido ao clamp max(1, ...).
    """
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": 0}]
    )
    assert normalized[0]["max_items"] == 1


def test_normalize_quantity_fields_max_items_boundary_value_one_is_preserved():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "1"}]
    )
    assert normalized[0]["max_items"] == 1


def test_normalize_quantity_fields_max_items_boundary_value_fifty_is_preserved():
    normalized = normalize_menu_process_quantity_fields(
        [{**BASE_RULE, "max_items": "50"}]
    )
    assert normalized[0]["max_items"] == 50


####################################################################################
# (8) COMPATIBILIDADE COM DADOS ANTIGOS (aliases de nomes de campo)
####################################################################################

def test_normalize_quantity_fields_accepts_camel_case_legacy_aliases():
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "rule_label": "Filhos",
                "quantityFieldKey": "custom_quantidade_filhos",
                "repeatedFieldKeys": ["custom_nome_filho"],
                "headerKey": "custom_dados",
                "maxItems": "3",
                "itemLabel": "Filho",
            }
        ]
    )
    assert normalized == [
        {
            "key": "qty_filhos",
            "label": "Filhos",
            "quantity_field_key": "custom_quantidade_filhos",
            "repeated_field_keys": ["custom_nome_filho"],
            "header_key": "custom_dados",
            "max_items": 3,
            "item_label": "Filho",
        }
    ]


def test_normalize_quantity_fields_accepts_csv_string_for_repeated_field_keys():
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "label": "Filhos",
                "field_key": "custom_quantidade_filhos",
                "field_keys": "custom_nome_filho, custom_data_nascimento_filho",
            }
        ]
    )
    assert normalized[0]["repeated_field_keys"] == [
        "custom_nome_filho",
        "custom_data_nascimento_filho",
    ]


def test_normalize_quantity_fields_accepts_json_string_for_repeated_field_keys():
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                **BASE_RULE,
                "repeated_field_keys": json.dumps(["custom_nome_filho"]),
            }
        ]
    )
    assert normalized[0]["repeated_field_keys"] == ["custom_nome_filho"]


####################################################################################
# (9) COMPORTAMENTO QUANDO O CAMPO ASSOCIADO JA NAO EXISTE (documentado, nao corrigido)
####################################################################################

def test_normalize_quantity_fields_does_not_cross_validate_against_additional_fields_at_read_time():
    """
    Comportamento estranho documentado (nao corrigido, regra 10): normalize_menu_process_quantity_fields
    (usada na leitura, via get_sidebar_menu_settings_v4) nao recebe nem consulta additional_fields --
    uma regra que referencia um campo ja apagado continua a ser devolvida intacta na leitura. A
    validacao contra Campos Adicionais so' acontece na GRAVACAO
    (update_sidebar_menu_process_quantity_fields_v1).
    """
    normalized = normalize_menu_process_quantity_fields(
        [
            {
                "key": "qty_orfa",
                "label": "Regra orfa",
                "quantity_field_key": "custom_campo_ha_muito_apagado",
                "repeated_field_keys": ["custom_outro_campo_apagado"],
            }
        ]
    )
    assert normalized == [
        {
            "key": "qty_orfa",
            "label": "Regra orfa",
            "quantity_field_key": "custom_campo_ha_muito_apagado",
            "repeated_field_keys": ["custom_outro_campo_apagado"],
            "header_key": "",
            "max_items": 1,
            "item_label": "Item",
        }
    ]
