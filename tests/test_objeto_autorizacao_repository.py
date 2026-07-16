from types import SimpleNamespace

from appgenesis.admin_subprocesses.registry import OBJETO_AUTORIZACAO_CONFIG
from appgenesis.admin_subprocesses.repositories.objeto_autorizacao_repository import (
    OBJETO_AUTORIZACAO_ENTITY_NUMBER_KEY,
    OBJETO_AUTORIZACAO_STORAGE_KEY,
    ObjetoAutorizacaoAdminRepository,
)
from appgenesis.services.profile import (
    build_menu_process_records_storage_key,
    parse_member_profile_fields,
    parse_menu_process_records,
)


def test_objeto_autorizacao_repository_list_rows_exposes_process_and_authorization_labels(monkeypatch) -> None:
    repo = ObjetoAutorizacaoAdminRepository(OBJETO_AUTORIZACAO_CONFIG)
    records = [
        {
            "record_id": "rec-1",
            "created_at": "2026-06-30 10:00 UTC",
            "section_key": "custom_objeto_de_autorizacao",
            "values": {
                "__key": "extrato",
                "objeto_de_autorizacao": "Extrato",
                "custom_processo": "Extratos bancários",
                "custom_subprocesso": "Todas autorizações",
                "__scope_label": "Default",
                "__estado": "ativo",
            },
        }
    ]

    monkeypatch.setattr(
        ObjetoAutorizacaoAdminRepository,
        "_load_record_bundle",
        lambda self, session, context=None: (None, {}, records, "all", "Default"),
    )

    rows = repo.list_rows(object())

    assert len(rows) == 1
    assert rows[0]["label"] == "Extrato"
    assert rows[0]["process_label"] == "Extratos bancários"
    assert rows[0]["authorization_label"] == "Todas autorizações"
    assert rows[0]["edit_values"]["custom_nome_do_perfil"] == "Extrato"
    assert rows[0]["edit_values"]["custom_processo"] == "Extratos bancários"
    assert rows[0]["edit_values"]["custom_subprocesso"] == "Todas autorizações"


def test_objeto_autorizacao_repository_list_rows_prefers_label_fields_and_supports_legacy_fallbacks(
    monkeypatch,
) -> None:
    repo = ObjetoAutorizacaoAdminRepository(OBJETO_AUTORIZACAO_CONFIG)
    records = [
        {
            "record_id": "rec-1",
            "created_at": "2026-06-30 10:00 UTC",
            "section_key": "custom_objeto_de_autorizacao",
            "values": {
                "__key": "extrato",
                "custom_objeto_label": "Extrato",
                "custom_processo": "extratos_bancarios",
                "processo_label": "Extratos bancários",
                "custom_subprocesso": "todas_autorizacoes",
                "autorizacao_label": "Todas autorizações",
                "__scope_label": "Default",
                "__estado": "ativo",
            },
        },
        {
            "record_id": "rec-2",
            "created_at": "2026-06-30 11:00 UTC",
            "section_key": "custom_objeto_de_autorizacao",
            "values": {
                "__key": "arquivo",
                "objeto_de_autorizacao": "Arquivo",
                "__scope_label": "Owner",
                "__estado": "inativo",
            },
        },
    ]

    monkeypatch.setattr(
        ObjetoAutorizacaoAdminRepository,
        "_load_record_bundle",
        lambda self, session, context=None: (None, {}, records, "owner", "Owner"),
    )

    rows = repo.list_rows(object())

    assert rows[0]["process_label"] == "Extratos bancários"
    assert rows[0]["authorization_label"] == "Todas autorizações"
    assert rows[1]["process_label"] == "-"
    assert rows[1]["authorization_label"] == "-"
    assert rows[0]["edit_values"]["custom_nome_do_perfil"] == "Extrato"
    assert rows[0]["edit_values"]["custom_processo"] == "extratos_bancarios"
    assert rows[0]["edit_values"]["custom_subprocesso"] == "todas_autorizacoes"


def test_objeto_autorizacao_repository_save_row_preserves_existing_dynamic_values(monkeypatch) -> None:
    records_storage_key = build_menu_process_records_storage_key(OBJETO_AUTORIZACAO_STORAGE_KEY)
    member = SimpleNamespace(profile_custom_fields=None)
    repo = ObjetoAutorizacaoAdminRepository(OBJETO_AUTORIZACAO_CONFIG)

    def fake_load_record_bundle(self, session, context=None):
        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))
        return member, existing_profile_fields, existing_records, "all", "Default"

    monkeypatch.setattr(
        ObjetoAutorizacaoAdminRepository,
        "_load_record_bundle",
        fake_load_record_bundle,
    )

    save_ok, save_reason, saved_key = repo.save_row(
        object(),
        {
            "label": "Extrato",
            "visibility_scope_mode": "all",
            "status": "ativo",
            "dynamic_values": {
                "custom_processo": "Extratos bancários",
                "custom_subprocesso": "Todas autorizações",
            },
        },
        context={"entity_number": "1001"},
    )

    assert save_ok is True
    assert save_reason == "saved"
    assert saved_key == "extrato"

    stored_fields = parse_member_profile_fields(member.profile_custom_fields)
    stored_records = parse_menu_process_records(stored_fields.get(records_storage_key))
    assert len(stored_records) == 1
    assert stored_records[0]["values"]["custom_processo"] == "Extratos bancários"
    assert stored_records[0]["values"]["custom_subprocesso"] == "Todas autorizações"


def test_objeto_autorizacao_repository_list_rows_filters_by_entity_number(monkeypatch) -> None:
    repo = ObjetoAutorizacaoAdminRepository(OBJETO_AUTORIZACAO_CONFIG)
    records = [
        {
            "record_id": "rec-entity-1001",
            "created_at": "2026-06-30 10:00 UTC",
            "section_key": "custom_objeto_de_autorizacao",
            "values": {
                "__key": "extrato",
                "objeto_de_autorizacao": "Extrato",
                OBJETO_AUTORIZACAO_ENTITY_NUMBER_KEY: "1001",
                "__scope_label": "Default",
                "__estado": "ativo",
            },
        },
        {
            "record_id": "rec-entity-2002",
            "created_at": "2026-06-30 11:00 UTC",
            "section_key": "custom_objeto_de_autorizacao",
            "values": {
                "__key": "extrato",
                "objeto_de_autorizacao": "Extrato de outra entidade",
                OBJETO_AUTORIZACAO_ENTITY_NUMBER_KEY: "2002",
                "__scope_label": "Default",
                "__estado": "ativo",
            },
        },
        {
            "record_id": "rec-legacy-global",
            "created_at": "2026-06-30 12:00 UTC",
            "section_key": "custom_objeto_de_autorizacao",
            "values": {
                "__key": "arquivo",
                "objeto_de_autorizacao": "Arquivo legado sem entidade",
                "__scope_label": "Default",
                "__estado": "ativo",
            },
        },
    ]

    monkeypatch.setattr(
        ObjetoAutorizacaoAdminRepository,
        "_load_record_bundle",
        lambda self, session, context=None: (None, {}, records, "all", "Default"),
    )

    rows_for_entity_1001 = repo.list_rows(object(), context={"entity_number": "1001"})
    labels = {row["label"] for row in rows_for_entity_1001}

    assert labels == {"Extrato", "Arquivo legado sem entidade"}


def test_objeto_autorizacao_repository_save_row_allows_same_key_across_different_entities(monkeypatch) -> None:
    records_storage_key = build_menu_process_records_storage_key(OBJETO_AUTORIZACAO_STORAGE_KEY)
    member = SimpleNamespace(profile_custom_fields=None)
    repo = ObjetoAutorizacaoAdminRepository(OBJETO_AUTORIZACAO_CONFIG)

    def fake_load_record_bundle(self, session, context=None):
        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))
        return member, existing_profile_fields, existing_records, "all", "Default"

    monkeypatch.setattr(
        ObjetoAutorizacaoAdminRepository,
        "_load_record_bundle",
        fake_load_record_bundle,
    )

    save_ok_entity_1001, save_reason_entity_1001, _ = repo.save_row(
        object(),
        {"label": "Extrato", "visibility_scope_mode": "all", "status": "ativo"},
        context={"entity_number": "1001"},
    )
    assert save_ok_entity_1001 is True
    assert save_reason_entity_1001 == "saved"

    save_ok_entity_2002, save_reason_entity_2002, _ = repo.save_row(
        object(),
        {"label": "Extrato", "visibility_scope_mode": "all", "status": "ativo"},
        context={"entity_number": "2002"},
    )

    assert save_ok_entity_2002 is True
    assert save_reason_entity_2002 == "saved"

    stored_fields = parse_member_profile_fields(member.profile_custom_fields)
    stored_records = parse_menu_process_records(stored_fields.get(records_storage_key))
    assert len(stored_records) == 2
    stored_entity_numbers = {
        record["values"][OBJETO_AUTORIZACAO_ENTITY_NUMBER_KEY] for record in stored_records
    }
    assert stored_entity_numbers == {"1001", "2002"}


def test_objeto_autorizacao_config_columns_include_process_and_authorization_in_order() -> None:
    column_labels = [column.label for column in OBJETO_AUTORIZACAO_CONFIG.columns]

    assert column_labels == [
        "OBJETO",
        "PROCESSO",
        "AUTORIZAÇÃO",
        "SISTEMA",
        "ESTADO",
    ]
