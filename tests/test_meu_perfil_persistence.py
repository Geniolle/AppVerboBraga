import json
from types import SimpleNamespace

from appgenesis.domains.meu_perfil.schemas import AddressProfileFormInput, TrainingProfileFormInput
from appgenesis.domains.meu_perfil.use_cases import (
    execute_update_address_profile,
    execute_update_training_profile,
)
from appgenesis.services.profile import (
    merge_member_profile_fields_v1,
    parse_menu_process_quantity_values,
    serialize_member_profile_fields,
    serialize_menu_process_quantity_values,
)
from appgenesis.routes.profile.profile_handlers import _normalize_submitted_quantity_items_v1


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


def test_quantity_payload_serialization_preserves_item_ids() -> None:
    raw_items = [
        {
            "item_id": "item-a",
            "custom_nome_do_agregado": "Ana",
            "custom_data_nascimento_do_agregado": "2000-01-01",
        },
        {
            "item_id": "item-b",
            "custom_nome_do_agregado": "Bruno",
            "custom_data_nascimento_do_agregado": "2001-02-02",
        },
    ]

    serialized = serialize_menu_process_quantity_values(raw_items)
    assert serialized is not None
    assert json.loads(serialized) == raw_items
    assert parse_menu_process_quantity_values(serialized) == raw_items


def test_partial_quantity_row_requires_all_configured_required_fields() -> None:
    cleaned_items, missing_required_labels = _normalize_submitted_quantity_items_v1(
        [
            {
                "item_id": "item-a",
                "custom_nome_do_agregado": "Ana",
                "custom_data_nascimento_do_agregado": "",
            }
        ],
        ["custom_nome_do_agregado", "custom_data_nascimento_do_agregado"],
        {
            "custom_nome_do_agregado": {
                "label": "Nome do agregado",
                "field_type": "text",
                "is_required": True,
            },
            "custom_data_nascimento_do_agregado": {
                "label": "Data de nascimento do agregado",
                "field_type": "date",
                "is_required": True,
            },
        },
        3,
    )

    assert cleaned_items == []
    assert missing_required_labels == ["Data de nascimento do agregado"]
