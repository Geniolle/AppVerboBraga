from appverbo.services.profile import (
    build_menu_process_quantity_storage_key,
    get_menu_process_quantity_repeated_field_keys,
    is_meu_perfil_builtin_duplicate_field,
    parse_menu_process_quantity_values,
    resolve_meu_perfil_builtin_duplicate_field_key,
    serialize_menu_process_quantity_values,
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


def test_process_quantity_values_serialize_then_parse() -> None:
    raw = [
        {
            "custom_nome_do_agregado": "João",
            "custom_data_nascimento_do_agregado": "2018-04-10",
        },
        {
            "custom_nome_do_agregado": "Maria",
            "custom_data_nascimento_do_agregado": "2020-09-15",
        },
    ]

    serialized = serialize_menu_process_quantity_values(raw)
    assert serialized is not None
    assert parse_menu_process_quantity_values(serialized) == raw


def test_build_menu_process_quantity_storage_key() -> None:
    assert build_menu_process_quantity_storage_key("empresa", "qty_agregados") == "quantity__empresa__qty_agregados"


def test_get_menu_process_quantity_repeated_field_keys() -> None:
    repeated_keys = get_menu_process_quantity_repeated_field_keys(
        [
            {
                "key": "qty_agregados",
                "repeated_field_keys": [
                    "custom_nome_do_agregado",
                    "custom_data_nascimento_do_agregado",
                    "custom_nome_do_agregado",
                ],
            }
        ]
    )

    assert repeated_keys == {
        "custom_nome_do_agregado",
        "custom_data_nascimento_do_agregado",
    }
