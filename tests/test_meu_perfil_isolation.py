from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from appgenesis.models import (
    Base,
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
)
from appgenesis.services.permissions import get_user_entity_permissions
from appgenesis.services.page import get_page_data
from appgenesis.services.profile import get_user_personal_data, serialize_member_profile_fields
from appgenesis.services.session import get_current_user, get_entity_context_for_user


def _build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[
            Entity.__table__,
            Member.__table__,
            MemberEntity.__table__,
            User.__table__,
        ],
    )
    return sessionmaker(bind=engine, future=True)


def _build_request(*, user_id: int, entity_id: int | None = None) -> Request:
    session_payload: dict[str, object] = {"user_id": user_id}
    if entity_id is not None:
        session_payload["entity_id"] = entity_id
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/users/new",
            "query_string": b"",
            "headers": [],
            "session": session_payload,
        }
    )


def test_get_entity_context_for_user_rejects_unlinked_or_inactive_entity_for_regular_user() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        linked_entity = Entity(entity_number=1001, name="Entidade Ligada", is_active=True)
        unlinked_entity = Entity(entity_number=1002, name="Entidade Estranha", is_active=True)
        inactive_entity = Entity(entity_number=1003, name="Entidade Inativa", is_active=False)
        member = Member(
            full_name="Utilizador Teste",
            primary_phone="912000111",
            email="utilizador.teste@example.com",
            member_status=MemberStatus.ACTIVE.value,
        )
        session.add_all([linked_entity, unlinked_entity, inactive_entity, member])
        session.flush()
        user = User(
            member_id=member.id,
            login_email=member.email,
            password_hash="hash",
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="default",
        )
        session.add(user)
        session.flush()
        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=linked_entity.id,
                status=MemberEntityStatus.ACTIVE.value,
            )
        )
        session.commit()

        assert get_entity_context_for_user(session, user.id, user.login_email, linked_entity.id) == {
            "id": linked_entity.id,
            "name": "Entidade Ligada",
            "logo_url": "",
        }
        assert get_entity_context_for_user(session, user.id, user.login_email, unlinked_entity.id) is None
        assert get_entity_context_for_user(session, user.id, user.login_email, inactive_entity.id) is None


def test_get_current_user_replaces_unlinked_session_entity_with_linked_active_entity() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        linked_entity = Entity(entity_number=1001, name="Entidade Ligada", is_active=True)
        other_entity = Entity(entity_number=1002, name="Outra Entidade", is_active=True)
        member = Member(
            full_name="Utilizador Teste",
            primary_phone="912000111",
            email="utilizador.teste@example.com",
            member_status=MemberStatus.ACTIVE.value,
        )
        session.add_all([linked_entity, other_entity, member])
        session.flush()
        user = User(
            member_id=member.id,
            login_email=member.email,
            password_hash="hash",
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="default",
        )
        session.add(user)
        session.flush()
        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=linked_entity.id,
                status=MemberEntityStatus.ACTIVE.value,
            )
        )
        session.commit()

        request = _build_request(user_id=user.id, entity_id=other_entity.id)
        current_user = get_current_user(request, session)

        assert current_user == {
            "id": user.id,
            "full_name": "Utilizador Teste",
            "login_email": "utilizador.teste@example.com",
        }
        assert request.session["entity_id"] == linked_entity.id
        assert request.session["entity_name"] == "Entidade Ligada"


def test_get_user_personal_data_uses_requested_active_entity_and_preserves_custom_fields() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        first_entity = Entity(entity_number=1001, name="Primeira Entidade", is_active=True)
        second_entity = Entity(entity_number=1002, name="Segunda Entidade", is_active=True)
        member = Member(
            full_name="Utilizador Teste",
            primary_phone="912000111",
            email="utilizador.teste@example.com",
            address="Rua Antiga",
            city="Porto",
            freguesia="Centro",
            postal_code="4000-000",
            training_discipulado_verbo_vida=True,
            training_outros="Curso base",
            profile_custom_fields=serialize_member_profile_fields(
                {
                    "campo_desconhecido": "preservar",
                    "custom_legacy": "valor legada",
                }
            ),
            member_status=MemberStatus.ACTIVE.value,
        )
        session.add_all([first_entity, second_entity, member])
        session.flush()
        user = User(
            member_id=member.id,
            login_email=member.email,
            password_hash="hash",
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="default",
        )
        session.add(user)
        session.flush()
        session.add_all(
            [
                MemberEntity(
                    member_id=member.id,
                    entity_id=first_entity.id,
                    status=MemberEntityStatus.ACTIVE.value,
                ),
                MemberEntity(
                    member_id=member.id,
                    entity_id=second_entity.id,
                    status=MemberEntityStatus.ACTIVE.value,
                ),
            ]
        )
        session.commit()

        personal_data = get_user_personal_data(session, user.id, selected_entity_id=second_entity.id)

        assert personal_data["primary_entity_name"] == "Segunda Entidade"
        assert personal_data["entities"] == "Primeira Entidade, Segunda Entidade"
        assert personal_data["address"] == "Rua Antiga"
        assert personal_data["training_selected"] == ["DISCIPULADO VERBO DA VIDA", "OUTROS: Curso base"]
        assert personal_data["custom_fields"] == {"custom_legacy": "valor legada"}
        assert "campo_desconhecido" not in personal_data["custom_fields"]


def test_get_user_entity_permissions_keeps_admin_and_owner_paths_separated() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        owner_entity = Entity(entity_number=1000, name="Owner", profile_scope="owner", is_active=True)
        legacy_entity = Entity(entity_number=1001, name="Legado", profile_scope="legado", is_active=True)
        member = Member(
            full_name="Admin Teste",
            primary_phone="912000111",
            email="admin.teste@example.com",
            member_status=MemberStatus.ACTIVE.value,
        )
        session.add_all([owner_entity, legacy_entity, member])
        session.flush()
        user = User(
            member_id=member.id,
            login_email=member.email,
            password_hash="hash",
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="owner",
        )
        session.add(user)
        session.flush()
        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=owner_entity.id,
                status=MemberEntityStatus.ACTIVE.value,
            )
        )
        session.commit()

        permissions = get_user_entity_permissions(session, user.id, user.login_email, None)

        assert permissions["is_admin"] is True
        assert permissions["can_manage_tenant_structure"] is True
        assert permissions["can_manage_all_entities"] is True
        assert permissions["allowed_structure_entity_ids"] == {owner_entity.id, legacy_entity.id}


def test_get_page_data_uses_active_entity_specific_meu_perfil_configuration(monkeypatch) -> None:
    SessionLocal = _build_session_factory()
    call_log: list[int | None] = []
    builder_calls: list[dict[str, object]] = []
    entity_a_id: int | None = None
    entity_b_id: int | None = None

    def _build_sidebar_menu_settings(active_entity_id: int | None) -> list[dict[str, object]]:
        if active_entity_id == entity_a_id:
            return [
                {
                    "key": "meu_perfil",
                    "label": "Meu Perfil",
                    "is_active": True,
                    "is_deleted": False,
                    "process_field_options": [
                        {"key": "custom_secao_a", "label": "Secção A", "field_type": "header"},
                        {"key": "nome", "label": "Nome", "field_type": "text"},
                    ],
                    "process_visible_fields": ["nome"],
                    "process_visible_field_header_map": {"nome": "custom_secao_a"},
                    "process_additional_fields": [
                        {"key": "custom_secao_a", "label": "Secção A", "field_type": "header"},
                    ],
                    "process_visible_field_rows": [
                        {"field_key": "nome", "header_key": "custom_secao_a"},
                    ],
                    "process_lists": [],
                    "process_quantity_fields": [],
                    "menu_config": {},
                }
            ]
        if active_entity_id == entity_b_id:
            return [
                {
                    "key": "meu_perfil",
                    "label": "Meu Perfil",
                    "is_active": True,
                    "is_deleted": False,
                    "process_field_options": [
                        {"key": "custom_secao_b", "label": "Secção B", "field_type": "header"},
                        {"key": "telefone", "label": "Telefone", "field_type": "text"},
                    ],
                    "process_visible_fields": ["telefone"],
                    "process_visible_field_header_map": {"telefone": "custom_secao_b"},
                    "process_additional_fields": [
                        {"key": "custom_secao_b", "label": "Secção B", "field_type": "header"},
                    ],
                    "process_visible_field_rows": [
                        {"field_key": "telefone", "header_key": "custom_secao_b"},
                    ],
                    "process_lists": [],
                    "process_quantity_fields": [],
                    "menu_config": {},
                }
            ]
        return []

    def fake_get_sidebar_menu_settings(session, active_entity_id=None):
        call_log.append(active_entity_id)
        return _build_sidebar_menu_settings(active_entity_id)

    def fake_build_meu_perfil_personal_sections_state_v1(**kwargs):
        builder_calls.append(dict(kwargs))
        visible_fields = list(kwargs.get("profile_personal_visible_fields") or [])
        field_header_map = dict(kwargs.get("profile_personal_field_header_map") or {})
        field_labels = dict(kwargs.get("profile_personal_field_labels") or {})
        first_visible_field = visible_fields[0] if visible_fields else ""
        first_section_key = field_header_map.get(first_visible_field, "") if first_visible_field else ""
        if not first_section_key:
            first_section_key = "default-section"
        return {
            "personalSections": [
                {
                    "key": first_section_key,
                    "label": field_labels.get(first_section_key, ""),
                    "order": 1,
                    "is_visible": True,
                    "is_active": True,
                }
            ],
            "personalFieldSectionMap": field_header_map,
            "activePersonalSection": first_section_key,
            "defaultPersonalSection": first_section_key,
        }

    monkeypatch.setattr("appgenesis.services.page.get_sidebar_menu_settings", fake_get_sidebar_menu_settings)
    monkeypatch.setattr("appgenesis.services.page.get_visible_sidebar_menu_keys", lambda *args, **kwargs: {"meu_perfil"})
    monkeypatch.setattr(
        "appgenesis.services.page.build_meu_perfil_personal_sections_state_v1",
        fake_build_meu_perfil_personal_sections_state_v1,
    )

    with SessionLocal() as session:
        entity_a = Entity(entity_number=1001, name="Entidade A", is_active=True)
        entity_b = Entity(entity_number=2002, name="Entidade B", is_active=True)
        member = Member(
            full_name="Utilizador Teste",
            primary_phone="912000111",
            email="utilizador.teste@example.com",
            member_status=MemberStatus.ACTIVE.value,
            profile_custom_fields=serialize_member_profile_fields({"campo_global": "preservar"}),
        )
        session.add_all([entity_a, entity_b, member])
        session.flush()
        user = User(
            member_id=member.id,
            login_email=member.email,
            password_hash="hash",
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="default",
        )
        session.add(user)
        session.add_all(
            [
                MemberEntity(
                    member_id=member.id,
                    entity_id=entity_a.id,
                    status=MemberEntityStatus.ACTIVE.value,
                ),
                MemberEntity(
                    member_id=member.id,
                    entity_id=entity_b.id,
                    status=MemberEntityStatus.ACTIVE.value,
                ),
            ]
        )
        session.commit()
        entity_a_id = entity_a.id
        entity_b_id = entity_b.id

        page_data_entity_a = get_page_data(
            session,
            actor_user_id=user.id,
            actor_login_email=user.login_email,
            selected_entity_id=entity_a.id,
        )
        page_data_entity_b = get_page_data(
            session,
            actor_user_id=user.id,
            actor_login_email=user.login_email,
            selected_entity_id=entity_b.id,
        )

        assert call_log == [entity_a.id, entity_b.id]
        assert len(builder_calls) == 2
        assert _build_sidebar_menu_settings(entity_a.id) != _build_sidebar_menu_settings(entity_b.id)
        assert _build_sidebar_menu_settings(entity_a.id)[0]["process_visible_fields"] == ["nome"]
        assert _build_sidebar_menu_settings(entity_b.id)[0]["process_visible_fields"] == ["telefone"]
        assert _build_sidebar_menu_settings(entity_a.id)[0]["process_visible_field_header_map"] == {
            "nome": "custom_secao_a"
        }
        assert _build_sidebar_menu_settings(entity_b.id)[0]["process_visible_field_header_map"] == {
            "telefone": "custom_secao_b"
        }
        assert page_data_entity_a["meu_perfil_bootstrap"]["menuKey"] == "meu_perfil"
        assert page_data_entity_b["meu_perfil_bootstrap"]["menuKey"] == "meu_perfil"
