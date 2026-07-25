"""
Testes de pipeline isolados com cleanup automático.
Nenhum dado de teste é deixado no banco após execução.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from appgenesis.db.session import SessionLocal
from appgenesis.models import Member, User, SidebarMenuSetting
from appgenesis.services.profile import (
    build_menu_process_records_storage_key,
    parse_member_profile_fields,
    serialize_member_profile_fields,
    parse_menu_process_records,
    serialize_menu_process_records,
)
from appgenesis.services.page import get_page_data
from appgenesis.dynamic_process_layout import resolve_dynamic_process_layout_config
import json


class TestExtratosPipelineIsolado:
    """Testes de pipeline com cleanup - banco fica limpo após teste"""

    def test_pipeline_criar_armazenar_recuperar_isolado(self):
        """
        Pipeline isolado com cleanup:
        1. Cria novo registro
        2. Recupera via bootstrap
        3. Valida configuracao
        4. Remove o registro (cleanup obrigatorio)
        """
        novo_record_id = str(uuid4().hex)
        session = SessionLocal()

        try:
            # 1. Criar registro de teste
            novo_registro = {
                "record_id": novo_record_id,
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "section_key": "custom_dados_de_extrato",
                "values": {
                    "custom_doc_soma": f"TST_{novo_record_id[:6]}",
                    "custom_descricao": "Teste Pipeline Isolado",
                    "custom_montante": "1000.00",
                    "custom_saldo_contabilistico": "5000.00",
                    "__estado": "ativo",
                }
            }

            member = session.query(Member).filter(Member.id == 1).first()
            profile_fields = parse_member_profile_fields(member.profile_custom_fields)
            records_key = build_menu_process_records_storage_key("extrato")

            existing_records = parse_menu_process_records(profile_fields.get(records_key))
            if not existing_records:
                existing_records = []

            existing_records.insert(0, novo_registro)
            serialized = serialize_menu_process_records(existing_records[:200])
            profile_fields[records_key] = serialized
            member.profile_custom_fields = serialize_member_profile_fields(profile_fields)
            session.commit()

            # 2. Recuperar e validar
            user = session.query(User).filter(User.member_id == member.id).first()
            page_data = get_page_data(session, actor_user_id=user.id)
            history_map = page_data.get("menu_process_history_map", {})

            assert "extrato" in history_map
            registos_recuperados = [
                r for r in history_map["extrato"]
                if r.get("record_id") == novo_record_id
            ]
            assert len(registos_recuperados) == 1

            # 3. Validar configuracao
            extrato_menu = session.query(SidebarMenuSetting).filter(
                SidebarMenuSetting.entity_id == 8,
                SidebarMenuSetting.menu_key == 'extrato'
            ).first()

            menu_config = json.loads(extrato_menu.menu_config) if extrato_menu.menu_config else {}
            config = resolve_dynamic_process_layout_config(
                menu_key='extrato',
                menu_label=extrato_menu.menu_label,
                menu_config=menu_config,
                visible_field_rows=menu_config.get('process_visible_field_rows', []),
                field_options=menu_config.get('additional_fields', []),
            )

            assert config.get("is_list_process") is True
            assert config.get("state_enabled") is True

        finally:
            # 4. Cleanup obrigatorio - remover registro de teste
            session2 = SessionLocal()
            try:
                member = session2.query(Member).filter(Member.id == 1).first()
                profile_fields = parse_member_profile_fields(member.profile_custom_fields)
                records_key = build_menu_process_records_storage_key("extrato")

                existing_records = parse_menu_process_records(profile_fields.get(records_key))
                existing_records = [
                    r for r in existing_records
                    if r.get("record_id") != novo_record_id
                ]

                serialized = serialize_menu_process_records(existing_records[:200])
                profile_fields[records_key] = serialized
                member.profile_custom_fields = serialize_member_profile_fields(profile_fields)
                session2.commit()
            finally:
                session2.close()

            session.close()

    def test_separacao_ativo_inativo(self):
        """
        Validar separacao de status sem deixar dados permanentes
        """
        session = SessionLocal()
        try:
            member = session.query(Member).filter(Member.id == 1).first()
            profile_fields = parse_member_profile_fields(member.profile_custom_fields)
            records_key = build_menu_process_records_storage_key("extrato")

            existing_records = parse_menu_process_records(profile_fields.get(records_key))
            assert existing_records, "Deve haver registos para testar"

            ativos = [
                r for r in existing_records
                if r.get("values", {}).get("__estado") == "ativo"
            ]
            inativos = [
                r for r in existing_records
                if r.get("values", {}).get("__estado") == "inativo"
            ]

            assert len(ativos) > 0, "Deve haver registos ativos"

            extrato_menu = session.query(SidebarMenuSetting).filter(
                SidebarMenuSetting.entity_id == 8,
                SidebarMenuSetting.menu_key == 'extrato'
            ).first()

            menu_config = json.loads(extrato_menu.menu_config) if extrato_menu.menu_config else {}
            config = resolve_dynamic_process_layout_config(
                menu_key='extrato',
                menu_label=extrato_menu.menu_label,
                menu_config=menu_config,
                visible_field_rows=menu_config.get('process_visible_field_rows', []),
                field_options=menu_config.get('additional_fields', []),
            )

            active_title = config.get("active_title")
            inactive_title = config.get("inactive_title")

            assert "Extratos ativos" in active_title
            assert "Extratos inativos" in inactive_title

        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
