#!/usr/bin/env python3
"""Procurar os valores monetários da transação Google One Dublin."""

import sys
import os
from pathlib import Path
import re

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account

print("\n" + "="*150)
print("PROCURANDO VALORES MONETARIOS: GOOGLE ONE DUBLIN")
print("="*150 + "\n")

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

# Procurar por "Dublin"
print("🔍 Procurando 'Dublin'...\n")

dublin_words = [w for w in words if 'dublin' in w['text'].lower()]

if not dublin_words:
    print("❌ 'Dublin' não encontrado!")
    sys.exit(1)

# Pegar primeira ocorrência
dublin_word = dublin_words[0]

print(f"✅ Encontrado 'Dublin' em:")
print(f"   X={dublin_word['x0']}-{dublin_word['x1']}")
print(f"   Y={dublin_word['y0']}-{dublin_word['y1']}")
print(f"   CY={dublin_word['cy']}\n")

# Encontrar todas as palavras após "Dublin" (X > Dublin.x1) na mesma linha ou linhas próximas
dublin_x = dublin_word['x1']
dublin_cy = dublin_word['cy']

print("📍 Procurando palavras DEPOIS de 'Dublin' (à direita) na mesma transação...\n")

# Palavras à direita de Dublin
words_after_dublin = [
    w for w in words
    if w['x0'] > dublin_x and abs(w['cy'] - dublin_cy) < 100
]

words_after_dublin = sorted(words_after_dublin, key=lambda w: (w['cy'], w['x0']))

print("Palavras encontradas após 'Dublin':\n")

money_pattern = re.compile(r'^[\d.,]+$')
dates_pattern = re.compile(r'^\d{1,2}/\d{1,2}$')

money_values = []

for i, word in enumerate(words_after_dublin[:30], 1):  # Mostrar primeiras 30
    is_money = bool(money_pattern.match(word['text']))
    is_date = bool(dates_pattern.match(word['text']))

    tag = ""
    if is_money:
        tag = "💰 VALOR"
        money_values.append(word['text'])
    elif is_date:
        tag = "📅 DATA"

    print(f"{i:2d}. X={int(word['x0']):4d}-{int(word['x1']):4d} | Y={int(word['y0']):3d}-{int(word['y1']):3d} | '{word['text']:15s}' {tag}")

print("\n" + "="*150)
print("VALORES MONETARIOS ENCONTRADOS")
print("="*150 + "\n")

if money_values:
    print(f"Encontrados {len(money_values)} valores:\n")
    for i, val in enumerate(money_values, 1):
        print(f"  {i}. {val}")

    print("\n" + "-"*150)
    print("ANALISE:")
    print("-"*150 + "\n")

    print(f"🎯 Primeiro valor encontrado: {money_values[0]}")
    print(f"   → Este é provavelmente a MOEDA ORIGINAL\n")

    if len(money_values) > 1:
        print(f"🎯 Segundo valor: {money_values[1]}")
        print(f"   → Este pode ser a TAXA DE CÂMBIO ou DÉBITO EUR\n")

    if len(money_values) > 2:
        print(f"🎯 Terceiro valor: {money_values[2]}")
        print(f"   → Este pode ser o DÉBITO EUR\n")

    print("\n" + "="*150)
    print("RESULTADO")
    print("="*150 + "\n")

    print(f"💱 MOEDA ORIGINAL: {money_values[0]}")
    if len(money_values) > 1:
        print(f"📊 TAXA/DÉBITO:   {money_values[1]}")
    if len(money_values) > 2:
        print(f"💸 DÉBITO EUR:    {money_values[2]}")

else:
    print("❌ Nenhum valor monetário encontrado após 'Dublin'")

print("\n" + "="*150 + "\n")
