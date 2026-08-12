#!/usr/bin/env python3
"""Teste específico para o caso MERCADONA DUBLIN + BRAGA."""

from ocr_postprocessor import can_merge_descriptions, merge_descriptions

print("\n" + "="*80)
print("TESTE: Merge MERCADONA DUBLIN + BRAGA")
print("="*80 + "\n")

# Teste 1: Verificar se identifica como mergeable
desc1 = "MERCADONA Dublin"
desc2 = "BRAGA"

print(f"Descrição 1: '{desc1}'")
print(f"Descrição 2: '{desc2}'")
print()

can_merge = can_merge_descriptions(desc1, desc2)
print(f"[1] Pode fazer merge? {can_merge}")
print(f"    Status: {'✓' if can_merge else '✗'}")

if can_merge:
    merged = merge_descriptions(desc1, desc2)
    print(f"\n[2] Resultado do merge: '{merged}'")
    print(f"    Esperado: 'MERCADONA BRAGA'")
    print(f"    Status: {'✓' if merged == 'MERCADONA BRAGA' else '✗'}")

print("\n" + "="*80 + "\n")
