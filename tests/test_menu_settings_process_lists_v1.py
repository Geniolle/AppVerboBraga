from appgenesis.menu_settings import normalize_menu_process_lists_v3, normalize_menu_process_lists_v4


def test_manual_default_and_items_dedup():
    raw = [
        {
            "key": "perfil",
            "label": "Perfil",
            "items_csv": "Ativo, Inativo, Ativo, Pendente",
        }
    ]

    normalized = normalize_menu_process_lists_v3(raw)
    assert len(normalized) == 1
    item = normalized[0]
    assert item["key"] == "list_perfil"
    assert item["label"] == "Perfil"
    assert item["field_type"] == "manual"
    assert item["items"] == ["Ativo", "Inativo", "Pendente"]
    assert item["items_csv"] == "Ativo, Inativo, Pendente"


def test_automatic_allows_empty_items():
    raw = [{"key": "perfil", "label": "Perfil", "field_type": "automatic"}]
    normalized = normalize_menu_process_lists_v3(raw)
    assert len(normalized) == 1
    item = normalized[0]
    assert item["field_type"] == "automatic"
    assert item["items"] == []
    assert item["items_csv"] == ""


def test_invalid_field_type_normalized_to_manual():
    raw = [{"key": "x", "label": "X", "field_type": "unknown", "items": ["A"]}]
    normalized = normalize_menu_process_lists_v3(raw)
    assert normalized[0]["field_type"] == "manual"
    assert normalized[0]["items"] == ["A"]


def test_existing_without_field_type_assumed_manual():
    raw = [{"key": "k1", "label": "K1", "items": ["One"]}]
    normalized = normalize_menu_process_lists_v3(raw)
    assert normalized[0]["field_type"] == "manual"
    assert normalized[0]["items"] == ["One"]


def test_automatic_source_subprocess_is_preserved_in_v4():
    raw = [
        {
            "key": "auto",
            "label": "Auto",
            "field_type": "automatic",
            "source_menu_key": "perfil_de_autorizacao",
            "source_subprocess_key": "perfis",
            "source_session_key": "sistema",
        }
    ]

    normalized = normalize_menu_process_lists_v4(raw)
    assert normalized[0]["source_menu_key"] == "perfil_de_autorizacao"
    assert normalized[0]["source_subprocess_key"] == "perfis"
    assert normalized[0]["source_session_key"] == "sistema"
    assert normalized[0]["source_sidebar_section_key"] == "sistema"
    assert normalized[0]["items"] == []
