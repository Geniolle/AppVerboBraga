"""
Teste de integração: verifica se process_dynamic_layout_map é populado corretamente.
"""

import pytest
from appgenesis.db.session import SessionLocal
from appgenesis.models import User
from appgenesis.services.page import get_page_data


class TestProcessDynamicLayoutIntegration:
    """Validar que process_dynamic_layout_map é retornado e populado"""

    def test_process_dynamic_layout_map_exists(self):
        """get_page_data deve retornar process_dynamic_layout_map no dicionário"""
        session = SessionLocal()
        try:
            page_data = get_page_data(session, actor_user_id=1)

            assert "process_dynamic_layout_map" in page_data, \
                "process_dynamic_layout_map não está em get_page_data()"
            assert isinstance(page_data["process_dynamic_layout_map"], dict), \
                "process_dynamic_layout_map deve ser um dict"
            print(f"\n[OK] process_dynamic_layout_map exists and is a dict")

        finally:
            session.close()

    def test_extrato_has_layout_config(self):
        """Se 'extrato' está em menu_process_history_map, deve estar em process_dynamic_layout_map"""
        session = SessionLocal()
        try:
            # User 1 é admin com acesso a Entity 8, que tem Extratos
            page_data = get_page_data(session, actor_user_id=1)

            history_map = page_data.get("menu_process_history_map", {})
            layout_map = page_data.get("process_dynamic_layout_map", {})

            if "extrato" in history_map:
                assert "extrato" in layout_map, \
                    "extrato deve estar em process_dynamic_layout_map se tem historico"

                config = layout_map["extrato"]
                assert isinstance(config, dict), "config deve ser dict"
                assert "layout" in config, "config deve ter 'layout'"
                assert "uses_record_history" in config, "config deve ter 'uses_record_history'"
                assert "list_columns" in config, "config deve ter 'list_columns'"

                assert config["layout"] == "list", \
                    f"extrato layout deve ser 'list', got {config['layout']}"
                assert config["uses_record_history"] is True, \
                    f"extrato uses_record_history deve ser True"
                assert len(config.get("list_columns", [])) > 0, \
                    "extrato deve ter list_columns"

                print(f"\n[OK] extrato config valid: layout={config['layout']}, "
                      f"uses_record_history={config['uses_record_history']}, "
                      f"columns={len(config.get('list_columns', []))}")

        finally:
            session.close()

    def test_process_dynamic_layout_map_not_empty(self):
        """process_dynamic_layout_map deve ter pelo menos alguns menus"""
        session = SessionLocal()
        try:
            page_data = get_page_data(session, actor_user_id=1)

            layout_map = page_data.get("process_dynamic_layout_map", {})

            assert len(layout_map) > 0, \
                "process_dynamic_layout_map nao pode estar vazio"

            print(f"\n[OK] process_dynamic_layout_map has {len(layout_map)} entries")

        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
