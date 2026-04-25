from appverbo.services.profile import parse_profile_custom_fields, serialize_profile_custom_fields


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

