#!/usr/bin/env python3
"""Atualizar a transação Google One Dublin com os valores encontrados."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build
import yaml

print("\n" + "="*150)
print("ATUALIZACAO: GOOGLE ONE DUBLIN COM VALORES")
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

print("📊 DADOS ATUALIZADOS:\n")

# Dados atualizados
transacao_atualizada = {
    'Data Mov.': '23/06/2026',
    'Data Valor': '20/06/2026',
    'Descrição': 'Google One Dublin',
    'País': 'IRL',
    'Moeda Original': '1,99',
    'Taxa de Câmbio': '',
    'Débito EUR (+)': '1,99',
    'Crédito EUR (-)': '',
}

for campo, valor in transacao_atualizada.items():
    print(f"  {campo:20s} = {valor or '(vazio)'}")

print("\n" + "="*150)
print("LOCALIZANDO ULTIMA LINHA NA SHEET...")
print("="*150 + "\n")

# Ler a sheet
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{worksheet}!A:H"
).execute()

rows = result.get('values', [])

print(f"Total de linhas na Sheet: {len(rows)}\n")

# Encontrar linha com "Google One Dublin"
google_one_line = None
for row_idx, row in enumerate(rows):
    if len(row) > 2 and 'Google One Dublin' in row[2]:
        google_one_line = row_idx
        print(f"✅ Encontrada linha {row_idx + 1} com 'Google One Dublin'")
        print(f"   Dados atuais: {row}")
        break

if not google_one_line:
    print("❌ Linha com 'Google One Dublin' não encontrada!")
    sys.exit(1)

print("\n" + "="*150)
print("ATUALIZANDO SHEET...")
print("="*150 + "\n")

# Preparar nova linha com valores completos
new_row = [
    transacao_atualizada['Data Mov.'],
    transacao_atualizada['Data Valor'],
    transacao_atualizada['Descrição'],
    transacao_atualizada['País'],
    transacao_atualizada['Moeda Original'],
    transacao_atualizada['Taxa de Câmbio'],
    transacao_atualizada['Débito EUR (+)'],
    transacao_atualizada['Crédito EUR (-)'],
]

# Atualizar a linha
range_to_update = f"{worksheet}!A{google_one_line + 1}:H{google_one_line + 1}"

try:
    request = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_to_update,
        valueInputOption="USER_ENTERED",
        body={
            'values': [new_row]
        }
    )

    response = request.execute()

    print(f"✅ ATUALIZADO COM SUCESSO!\n")
    print(f"Range: {range_to_update}")
    print(f"Células atualizadas: {response.get('updatedCells', 'desconhecido')}")
    print(f"Colunas atualizadas: {response.get('updatedColumns', 'desconhecido')}")
    print(f"Linhas atualizadas: {response.get('updatedRows', 'desconhecido')}")

    print("\n" + "="*150)
    print("CONFIRMACAO: LINHA ATUALIZADA NA SHEET")
    print("="*150 + "\n")

    # Ler a linha atualizada
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_to_update
    ).execute()

    updated_row = result.get('values', [])[0] if result.get('values') else []

    print(f"Linha {google_one_line + 1} (atualizada):\n")

    headers = rows[0]
    for i, (header, value) in enumerate(zip(headers, updated_row)):
        status = "✅" if value else "❌"
        print(f"  {status} {header:20s} = {value}")

    print("\n" + "="*150)
    print("RESUMO DA ATUALIZACAO")
    print("="*150 + "\n")

    print(f"Transação: Google One Dublin")
    print(f"Data Mov.: 23/06/2026")
    print(f"Data Valor: 20/06/2026")
    print(f"País: IRL")
    print(f"Moeda Original: 1,99 ✅ ADICIONADO")
    print(f"Débito EUR: 1,99 ✅ ADICIONADO")

    print("\n✅ Transação atualizada com sucesso na Sheet!\n")

except Exception as e:
    print(f"❌ ERRO ao atualizar: {e}")
    sys.exit(1)

print("="*150 + "\n")
