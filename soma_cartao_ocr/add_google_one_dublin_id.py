#!/usr/bin/env python3
"""Adicionar ID_INTERNO à transação Google One Dublin."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build
import yaml

print("\n" + "="*150)
print("ADICIONAR ID_INTERNO: GOOGLE ONE DUBLIN")
print("="*150 + "\n")

# Carregar config
with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# Carregar credenciais
creds_file = Path("credentials/soma-cartao-ocr.json")
credentials = service_account.Credentials.from_service_account_file(str(creds_file))
sheets_service = build("sheets", "v4", credentials=credentials)

# IDs
spreadsheet_id = cfg['google_sheets']['spreadsheet_id']
worksheet = cfg['google_sheets']['worksheet']
id_prefix = cfg['google_sheets']['id_prefix']
id_digits = cfg['google_sheets']['id_digits']

print(f"📋 CONFIG:\n")
print(f"  ID Prefix: {id_prefix}")
print(f"  ID Digits: {id_digits}")
print(f"  Padrão: {id_prefix}{'0' * id_digits}\n")

# Ler a sheet
print("📊 LENDO SHEET...\n")

result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{worksheet}!A:H"
).execute()

rows = result.get('values', [])

print(f"Total de linhas: {len(rows)}\n")

# Verificar estrutura - precisa inserir coluna de ID
header = rows[0] if rows else []

print(f"Cabeçalho atual: {header}\n")

# Se não tiver coluna de ID, precisa adicionar
if not header or header[0] != 'ID_INTERNO':
    print("⚠️  Cabeçalho não tem coluna ID_INTERNO na primeira posição")
    print("📝 Será criada coluna ID_INTERNO\n")

# Encontrar linha com "Google One Dublin"
google_one_line = None
for row_idx, row in enumerate(rows):
    if len(row) > 2 and 'Google One Dublin' in row[2]:
        google_one_line = row_idx
        print(f"✅ Encontrada linha {row_idx + 1} com 'Google One Dublin'")
        break

if not google_one_line:
    print("❌ Linha com 'Google One Dublin' não encontrada!")
    sys.exit(1)

# Calcular próximo ID
# Se temos dados anteriores, pega o último ID
max_id_num = 0

for row in rows[1:]:  # Pula cabeçalho
    if row and row[0]:
        id_str = row[0]
        # Tenta extrair número do ID
        if id_str.startswith(id_prefix):
            try:
                num = int(id_str[len(id_prefix):])
                max_id_num = max(max_id_num, num)
            except:
                pass

next_id_num = max_id_num + 1
next_id = f"{id_prefix}{next_id_num:0{id_digits}d}"

print(f"\n📍 Calculando próximo ID:")
print(f"  Último ID número: {max_id_num}")
print(f"  Próximo ID: {next_id}\n")

print("="*150)
print("ATUALIZANDO SHEET...")
print("="*150 + "\n")

# Primeiramente, adicionar/atualizar cabeçalho se necessário
if not header or header[0] != 'ID_INTERNO':
    # Inserir coluna de ID no cabeçalho
    new_header = ['ID_INTERNO'] + header

    print("📝 Atualizando cabeçalho com coluna ID_INTERNO...\n")

    request = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A1:I1",
        valueInputOption="USER_ENTERED",
        body={'values': [new_header]}
    )
    request.execute()
    print("✅ Cabeçalho atualizado\n")

# Agora adicionar ID à linha do Google One Dublin
# Número da linha no Google Sheets é (row_idx + 1)
# Mas se adicionou coluna de ID, precisa considerar isto
sheet_row_num = google_one_line + 1

# Preparar dados com ID no início
current_row = rows[google_one_line] if google_one_line < len(rows) else []

# Adicionar ID no início
new_row_with_id = [next_id] + current_row

print(f"Atualizando linha {sheet_row_num}:")
print(f"  ID adicionado: {next_id}")
print(f"  Dados: {current_row}\n")

# Atualizar linha com ID
request = sheets_service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range=f"{worksheet}!A{sheet_row_num}:I{sheet_row_num}",
    valueInputOption="USER_ENTERED",
    body={'values': [new_row_with_id]}
)

response = request.execute()

print(f"✅ ATUALIZADO COM SUCESSO!\n")
print(f"Células atualizadas: {response.get('updatedCells', 'desconhecido')}")
print(f"Colunas atualizadas: {response.get('updatedColumns', 'desconhecido')}")

# Confirmação
print("\n" + "="*150)
print("CONFIRMACAO: TRANSACAO COM ID")
print("="*150 + "\n")

result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{worksheet}!A{sheet_row_num}:I{sheet_row_num}"
).execute()

updated_row = result.get('values', [])[0] if result.get('values') else []

print(f"Linha {sheet_row_num} (com ID):\n")
print(f"  ID_INTERNO: {updated_row[0]}")
print(f"  Data Mov.: {updated_row[1] if len(updated_row) > 1 else '(vazio)'}")
print(f"  Data Valor: {updated_row[2] if len(updated_row) > 2 else '(vazio)'}")
print(f"  Descrição: {updated_row[3] if len(updated_row) > 3 else '(vazio)'}")
print(f"  País: {updated_row[4] if len(updated_row) > 4 else '(vazio)'}")
print(f"  Moeda Original: {updated_row[5] if len(updated_row) > 5 else '(vazio)'}")
print(f"  Débito EUR: {updated_row[7] if len(updated_row) > 7 else '(vazio)'}")

print("\n" + "="*150)
print("✅ ID_INTERNO ADICIONADO COM SUCESSO!")
print("="*150 + "\n")

print(f"Transação: Google One Dublin")
print(f"ID Único: {next_id}")

print("\n" + "="*150 + "\n")
