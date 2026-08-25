#!/usr/bin/env python3
"""Debug das posições X das palavras extraídas pelo Vision API."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*150)
print("DEBUG: POSIÇÕES X DAS PALAVRAS EXTRAÍDAS")
print("="*150 + "\n")

# Carregar config e imagem
import yaml
from PIL import Image

with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

img = Image.open("output/01_contraste.png")
width, height = img.size

print(f"Imagem preprocessada: {width}x{height}\n")

# Mostrar limites de coluna em pixels
print("LIMITES DE COLUNA (em pixels para {width}px):")
print("-"*150)

for col_name, bounds in cfg["table"]["columns"].items():
    start_px = int(bounds[0] * width)
    end_px = int(bounds[1] * width)
    print(f"  {col_name:<20} : [{start_px:4d}, {end_px:4d}] ({end_px-start_px:3d}px)")

print("\n" + "="*150)
print("VALORES MONETÁRIOS NA IMAGEM")
print("="*150 + "\n")

print("""
Na imagem 01_contraste.png, procurando pelos valores esperados:

Valores que deveriam estar em DÉBITO EUR:
- 1,99 (Google One)
- 35,15 (MERCADONA)
- 5,90 (FACEBK) - também está em Taxa Câmbio
- 29,00 (OPUS) - também está em Taxa Câmbio
- etc.

Valores que deveriam estar em MOEDA ORIGINAL:
- (nenhum esperado neste extrato)

Valores que deveriam estar em TAXA CÂMBIO:
- 5,90 (FACEBK)
- 29,00 (COMISSAO ESTR)
- etc.

PERGUNTA:
─────────
Se 1,99 aparece visualmente na SEGUNDA coluna de valores (Moeda Original)
em vez de estar na TERCEIRA coluna de valores (Débito EUR),
isso pode significar que:

1. Os limites de coluna estão deslocados
2. Ou as palavras têm cx incorreto
3. Ou há um padrão específico de como os valores são dispostos

PRÓXIMO PASSO:
───────────────
Executar Vision API novamente com debug para salvar as posições X de cada palavra.
Depois comparar se 1,99 está em cx ≈ 1259-1451 (moeda_original) ou em cx ≈ 1749-1963 (debito_eur).
""")

print("="*150 + "\n")
