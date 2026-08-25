#!/usr/bin/env python3
"""Teste da função de merge de descrições quebradas."""

from ocr_postprocessor import (
    is_description_incomplete,
    can_merge_descriptions,
    merge_descriptions,
    detect_broken_descriptions,
    merge_broken_movement_descriptions,
)

print("\n" + "="*80)
print("TESTE: Merge de Descrições Quebradas")
print("="*80 + "\n")

# Teste 1: Detectar descrição incompleta
print("[TESTE 1] Detectar descrições incompletas:")
print("-" * 80)
test_cases = [
    ("BRAGA", True),
    ("DUBLIN", True),
    ("MERCADONA BRAGA", False),
    ("RECHEIO", True),
    ("RECHEIO CASH & CARRY BRAGA", False),
]
for desc, expected in test_cases:
    result = is_description_incomplete(desc)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{desc}' -> {result} (esperado: {expected})")

# Teste 2: Validar merge de descrições
print("\n[TESTE 2] Validar merge de descrições:")
print("-" * 80)
merge_cases = [
    ("MERCADONA", "BRAGA", True),  # Localização após nome
    ("RECHEIO CASH & CARRY", "BRAGA", True),  # Localização após estabelecimento
    ("GOOGLE ONE", "DUBLIN", True),  # Localização após serviço
    ("FACEBK 8HJ84THS72", "DUBLIN", True),  # ID + localização
    ("1,99", "EUR", False),  # Não deve fazer merge
]
for desc1, desc2, expected in merge_cases:
    result = can_merge_descriptions(desc1, desc2)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{desc1}' + '{desc2}' -> {result} (esperado: {expected})")

# Teste 3: Executar merge
print("\n[TESTE 3] Executar merge:")
print("-" * 80)
merged = merge_descriptions("MERCADONA", "BRAGA")
print(f"Resultado: '{merged}'")
print(f"Status: {'✓' if merged == 'MERCADONA BRAGA' else '✗'}")

# Teste 4: Detectar pares para merge em lista de movimentos
print("\n[TESTE 4] Detectar pares para merge:")
print("-" * 80)
movimentos_teste = [
    {
        "line": 10,
        "data_movimento": "23/06",
        "data_valor": "20/06",
        "descricao": "Google One Dublin",
        "pais": "",
    },
    {
        "line": 11,
        "data_movimento": "26/06",
        "data_valor": "25/06",
        "descricao": "MERCADONA",  # Descrição incompleta!
        "pais": "IRL",
    },
    {
        "line": 12,
        "data_movimento": "26/06",
        "data_valor": "26/06",
        "descricao": "BRAGA",  # Deve fazer merge com linha anterior
        "pais": "",
    },
    {
        "line": 13,
        "data_movimento": "27/06",
        "data_valor": "26/06",
        "descricao": "FACEBK 8HJ84THS72 Dublin",
        "pais": "",
    },
]

merge_pairs = detect_broken_descriptions(movimentos_teste)
print(f"Pares detectados: {merge_pairs}")
if merge_pairs:
    for idx1, idx2 in merge_pairs:
        print(f"  → Linha {idx1} + Linha {idx2}")
        print(f"    '{movimentos_teste[idx1]['descricao']}' + '{movimentos_teste[idx2]['descricao']}'")

# Teste 5: Fazer merge completo
print("\n[TESTE 5] Fazer merge completo:")
print("-" * 80)
movimentos_antes = len(movimentos_teste)
result = merge_broken_movement_descriptions(movimentos_teste)
movimentos_depois = len(result)
print(f"Movimentos antes: {movimentos_antes}")
print(f"Movimentos depois: {movimentos_depois}")
print(f"Descrição da linha 11 (após merge): '{result[1]['descricao']}'")
print(f"Status: {'✓ MERGE BEM-SUCEDIDO' if result[1]['descricao'] == 'MERCADONA BRAGA' else '✗ MERGE FALHOU'}")

print("\n" + "="*80)
print("TESTES CONCLUÍDOS")
print("="*80 + "\n")
