#!/usr/bin/env python3
"""Debug: Encontrar o que está faltando na coluna Débito EUR."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import yaml
import json

print("\n" + "="*150)
print("DEBUG: INVESTIGAÇÃO DE DÉBITO EUR - LINHA 1 (GOOGLE ONE)")
print("="*150 + "\n")

# Carregar config
with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# Limites de coluna atuais
debito_bounds = cfg["table"]["columns"]["debito_eur"]
img_width = 2134  # Largura da imagem preprocessada

debito_start_px = int(debito_bounds[0] * img_width)
debito_end_px = int(debito_bounds[1] * img_width)

print(f"LIMITES ATUAIS de Débito EUR:")
print(f"  Percentual: [{debito_bounds[0]:.3f}, {debito_bounds[1]:.3f}]")
print(f"  Pixels: [{debito_start_px}, {debito_end_px}] ({debito_end_px - debito_start_px}px)")

print("\n" + "="*150)
print("POSSÍVEIS CAUSAS DO PROBLEMA")
print("="*150 + "\n")

print("""
1. LIMITE DE COLUNA MUITO APERTADO OU MAL POSICIONADO
   ───────────────────────────────────────────────────
   - Se o valor está visualmente em Débito EUR mas fora do intervalo [0.82, 0.93]
   - Split_columns() não vai capturar

   Solução: Expandir o limite para esquerda ou direita

2. VALOR NÃO FOI EXTRAÍDO PELO VISION API
   ───────────────────────────────────────
   - O Vision API pode ter falhado em extrair o texto
   - Ou o preprocessing removeu/desbotou o valor

   Solução: Verificar o preprocessing (contrast, binarização)

3. VALOR FOI EXTRAÍDO MAS COM POSIÇÃO X INCORRETA
   ───────────────────────────────────────────────
   - Vision API extraiu mas com cx fora do intervalo

   Solução: Verificar coordenadas X das palavras extraídas

4. VALOR ESTÁ NUMA COLUNA VIZINHA
   ────────────────────────────────
   - Está sendo capturado como Taxa Câmbio ou Crédito EUR

   Solução: Verificar outras colunas

PRÓXIMOS PASSOS:
────────────────
1. Verificar o resultado.json linha 1 (Google One) - qual coluna tem o valor?
2. Se nenhuma coluna tem, o Vision API não extraiu
3. Se está em outra coluna, ajustar limites
4. Se totalmente faltando, pode ser problema de preprocessing
""")

print("\n" + "="*150)
print("SUGESTÃO DE AJUSTE")
print("="*150 + "\n")

print("""
O limite atual [0.82, 0.93] ocupa 11% de largura (234px).

Se o valor estiver visível mas fora deste intervalo:
- Se está mais à esquerda: expandir para [0.80, 0.93] (mais 43px)
- Se está mais à direita: expandir para [0.82, 0.95] (mais 43px)

Recomendação: Aumentar para [0.80, 0.94] para capturar melhor
""")

print("="*150 + "\n")
