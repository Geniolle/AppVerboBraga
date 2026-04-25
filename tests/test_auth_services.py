from appverbo.services.auth import (
    build_user_invite_token,
    get_signup_country_options,
    hash_password,
    parse_user_invite_token,
    validate_signup_phone_country,
    verify_password,
)


def test_hash_password_and_verify() -> None:
    raw_password = "SenhaForte123!"
    stored_hash = hash_password(raw_password)
    assert stored_hash.startswith("pbkdf2_sha256$")
    assert verify_password(raw_password, stored_hash)
    assert not verify_password("SenhaErrada", stored_hash)


def test_user_invite_token_roundtrip() -> None:
    token = build_user_invite_token(10, "user@example.com", 42)
    payload = parse_user_invite_token(token)
    assert payload is not None
    assert payload["uid"] == 10
    assert payload["email"] == "user@example.com"
    assert payload["entity_id"] == 42


def test_signup_country_options_include_supported_codes() -> None:
    options = get_signup_country_options()

    assert {"value": "PT", "label": "Portugal", "calling_code": "+351", "placeholder": "+351 910 000 000"} in options
    assert {"value": "BR", "label": "Brasil", "calling_code": "+55", "placeholder": "+55 11 99999-9999"} in options


def test_validate_signup_phone_country_accepts_matching_calling_code() -> None:
    assert validate_signup_phone_country("PT", "+351 912 345 678") == ""
    assert validate_signup_phone_country("BR", "+55 11 99999-9999") == ""


def test_validate_signup_phone_country_rejects_wrong_calling_code() -> None:
    assert validate_signup_phone_country("PT", "+55 11 99999-9999") == "Telefone inválido para Portugal. Use o código +351."
    assert validate_signup_phone_country("BR", "+351 912 345 678") == "Telefone inválido para Brasil. Use o código +55."
