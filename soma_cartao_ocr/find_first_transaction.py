#!/usr/bin/env python3
"""Encontrar a PRIMEIRA linha de lançamento (transação) da tabela."""

import sys
import os
from pathlib import Path
import re

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account

print("\n" + "="*150)
print("IDENTIFICACAO: PRIMEIRA LINHA DE LANCAMENTOS")
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

print("🔍 ANALISE: PROCURANDO PADROES DE TRANSACAO\n")

# Padrões que indicam uma transação real:
# 1. Começa com DD/MM (data de movimento)
# 2. Tem números decimais (valores)
# 3. Não tem palavras de cabeçalho (Data, Mov, Valor, Descrição, etc)

date_pattern = r'^\d{1,2}/\d{1,2}'
amount_pattern = r'\d+[.,]\d{2}'

transaction_candidates = []

for line_idx, (cy, words_in_line) in enumerate(sorted_y_groups, 1):
    sorted_words = sorted(words_in_line, key=lambda x: x['x0'])
    text_line = " ".join([w['text'] for w in sorted_words])
    y_range = f"Y={words_in_line[0]['y0']}-{words_in_line[0]['y1']}"

    # Verificar se parece uma transação
    starts_with_date = bool(re.match(date_pattern, text_line.strip()))
    has_amounts = bool(re.search(amount_pattern, text_line))
    is_short = len(text_line.strip()) < 200

    # Linhas de cabeçalho típicas têm estas palavras
    header_keywords = ['data', 'mov', 'valor', 'descrição', 'descricao', 'país', 'pais', 'câmbio', 'cambio', 'detalhe']
    is_header = any(keyword in text_line.lower() for keyword in header_keywords)

    # Uma transação típica:
    # - Começa com DD/MM
    # - Tem valores (números com ,)
    # - Não é cabeçalho
    # - Tem comprimento moderado

    if starts_with_date and has_amounts and not is_header:
        transaction_candidates.append({
            'line': line_idx,
            'cy': cy,
            'y0': words_in_line[0]['y0'],
            'y1': words_in_line[0]['y1'],
            'text': text_line,
            'date_match': True,
            'amount_match': True
        })

    # Debug: mostrar linhas importantes
    if line_idx <= 20:
        status = ""
        if is_header:
            status = "❌ CABEÇALHO"
        elif starts_with_date and has_amounts:
            status = "✅ TRANSACAO"
        elif starts_with_date:
            status = "⚠️  DATA MAS SEM VALOR"
        elif has_amounts:
            status = "⚠️  VALOR MAS SEM DATA"
        else:
            status = "❓ OUTRA"

        print(f"Linha {line_idx:2d}: {y_range} {status}")
        print(f"  CY={cy:4d} | {text_line[:100]}")
        print()

print("\n" + "="*150)
print("🎯 RESULTADO")
print("="*150 + "\n")

if transaction_candidates:
    first_tx = transaction_candidates[0]
    print(f"✅ PRIMEIRA TRANSACAO ENCONTRADA:\n")
    print(f"   Linha visual: {first_tx['line']}")
    print(f"   Coordenada Y: CY={first_tx['cy']} (pixel range: Y={first_tx['y0']}-{first_tx['y1']})")
    print(f"   Texto: {first_tx['text']}\n")

    # Mostrar as 3 primeiras
    print(f"\n📊 PRIMEIRAS 3 TRANSACOES:\n")
    for i, tx in enumerate(transaction_candidates[:3], 1):
        print(f"{i}. Linha {tx['line']:2d} (CY={tx['cy']:4d}): {tx['text'][:90]}")
else:
    print("❌ Nenhuma transação encontrada")

print("\n" + "="*150 + "\n")
