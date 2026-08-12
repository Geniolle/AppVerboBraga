#!/usr/bin/env python3
"""Debug dos limites de coluna - detectar overlaps e problemas."""

import yaml
from pathlib import Path

print("\n" + "="*140)
print("DEBUG: LIMITES DE COLUNA E DETECÇÃO DE OVERLAP")
print("="*140 + "\n")

# Carregar config
with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

columns = cfg["table"]["columns"]
img_width = 1200  # Aproximadamente

print("LIMITES ATUAIS (em percentual e pixels para 1200px):")
print("-" * 140)
print(f"{'COLUNA':<20} {'INÍCIO %':<10} {'FIM %':<10} {'LARGURA %':<10} {'PIXELS':<15}")
print("-" * 140)

col_list = []
for name, bounds in columns.items():
    start_pct = bounds[0]
    end_pct = bounds[1]
    width_pct = end_pct - start_pct

    start_px = int(start_pct * img_width)
    end_px = int(end_pct * img_width)
    width_px = end_px - start_px

    col_list.append((name, start_px, end_px, width_px, start_pct, end_pct))

    print(f"{name:<20} {start_pct:<10.2f} {end_pct:<10.2f} {width_pct:<10.1%} [{start_px:4d}, {end_px:4d}] ({width_px:3d}px)")

print("\n" + "="*140)
print("DETECÇÃO DE OVERLAPS E GAPS")
print("="*140 + "\n")

# Ordenar por início
col_list_sorted = sorted(col_list, key=lambda x: x[1])

overlaps = []
gaps = []

for i in range(len(col_list_sorted) - 1):
    name1, start1, end1, width1, _, _ = col_list_sorted[i]
    name2, start2, end2, width2, _, _ = col_list_sorted[i + 1]

    if end1 > start2:
        overlap = end1 - start2
        overlaps.append((name1, name2, overlap))
        print(f"⚠️  OVERLAP: {name1} (ends {end1}) → {name2} (starts {start2})")
        print(f"   Overlap de {overlap}px")
    elif end1 < start2:
        gap = start2 - end1
        gaps.append((name1, name2, gap))
        print(f"⚠️  GAP: {name1} (ends {end1}) → {name2} (starts {start2})")
        print(f"   Gap de {gap}px")
    else:
        print(f"✓ {name1} → {name2}: Sem gap, sem overlap")

print("\n" + "="*140)
print("ANÁLISE ESPECÍFICA: DÉBITO EUR vs CRÉDITO EUR")
print("="*140 + "\n")

debito_bounds = columns["debito_eur"]
credito_bounds = columns["credito_eur"]

debito_start_px = int(debito_bounds[0] * img_width)
debito_end_px = int(debito_bounds[1] * img_width)
credito_start_px = int(credito_bounds[0] * img_width)
credito_end_px = int(credito_bounds[1] * img_width)

print(f"Débito EUR:  [{debito_start_px:4d}, {debito_end_px:4d}] ({debito_end_px - debito_start_px:3d}px)")
print(f"Crédito EUR: [{credito_start_px:4d}, {credito_end_px:4d}] ({credito_end_px - credito_start_px:3d}px)")

if debito_end_px > credito_start_px:
    overlap = debito_end_px - credito_start_px
    print(f"\n❌ PROBLEMA CRÍTICO: Débito sobrepõe Crédito por {overlap}px!")
    print(f"   Débito captura de 0-{debito_end_px}px")
    print(f"   Crédito captura de {credito_start_px}-{credito_end_px}px")
    print(f"\n   SOLUÇÃO: Reduzir Débito para [{debito_bounds[0]:.2f}, {(credito_start_px/img_width):.2f}]")
else:
    print(f"\n✓ Sem overlap entre Débito e Crédito")

print("\n" + "="*140)
print("COMPARAÇÃO COM ESTRUTURA ESPERADA")
print("="*140 + "\n")

print("""
Esperado na imagem (8 colunas):
  1. Data MOV     (10%)
  2. Data Valor   (9%)
  3. Descrição    (37%)
  4. País         (3%)
  5. Moeda Orig   (10%)
  6. Taxa Câmbio  (13%)
  7. Débito EUR   (10%)
  8. Crédito EUR  (8%)

Atual no config:
  1. Data Mov     (10%) ✓
  2. Data Valor   (7%)  ⚠ Um pouco estreita
  3. Descrição    (35%) ⚠ Um pouco estreita
  4. País         (3%)  ✓
  5. Moeda Orig   (10%) ✓
  6. Taxa Câmbio  (13%) ✓
  7. Débito EUR   (10%) ⚠ Pode estar sobrepondo Crédito
  8. Crédito EUR  (12%) ⚠ Pode estar capturando valor anterior
""")

print("="*140 + "\n")
