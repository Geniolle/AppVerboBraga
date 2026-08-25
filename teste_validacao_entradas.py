#!/usr/bin/env python3
"""
Script de Análise de Validação - Processo Entradas

Simula a validação de registos de DÍZIMOS/OFERTAS contra os 5 critérios
de negócio do processo Entradas.

Uso:
    python teste_validacao_entradas.py
"""

from typing import Optional, Tuple
from datetime import datetime


class EntradaValidator:
    """Validador de entradas para processo Entradas."""

    def __init__(self):
        """Inicializa validador com critérios."""
        self.total_validados = 0
        self.total_validos = 0
        self.total_invalidos = 0
        self.erros_por_tipo = {}

    def validar_entrada(
        self,
        data: str,
        tipo: str,
        doc_soma: str,
        finance: str,
        valor: str,
        numero_linha: int = 0
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida uma entrada contra 5 critérios.

        Args:
            data: Data do movimento (DD/MM/YYYY ou YYYY-MM-DD)
            tipo: Tipo de entrada
            doc_soma: Documento SOMA (deve estar vazio)
            finance: Status FINANCE (deve estar vazio)
            valor: Valor da entrada
            numero_linha: Número da linha (para logging)

        Returns:
            Tupla (is_valid, erro_message)
        """
        self.total_validados += 1

        # Critério 1: DATA
        if not data or not str(data).strip():
            erro = "DATA vazia"
            self._registrar_erro(erro)
            self.total_invalidos += 1
            return False, erro

        # Critério 2: TIPO
        tipos_validos = ["DÍZIMOS/OFERTAS", "DIA VERBO MISSÔES"]
        if tipo not in tipos_validos:
            erro = f"TIPO inválido: {tipo}"
            self._registrar_erro(erro)
            self.total_invalidos += 1
            return False, erro

        # Critério 3: DOC.SOMA (deve estar vazio)
        if doc_soma and str(doc_soma).strip():
            erro = "DOC.SOMA não está vazio"
            self._registrar_erro(erro)
            self.total_invalidos += 1
            return False, erro

        # Critério 4: FINANCE (deve estar vazio)
        if finance and str(finance).strip():
            erro = "FINANCE não está vazio"
            self._registrar_erro(erro)
            self.total_invalidos += 1
            return False, erro

        # Critério 5: VALOR (deve ser > 0 e numérico)
        if not valor or not str(valor).strip():
            erro = "VALOR vazio"
            self._registrar_erro(erro)
            self.total_invalidos += 1
            return False, erro

        try:
            valor_decimal = float(str(valor).replace(",", "."))
            if valor_decimal <= 0:
                erro = f"VALOR <= 0: {valor}"
                self._registrar_erro(erro)
                self.total_invalidos += 1
                return False, erro
        except (ValueError, TypeError):
            erro = f"VALOR inválido: {valor}"
            self._registrar_erro(erro)
            self.total_invalidos += 1
            return False, erro

        # ✅ Todos os critérios atendidos
        self.total_validos += 1
        return True, None

    def _registrar_erro(self, erro: str) -> None:
        """Registra tipo de erro."""
        self.erros_por_tipo[erro] = self.erros_por_tipo.get(erro, 0) + 1

    def gerar_relatorio(self) -> str:
        """Gera relatório de validação."""
        taxa_sucesso = (
            (self.total_validos / self.total_validados * 100)
            if self.total_validados > 0
            else 0
        )

        relatorio = f"""
{'='*80}
RELATÓRIO DE VALIDAÇÃO - PROCESSO ENTRADAS
{'='*80}
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RESUMO GERAL:
  Total analisado:       {self.total_validados}
  [OK] Válidos:          {self.total_validos} ({taxa_sucesso:.1f}%)
  [ERRO] Inválidos:      {self.total_invalidos} ({100-taxa_sucesso:.1f}%)

ERROS ENCONTRADOS:
"""
        if self.erros_por_tipo:
            for erro, count in sorted(
                self.erros_por_tipo.items(), key=lambda x: x[1], reverse=True
            ):
                relatorio += f"  • {erro:<40} {count:>2} ocorrência(s)\n"
        else:
            relatorio += "  Nenhum erro encontrado!\n"

        relatorio += f"{'='*80}\n"
        return relatorio


# Dados de Teste
DADOS_TESTE = [
    {
        "linha": 2,
        "data": "2024-08-15",
        "tipo": "DÍZIMOS/OFERTAS",
        "doc_soma": "",
        "finance": "",
        "valor": "35,50",
        "descricao": "Doação regular",
    },
    {
        "linha": 3,
        "data": "2024-08-16",
        "tipo": "DÍZIMOS/OFERTAS",
        "doc_soma": "",
        "finance": "",
        "valor": "100,00",
        "descricao": "Doação maior",
    },
    {
        "linha": 4,
        "data": "2024-08-17",
        "tipo": "SAÍDA",
        "doc_soma": "",
        "finance": "",
        "valor": "50,00",
        "descricao": "Tipo inválido",
    },
    {
        "linha": 5,
        "data": "2024-08-18",
        "tipo": "DÍZIMOS/OFERTAS",
        "doc_soma": "4606815",
        "finance": "",
        "valor": "75,00",
        "descricao": "Já processado em outro sistema",
    },
    {
        "linha": 6,
        "data": "2024-08-19",
        "tipo": "DÍZIMOS/OFERTAS",
        "doc_soma": "",
        "finance": "Transferido",
        "valor": "25,00",
        "descricao": "Já processado neste ciclo",
    },
    {
        "linha": 7,
        "data": "2024-08-20",
        "tipo": "DÍZIMOS/OFERTAS",
        "doc_soma": "",
        "finance": "",
        "valor": "0",
        "descricao": "Valor zero",
    },
    {
        "linha": 8,
        "data": "",
        "tipo": "DÍZIMOS/OFERTAS",
        "doc_soma": "",
        "finance": "",
        "valor": "45,50",
        "descricao": "Sem data",
    },
    {
        "linha": 9,
        "data": "2024-08-22",
        "tipo": "DIA VERBO MISSÔES",
        "doc_soma": "",
        "finance": "",
        "valor": "60,00",
        "descricao": "Tipo alternativo válido",
    },
    {
        "linha": 10,
        "data": "2024-08-23",
        "tipo": "DÍZIMOS/OFERTAS",
        "doc_soma": "",
        "finance": "",
        "valor": "ABC",
        "descricao": "Valor não-numérico",
    },
    {
        "linha": 11,
        "data": "2024-08-24",
        "tipo": "DÍZIMOS/OFERTAS",
        "doc_soma": "",
        "finance": "",
        "valor": "-15,00",
        "descricao": "Valor negativo",
    },
]


def main():
    """Executa validação de dados de teste."""
    validator = EntradaValidator()

    print("\n" + "="*80)
    print("ANÁLISE DE VALIDAÇÃO - PROCESSO ENTRADAS")
    print("="*80)
    print(f"Data de Análise: {datetime.now().strftime('%d de %B de %Y')}\n")

    # Cabeçalho da tabela
    print(f"{'Linha':<6} {'Data':<12} {'Tipo':<20} {'Valor':<10} {'Status':<10} {'Motivo':<30}")
    print("-"*88)

    linhas_validas = []
    linhas_invalidas = []

    # Validar cada linha
    for dados in DADOS_TESTE:
        is_valid, erro = validator.validar_entrada(
            data=dados["data"],
            tipo=dados["tipo"],
            doc_soma=dados["doc_soma"],
            finance=dados["finance"],
            valor=dados["valor"],
            numero_linha=dados["linha"],
        )

        linha = dados["linha"]
        data = dados["data"] if dados["data"] else "(vazio)"
        tipo = dados["tipo"][:20]
        valor = dados["valor"]
        status = "[OK]" if is_valid else "[ERRO]"
        motivo = erro if erro else "-"

        print(f"{linha:<6} {data:<12} {tipo:<20} {valor:<10} {status:<10} {motivo:<30}")

        if is_valid:
            linhas_validas.append(dados)
        else:
            linhas_invalidas.append(dados)

    # Gerar relatório
    print("\n" + validator.gerar_relatorio())

    # Resumo de linhas válidas
    if linhas_validas:
        print(f"\n[OK] LINHAS VÁLIDAS ({len(linhas_validas)}):")
        print("-"*80)
        for dados in linhas_validas:
            print(f"  • Linha {dados['linha']}: {dados['descricao']}")
            print(f"    Data: {dados['data']} | Tipo: {dados['tipo']} | Valor: {dados['valor']}")
            print()

    # Resumo de linhas inválidas
    if linhas_invalidas:
        print(f"\n[ERRO] LINHAS INVÁLIDAS ({len(linhas_invalidas)}):")
        print("-"*80)
        for dados in linhas_invalidas:
            is_valid, erro = validator.validar_entrada(
                data=dados["data"],
                tipo=dados["tipo"],
                doc_soma=dados["doc_soma"],
                finance=dados["finance"],
                valor=dados["valor"],
            )
            print(f"  • Linha {dados['linha']}: {dados['descricao']}")
            print(f"    Erro: {erro}")
            print()

    # Recomendações
    print("\n[INFO] RECOMENDAÇÕES:")
    print("-"*80)
    print("""
  1. Validar TIPO no formulário de entrada (dropdown com 2 opções)
  2. Validar VALOR como campo numérico com mínimo > 0
  3. Fazer DATA obrigatória (usar date picker)
  4. Limpar DOC.SOMA e FINANCE antes de nova transferência
  5. Alertar usuários sobre registos rejeitados
  6. Implementar re-tentativa automática após correção

Taxa de aceitação esperada: {len(linhas_validas)}/{len(DADOS_TESTE)} = {len(linhas_validas)/len(DADOS_TESTE)*100:.1f}%
    """)


if __name__ == "__main__":
    main()
