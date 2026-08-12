#!/usr/bin/env python3
"""Debug do agrupamento de linhas OCR com diferentes tolerâncias."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*150)
print("DEBUG: COMO row_tolerance_ratio AFECTA O AGRUPAMENTO DE LINHAS")
print("="*150 + "\n")

print("""
QUESTÃO CRÍTICA:
────────────────
Se mudei row_tolerance_ratio de 0.010 para 0.004, as linhas agrupadas deveriam ter mudado.

MUDARAM?
────────
Antes: linhas com números [11, 12, 14, 15, 16, 17, 18, 20, 21, 22] (10 movimentos)
Depois: linhas com números [11, 12, 14, 15, 16, 17, 18, 20, 21, 22] (10 movimentos) ← IGUAIS!

CONCLUSÃO:
──────────
A mudança de row_tolerance_ratio NÃO afectou o resultado!

Isto significa:
1. As linhas OCR já estavam bem agrupadas (threshold de 0.010 era suficiente)
2. OU o threshold não afecta o agrupamento das linhas que importam
3. OU há um problema diferente não relacionado a row_tolerance_ratio

POSSÍVEL RAIZ DO PROBLEMA:
──────────────────────────

Se row_tolerance não é o problema, então o desalinhamento vem de:

A) split_columns() capturando palavras da coluna errada
   → Isto aconteceria se as posições X das palavras estão incorretas
   → Ou se os limites de coluna estão deslocados

B) Múltiplas transações numa única linha OCR
   → Exemplo: Vision API agrupa "MERCADONA BRAGA" e "1,99" (FACEBK) na mesma linha
   → Então split_columns() captura "1,99" como fazendo parte de MERCADONA

C) Ordem incorreta das palavras na linha
   → Vision API retorna as palavras numa ordem diferente de esquerda para direita
   → split_columns() seleciona as primeiras palavras que match ao intervalo X

TESTE PARA DESCOBRIR QUAL:
──────────────────────────

Se for (A): Todos os valores monetários estariam na coluna errada de forma consistente
Se for (B): Os valores apareceríam em linhas diferentes (Google One sem débito, MERCADONA com o débito do FACEBK)
Se for (C): Os valores apareceriam numa ordem aleatória

OBSERVAÇÃO ACTUAL:
───────────────────
Google One: débito vazio
MERCADONA: débito vazio
FACEBK: débito 1,99 (que é do Google One)

Isto sugere (B): múltiplas transações agrupadas, com valores de uma transação capturados em outra.
""")

print("="*150 + "\n")
