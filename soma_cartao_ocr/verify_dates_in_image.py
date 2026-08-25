#!/usr/bin/env python3
"""Verificar visualmente as datas CORRETAS na imagem para Transação 1."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account
import re

print("\n" + "="*200)
print("VERIFICACAO: DATAS CORRETAS NA IMAGEM - TRANSACAO 1 (GOOGLE ONE DUBLIN)")
print("="*200 + "\n")

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

print("🔍 PROCURANDO TRANSACAO 1 (GOOGLE ONE DUBLIN)\n")

# Encontrar "Dublin" para delimitar a transação
dublin_words = [w for w in words if 'dublin' in w['text'].lower()]

if not dublin_words:
    print("❌ 'Dublin' não encontrado na imagem!")
    sys.exit(1)

print(f"✅ Encontradas {len(dublin_words)} ocorrências de 'Dublin'\n")

# Usar primeira ocorrência
dublin_word = dublin_words[0]
target_cy = dublin_word['cy']

print(f"Primeira ocorrência: Y={dublin_word['y0']}-{dublin_word['y1']} (CY={target_cy})\n")

# Encontrar todas as palavras na mesma transação
tolerance = 100  # pixels
range_y = (target_cy - tolerance, target_cy + tolerance)

transacao_words = [w for w in words if range_y[0] <= w['cy'] <= range_y[1]]
transacao_words_sorted = sorted(transacao_words, key=lambda w: w['x0'])

print("="*200)
print("TODAS AS PALAVRAS DA TRANSACAO 1 (EM ORDEM DE POSICAO X)")
print("="*200 + "\n")

date_pattern = re.compile(r'^\d{1,2}/\d{1,2}$')

print("Procurando DATAS (padrão DD/MM):\n")

date_words = []
for i, word in enumerate(transacao_words_sorted, 1):
    if date_pattern.match(word['text'].strip()):
        date_words.append(word)
        print(f"  {len(date_words)}. '{word['text']}' em X={int(word['x0']):4d}-{int(word['x1']):4d}, Y={int(word['y0']):3d}-{int(word['y1']):3d} (CY={int(word['cy']):3d})")

if len(date_words) < 2:
    print("\n❌ Menos de 2 datas encontradas!")
else:
    print(f"\n✅ Encontradas {len(date_words)} datas\n")

print("="*200)
print("INTERPRETACAO DAS DATAS")
print("="*200 + "\n")

img_width = max(w['x1'] for w in words)

print(f"ANALISE DETALHADA DAS DATAS POR COLUNA:\n")

# Data Movimento: [0.00, 0.10]  (10%)
# Data Valor:     [0.10, 0.19]  (9%)

data_movimento_dates = []
data_valor_dates = []

for date_word in date_words:
    x_pct = date_word['cx'] / img_width

    print(f"Data: {date_word['text']:6s} | X={int(date_word['x0']):4d}-{int(date_word['x1']):4d} | X%={x_pct:6.2%} | Y={int(date_word['y0']):3d}-{int(date_word['y1']):3d}", end="")

    if x_pct < 0.10:
        print(" → Coluna DATA MOVIMENTO [0.00-0.10]")
        data_movimento_dates.append(date_word)
    elif x_pct < 0.19:
        print(" → Coluna DATA VALOR [0.10-0.19]")
        data_valor_dates.append(date_word)
    else:
        print(" → Outra coluna")

print("\n" + "="*200)
print("CONCLUSAO: DATAS CORRETAS DA TRANSACAO 1")
print("="*200 + "\n")

if data_movimento_dates and data_valor_dates:
    data_mov = data_movimento_dates[0]['text']
    data_val = data_valor_dates[0]['text']

    print(f"✅ DATA MOVIMENTO: {data_mov}")
    print(f"✅ DATA VALOR: {data_val}\n")
    print(f"TRANSACAO 1 (GOOGLE ONE DUBLIN) - DATAS CORRETAS:")
    print(f"  Data Movimento: {data_mov}/2026")
    print(f"  Data Valor: {data_val}/2026\n")

    # Validação
    if data_mov <= data_val:
        print(f"✅ Validação: Data Movimento ({data_mov}) ≤ Data Valor ({data_val}) - CORRETO")
    else:
        print(f"⚠️ Validação: Data Movimento ({data_mov}) > Data Valor ({data_val}) - INVERTIDO!")
else:
    print("❌ Não foi possível identificar as datas corretamente")

print("\n" + "="*200 + "\n")
