"""
Teste de isolamento multi-tenant para Extratos.
Valida que usuarios sem entidade nao veem dados de outras entidades.
"""

import pytest
from appgenesis.db.session import SessionLocal
from appgenesis.models import User
from appgenesis.services.page import get_page_data


class TestExtratosIsolamentoMultitenant:
    """Validar isolamento multi-tenant"""

    def test_usuario_com_entity_ve_extratos(self):
        """
        User ID 1 (Admin Sistema) tem Entity 8.
        Deve ver os 11 registos de Extratos.
        """
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == 1).first()
            assert user, "User 1 nao encontrado"

            page_data = get_page_data(session, actor_user_id=user.id)
            history_map = page_data.get("menu_process_history_map", {})
            extratos = history_map.get("extrato", [])

            print(f"\n[User com Entity 8] Registos: {len(extratos)}")
            assert len(extratos) == 11, f"User 1 deveria ver 11 registos, recebeu {len(extratos)}"

        finally:
            session.close()

    def test_usuario_sem_entity_nao_ve_extratos(self):
        """
        User ID 76 (admin_tabs_b1de8c) nao tem nenhuma entity.
        Nao deve ver Extratos de nenhuma entity.
        """
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == 76).first()
            if not user:
                pytest.skip("User 76 nao existe para teste")

            page_data = get_page_data(session, actor_user_id=user.id)
            history_map = page_data.get("menu_process_history_map", {})
            extratos = history_map.get("extrato", [])

            print(f"\n[User sem Entity] Registos: {len(extratos)}")
            assert len(extratos) == 0, f"User sem entity nao deveria ver Extratos, recebeu {len(extratos)}"

        finally:
            session.close()

    def test_isolamento_entity_nao_ha_fuga_dados(self):
        """
        Validar que nao ha fuga de dados entre entidades.
        """
        session = SessionLocal()
        try:
            # User 1: Entity 8
            page_data_1 = get_page_data(session, actor_user_id=1)
            history_map_1 = page_data_1.get("menu_process_history_map", {})
            extratos_1 = history_map_1.get("extrato", [])

            # User sem entity
            page_data_76 = get_page_data(session, actor_user_id=76)
            history_map_76 = page_data_76.get("menu_process_history_map", {})
            extratos_76 = history_map_76.get("extrato", [])

            print(f"\n[Isolamento] User 1: {len(extratos_1)} | User 76: {len(extratos_76)}")

            # Nao ha fuga: User sem entity nao ve dados de User com entity
            assert len(extratos_1) > 0, "User 1 deveria ter dados"
            assert len(extratos_76) == 0, "User 76 nao deveria ver dados"

            # Record IDs sao diferentes (nao ha sobreposicao)
            if extratos_76:
                ids_1 = {r.get('record_id') for r in extratos_1}
                ids_76 = {r.get('record_id') for r in extratos_76}
                assert not (ids_1 & ids_76), "IDs se sobrepoem - fuga de dados!"

        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
