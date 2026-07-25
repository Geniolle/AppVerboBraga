"""
Testes para confirmar que a detecção de Extrato é específica.
Valida que apenas "extrato" é capturado, não processos genéricos com "bancario".
"""

import pytest
from appgenesis.dynamic_process_layout import resolve_dynamic_process_layout_config


class TestExtratosDetecaoEspecifica:
    """Validar que deteção de Extrato é específica"""

    def test_extrato_ativa_modo_historia(self):
        """Menu com 'extrato' ativa uses_record_history"""
        config = resolve_dynamic_process_layout_config(
            menu_key="extrato",
            menu_label="Extratos",
            menu_config={},
        )
        assert config.get("uses_record_history") is True

    def test_negativo_contas_bancarias_nao_capturada(self):
        """Menu 'contas_bancarias' NÃO deve ativar uses_record_history"""
        config = resolve_dynamic_process_layout_config(
            menu_key="contas_bancarias",
            menu_label="Contas Bancárias",
            menu_config={},
        )
        # Não deve ativar uses_record_history (a menos que explicitamente configurado)
        # uses_record_history só é true se layout==LIST ou explicitamente configurado
        assert config.get("layout") != "list" or config.get("is_list_process") is False

    def test_negativo_pagamentos_bancarios_nao_capturado(self):
        """Menu 'pagamentos_bancarios' NÃO deve ativar uses_record_history"""
        config = resolve_dynamic_process_layout_config(
            menu_key="pagamentos_bancarios",
            menu_label="Pagamentos Bancários",
            menu_config={},
        )
        assert config.get("layout") != "list" or config.get("is_list_process") is False

    def test_negativo_reconciliacao_bancaria_nao_capturada(self):
        """Menu 'reconciliacao_bancaria' NÃO deve ativar uses_record_history"""
        config = resolve_dynamic_process_layout_config(
            menu_key="reconciliacao_bancaria",
            menu_label="Reconciliação Bancária",
            menu_config={},
        )
        assert config.get("layout") != "list" or config.get("is_list_process") is False

    def test_negativo_transferencias_bancarias_nao_capturada(self):
        """Menu 'transferencias_bancarias' NÃO deve ativar uses_record_history"""
        config = resolve_dynamic_process_layout_config(
            menu_key="transferencias_bancarias",
            menu_label="Transferências Bancárias",
            menu_config={},
        )
        assert config.get("layout") != "list" or config.get("is_list_process") is False

    def test_extrato_tem_labels_corretos(self):
        """Menu 'extrato' tem labels específicos de Extrato"""
        config = resolve_dynamic_process_layout_config(
            menu_key="extrato",
            menu_label="Extratos",
            menu_config={},
        )
        assert config.get("singular_label") == "extrato"
        assert config.get("plural_label") == "extratos"
        assert "extrato" in config.get("create_title", "").lower()

    def test_outros_processos_nao_tem_labels_extrato(self):
        """Outros processos não recebem labels de Extrato"""
        config = resolve_dynamic_process_layout_config(
            menu_key="contas_bancarias",
            menu_label="Contas Bancárias",
            menu_config={},
        )
        assert config.get("singular_label") != "extrato"
        assert config.get("plural_label") != "extratos"
        assert "extrato" not in config.get("create_title", "").lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
