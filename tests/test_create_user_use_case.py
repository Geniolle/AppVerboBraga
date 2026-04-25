from appverbo.use_cases.users.create_user import normalize_create_user_input


def test_normalize_create_user_input_success() -> None:
    payload = normalize_create_user_input(
        full_name="  Joao Silva  ",
        primary_phone=" 912345678 ",
        email="  JOAO@EXAMPLE.COM ",
        profile_id=" 10 ",
        invite_delivery="link",
    )

    assert payload.clean_full_name == "Joao Silva"
    assert payload.clean_primary_phone == "912345678"
    assert payload.clean_email == "joao@example.com"
    assert payload.clean_profile_id == "10"
    assert payload.clean_invite_delivery == "link"
    assert payload.form_data["entity_id"] == ""
    assert payload.form_data["entity_name"] == ""
    assert payload.errors == []


def test_normalize_create_user_input_invalid_delivery_defaults_to_email() -> None:
    payload = normalize_create_user_input(
        full_name="Ana",
        primary_phone="999",
        email="ana@example.com",
        profile_id="",
        invite_delivery="sms",
    )

    assert payload.clean_invite_delivery == "email"


def test_normalize_create_user_input_required_fields() -> None:
    payload = normalize_create_user_input(
        full_name=" ",
        primary_phone=" ",
        email=" ",
        profile_id="",
        invite_delivery="email",
    )

    assert payload.errors == [
        "Nome completo é obrigatório.",
        "Telefone principal é obrigatório.",
        "Email é obrigatório.",
    ]

