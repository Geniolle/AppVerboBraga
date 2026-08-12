#!/usr/bin/env python3
"""Debug para rastrear quais linhas OCR são puladas em build_movements()."""

import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent))

# Simulate the filtering in build_movements()
print("\n" + "="*150)
print("DEBUG: QUAIS LINHAS OCR SÃO PULADAS?")
print("="*150 + "\n")

import re

DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})$")

def has_date_pattern(data_mov, data_val):
    """Simula a verificação de padrão de data em build_movements()."""
    return (
        bool(DATE_RE.search(data_mov.strip()))
        or bool(DATE_RE.search(data_val.strip()))
        or ("/" in data_mov)
        or ("/" in data_val)
        or bool(re.search(r"\d{4}-\d{2}-\d{2}", data_mov))
        or bool(re.search(r"\d{4}-\d{2}-\d{2}", data_val))
    )

# Esperado do extrato:
# Cabeçalho, depois transações

print("PADRÃO DE FILTRAGEM EM build_movements():")
print("-"*150)
print("""
Para cada linha OCR (index = 1, 2, 3, ...):
  1. Se não tem data_movimento E não tem data_valor → PULA
  2. Se não tem padrão de data → PULA
  3. Caso contrário → processa como movimento (line = index + 5)

Resultado no movimento:
  - Linha OCR index 1 → Movement line 6
  - Linha OCR index 2 → Movement line 7
  - ...
  - Linha OCR index N → Movement line N+5
""")

print("\n" + "="*150)
print("DADOS ESPERADOS DO RESULTADO.json")
print("="*150 + "\n")

# Dados que vimos no resultado.json
resultado_lines = [11, 12, 14, 15, 16, 17, 18, 20, 21, 22]

print("Lines no resultado.json: ", resultado_lines)
print("\nCorrespondência de indices OCR:")
print("-"*150)

for line in resultado_lines:
    index = line - 5
    print(f"  Movement line {line} = Linha OCR índice {index}")

print("\n" + "="*150)
print("DESCOBERTAS")
print("="*150 + "\n")

print(f"""
Se a primeira linha é Google One com line=11:
  - Linha OCR index 6 → line 6+5=11

Isto significa que as linhas OCR 1-5 foram PULADAS!

Possíveis razões:
  1. Linhas 1-5 são cabeçalho (sem datas)
  2. Ou as primeiras 10 linhas têm problemas, deixando 5 linhas do cabeçalho + 5 linhas extras puladas

GAPS observados:
  - Falta line 13 (index 8)
  - Falta line 19 (index 14)

Isto significa que as linhas OCR 8 e 14 foram PULADAS no meio do processamento!

Provavelmente porque não têm padrão de data válido, ou foram filtradas por should_skip_line().
""")

print("="*150 + "\n")
