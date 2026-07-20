from __future__ import annotations

import asyncio
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import FormData

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
from appgenesis.routes.profile import profile_handlers as profile_handlers_module
from appgenesis.routes.profile.profile_handlers import update_personal_profile
from appgenesis.services.profile import parse_member_profile_fields, serialize_member_profile_fields


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


def _build_meu_perfil_settings(
    *,
    section_key: str,
    field_key: str,
    field_label: str,
    section_label: str,
) -> list[dict[str, object]]:
    return [
        {
            "key": "meu_perfil",
            "label": "Meu Perfil",
            "is_active": True,
            "is_deleted": False,
            "process_field_options": [
                {"key": section_key, "label": section_label, "field_type": "header"},
                {"key": field_key, "label": field_label, "field_type": "text"},
            ],
            "process_visible_fields": [field_key],
            "process_visible_field_header_map": {field_key: section_key},
            "process_visible_field_rows": [
                {"field_key": field_key, "header_key": section_key},
            ],
            "process_additional_fields": [
                {"key": section_key, "label": section_label, "field_type": "header"},
                {"key": field_key, "label": field_label, "field_type": "text"},
            ],
            "process_lists": [],
            "process_quantity_fields": [],
            "menu_config": {},
        }
    ]


class DummyRequest:
    def __init__(self, *, user_id: int, entity_id: int, form_data: dict[str, str]) -> None:
        self.session = {"user_id": user_id, "entity_id": entity_id}
        self._form = FormData(form_data)

    async def form(self) -> FormData:
        return self._form


def _build_base_form() -> dict[str, str]:
    return {
        "target": "#perfil-pessoal-card",
        "profile_section": "dados_ministeriais",
        "full_name": "Utilizador Teste",
        "primary_phone": "912000111",
        "login_email": "utilizador.teste@example.com",
        "country": "Portugal",
        "birth_date": "",
        "whatsapp_notice_opt_in": "0",
    }


def test_update_personal_profile_ignores_fields_not_configured_for_active_entity(monkeypatch) -> None:
    SessionLocal = _build_session_factory()
    current_sidebar_settings: list[dict[str, object]] = []

    def fake_get_sidebar_menu_settings(session, active_entity_id=None):
        return current_sidebar_settings

    monkeypatch.setattr(profile_handlers_module, "SessionLocal", SessionLocal)
    monkeypatch.setattr(profile_handlers_module, "get_sidebar_menu_settings", fake_get_sidebar_menu_settings)

    with SessionLocal() as session:
        entity_a = Entity(entity_number=1001, name="Entidade 1001", is_active=True)
        entity_b = Entity(entity_number=2002, name="Entidade 2002", is_active=True)
        member = Member(
            full_name="Utilizador Teste",
            primary_phone="912000111",
            email="utilizador.teste@example.com",
            member_status=MemberStatus.ACTIVE.value,
            profile_custom_fields=serialize_member_profile_fields(
                {
                    "custom_campo_entidade_1001": "valor_original_1001",
                    "custom_campo_entidade_2002": "valor_original_2002",
                    "campo_legado": "preservar",
                }
            ),
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

        current_sidebar_settings = _build_meu_perfil_settings(
            section_key="custom_dados_ministeriais",
            field_key="custom_campo_entidade_1001",
            field_label="Campo entidade 1001",
            section_label="Dados ministeriais",
        )
        request_entity_1001 = DummyRequest(
            user_id=user.id,
            entity_id=entity_a.id,
            form_data={
                **_build_base_form(),
                "custom_field__custom_campo_entidade_1001": "novo_1001",
                "custom_field__custom_campo_entidade_2002": "forjado_1001",
                "custom_field__campo_arbitrario": "invasao",
            },
        )

        response_1001 = asyncio.run(update_personal_profile(request_entity_1001))
        assert response_1001.status_code == 303

        with SessionLocal() as verify_session:
            stored_after_entity_1001 = parse_member_profile_fields(
                verify_session.get(Member, member.id).profile_custom_fields
            )
        assert stored_after_entity_1001["custom_campo_entidade_1001"] == "novo_1001"
        assert stored_after_entity_1001["custom_campo_entidade_2002"] == "valor_original_2002"
        assert stored_after_entity_1001["campo_legado"] == "preservar"
        assert "campo_arbitrario" not in stored_after_entity_1001

        current_sidebar_settings = _build_meu_perfil_settings(
            section_key="custom_dados_academicos",
            field_key="custom_campo_entidade_2002",
            field_label="Campo entidade 2002",
            section_label="Dados académicos",
        )
        request_entity_2002 = DummyRequest(
            user_id=user.id,
            entity_id=entity_b.id,
            form_data={
                **_build_base_form(),
                "custom_field__custom_campo_entidade_1001": "forjado_2002",
                "custom_field__custom_campo_entidade_2002": "novo_2002",
                "custom_field__campo_arbitrario": "invasao_2",
            },
        )

        response_2002 = asyncio.run(update_personal_profile(request_entity_2002))
        assert response_2002.status_code == 303

        with SessionLocal() as verify_session:
            stored_after_entity_2002 = parse_member_profile_fields(
                verify_session.get(Member, member.id).profile_custom_fields
            )
        assert stored_after_entity_2002["custom_campo_entidade_1001"] == "novo_1001"
        assert stored_after_entity_2002["custom_campo_entidade_2002"] == "novo_2002"
        assert stored_after_entity_2002["campo_legado"] == "preservar"
        assert "campo_arbitrario" not in stored_after_entity_2002
