#!/usr/bin/env python3
"""Debug visual da extração de colunas."""

import yaml
from pathlib import Path

print("\n" + "="*120)
print("DEBUG: VISUALIZAÇÃO DA EXTRAÇÃO DE COLUNAS")
print("="*120 + "\n")

# Carregar config
with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

columns = cfg["table"]["columns"]

print("CONFIGURAÇÃO ATUAL (config.yaml):")
print("-" * 120)
for name, bounds in columns.items():
    print(f"  {name:<20} : [{bounds[0]:.2f}, {bounds[1]:.2f}]  ({(bounds[1]-bounds[0]):.1%})")

print("\n" + "="*120)
print("ANÁLISE DO PROBLEMA")
print("="*120 + "\n")

print("""
OBSERVAÇÃO CRÍTICA:
───────────────────
Os dados de DÉBITO estão SEMPRE uma linha atrasados.

HIPÓTESES:

1. ❌ Merge de descrições (JÁ DESCARTADO)
   → Já removemos o código que copiava campos
   → Problema persiste mesmo assim

2. ⚠️  EXTRAÇÃO DE COLUNAS (SUSPEITA ATUAL)
   → Os limites de colunas podem estar sobrepostos
   → Uma coluna pode estar capturando dados de outra
   → Split_columns() pode estar selecionando a palavra errada

3. ⚠️  ORDEM DE PROCESSAMENTO
   → Os movimentos podem estar sendo processados fora de ordem
   → A linha 5 (cabeçalho vazio) pode estar desalinhando contadores

PRÓXIMAS AÇÕES:
───────────────

1. Gerar debug da extração COMPLETA (com índices e valores)
2. Verificar se as colunas estão realmente sobrepostas
3. Validar se todas as 18 linhas OCR estão sendo processadas corretamente
4. Comparar posição X de cada palavra com os limites de coluna

SOLUÇÃO:
─────────

O problema pode estar nos limites de coluna. Se Débito EUR captura da coluna Crédito EUR,
teríamos exatamente este padrão de desalinhamento!

Preciso:
1. Extrair as posições X exatas de cada palavra da imagem OCR
2. Comparar com os limites de coluna
3. Ajustar limites se necessário
""")

print("="*120 + "\n")
