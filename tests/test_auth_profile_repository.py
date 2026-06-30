from types import SimpleNamespace

from appverbo.admin_subprocesses.registry import AUTHORIZATION_PROFILE_CONFIG
from appverbo.admin_subprocesses.repositories import auth_profile_repository as auth_profile_module
from appverbo.admin_subprocesses.repositories.auth_profile_repository import (
    AUTH_PROFILE_MENU_KEY,
    AUTH_PROFILE_SECTION_KEY,
    AuthorizationProfileAdminRepository,
)
from appverbo.services.profile import (
    build_menu_process_records_storage_key,
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_member_profile_fields,
    serialize_menu_process_records,
)


def _build_auth_profile_sidebar_settings() -> list[dict[str, object]]:
    return [
        {
            "key": "perfil_de_autorizacao",
            "label": "Perfil de autorizacao",
            "is_active": True,
            "is_deleted": False,
            "process_field_options": [
                {"key": "custom_perfil", "label": "Perfil", "field_type": "header"},
                {"key": "custom_perfil_2", "label": "Perfil", "field_type": "list"},
            ],
            "process_visible_field_rows": [
                {"field_key": "custom_perfil_2", "header_key": "custom_perfil"},
            ],
        },
        {
            "key": "sessoes",
            "label": "Estruturas",
            "is_active": True,
            "is_deleted": False,
        },
        {
            "key": "musicas",
            "label": "Musicas",
            "is_active": True,
            "is_deleted": False,
        },
    ]


def test_auth_profile_repository_saves_menu_key_and_current_label(monkeypatch) -> None:
    records_storage_key = build_menu_process_records_storage_key(AUTH_PROFILE_MENU_KEY)
    member = SimpleNamespace(profile_custom_fields=None)
    repo = AuthorizationProfileAdminRepository(AUTHORIZATION_PROFILE_CONFIG)

    def fake_load_record_bundle(self, session, context=None):
        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))
        return member, existing_profile_fields, existing_records, "owner", "Owner"

    monkeypatch.setattr(
        AuthorizationProfileAdminRepository,
        "_load_record_bundle",
        fake_load_record_bundle,
    )
    monkeypatch.setattr(
        auth_profile_module,
        "get_sidebar_menu_settings",
        lambda session: _build_auth_profile_sidebar_settings(),
    )

    save_ok, save_reason, saved_key = repo.save_row(
        object(),
        {
            "dynamic_values": {"custom_perfil_2": "sessoes"},
            "visibility_scope_mode": "owner",
            "status": "ativo",
        },
        context={"entity_number": "1001"},
    )

    assert save_ok is True
    assert save_reason == "saved"
    assert saved_key == "sessoes"

    stored_fields = parse_member_profile_fields(member.profile_custom_fields)
    stored_records = parse_menu_process_records(stored_fields.get(records_storage_key))
    assert len(stored_records) == 1

    stored_values = stored_records[0]["values"]
    assert stored_values["__menu_key"] == "sessoes"
    assert stored_values["custom_perfil_2"] == "sessoes"
    assert stored_values["custom_perfil"] == "Estruturas"
    assert stored_values["custom_nome_do_perfil"] == "Estruturas"
    assert stored_fields["process__perfil_de_autorizacao__custom_perfil"] == "Estruturas"

    rows = repo.list_rows(object())
    assert rows[0]["key"] == "sessoes"
    assert rows[0]["menu_key"] == "sessoes"
    assert rows[0]["label"] == "Estruturas"
    assert rows[0]["values"]["custom_perfil_2"] == "sessoes"


def test_auth_profile_repository_blocks_duplicate_menu_key_from_legacy_label(monkeypatch) -> None:
    records_storage_key = build_menu_process_records_storage_key(AUTH_PROFILE_MENU_KEY)
    member = SimpleNamespace(
        profile_custom_fields=serialize_member_profile_fields(
            {
                records_storage_key: serialize_menu_process_records(
                    [
                        {
                            "record_id": "legacy-1",
                            "created_at": "",
                            "section_key": AUTH_PROFILE_SECTION_KEY,
                            "values": {
                                "custom_perfil": "Estruturas",
                                "custom_nome_do_perfil": "Estruturas",
                                "__estado": "ativo",
                            },
                        }
                    ]
                )
            }
        )
    )
    repo = AuthorizationProfileAdminRepository(AUTHORIZATION_PROFILE_CONFIG)

    def fake_load_record_bundle(self, session, context=None):
        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))
        return member, existing_profile_fields, existing_records, "owner", "Owner"

    monkeypatch.setattr(
        AuthorizationProfileAdminRepository,
        "_load_record_bundle",
        fake_load_record_bundle,
    )
    monkeypatch.setattr(
        auth_profile_module,
        "get_sidebar_menu_settings",
        lambda session: _build_auth_profile_sidebar_settings(),
    )

    save_ok, save_reason, saved_key = repo.save_row(
        object(),
        {
            "dynamic_values": {"custom_perfil_2": "sessoes"},
            "visibility_scope_mode": "owner",
            "status": "ativo",
        },
        context={"entity_number": "1001"},
    )

    assert save_ok is False
    assert save_reason == "duplicate_key"
    assert saved_key == ""

    rows = repo.list_rows(object())
    assert rows[0]["key"] == "sessoes"
    assert rows[0]["label"] == "Estruturas"


def test_auth_profile_repository_delete_row_removes_only_selected_profile(monkeypatch) -> None:
    records_storage_key = build_menu_process_records_storage_key(AUTH_PROFILE_MENU_KEY)
    member = SimpleNamespace(
        profile_custom_fields=serialize_member_profile_fields(
            {
                records_storage_key: serialize_menu_process_records(
                    [
                        {
                            "record_id": "rec-1",
                            "created_at": "",
                            "section_key": AUTH_PROFILE_SECTION_KEY,
                            "values": {
                                "__menu_key": "sessoes",
                                "__key": "sessoes",
                                "custom_perfil_2": "sessoes",
                                "custom_perfil": "Estruturas",
                                "custom_nome_do_perfil": "Estruturas",
                                "__estado": "ativo",
                            },
                        },
                        {
                            "record_id": "rec-2",
                            "created_at": "",
                            "section_key": AUTH_PROFILE_SECTION_KEY,
                            "values": {
                                "__menu_key": "musicas",
                                "__key": "musicas",
                                "custom_perfil_2": "musicas",
                                "custom_perfil": "Musicas",
                                "custom_nome_do_perfil": "Musicas",
                                "__estado": "ativo",
                            },
                        },
                    ]
                ),
                "process__perfil_de_autorizacao__custom_perfil": "Musicas",
            }
        )
    )
    repo = AuthorizationProfileAdminRepository(AUTHORIZATION_PROFILE_CONFIG)

    def fake_load_record_bundle(self, session, context=None):
        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))
        return member, existing_profile_fields, existing_records, "owner", "Owner"

    monkeypatch.setattr(
        AuthorizationProfileAdminRepository,
        "_load_record_bundle",
        fake_load_record_bundle,
    )
    monkeypatch.setattr(
        auth_profile_module,
        "get_sidebar_menu_settings",
        lambda session: _build_auth_profile_sidebar_settings(),
    )

    delete_ok, delete_reason = repo.delete_row(
        object(),
        "musicas",
        context={"user_id": 1},
    )

    assert delete_ok is True
    assert delete_reason == "deleted"

    stored_fields = parse_member_profile_fields(member.profile_custom_fields)
    stored_records = parse_menu_process_records(stored_fields.get(records_storage_key))
    assert len(stored_records) == 1
    assert stored_records[0]["values"]["__menu_key"] == "sessoes"
    assert stored_records[0]["values"]["custom_perfil"] == "Estruturas"
    assert stored_fields["process__perfil_de_autorizacao__custom_perfil"] == "Estruturas"

    rows = repo.list_rows(object())
    assert [row["key"] for row in rows] == ["sessoes"]
    assert [row["label"] for row in rows] == ["Estruturas"]


def test_auth_profile_repository_delete_row_removes_storage_when_last_profile_is_deleted(monkeypatch) -> None:
    records_storage_key = build_menu_process_records_storage_key(AUTH_PROFILE_MENU_KEY)
    member = SimpleNamespace(
        profile_custom_fields=serialize_member_profile_fields(
            {
                records_storage_key: serialize_menu_process_records(
                    [
                        {
                            "record_id": "rec-1",
                            "created_at": "",
                            "section_key": AUTH_PROFILE_SECTION_KEY,
                            "values": {
                                "custom_perfil": "Input Bancario",
                                "custom_nome_do_perfil": "Input Bancario",
                                "__estado": "ativo",
                            },
                        },
                    ]
                ),
                "process__perfil_de_autorizacao__custom_perfil": "Input Bancario",
                "custom_perfil": "Input Bancario",
                "custom_nome_do_perfil": "Input Bancario",
            }
        )
    )
    repo = AuthorizationProfileAdminRepository(AUTHORIZATION_PROFILE_CONFIG)

    def fake_load_record_bundle(self, session, context=None):
        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))
        return member, existing_profile_fields, existing_records, "owner", "Owner"

    monkeypatch.setattr(
        AuthorizationProfileAdminRepository,
        "_load_record_bundle",
        fake_load_record_bundle,
    )
    monkeypatch.setattr(
        auth_profile_module,
        "get_sidebar_menu_settings",
        lambda session: _build_auth_profile_sidebar_settings(),
    )

    delete_ok, delete_reason = repo.delete_row(
        object(),
        "input_bancario",
        context={"user_id": 1},
    )

    assert delete_ok is True
    assert delete_reason == "deleted"

    stored_fields = parse_member_profile_fields(member.profile_custom_fields)
    assert records_storage_key not in stored_fields
    assert "process__perfil_de_autorizacao__custom_perfil" not in stored_fields
    assert "custom_perfil" not in stored_fields
    assert "custom_nome_do_perfil" not in stored_fields


def test_auth_profile_repository_delete_row_returns_safe_error_for_unknown_key(monkeypatch) -> None:
    records_storage_key = build_menu_process_records_storage_key(AUTH_PROFILE_MENU_KEY)
    member = SimpleNamespace(
        profile_custom_fields=serialize_member_profile_fields(
            {
                records_storage_key: serialize_menu_process_records(
                    [
                        {
                            "record_id": "rec-1",
                            "created_at": "",
                            "section_key": AUTH_PROFILE_SECTION_KEY,
                            "values": {
                                "__menu_key": "sessoes",
                                "__key": "sessoes",
                                "custom_perfil_2": "sessoes",
                                "custom_perfil": "Estruturas",
                                "custom_nome_do_perfil": "Estruturas",
                                "__estado": "ativo",
                            },
                        },
                    ]
                ),
            }
        )
    )
    repo = AuthorizationProfileAdminRepository(AUTHORIZATION_PROFILE_CONFIG)

    def fake_load_record_bundle(self, session, context=None):
        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))
        return member, existing_profile_fields, existing_records, "owner", "Owner"

    monkeypatch.setattr(
        AuthorizationProfileAdminRepository,
        "_load_record_bundle",
        fake_load_record_bundle,
    )
    monkeypatch.setattr(
        auth_profile_module,
        "get_sidebar_menu_settings",
        lambda session: _build_auth_profile_sidebar_settings(),
    )

    delete_ok, delete_reason = repo.delete_row(
        object(),
        "inexistente",
        context={"user_id": 1},
    )

    assert delete_ok is False
    assert delete_reason == "delete_key_not_found"

    stored_fields = parse_member_profile_fields(member.profile_custom_fields)
    stored_records = parse_menu_process_records(stored_fields.get(records_storage_key))
    assert len(stored_records) == 1
    assert stored_records[0]["values"]["__menu_key"] == "sessoes"


def test_auth_profile_config_exposes_delete_action() -> None:
    assert AUTHORIZATION_PROFILE_CONFIG.delete_endpoint == "/users/profile/auth-profile-delete"
    assert AUTHORIZATION_PROFILE_CONFIG.action_form_key_field == "auth_profile_key"
    delete_action = next(action for action in AUTHORIZATION_PROFILE_CONFIG.actions if action.key == "delete")
    assert delete_action.visible_when == ("inativo",)
