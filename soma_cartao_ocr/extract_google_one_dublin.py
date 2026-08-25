#!/usr/bin/env python3
"""Extrair e mostrar TODOS os dados da linha 'Google One Dublin'."""

import sys
import os
from pathlib import Path
import re

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account
import yaml

print("\n" + "="*200)
print("ANALISE DETALHADA: LINHA COM 'GOOGLE ONE DUBLIN'")
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

# Procurar por "Google"
print("🔍 PROCURANDO 'GOOGLE' NA IMAGEM\n")

google_words = [w for w in words if 'google' in w['text'].lower()]

if not google_words:
    print("❌ Nenhuma palavra 'Google' encontrada!")
    sys.exit(1)

print(f"✅ Encontradas {len(google_words)} palavra(s) com 'Google':\n")

for i, w in enumerate(google_words, 1):
    print(f"{i}. '{w['text']}' em Y={w['y0']}-{w['y1']} (CY={w['cy']})")

# Pegar a primeira ocorrência de Google
google_word = google_words[0]
target_cy_range = (google_word['cy'] - 50, google_word['cy'] + 50)

print(f"\n📍 Focando na primeira ocorrência: '{google_word['text']}'")
print(f"   Y Range: {google_word['y0']}-{google_word['y1']}")
print(f"   CY: {google_word['cy']}")
print(f"   Procurando palavras em Y: {target_cy_range[0]}-{target_cy_range[1]}\n")

# Encontrar todas as palavras na mesma linha Y (±50 pixels)
line_words = [w for w in words if target_cy_range[0] <= w['cy'] <= target_cy_range[1]]
line_words = sorted(line_words, key=lambda w: w['x0'])

print("="*200)
print("TODAS AS PALAVRAS NA MESMA LINHA Y (em ordem de X)")
print("="*200 + "\n")

img_width = max(w['x1'] for w in words)

for i, word in enumerate(line_words, 1):
    x_pct = (word['cx'] / img_width) * 100
    print(f"{i:2d}. X={int(word['x0']):4d}-{int(word['x1']):4d} ({x_pct:5.1f}%) | Y={int(word['y0']):3d}-{int(word['y1']):3d} (CY={int(word['cy']):3d}) | '{word['text']}'")

# Mostrar texto completo
print("\n" + "="*200)
print("TEXTO COMPLETO DA LINHA (esquerda para direita)")
print("="*200 + "\n")

full_text = " ".join([w['text'] for w in line_words])
print(f"'{full_text}'\n")

# Mostrar colunas configuradas
print("="*200)
print("MAPEAMENTO DAS COLUNAS CONFIGURADAS")
print("="*200 + "\n")

columns = cfg['table']['columns']

print("Colunas definidas no config.yaml:\n")
for col_name, (x_min, x_max) in columns.items():
    x_min_px = int(x_min * img_width)
    x_max_px = int(x_max * img_width)
    width_pct = (x_max - x_min) * 100
    print(f"  {col_name:20s} X=[{x_min_px:4d}-{x_max_px:4d}] ({width_pct:5.1f}%)")

# Mapear palavras às colunas
print("\n" + "="*200)
print("PALAVRAS MAPEADAS ÀS COLUNAS")
print("="*200 + "\n")

col_data = {}
for col_name in columns.keys():
    col_data[col_name] = []

for word in line_words:
    x_pct = word['cx'] / img_width
    found_col = None
    for col_name, (x_min, x_max) in columns.items():
        if x_min <= x_pct <= x_max:
            col_data[col_name].append(word['text'])
            found_col = col_name
            break
    if not found_col:
        print(f"⚠️  '{word['text']}' em X={word['x0']}-{word['x1']} ({x_pct:.2%}) - FORA DAS COLUNAS")

# Mostrar dados por coluna
print("\n" + "="*200)
print("DADOS EXTRAIDOS POR COLUNA")
print("="*200 + "\n")

for col_name, (x_min, x_max) in columns.items():
    words_in_col = col_data[col_name]
    if words_in_col:
        text = " ".join(words_in_col)
        print(f"✅ {col_name:20s} = '{text}'")
    else:
        print(f"❌ {col_name:20s} = (vazio)")

print("\n" + "="*200)
print("RESULTADO FINAL - TRANSACAO 'GOOGLE ONE DUBLIN'")
print("="*200 + "\n")

result = {
    'data_movimento': " ".join(col_data.get('data_movimento', [])),
    'data_valor': " ".join(col_data.get('data_valor', [])),
    'descricao': " ".join(col_data.get('descricao', [])),
    'pais': " ".join(col_data.get('pais', [])),
    'moeda_original': " ".join(col_data.get('moeda_original', [])),
    'taxa_cambio': " ".join(col_data.get('taxa_cambio', [])),
    'debito_eur': " ".join(col_data.get('debito_eur', [])),
    'credito_eur': " ".join(col_data.get('credito_eur', [])),
}

print(f"📅 Data Movimento:    {result['data_movimento'] or '(vazio)'}")
print(f"📅 Data Valor:        {result['data_valor'] or '(vazio)'}")
print(f"📝 Descrição:         {result['descricao'] or '(vazio)'}")
print(f"🌍 País:              {result['pais'] or '(vazio)'}")
print(f"💱 Moeda Original:    {result['moeda_original'] or '(vazio)'}")
print(f"📊 Taxa de Câmbio:    {result['taxa_cambio'] or '(vazio)'}")
print(f"💸 Débito EUR (+):    {result['debito_eur'] or '(vazio)'}")
print(f"💰 Crédito EUR (-):   {result['credito_eur'] or '(vazio)'}")

print("\n" + "="*200 + "\n")
