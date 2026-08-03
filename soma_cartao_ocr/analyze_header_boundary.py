#!/usr/bin/env python3
"""Identificar exatamente onde termina o cabeçalho e começam os lançamentos."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account
import yaml

print("\n" + "="*150)
print("IDENTIFICACAO: LIMITES DO CABECALHO E INICIO DOS LANCAMENTOS")
print("="*150 + "\n")

# Carregar credenciais e config
creds_file = Path("credentials/soma-cartao-ocr.json")
credentials = service_account.Credentials.from_service_account_file(str(creds_file))
vision_client = vision.ImageAnnotatorClient(credentials=credentials)

with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# Carregar imagem
img_path = Path("output/01_contraste.png")
with open(img_path, "rb") as f:
    image_content = f.read()

image = vision.Image(content=image_content)
response = vision_client.document_text_detection(image=image)

# Extrair todos os Words
words = []
for page in response.full_text_annotation.pages:
    for block in page.blocks:
        for paragraph in block.paragraphs:
            for word in paragraph.words:
                text = "".join([symbol.text for symbol in word.symbols])
                x0 = word.bounding_box.vertices[0].x
                y0 = word.bounding_box.vertices[0].y
                x1 = word.bounding_box.vertices[2].x
                y1 = word.bounding_box.vertices[2].y
                words.append({
                    'text': text,
                    'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                    'cy': (y0 + y1) // 2,
                })

# Agrupar por Y
y_groups = {}
for word in words:
    cy = word['cy']
    found_group = False
    for group_y in list(y_groups.keys()):
        if abs(group_y - cy) <= 15:
            y_groups[group_y].append(word)
            found_group = True
            break
    if not found_group:
        y_groups[cy] = [word]

sorted_y_groups = sorted(y_groups.items())

print("🔍 ANALISE LINHA POR LINHA\n")
print("="*150)

# Mostrar todas as linhas com análise
header_terms = cfg['table']['header_terms']

for i, (cy, words_in_line) in enumerate(sorted_y_groups[:15], 1):
    sorted_words = sorted(words_in_line, key=lambda x: x['x0'])
    text_line = " ".join([w['text'] for w in sorted_words])
    y_range = f"Y={words_in_line[0]['y0']}-{words_in_line[0]['y1']}"

    # Verificar se contém header terms
    text_lower = text_line.lower()
    is_header = any(term.lower() in text_lower for term in header_terms)

    # Determinar tipo de linha
    if is_header:
        tipo = "📌 CABEÇALHO"
    elif any(c.isdigit() for c in text_line):
        tipo = "📊 LANÇAMENTO"
    else:
        tipo = "❓ INDEFINIDO"

    print(f"Linha {i:2d}: {y_range:15s} | CY={cy:4d} | {tipo}")
    print(f"           Texto: {text_line[:120]}")
    print()

print("\n" + "="*150)
print("RESUMO DOS LIMITES")
print("="*150 + "\n")

# Identificar limites
header_lines = []
data_lines = []

for i, (cy, words_in_line) in enumerate(sorted_y_groups[:20], 1):
    sorted_words = sorted(words_in_line, key=lambda x: x['x0'])
    text_line = " ".join([w['text'] for w in sorted_words])
    text_lower = text_line.lower()
    is_header = any(term.lower() in text_lower for term in header_terms)

    if is_header:
        header_lines.append({'line': i, 'cy': cy, 'text': text_line})
    elif any(c.isdigit() for c in text_line) and len(text_line.strip()) > 5:
        data_lines.append({'line': i, 'cy': cy, 'text': text_line})

print("📌 CABEÇALHO:")
for hl in header_lines:
    print(f"  Linha {hl['line']:2d} (CY={hl['cy']:4d}): {hl['text'][:80]}")

print("\n📊 LANÇAMENTOS (Primeiros 5):")
for dl in data_lines[:5]:
    print(f"  Linha {dl['line']:2d} (CY={dl['cy']:4d}): {dl['text'][:80]}")

if header_lines and data_lines:
    last_header = header_lines[-1]
    first_data = data_lines[0]
    gap = first_data['cy'] - last_header['cy']

    print("\n" + "="*150)
    print("🎯 RESPOSTA FINAL")
    print("="*150 + "\n")

    print(f"✅ CABEÇALHO TERMINA em:")
    print(f"   Linha visual: {last_header['line']}")
    print(f"   Coordenada Y: CY={last_header['cy']} (Y={sorted_y_groups[last_header['line']-1][1][0]['y0']}-{sorted_y_groups[last_header['line']-1][1][0]['y1']})")
    print(f"   Texto: {last_header['text'][:80]}")

    print(f"\n✅ LANÇAMENTOS COMEÇAM em:")
    print(f"   Linha visual: {first_data['line']}")
    print(f"   Coordenada Y: CY={first_data['cy']} (Y={sorted_y_groups[first_data['line']-1][1][0]['y0']}-{sorted_y_groups[first_data['line']-1][1][0]['y1']})")
    print(f"   Texto: {first_data['text'][:80]}")

    print(f"\n📏 ESPAÇAMENTO:")
    print(f"   Gap vertical entre cabeçalho e primeiro lançamento: {gap} pixels")
    print(f"   (Típico: 20-40 pixels)")

print("\n" + "="*150 + "\n")
