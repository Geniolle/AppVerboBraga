#!/usr/bin/env python3
"""Debug de como group_rows() agrupa as palavras em linhas."""

import json
import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent))

import yaml
from PIL import Image

print("\n" + "="*150)
print("DEBUG: ANÁLISE DE COMO group_rows() AGRUPA AS PALAVRAS EM LINHAS OCR")
print("="*150 + "\n")

# Carregar config
with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# Carregar imagem preprocessada
ocr_image = Path("output/01_contraste.png")
if not ocr_image.exists():
    print(f"❌ Imagem OCR não encontrada: {ocr_image}")
    sys.exit(1)

img = Image.open(ocr_image)
width, height = img.size
print(f"Imagem: {width}x{height}\n")

# Carregar resultado.json para ver quais são as linhas
resultado_path = Path("output/resultado.json")
if not resultado_path.exists():
    print(f"❌ {resultado_path} não encontrado")
    sys.exit(1)

with open(resultado_path, encoding="utf-8") as f:
    data = json.load(f)

movimentos = data.get("movimentos", [])
print(f"Movimentos esperados (do resultado.json): {len(movimentos)}")
print(f"Números das linhas OCR: {[m.get('line') for m in movimentos[:10]]}\n")

# Carregar metadata de OCR para ver as palavras extraídas
ocr_metadata = Path("output/ocr_metadata.json")
if ocr_metadata.exists():
    with open(ocr_metadata, encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"✓ OCR metadata encontrado")
    print(f"Total de palavras extraídas: {len(metadata.get('words', []))}\n")

    print("="*150)
    print("ANÁLISE: DISTRIBUIÇÃO DE PALAVRAS POR Y (altura)")
    print("="*150 + "\n")

    # Agrupar palavras por faixa Y
    words = metadata.get("words", [])

    # Encontrar grupos de Y próximos
    if words:
        words_sorted = sorted(words, key=lambda w: w.get("y0", 0))

        y_groups = {}
        for word in words_sorted:
            y = word.get("y0", 0)

            # Achar o grupo mais próximo
            found_group = False
            for group_y in list(y_groups.keys()):
                if abs(group_y - y) < 15:  # Mesma linha se diferença < 15px
                    y_groups[group_y].append(word)
                    found_group = True
                    break

            if not found_group:
                y_groups[y] = [word]

        print(f"Grupos de palavras por linha: {len(y_groups)}\n")

        for idx, (y_val, group_words) in enumerate(sorted(y_groups.items())[:15], 1):
            texts = [w.get("text", "") for w in group_words]
            print(f"Grupo {idx} (Y≈{y_val:.0f}): {' '.join(texts)[:100]}")

            # Verificar se este grupo contém "Débito" ou valores numéricos
            all_text = " ".join(texts)
            if any(x in all_text for x in ["1.99", "35.15", "29.00", "160.00", "11.20", "12.00"]):
                print(f"   ⚠️  CONTÉM UM VALOR DE DÉBITO!")
            if "Débito" in all_text or "Crédito" in all_text:
                print(f"   ℹ️  Contém label de coluna")

        print()
else:
    print("⚠️  ocr_metadata.json não encontrado")

print("="*150)
print("CONCLUSÃO")
print("="*150)
print("""
Se vemos múltiplas linhas com a mesma posição Y (altura), significa que group_rows()
está agrupando corretamente e as palavras separadas horizontalmente.

Se vemos valores de débito (1.99, 35.15, etc) na mesma linha com descrições de OUTRAS
transações, isso confirma que as palavras estão sendo misturadas incorretamente durante
a extração ou preprocessing OCR.

A causa pode ser:
1. Preprocessing (contrast, skew correction) moveu as palavras
2. Vision API extraiu as palavras com Y incorreto
3. group_rows() tem um threshold de agrupamento muito alto
""")

print("="*150 + "\n")
