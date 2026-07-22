from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
from appgenesis.domains.meu_perfil.constants import (
    MEU_PERFIL_MENU_KEY_V1,
    MEU_PERFIL_TAB_TARGETS_V1,
)
from appgenesis.services.page import get_page_data
from appgenesis.services.profile import get_user_personal_data, serialize_member_profile_fields


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
    visible_label: str,
    process_sections: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    setting = {
        "key": "meu_perfil",
        "label": "Meu Perfil",
        "is_active": True,
        "is_deleted": False,
        "process_field_options": [
            {"key": section_key, "label": visible_label, "field_type": "header"},
            {"key": field_key, "label": field_label, "field_type": "text"},
            {"key": "nome", "label": "Nome", "field_type": "text"},
        ],
        "process_visible_fields": [field_key],
        "process_visible_field_header_map": {field_key: section_key},
        "process_visible_field_rows": [
            {"field_key": field_key, "header_key": section_key},
        ],
        "process_additional_fields": [
            {"key": section_key, "label": visible_label, "field_type": "header"},
            {"key": field_key, "label": field_label, "field_type": "text"},
        ],
        "process_lists": [],
        "process_quantity_fields": [],
        "menu_config": {},
    }
    if process_sections is not None:
        setting["process_sections"] = process_sections
    return [setting]


def _build_snapshot(page_data: dict[str, object]) -> dict[str, object]:
    meu_perfil_bootstrap = dict(page_data["meu_perfil_bootstrap"])
    return {
        "visible_fields": list(page_data["profile_personal_visible_fields"]),
        "field_labels": dict(page_data["profile_personal_field_labels"]),
        "field_section_map": dict(page_data["profile_personal_field_section_map"]),
        "sections": [section["key"] for section in page_data["profile_personal_sections"]],
        "bootstrap_menu_key": meu_perfil_bootstrap["menuKey"],
        "bootstrap_active_tab": meu_perfil_bootstrap["activeTab"],
        "bootstrap_active_target": meu_perfil_bootstrap["activeTarget"],
        "bootstrap_personal_card_target": meu_perfil_bootstrap["personalCardTarget"],
        "bootstrap_personal_sections": [section["key"] for section in meu_perfil_bootstrap["personalSections"]],
        "bootstrap_visible_fields": list(meu_perfil_bootstrap["visibleFields"]),
        "bootstrap_field_labels": dict(meu_perfil_bootstrap["fieldLabels"]),
        "bootstrap_active_personal_section": meu_perfil_bootstrap["activePersonalSection"],
    }


def test_get_page_data_keeps_meu_perfil_configuration_isolated_by_entity(monkeypatch) -> None:
    SessionLocal = _build_session_factory()
    call_log: list[int | None] = []
    entity_a_id: int | None = None
    entity_b_id: int | None = None

    def fake_get_sidebar_menu_settings(session, active_entity_id=None):
        call_log.append(active_entity_id)
        if active_entity_id == entity_a_id:
            return _build_meu_perfil_settings(
                section_key="custom_dados_ministeriais",
                field_key="custom_campo_entidade_1001",
                field_label="Campo entidade 1001",
                visible_label="Dados ministeriais",
            )
        if active_entity_id == entity_b_id:
            return _build_meu_perfil_settings(
                section_key="custom_dados_academicos",
                field_key="custom_campo_entidade_2002",
                field_label="Campo entidade 2002",
                visible_label="Dados académicos",
            )
        return []

    monkeypatch.setattr("appgenesis.services.page.get_sidebar_menu_settings", fake_get_sidebar_menu_settings)
    monkeypatch.setattr("appgenesis.services.page.get_visible_sidebar_menu_keys", lambda *args, **kwargs: {"meu_perfil"})

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
                    "campo_global": "preservar",
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
        entity_a_id = entity_a.id
        entity_b_id = entity_b.id

        page_1001 = get_page_data(
            session,
            actor_user_id=user.id,
            actor_login_email=user.login_email,
            selected_entity_id=entity_a.id,
        )
        page_2002 = get_page_data(
            session,
            actor_user_id=user.id,
            actor_login_email=user.login_email,
            selected_entity_id=entity_b.id,
        )
        page_1001_again = get_page_data(
            session,
            actor_user_id=user.id,
            actor_login_email=user.login_email,
            selected_entity_id=entity_a.id,
        )

        snapshot_1001 = _build_snapshot(page_1001)
        snapshot_2002 = _build_snapshot(page_2002)
        snapshot_1001_again = _build_snapshot(page_1001_again)

        assert call_log == [entity_a_id, entity_b_id, entity_a_id]
        assert snapshot_1001["bootstrap_menu_key"] == MEU_PERFIL_MENU_KEY_V1
        assert snapshot_2002["bootstrap_menu_key"] == MEU_PERFIL_MENU_KEY_V1
        assert snapshot_1001["bootstrap_active_tab"] == "pessoal"
        assert snapshot_2002["bootstrap_active_tab"] == "pessoal"
        assert snapshot_1001["bootstrap_active_target"] == MEU_PERFIL_TAB_TARGETS_V1["pessoal"]
        assert snapshot_2002["bootstrap_active_target"] == MEU_PERFIL_TAB_TARGETS_V1["pessoal"]
        assert snapshot_1001["bootstrap_personal_card_target"] == MEU_PERFIL_TAB_TARGETS_V1["pessoal"]
        assert snapshot_2002["bootstrap_personal_card_target"] == MEU_PERFIL_TAB_TARGETS_V1["pessoal"]
        assert snapshot_1001["bootstrap_visible_fields"] != snapshot_2002["bootstrap_visible_fields"]
        assert "custom_campo_entidade_1001" in snapshot_1001["visible_fields"]
        assert "custom_campo_entidade_2002" not in snapshot_1001["visible_fields"]
        assert "custom_campo_entidade_2002" in snapshot_2002["visible_fields"]
        assert "custom_campo_entidade_1001" not in snapshot_2002["visible_fields"]
        assert snapshot_1001["field_section_map"]["custom_campo_entidade_1001"] == "custom_dados_ministeriais"
        assert snapshot_2002["field_section_map"]["custom_campo_entidade_2002"] == "custom_dados_academicos"
        assert snapshot_1001["field_labels"]["custom_campo_entidade_1001"] == "Campo entidade 1001"
        assert snapshot_2002["field_labels"]["custom_campo_entidade_2002"] == "Campo entidade 2002"
        assert snapshot_1001["bootstrap_field_labels"]["custom_campo_entidade_1001"] == "Campo entidade 1001"
        assert snapshot_2002["bootstrap_field_labels"]["custom_campo_entidade_2002"] == "Campo entidade 2002"
        assert snapshot_1001_again == snapshot_1001

        member_personal_1001 = get_user_personal_data(session, user.id, selected_entity_id=entity_a.id)
        member_personal_2002 = get_user_personal_data(session, user.id, selected_entity_id=entity_b.id)
        assert member_personal_1001["address"] == member_personal_2002["address"]
        assert member_personal_1001["training_selected"] == member_personal_2002["training_selected"]
        assert member_personal_1001["custom_fields"] == member_personal_2002["custom_fields"]
        assert member_personal_1001["custom_fields"] == {}


def test_get_page_data_includes_quantity_only_profile_section_from_process_sections(monkeypatch) -> None:
    SessionLocal = _build_session_factory()

    def fake_get_sidebar_menu_settings(session, active_entity_id=None):
        settings = _build_meu_perfil_settings(
            section_key="custom_dados_pessoais",
            field_key="custom_campo_entidade_1001",
            field_label="Campo entidade 1001",
            visible_label="Dados pessoais",
            process_sections=[
                {
                    "key": "custom_dados_pessoais",
                    "label": "custom_dados_pessoais",
                    "field_keys": ["custom_campo_entidade_1001"],
                    "quantity_rule_keys": [],
                },
                {
                    "key": "custom_dados_de_agregados",
                    "label": "custom_dados_de_agregados",
                    "field_keys": [],
                    "quantity_rule_keys": ["qty_agregados"],
                },
            ],
        )
        setting = settings[0]
        setting["process_additional_fields"].extend(
            [
                {"key": "custom_dados_de_agregados", "label": "Dados de agregados", "field_type": "header"},
                {"key": "custom_nome_do_agregado", "label": "Nome do agregado", "field_type": "text"},
                {"key": "custom_quantos_filhos_tens", "label": "Quantos filhos tens?", "field_type": "number"},
            ]
        )
        setting["process_field_options"].extend(
            [
                {"key": "custom_dados_de_agregados", "label": "Dados de agregados", "field_type": "header"},
                {"key": "custom_nome_do_agregado", "label": "Nome do agregado", "field_type": "text"},
                {"key": "custom_quantos_filhos_tens", "label": "Quantos filhos tens?", "field_type": "number"},
            ]
        )
        setting["process_quantity_fields"] = [
            {
                "key": "qty_agregados",
                "label": "Agregados",
                "quantity_field_key": "custom_quantos_filhos_tens",
                "repeated_field_keys": ["custom_nome_do_agregado"],
                "header_key": "custom_dados_de_agregados",
                "max_items": 10,
                "item_label": "Agregado",
            }
        ]
        return settings

    monkeypatch.setattr("appgenesis.services.page.get_sidebar_menu_settings", fake_get_sidebar_menu_settings)
    monkeypatch.setattr("appgenesis.services.page.get_visible_sidebar_menu_keys", lambda *args, **kwargs: {"meu_perfil"})

    with SessionLocal() as session:
        entity = Entity(entity_number=1001, name="Entidade 1001", is_active=True)
        member = Member(
            full_name="Utilizador Teste",
            primary_phone="912000111",
            email="utilizador.teste@example.com",
            member_status=MemberStatus.ACTIVE.value,
            profile_custom_fields=serialize_member_profile_fields({}),
        )
        session.add_all([entity, member])
        session.flush()
        user = User(
            member_id=member.id,
            login_email=member.email,
            password_hash="hash",
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="default",
        )
        session.add(user)
        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=entity.id,
                status=MemberEntityStatus.ACTIVE.value,
            )
        )
        session.commit()

        page_data = get_page_data(
            session,
            actor_user_id=user.id,
            actor_login_email=user.login_email,
            selected_entity_id=entity.id,
        )

        assert [section["key"] for section in page_data["profile_personal_sections"]] == [
            "custom_dados_pessoais",
            "custom_dados_de_agregados",
        ]
        assert [section["label"] for section in page_data["profile_personal_sections"]] == [
            "Dados pessoais",
            "Dados de agregados",
        ]


def test_get_page_data_ignores_technical_field_keys_as_meu_perfil_tabs(monkeypatch) -> None:
    SessionLocal = _build_session_factory()

    def fake_get_sidebar_menu_settings(session, active_entity_id=None):
        settings = _build_meu_perfil_settings(
            section_key="custom_dados_pessoais",
            field_key="custom_nome",
            field_label="Nome",
            visible_label="Dados pessoais",
            process_sections=[
                {
                    "key": "custom_dados_pessoais",
                    "label": "custom_dados_pessoais",
                    "field_keys": ["custom_nome"],
                    "quantity_rule_keys": [],
                },
                {
                    "key": "custom_nome_do_conjuge",
                    "label": "custom_nome_do_conjuge",
                    "field_keys": ["custom_nome_do_conjuge"],
                    "quantity_rule_keys": [],
                },
                {
                    "key": "custom_canais_de_comunicacao_instantanea",
                    "label": "custom_canais_de_comunicacao_instantanea",
                    "field_keys": ["custom_canais_de_comunicacao_instantanea"],
                    "quantity_rule_keys": [],
                },
                {
                    "key": "custom_dados_de_agregados",
                    "label": "custom_dados_de_agregados",
                    "field_keys": [],
                    "quantity_rule_keys": ["qty_agregados"],
                },
            ],
        )
        setting = settings[0]
        setting["process_additional_fields"].extend(
            [
                {"key": "custom_dados_de_agregados", "label": "Dados de agregados", "field_type": "header"},
                {"key": "custom_nome_do_agregado", "label": "Nome do agregado", "field_type": "text"},
                {"key": "custom_quantos_filhos_tens", "label": "Quantos filhos tens?", "field_type": "number"},
            ]
        )
        setting["process_field_options"].extend(
            [
                {"key": "custom_dados_de_agregados", "label": "Dados de agregados", "field_type": "header"},
                {"key": "custom_nome_do_agregado", "label": "Nome do agregado", "field_type": "text"},
                {"key": "custom_quantos_filhos_tens", "label": "Quantos filhos tens?", "field_type": "number"},
            ]
        )
        setting["process_quantity_fields"] = [
            {
                "key": "qty_agregados",
                "label": "Agregados",
                "quantity_field_key": "custom_quantos_filhos_tens",
                "repeated_field_keys": ["custom_nome_do_agregado"],
                "header_key": "custom_dados_de_agregados",
                "max_items": 10,
                "item_label": "Agregado",
            }
        ]
        return settings

    monkeypatch.setattr("appgenesis.services.page.get_sidebar_menu_settings", fake_get_sidebar_menu_settings)
    monkeypatch.setattr("appgenesis.services.page.get_visible_sidebar_menu_keys", lambda *args, **kwargs: {"meu_perfil"})

    with SessionLocal() as session:
        entity = Entity(entity_number=2002, name="Entidade 2002", is_active=True)
        member = Member(
            full_name="Utilizador Teste",
            primary_phone="912000111",
            email="utilizador.teste@example.com",
            member_status=MemberStatus.ACTIVE.value,
            profile_custom_fields=serialize_member_profile_fields({}),
        )
        session.add_all([entity, member])
        session.flush()
        user = User(
            member_id=member.id,
            login_email=member.email,
            password_hash="hash",
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="default",
        )
        session.add(user)
        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=entity.id,
                status=MemberEntityStatus.ACTIVE.value,
            )
        )
        session.commit()

        page_data = get_page_data(
            session,
            actor_user_id=user.id,
            actor_login_email=user.login_email,
            selected_entity_id=entity.id,
        )

        assert [section["key"] for section in page_data["profile_personal_sections"]] == [
            "custom_dados_pessoais",
            "custom_dados_de_agregados",
        ]
        assert [section["label"] for section in page_data["profile_personal_sections"]] == [
            "Dados pessoais",
            "Dados de agregados",
        ]
