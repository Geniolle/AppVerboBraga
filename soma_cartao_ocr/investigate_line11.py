#!/usr/bin/env python3
"""Investigar por que linha 11 (Google One) não tem dados."""

import json

print("\n" + "="*150)
print("INVESTIGAÇÃO: POR QUE L11 NÃO TEM DADOS?")
print("="*150 + "\n")

with open('output/resultado.json', encoding='utf-8') as f:
    data = json.load(f)

movimentos = data['movimentos']

print(f"Total de movimentos: {len(movimentos)}")
print(f"Números de linhas OCR: {[m['line'] for m in movimentos]}\n")

# Procurar a linha 11
linha11 = [m for m in movimentos if m['line'] == 11]

if linha11:
    print("LINHA 11 (Google One):")
    print("-" * 150)
    mov = linha11[0]
    for field in ['line', 'data_movimento', 'data_valor', 'descricao', 'pais', 'moeda_original', 'taxa_cambio', 'debito_eur', 'credito_eur', 'texto_ocr']:
        val = mov.get(field, '[NÃO EXISTE]')
        print(f"  {field:<20}: {val}")
else:
    print("❌ LINHA 11 NÃO ENCONTRADA NO RESULTADO!")

print("\n" + "="*150)
print("VERIFICAÇÃO: HÁ LINHAS FALTANDO?")
print("="*150 + "\n")

# Verificar se há gaps
linhas = sorted([m['line'] for m in movimentos])
print(f"Linhas capturadas: {linhas}\n")

# Procurar gaps
for i in range(len(linhas) - 1):
    if linhas[i+1] - linhas[i] > 1:
        gap_start = linhas[i] + 1
        gap_end = linhas[i+1] - 1
        print(f"⚠️  GAP: Linhas {gap_start} a {gap_end} faltam")

print("\n" + "="*150 + "\n")
