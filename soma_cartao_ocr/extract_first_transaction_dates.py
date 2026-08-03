#!/usr/bin/env python3
"""Extrair as datas corretas da PRIMEIRA transação da imagem."""

import sys
import os
from pathlib import Path
import re

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account

print("\n" + "="*150)
print("EXTRAIR DATAS CORRETAS - PRIMEIRA TRANSACAO")
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

print("🔍 PROCURANDO PRIMEIRA TRANSACAO COM DATAS\n")

date_pattern = re.compile(r'^\d{1,2}/\d{1,2}$')

transactions = []

for line_idx, (cy, words_in_line) in enumerate(sorted_y_groups, 1):
    sorted_words = sorted(words_in_line, key=lambda x: x['x0'])
    text_line = " ".join([w['text'] for w in sorted_words])

    # Procurar por linhas com datas
    date_words = [w for w in sorted_words if date_pattern.match(w['text'].strip())]

    if len(date_words) >= 2:
        # Verificar se não é cabeçalho
        text_lower = text_line.lower()
        if not any(keyword in text_lower for keyword in ['data', 'movimento', 'valor', 'descrição', 'cabeçalho']):
            data_mov = date_words[0]['text']
            data_valor = date_words[1]['text']
            descricao = ' '.join([w['text'] for w in sorted_words if not date_pattern.match(w['text'].strip())])

            transactions.append({
                'line_idx': line_idx,
                'y_range': f"{words_in_line[0]['y0']}-{words_in_line[0]['y1']}",
                'data_movimento': data_mov,
                'data_valor': data_valor,
                'descricao': descricao,
                'texto': text_line
            })

# Guardar primeira transação
if transactions:
    transaction_data = transactions[0]

print("\n" + "="*150)
print("RESULTADO: PRIMEIRAS 3 TRANSACOES ENCONTRADAS")
print("="*150 + "\n")

if transactions:
    for i, tx in enumerate(transactions[:3], 1):
        print(f"{i}. Linha {tx['line_idx']} (Y={tx['y_range']})")
        print(f"   ORIGINAL - Data Movimento: {tx['data_movimento']}, Data Valor: {tx['data_valor']}")

        # Tentar invertido (talvez os nomes estão trocados)
        inv_mov = tx['data_valor']
        inv_valor = tx['data_movimento']

        print(f"   INVERTIDO - Data Movimento: {inv_mov}, Data Valor: {inv_valor}")
        print(f"   Descrição: {tx['descricao'][:70]}")

        # Validar ordem
        if inv_mov <= inv_valor:
            print(f"   Status: ✅ Ordem correta (INVERTIDO)")
        else:
            print(f"   Status: ❌ Ainda errado")
        print()

    print("\n" + "-"*150)
    print("CONCLUSÃO: DATAS CORRETAS DA PRIMEIRA TRANSACAO")
    print("-"*150 + "\n")

    tx = transactions[0]
    print(f"📅 Data Movimento: {tx['data_movimento']}/2026")
    print(f"📅 Data Valor:     {tx['data_valor']}/2026\n")
else:
    print("❌ Nenhuma transação com datas encontrada")

print("\n" + "="*150 + "\n")
