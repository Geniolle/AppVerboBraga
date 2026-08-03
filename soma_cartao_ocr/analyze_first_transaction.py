#!/usr/bin/env python3
"""Analisar a primeira transação em detalhe - extrair valores de cada coluna."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account
import yaml

print("\n" + "="*150)
print("ANALISE DETALHADA: PRIMEIRA TRANSACAO")
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

# Extrair todos os Words com coordenadas precisas
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
                    'width': x1 - x0,
                    'height': y1 - y0,
                })

# Filtrar palavras da primeira transação (Y entre 220-232)
first_tx_y_min = 220
first_tx_y_max = 232

first_tx_words = [w for w in words if first_tx_y_min <= w['y0'] <= first_tx_y_max or
                                       first_tx_y_min <= w['y1'] <= first_tx_y_max or
                                       (w['y0'] < first_tx_y_min and w['y1'] > first_tx_y_max)]

print(f"🔍 PRIMEIRA TRANSACAO: Y={first_tx_y_min}-{first_tx_y_max}\n")

# Determinar largura da imagem
img_width = max(w['x1'] for w in words)
print(f"Largura da imagem: {img_width} pixels\n")

# Definição das colunas (do config.yaml)
columns = cfg['table']['columns']

print("📐 MAPEAMENTO DAS COLUNAS:")
print("-" * 150)
for col_name, (x_min, x_max) in columns.items():
    x_min_px = int(x_min * img_width)
    x_max_px = int(x_max * img_width)
    width_pct = (x_max - x_min) * 100
    print(f"  {col_name:20} X=[{x_min_px:4d}-{x_max_px:4d}] ({width_pct:5.1f}%)")

print("\n" + "="*150)
print("PALAVRAS DA PRIMEIRA TRANSACAO - POR ORDEM DE X (esquerda para direita)")
print("="*150 + "\n")

# Ordenar por X para ver sequência
sorted_words = sorted(first_tx_words, key=lambda w: w['x0'])

for i, word in enumerate(sorted_words, 1):
    x_pct = (word['cx'] / img_width) * 100
    print(f"{i:2d}. X={word['x0']:4d}-{word['x1']:4d} ({x_pct:5.1f}%) | Y={word['y0']:3d}-{word['y1']:3d} | '{word['text']}'")

print("\n" + "="*150)
print("EXTRACTO POR COLUNA")
print("="*150 + "\n")

# Extrair valores por coluna
col_values = {}
for col_name, (x_min, x_max) in columns.items():
    x_min_px = int(x_min * img_width)
    x_max_px = int(x_max * img_width)

    # Palavras nesta coluna
    col_words = [w for w in sorted_words if
                 (w['cx'] >= x_min_px and w['cx'] <= x_max_px) or
                 (w['x0'] >= x_min_px and w['x0'] < x_max_px) or
                 (w['x1'] > x_min_px and w['x1'] <= x_max_px)]

    if col_words:
        text = " ".join([w['text'] for w in col_words])
        col_values[col_name] = text
    else:
        col_values[col_name] = "(vazio)"

# Mostrar com melhor formatação
print("Coluna                      | Valor Extraído")
print("-" * 150)
for col_name, (x_min, x_max) in columns.items():
    value = col_values.get(col_name, "(não encontrado)")
    print(f"{col_name:25s} | {value}")

print("\n" + "="*150)
print("🎯 RESPOSTA: PRIMEIRA TRANSACAO")
print("="*150 + "\n")

print(f"📅 DATA MOVIMENTO:    {col_values.get('data_movimento', '(não encontrado)')}")
print(f"📅 DATA VALOR:        {col_values.get('data_valor', '(não encontrado)')}")
print(f"📝 DESCRIÇÃO:         {col_values.get('descricao', '(não encontrado)')}")
print(f"🌍 PAÍS:              {col_values.get('pais', '(não encontrado)')}")
print(f"💱 MOEDA ORIGINAL:    {col_values.get('moeda_original', '(não encontrado)')}")
print(f"📊 TAXA CÂMBIO:       {col_values.get('taxa_cambio', '(não encontrado)')}")
print(f"💸 DÉBITO EUR:        {col_values.get('debito_eur', '(não encontrado)')}")
print(f"💰 CRÉDITO EUR:       {col_values.get('credito_eur', '(não encontrado)')}")

print("\n" + "="*150)
print("ANALISE DETALHADA DAS DATAS")
print("="*150 + "\n")

data_mov = col_values.get('data_movimento', '').strip()
data_valor = col_values.get('data_valor', '').strip()

print(f"Data Movimento Raw: '{data_mov}'")
print(f"Data Valor Raw:     '{data_valor}'")

# Tentar normalizar as datas
def parse_date(date_str):
    """Tenta extrair DD/MM de uma string."""
    import re
    # Procura por padrão DD/MM
    match = re.search(r'(\d{1,2})/(\d{1,2})', date_str)
    if match:
        day, month = match.groups()
        return f"{int(day):02d}/{int(month):02d}"
    # Se não encontrar, tenta padrão DDMM
    match = re.search(r'(\d{4})', date_str)
    if match:
        ddmm = match.group(1)
        day = int(ddmm[:2])
        month = int(ddmm[2:])
        return f"{day:02d}/{month:02d}"
    return "❌ Formato não reconhecido"

print(f"\n✅ Data Movimento Normalizada: {parse_date(data_mov)}")
print(f"✅ Data Valor Normalizada:     {parse_date(data_valor)}")

print("\n" + "="*150 + "\n")
