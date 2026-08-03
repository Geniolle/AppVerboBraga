#!/usr/bin/env python3
"""Debug: Investigar por que primeira linha (Google One Dublin) não está correta."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

import cv2
import numpy as np
from google.cloud import vision
from google.oauth2 import service_account
import json

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

print("\n" + "="*150)
print("DEBUG: PRIMEIRA LINHA - GOOGLE ONE DUBLIN")
print("="*150 + "\n")

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
                confidence = word.confidence
                words.append({
                    'text': text,
                    'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                    'cx': (x0 + x1) // 2,
                    'cy': (y0 + y1) // 2,
                    'confidence': confidence
                })

print(f"Total de Words encontrados: {len(words)}\n")

# Procurar palavras chave da primeira linha
keywords = ['Google', 'One', 'Dublin', 'IRL', '1.99', '1,99']
found_keywords = []

print("PROCURANDO PALAVRAS-CHAVE:")
print("-" * 150)
for keyword in keywords:
    for word in words:
        if keyword.lower() in word['text'].lower():
            found_keywords.append(word)
            print(f"✓ '{keyword}' encontrado: '{word['text']}'")
            print(f"  Posição: X={word['x0']}-{word['x1']}, Y={word['y0']}-{word['y1']}")
            print(f"  Centro: CX={word['cx']}, CY={word['cy']}")
            print()

if not found_keywords:
    print("✗ Nenhuma palavra-chave encontrada!")

# Agrupar por Y (tentando entender o agrupamento de linhas)
print("\n" + "="*150)
print("AGRUPAMENTO POR COORDENADA Y (Centro Vertical)")
print("="*150 + "\n")

# Agrupar words por Y aproximado (±10 pixels)
y_groups = {}
for word in words:
    cy = word['cy']
    # Encontrar grupo mais próximo
    found_group = False
    for group_y in list(y_groups.keys()):
        if abs(group_y - cy) <= 15:  # Tolerância de 15 pixels
            y_groups[group_y].append(word)
            found_group = True
            break
    if not found_group:
        y_groups[cy] = [word]

# Ordenar por Y
sorted_y_groups = sorted(y_groups.items())

print(f"Total de linhas (grupos Y): {len(sorted_y_groups)}\n")

# Mostrar primeiras 10 linhas
for i, (cy, words_in_line) in enumerate(sorted_y_groups[:10], 1):
    text_line = " ".join([w['text'] for w in sorted(words_in_line, key=lambda x: x['cx'])])
    y_range = f"Y={words_in_line[0]['y0']}-{words_in_line[0]['y1']}"
    print(f"Linha {i}: {y_range}")
    print(f"  Texto: {text_line[:100]}")
    print(f"  CY (centro): {cy}")

    # Procurar "Google" ou "One"
    if any('google' in w['text'].lower() or 'one' in w['text'].lower() for w in words_in_line):
        print(f"  ⭐ CONTEM GOOGLE/ONE!")
    print()

# Análise específica dos primeiros 100 Words
print("\n" + "="*150)
print("PRIMEIROS 100 WORDS (Ordem de Leitura)")
print("="*150 + "\n")

for i, word in enumerate(words[:100], 1):
    marker = " ⭐" if any(kw.lower() in word['text'].lower() for kw in keywords) else ""
    print(f"{i:3d}. [{word['y0']:4d}-{word['y1']:4d}] [{word['x0']:4d}-{word['x1']:4d}] '{word['text']}'  conf={word['confidence']:.2%}{marker}")

# Análise de colunas
print("\n" + "="*150)
print("ANALISE DE COLUNAS (Limite de X)")
print("="*150 + "\n")

# Encontrar as colunas esperadas
# Assumindo: 0-10% data_movimento, 10-19% data_valor, 19-56% descricao, etc
width = max(w['x1'] for w in words)
print(f"Largura total da imagem: {width}\n")

columns = {
    'data_movimento': (0.00, 0.10),
    'data_valor': (0.10, 0.19),
    'descricao': (0.19, 0.56),
    'pais': (0.56, 0.62),
    'moeda_original': (0.62, 0.72),
}

for col_name, (x_min, x_max) in columns.items():
    x_min_px = int(width * x_min)
    x_max_px = int(width * x_max)
    print(f"{col_name:15} [{x_min_px:4d}-{x_max_px:4d}] ({x_min:.0%}-{x_max:.0%})")

# Verificar em qual coluna estão as palavras-chave
print("\nONDE ESTAO AS PALAVRAS-CHAVE:")
print("-" * 150)

for word in found_keywords:
    x = word['cx']
    for col_name, (x_min, x_max) in columns.items():
        x_min_px = int(width * x_min)
        x_max_px = int(width * x_max)
        if x_min_px <= x <= x_max_px:
            print(f"'{word['text']}' está em coluna: {col_name}")
            break
    else:
        print(f"'{word['text']}' está FORA das colunas definidas (X={x})")

print("\n" + "="*150 + "\n")
