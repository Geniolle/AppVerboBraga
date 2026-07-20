from types import SimpleNamespace

from appgenesis.domains.meu_perfil.schemas import AddressProfileFormInput, TrainingProfileFormInput
from appgenesis.domains.meu_perfil.use_cases import (
    execute_update_address_profile,
    execute_update_training_profile,
)
from appgenesis.services.profile import (
    merge_member_profile_fields_v1,
    serialize_member_profile_fields,
)


def test_merge_member_profile_fields_v1_preserves_unrelated_keys_and_replaces_requested_prefixes() -> None:
    merged = merge_member_profile_fields_v1(
        {
            "pessoal": "nome atual",
            "morada": "braga",
            "treinamento": "discipulado",
            "campo_desconhecido": "preservar",
            "custom_nome": "antigo",
            "custom_flag": "1",
            "quantity__meu_perfil__qty_agregados": "antigo",
        },
        {
            "custom_nome": "novo",
            "custom_flag": "",
            "quantity__meu_perfil__qty_agregados": "novo-json",
            "quantity__meu_perfil__qty_extra": "1",
        },
        removed_prefixes=(
            "custom_",
            "quantity__meu_perfil__",
        ),
    )

    assert merged["pessoal"] == "nome atual"
    assert merged["morada"] == "braga"
    assert merged["treinamento"] == "discipulado"
    assert merged["campo_desconhecido"] == "preservar"
    assert merged["custom_nome"] == "novo"
    assert "custom_flag" not in merged
    assert merged["quantity__meu_perfil__qty_agregados"] == "novo-json"
    assert merged["quantity__meu_perfil__qty_extra"] == "1"


def test_execute_update_address_profile_preserves_profile_custom_fields(monkeypatch) -> None:
    member = SimpleNamespace(
        address="Rua antiga",
        city="Porto",
        freguesia="Centro",
        postal_code="4000-000",
        profile_custom_fields=serialize_member_profile_fields(
            {
                "pessoal": "valor",
                "morada": "preservar",
                "treinamento": "preservar",
                "campo_desconhecido": "sim",
            }
        ),
    )
    session = SimpleNamespace(commit=lambda: None, rollback=lambda: None)

    monkeypatch.setattr(
        "appgenesis.domains.meu_perfil.use_cases.find_member_for_user",
        lambda _session, _user_id: member,
    )

    result = execute_update_address_profile(
        session,
        7,
        AddressProfileFormInput(
            address="Rua Nova",
            city="Braga",
            freguesia="São José",
            postal_code="4700-000",
        ),
    )

    assert result.success == "Dados de morada atualizados com sucesso."
    assert member.address == "Rua Nova"
    assert member.city == "Braga"
    assert member.freguesia == "São José"
    assert member.postal_code == "4700-000"
    assert member.profile_custom_fields == serialize_member_profile_fields(
        {
            "pessoal": "valor",
            "morada": "preservar",
            "treinamento": "preservar",
            "campo_desconhecido": "sim",
        }
    )


def test_execute_update_training_profile_preserves_profile_custom_fields(monkeypatch) -> None:
    member = SimpleNamespace(
        training_discipulado_verbo_vida=False,
        training_ebvv=False,
        training_rhema=False,
        training_escola_ministerial=False,
        training_escola_missoes=False,
        training_outros="curso antigo",
        profile_custom_fields=serialize_member_profile_fields(
            {
                "pessoal": "valor",
                "morada": "preservar",
                "treinamento": "preservar",
                "campo_desconhecido": "sim",
            }
        ),
    )
    session = SimpleNamespace(commit=lambda: None, rollback=lambda: None)

    monkeypatch.setattr(
        "appgenesis.domains.meu_perfil.use_cases.find_member_for_user",
        lambda _session, _user_id: member,
    )

    result = execute_update_training_profile(
        session,
        7,
        TrainingProfileFormInput(
            training_discipulado_verbo_vida="1",
            training_ebvv=None,
            training_rhema="1",
            training_escola_ministerial=None,
            training_escola_missoes=None,
            training_outros_enabled="1",
            training_outros="Treino novo",
        ),
    )

    assert result.success == "Dados de treinamento atualizados com sucesso."
    assert member.training_discipulado_verbo_vida is True
    assert member.training_ebvv is False
    assert member.training_rhema is True
    assert member.training_escola_ministerial is False
    assert member.training_escola_missoes is False
    assert member.training_outros == "Treino novo"
    assert member.profile_custom_fields == serialize_member_profile_fields(
        {
            "pessoal": "valor",
            "morada": "preservar",
            "treinamento": "preservar",
            "campo_desconhecido": "sim",
        }
    )
