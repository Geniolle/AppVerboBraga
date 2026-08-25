#!/usr/bin/env python3
"""Debug completo da extração de colunas OCR."""

import sys
import yaml
import json
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, str(Path(__file__).parent))

from main import extract_words, group_rows, split_columns, vision_request

print("\n" + "="*150)
print("DEBUG COMPLETO: EXTRAÇÃO DE COLUNAS OCR")
print("="*150 + "\n")

# Carregar config
with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# Carregar imagem OCR
ocr_image_path = Path("output/01_contraste.png")
if not ocr_image_path.exists():
    print(f"❌ Imagem OCR não encontrada: {ocr_image_path}\n")
    sys.exit(1)

print(f"Carregando imagem OCR: {ocr_image_path}\n")

# Extrair palavras usando vision_request
from PIL import Image
img = Image.open(ocr_image_path)
width, height = img.size
print(f"Dimensões da imagem: {width}x{height}\n")

# Se já temos resultado.json, carregar de lá; senão fazer a chamada vision
import json
resultado_path = Path("output/resultado.json")
if resultado_path.exists():
    print("⚠️  Resultado.json encontrado, pulando vision_request\n")
    # Vamos extrair os movimentos e analisar a estrutura
    with open(resultado_path) as f:
        result = json.load(f)
    words = []  # Não vamos usar as words
    print(f"Movimentos carregados: {len(result.get('movimentos', []))}\n")
else:
    try:
        result = vision_request(ocr_image_path, cfg, None)
        words = extract_words(result)
        print(f"✓ Palavras extraídas: {len(words)}\n")
    except Exception as e:
        print(f"❌ Erro ao chamar vision_request: {e}\n")
        print("Usando resultado.json se disponível...")
        sys.exit(1)

rows = group_rows(words, width, height, cfg["table"]) if words else []
print(f"✓ Linhas agrupadas: {len(rows)}\n")

# Debug: mostrar cada linha e suas colunas
print("="*150)
print("ANÁLISE LINHA POR LINHA")
print("="*150 + "\n")

for line_idx, row in enumerate(rows, 1):
    # Split columns
    fields = split_columns(row, width, cfg["table"]["columns"])

    print(f"LINHA {line_idx}:")
    print("-" * 150)

    # Mostrar posições X das palavras
    print(f"  Palavras nesta linha: {len(row)}")
    for word in row:
        print(f"    X: {word.x0:4.0f}-{word.x1:4.0f} (centro: {word.cx:4.0f}) | '{word.text}'")

    # Mostrar quais palavras foram atribuídas a cada coluna
    print(f"\n  Colunas extraídas:")
    for col_name, value in fields.items():
        if value.strip():
            print(f"    {col_name:<20} : '{value}'")
        else:
            print(f"    {col_name:<20} : (vazio)")

    print()

print("="*150)
print("LIMITES DE COLUNA (em pixels para {width}px de largura)")
print("="*150 + "\n")

for col_name, bounds in cfg["table"]["columns"].items():
    start_px = int(bounds[0] * width)
    end_px = int(bounds[1] * width)
    width_px = end_px - start_px
    print(f"  {col_name:<20} : [{start_px:4d}, {end_px:4d}] ({width_px:3d}px)")

print("\n" + "="*150)
print("ANÁLISE: Verificar se as palavras estão na coluna correta")
print("="*150 + "\n")

print("""
PRÓXIMOS PASSOS:
────────────────
1. Procure pela palavra "Débito" ou "1,99" e anote em qual coluna foi capturada
2. Procure pela palavra "Crédito" ou "Dublin" e anote em qual coluna foi capturada
3. Se "Débito" aparecer na coluna "credito_eur", isso confirma o overlap
4. Se "Crédito" aparecer vazio enquanto "Débito" tem valores, há definitivamente overlap

SE CONFIRMAR OVERLAP:
─────────────────────
- Ajustar os limites das colunas "debito_eur" e "credito_eur"
- Provavelmente reduzir a largura de uma ou aumentar a lacuna entre elas
""")

print("="*150 + "\n")
