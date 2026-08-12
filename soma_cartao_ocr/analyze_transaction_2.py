#!/usr/bin/env python3
"""Analisar e extrair dados da Transação 2 usando as mesmas 8 regras."""

import sys
import os
from pathlib import Path
import json
import re

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account
import yaml

print("\n" + "="*200)
print("ANALISE TRANSACAO 2 - APLICANDO AS 8 REGRAS")
print("="*200 + "\n")

# Carregar resultado.json para identificar Transação 2
with open("output/resultado.json", encoding='utf-8') as f:
    resultado = json.load(f)

movimentos = resultado.get('movimentos', [])

# Encontrar segunda transação COMPLETA (MERCADONA BRAGA)
# Pular "One Dublin" que é parte de "Google One Dublin"
transacao_2 = None
for idx, mov in enumerate(movimentos):
    desc = mov.get('descricao', '')
    if ('Google One Dublin' not in desc and
        'One Dublin' not in desc and
        mov.get('status') == 'VÁLIDO'):
        transacao_2 = mov
        trans_2_idx = idx
        break

# Se não encontrou válida, pega qualquer uma diferente
if not transacao_2:
    for idx, mov in enumerate(movimentos):
        desc = mov.get('descricao', '')
        if ('Google One Dublin' not in desc and 'One Dublin' not in desc):
            transacao_2 = mov
            trans_2_idx = idx
            break

if not transacao_2:
    print("❌ Transação 2 não encontrada!")
    sys.exit(1)

print("✅ TRANSACAO 2 IDENTIFICADA:\n")
print(f"Descrição: {transacao_2.get('descricao', '')}")
print(f"Data Movimento: {transacao_2.get('data_movimento', '')}")
print(f"Data Valor: {transacao_2.get('data_valor', '')}")
print(f"Débito EUR: {transacao_2.get('debito_eur', '')}")
print(f"Status: {transacao_2.get('status', '')}\n")

# Carregar credenciais
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

# Extrair todas as palavras
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

img_width = max(w['x1'] for w in words)

print("="*200)
print("APLICANDO AS 8 REGRAS")
print("="*200 + "\n")

# REGRA 1: Procurar palavra-chave da descrição
desc_keywords = transacao_2.get('descricao', '').split()[:2]  # Primeiras 2 palavras
print(f"🔍 REGRA 1: Procurar descrição em '{' '.join(desc_keywords)}'\n")

desc_words = []
for keyword in desc_keywords:
    matches = [w for w in words if keyword.lower() in w['text'].lower()]
    if matches:
        desc_words.extend(matches)
        print(f"  ✅ Encontrado '{keyword}' em {len(matches)} posição(ões)")

if not desc_words:
    print(f"  ❌ Nenhuma palavra encontrada!")
    sys.exit(1)

# Usar primeira ocorrência como referência
ref_word = desc_words[0]
target_cy = ref_word['cy']

print(f"\n  Usando como referência: '{ref_word['text']}'")
print(f"  Posição Y: {ref_word['y0']}-{ref_word['y1']} (CY={target_cy})\n")

# REGRA 3: Agrupamento de Linhas Y
print(f"🔍 REGRA 3: Agrupamento de linhas (tolerance=0.003)\n")

tolerance = 0.003 * img_width
tolerance_pixels = int(tolerance)
range_y = (target_cy - tolerance_pixels, target_cy + tolerance_pixels)

print(f"  Tolerância: 0.003 × {img_width}px = {tolerance_pixels}px")
print(f"  Range Y: CY={range_y[0]:.0f} até CY={range_y[1]:.0f}\n")

# Extrair todas as palavras na mesma linha Y
line_words = [w for w in words if range_y[0] <= w['cy'] <= range_y[1]]
line_words_sorted = sorted(line_words, key=lambda w: w['x0'])

print(f"  Palavras encontradas: {len(line_words_sorted)}\n")

# REGRA 2: Extrair posição X e normalizar
print(f"🔍 REGRA 2: Mapeamento de colunas (posição X)\n")

columns = cfg['table']['columns']

print(f"  Palavras em ordem de X (esquerda para direita):\n")

col_data = {col: [] for col in columns.keys()}

for i, word in enumerate(line_words_sorted[:15], 1):
    x_pct = word['cx'] / img_width
    found_col = None

    for col_name, (x_min, x_max) in columns.items():
        if x_min <= x_pct <= x_max:
            col_data[col_name].append(word['text'])
            found_col = col_name
            break

    col_label = f"→ {found_col}" if found_col else "→ FORA"
    print(f"    {i:2d}. X={int(word['x0']):4d}-{int(word['x1']):4d} ({x_pct:5.1f}%) | '{word['text']:15s}' {col_label}")

print("\n" + "="*200)
print("DADOS EXTRAIDOS POR COLUNA")
print("="*200 + "\n")

extracted_data = {}
for col_name in columns.keys():
    words_in_col = col_data[col_name]
    if words_in_col:
        text = " ".join(words_in_col)
        extracted_data[col_name] = text
    else:
        extracted_data[col_name] = ""

for col_name, value in extracted_data.items():
    status = "✅" if value else "❌"
    print(f"  {status} {col_name:20s} = {value or '(vazio)'}")

print("\n" + "="*200)
print("RESULTADO FINAL - TRANSACAO 2")
print("="*200 + "\n")

print(f"📝 Descrição da Imagem: {extracted_data.get('descricao', '')[:50]}")
print(f"📝 Descrição do JSON:  {transacao_2.get('descricao', '')}\n")

print(f"📅 Data Movimento:     {extracted_data.get('data_movimento', '') or '(extrair manualmente)'}")
print(f"📅 Data Valor:         {extracted_data.get('data_valor', '') or '(extrair manualmente)'}")
print(f"🌍 País:               {extracted_data.get('pais', '') or transacao_2.get('pais', '')}")
print(f"💱 Moeda Original:     {extracted_data.get('moeda_original', '') or transacao_2.get('moeda_original', '')}")
print(f"💸 Débito EUR:         {extracted_data.get('debito_eur', '') or transacao_2.get('debito_eur', '')}")

print("\n" + "="*200 + "\n")
