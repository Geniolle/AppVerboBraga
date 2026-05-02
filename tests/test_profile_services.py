from appverbo.services.profile import (
    is_meu_perfil_builtin_duplicate_field,
    resolve_meu_perfil_builtin_duplicate_field_key,
    parse_profile_custom_fields,
    serialize_profile_custom_fields,
)


def test_custom_fields_serialize_then_parse() -> None:
    raw = {
        "custom_campo_1": "valor 1",
        "custom_campo_2": "valor 2",
        "invalid": "ignored",
    }
    serialized = serialize_profile_custom_fields(raw)
    assert serialized is not None
    parsed = parse_profile_custom_fields(serialized)
    assert parsed == {
        "custom_campo_1": "valor 1",
        "custom_campo_2": "valor 2",
    }


def test_parse_profile_custom_fields_invalid_json() -> None:
    assert parse_profile_custom_fields("{invalid}") == {}


def test_is_meu_perfil_builtin_duplicate_field_detects_native_duplicates() -> None:
    builtin_labels = {
        "nome": "Nome",
        "telefone": "Telefone",
        "email": "Email",
        "pais": "País",
    }

    assert is_meu_perfil_builtin_duplicate_field("custom_nome", "Nome", builtin_labels) is True
    assert is_meu_perfil_builtin_duplicate_field("custom_pais", "País", builtin_labels) is True
    assert is_meu_perfil_builtin_duplicate_field("custom_cidade", "Cidade", builtin_labels) is False


def test_resolve_meu_perfil_builtin_duplicate_field_key_maps_custom_fields() -> None:
    builtin_labels = {
        "nome": "Nome",
        "telefone": "Telefone",
        "email": "Email",
        "pais": "País",
        "data_nascimento": "Data de nascimento",
    }

    assert resolve_meu_perfil_builtin_duplicate_field_key("custom_nome", "Nome", builtin_labels) == "nome"
    assert resolve_meu_perfil_builtin_duplicate_field_key("custom_data_de_nascimento", "Data de nascimento", builtin_labels) == "data_nascimento"
    assert resolve_meu_perfil_builtin_duplicate_field_key("custom_cidade", "Cidade", builtin_labels) == ""
