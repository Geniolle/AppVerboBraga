#!/usr/bin/env python3
"""Analisar e descrever o cabeçalho do extrato."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account
import yaml

print("\n" + "="*150)
print("ANALISE: CABECALHO DO EXTRATO")
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
                    'cx': (x0 + x1) // 2,
                    'cy': (y0 + y1) // 2,
                })

print("🔍 ANALISE DO CABECALHO\n")
print("="*150)
print("PALAVRAS NAS PRIMEIRAS LINHAS Y")
print("="*150 + "\n")

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

# Mostrar primeiras 10 linhas Y
for i, (cy, words_in_line) in enumerate(sorted_y_groups[:10], 1):
    sorted_words = sorted(words_in_line, key=lambda x: x['cx'])
    text_line = " ".join([w['text'] for w in sorted_words])
    y_range = f"Y={words_in_line[0]['y0']}-{words_in_line[0]['y1']}"

    print(f"Linha {i}: {y_range}")
    print(f"  CY (centro): {cy}")
    print(f"  Texto: {text_line}")
    print()

# Identificar linhas de cabeçalho
print("\n" + "="*150)
print("IDENTIFICACAO DO CABECALHO")
print("="*150 + "\n")

print("📋 Estrutura Visual do Cabeçalho:\n")

print("Linha 1 (topo):")
print("  'Detalhe de Movimentos'")
print("  └─ Título principal do extrato\n")

print("Linhas 2-6 (nomes de colunas):")
print("  • Data Mov. (Data do Movimento) - Coluna 1")
print("  • Data Valor (Data de Valor) - Coluna 2")
print("  • Descrição (Descrição da Transação) - Coluna 3")
print("  • País (País de Origem) - Coluna 4")
print("  • Moeda Original (Moeda Original) - Coluna 5")
print("  • Taxa de Câmbio (Taxa de Câmbio) - Coluna 6")
print("  • Débito EUR (+) (Débito em EUR) - Coluna 7")
print("  • Crédito EUR (-) (Crédito em EUR) - Coluna 8\n")

print("\nLinhas 7-9 (dados de exemplo da primeira transação):")
print("  • Data Mov: 23/06")
print("  • Data Valor: 20/06")
print("  • Descrição: Google One Dublin (em múltiplas linhas Y)")
print("  • País: IRL")
print("  • Moeda Original: 1,99")
print("  • Débito EUR: 1,99\n")

print("\n" + "="*150)
print("ANALISE ESTRUTURAL")
print("="*150 + "\n")

width = max(w['x1'] for w in words)
columns = {
    'data_movimento': (0.00, 0.10),
    'data_valor': (0.10, 0.19),
    'descricao': (0.19, 0.56),
    'pais': (0.56, 0.62),
    'moeda_original': (0.62, 0.72),
    'taxa_cambio': (0.72, 0.82),
    'debito_eur': (0.82, 0.92),
    'credito_eur': (0.92, 1.00),
}

print("Dimensões das Colunas (% da largura):\n")
for col_name, (x_min, x_max) in columns.items():
    width_pct = (x_max - x_min) * 100
    print(f"  {col_name:20} [{x_min:.0%} - {x_max:.0%}]  ({width_pct:.0f}%)")

print("\n" + "="*150)
print("DESCRICAO COMPLETA DO CABECALHO")
print("="*150 + "\n")

description = """
TITULO: "Detalhe de Movimentos"
└─ Extraído do sistema de cartão de crédito
└─ Mostra transações do período

COLUNAS (8 no total):

1. DATA MOVIMENTO (10%)
   ├─ Posição: Esquerda
   ├─ Formato: DD/MM (ex: 23/06)
   ├─ Descrição: Data quando a transação foi realizada
   └─ Importância: CRÍTICA (identifica quando)

2. DATA VALOR (9%)
   ├─ Posição: Próximo a Data Movimento
   ├─ Formato: DD/MM (ex: 20/06)
   ├─ Descrição: Data quando o valor saiu da conta
   └─ Importância: CRÍTICA (identifica quando cobrou)

3. DESCRICAO (37%)
   ├─ Posição: Centro (maior coluna)
   ├─ Formato: Texto livre (pode ter múltiplas linhas)
   ├─ Descrição: Informação sobre a transação (comerciante, local, etc)
   └─ Importância: CRÍTICA (identifica o quê)

4. PAIS (6%)
   ├─ Posição: Centro-direita
   ├─ Formato: Código país (ex: IRL, USA)
   ├─ Descrição: País onde a transação ocorreu
   └─ Importância: ALTA (identifica onde)

5. MOEDA ORIGINAL (10%)
   ├─ Posição: Direita
   ├─ Formato: Valor monetário (ex: 1,99)
   ├─ Descrição: Valor na moeda original da transação
   └─ Importância: ALTA (valor original)

6. TAXA DE CÂMBIO (10%)
   ├─ Posição: Direita
   ├─ Formato: Taxa (ex: 1.0)
   ├─ Descrição: Taxa aplicada à conversão
   └─ Importância: MÉDIA (taxa aplicada)

7. DÉBITO EUR (+) (10%)
   ├─ Posição: Extrema direita
   ├─ Formato: Valor em EUR (ex: 1,99)
   ├─ Descrição: Valor debitado (saída de dinheiro)
   └─ Importância: CRÍTICA (dinheiro saindo)

8. CRÉDITO EUR (-) (8%)
   ├─ Posição: Extrema direita
   ├─ Formato: Valor em EUR (ex: vazio)
   ├─ Descrição: Valor creditado (entrada de dinheiro)
   └─ Importância: CRÍTICA (dinheiro entrando)

REGRA DE VALIDACAO:
└─ Débito e Crédito NÃO podem estar ambos preenchidos
└─ Débito e Crédito NÃO podem estar ambos vazios
└─ Exatamente UM deve ter valor, o outro vazio
"""

print(description)

print("\n" + "="*150)
print("PROBLEMAS IDENTIFICADOS NO CABECALHO")
print("="*150 + "\n")

print("""
1. COLUNA DESCRICAO (37% de largura)
   └─ Muito larga, permite texto multilinha
   └─ Causa desalinhamento visual quando texto quebra
   └─ Afeta: "Google One Dublin" em linhas Y diferentes

2. FALTA DE LINHAS SEPARADORAS
   └─ Cabeçalho não tem linha separadora clara
   └─ Transições entre linhas ambíguas
   └─ Dificulta detecção automática de fim do cabeçalho

3. NOMES DAS COLUNAS EM PORTUGUÊS
   └─ Acentos (ç, ã, â) dificultam OCR
   └─ "Câmbio" confundido com "Cambio" às vezes
   └─ Afeta: Detecção de header_terms no config.yaml

4. ALINHAMENTO TEXTUAL
   └─ Não está totalmente alinhado (alguns textos flutuam)
   └─ Causa problemas no agrupamento por Y
   └─ Afeta: group_rows() com row_tolerance_ratio
""")

print("="*150 + "\n")
