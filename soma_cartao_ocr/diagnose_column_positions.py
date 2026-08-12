#!/usr/bin/env python3
"""Diagnosticar a posição correta das colunas na imagem."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account
import yaml

print("\n" + "="*200)
print("DIAGNOSTICO: POSICOES DAS COLUNAS NA IMAGEM")
print("="*200 + "\n")

# Carregar config
with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# Carregar credenciais
creds_file = Path("credentials/soma-cartao-ocr.json")
credentials = service_account.Credentials.from_service_account_file(str(creds_file))
vision_client = vision.ImageAnnotatorClient(credentials=credentials)

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
                    'cx': (x0 + x1) / 2,
                    'cy': (y0 + y1) / 2,
                })

# Determinar largura
img_width = max(w['x1'] for w in words)
print(f"Largura total da imagem: {img_width} pixels\n")

# Colunas configuradas
columns = cfg['table']['columns']

print("="*200)
print("COLUNAS CONFIGURADAS NO CONFIG.YAML")
print("="*200 + "\n")

for col_name, (x_min, x_max) in columns.items():
    x_min_px = int(x_min * img_width)
    x_max_px = int(x_max * img_width)
    width = x_max_px - x_min_px
    print(f"{col_name:20s} X=[{x_min_px:4d}-{x_max_px:4d}] ({width:4d}px wide, {(x_max-x_min)*100:5.1f}%)")

# Analisar primeira linha de dados (Y entre 218-245 - apenas transação, sem cabeçalho)
print("\n" + "="*200)
print("ANALISE: PRIMEIRA TRANSACAO (Y=218-245)")
print("="*200 + "\n")

first_line_words = [w for w in words if (218 <= w['y0'] <= 245 or 218 <= w['y1'] <= 245)]

if first_line_words:
    sorted_words = sorted(first_line_words, key=lambda w: w['x0'])

    print("Palavras em ordem (esquerda para direita):\n")
    for i, word in enumerate(sorted_words, 1):
        x_pct = (word['cx'] / img_width) * 100
        print(f"{i:2d}. X={word['x0']:4d}-{word['x1']:4d} ({x_pct:5.1f}%) | '{word['text']}'")

    print("\n" + "-"*200)
    print("MAPEAMENTO: Qual coluna cada palavra cai?\n")

    for word in sorted_words:
        x_pct = word['cx'] / img_width
        found_col = None
        for col_name, (x_min, x_max) in columns.items():
            if x_min <= x_pct <= x_max:
                found_col = col_name
                break
        if found_col:
            print(f"'{word['text']:20s}' → {found_col}")
        else:
            print(f"'{word['text']:20s}' → ❌ FORA DAS COLUNAS (x={word['cx']/img_width:.2%})")

    print("\n" + "="*200)
    print("AGRUPAMENTO POR COLUNA")
    print("="*200 + "\n")

    col_data = {}
    for col_name in columns.keys():
        col_data[col_name] = []

    for word in sorted_words:
        x_pct = word['cx'] / img_width
        for col_name, (x_min, x_max) in columns.items():
            if x_min <= x_pct <= x_max:
                col_data[col_name].append(word['text'])
                break

    for col_name, (x_min, x_max) in columns.items():
        words_in_col = col_data[col_name]
        if words_in_col:
            text = " ".join(words_in_col)
            print(f"{col_name:20s}: '{text}'")
        else:
            print(f"{col_name:20s}: (vazio)")

print("\n" + "="*200 + "\n")
