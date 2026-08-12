#!/usr/bin/env python3
"""Analisar especificamente como split_columns() está capturando débito/crédito."""

import json
from pathlib import Path

print("\n" + "="*150)
print("DEBUG: ANÁLISE DE COMO split_columns() EXTRAI DÉBITO/CRÉDITO")
print("="*150 + "\n")

# Carregar resultado.json
resultado_path = Path("output/resultado.json")
if not resultado_path.exists():
    print(f"❌ {resultado_path} não encontrado")
    exit(1)

with open(resultado_path, encoding="utf-8") as f:
    data = json.load(f)

movimentos = data.get("movimentos", [])
print(f"Movimentos no resultado.json: {len(movimentos)}\n")

print("="*150)
print("ANÁLISE LINHA POR LINHA")
print("="*150 + "\n")

for idx, mov in enumerate(movimentos[:10], 1):
    linha = mov.get("line", "?")
    desc = mov.get("descricao", "")[:30]
    pais = mov.get("pais", "")
    taxa = mov.get("taxa_cambio", "")
    debito = mov.get("debito_eur", "")
    credito = mov.get("credito_eur", "")

    print(f"Linha {linha}: {desc}")
    print(f"  Débito: '{debito}'  |  Crédito: '{credito}'  |  País: '{pais}'  |  Taxa: '{taxa}'")

    # Se débito começa com um número que parece ser do campo anterior
    if debito and ("." in debito or "," in debito):
        print(f"  ⚠️  Débito tem valor numérico: {debito}")

    print()

print("="*150)
print("OBSERVAÇÃO")
print("="*150)
print("""
Se os débitos estão corretos (1,99 | 35,15 | 5,90 etc) mas desalinhados com suas linhas,
significa que split_columns() está extraindo corretamente, mas os dados estão sendo
atribuídos às linhas erradas.

HIPÓTESE: O problema pode estar em build_movements(), que agrupa as palavras em linhas
e depois extrai os campos com split_columns().

Se uma linha tem as palavras descrição/país/taxa/débito/crédito misturadas com a próxima linha,
split_columns() vai capturar tudo incorretamente.

PRÓXIMO PASSO: Verificar como group_rows() está agrupando as palavras em linhas.
Se há uma falha lá, todas as linhas subseqüentes terão seus dados desalinhados.
""")

print("="*150 + "\n")
