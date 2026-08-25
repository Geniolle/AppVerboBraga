#!/usr/bin/env python3
"""Reescrever Transação 1 (Google One Dublin) na Sheet com dados completos."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build
import yaml

print("\n" + "="*200)
print("REESCRITA: TRANSACAO 1 - GOOGLE ONE DUBLIN")
print("="*200 + "\n")

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

print("📋 DADOS COMPLETOS DA TRANSACAO 1:\n")

transacao_1_completa = {
    'ID_INTERNO': 'CAR0000000001',
    'Data Mov.': '23/06/2026',
    'Data Valor': '20/06/2026',
    'Descrição': 'Google One Dublin',
    'País': 'IRL',
    'Moeda Original': '1,99',
    'Taxa de Câmbio': '',
    'Débito EUR (+)': '1,99',
    'Crédito EUR (-)': '',
}

for campo, valor in transacao_1_completa.items():
    print(f"  {campo:20s} = {valor or '(vazio)'}")

print("\n" + "="*200)
print("LENDO SHEET ATUAL...")
print("="*200 + "\n")

# Ler a sheet
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{worksheet}!A:I"
).execute()

rows = result.get('values', [])

print(f"Linhas na Sheet: {len(rows)}\n")

if len(rows) < 2:
    print("❌ Sheet não tem dados suficientes!")
    sys.exit(1)

# Mostrar dados atuais da linha 2
print("Dados atuais da Linha 2 (Transação 1):\n")
current_row = rows[1]
header = rows[0]

for i, (col_name, value) in enumerate(zip(header, current_row if current_row else [])):
    print(f"  {i}: {col_name:20s} = {value}")

print("\n" + "="*200)
print("REESCREVENDO NA SHEET...")
print("="*200 + "\n")

# Preparar dados para escrever
new_row = [
    transacao_1_completa['ID_INTERNO'],
    transacao_1_completa['Data Mov.'],
    transacao_1_completa['Data Valor'],
    transacao_1_completa['Descrição'],
    transacao_1_completa['País'],
    transacao_1_completa['Moeda Original'],
    transacao_1_completa['Taxa de Câmbio'],
    transacao_1_completa['Débito EUR (+)'],
    transacao_1_completa['Crédito EUR (-)'],
]

# Atualizar linha 2
try:
    request = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A2:I2",
        valueInputOption="USER_ENTERED",
        body={'values': [new_row]}
    )

    response = request.execute()

    print(f"✅ REESCRITA COM SUCESSO!\n")
    print(f"Range: {worksheet}!A2:I2")
    print(f"Células atualizadas: {response.get('updatedCells', 'desconhecido')}")
    print(f"Colunas atualizadas: {response.get('updatedColumns', 'desconhecido')}")

    print("\n" + "="*200)
    print("CONFIRMACAO: LINHA 2 REESCRITA")
    print("="*200 + "\n")

    # Ler novamente para confirmar
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A2:I2"
    ).execute()

    updated_row = result.get('values', [])[0] if result.get('values') else []

    print(f"Linha 2 (REESCRITA):\n")

    headers = rows[0]
    for i, (header_col, value) in enumerate(zip(headers, updated_row)):
        status = "✅" if value else "❌"
        print(f"  {status} {i}: {header_col:20s} = {value}")

    print("\n" + "="*200)
    print("RESUMO DA REESCRITA")
    print("="*200 + "\n")

    print("Transação 1: Google One Dublin")
    print("─" * 100)
    print(f"ID:              CAR0000000001 ✅")
    print(f"Data Movimento:  23/06/2026 ✅")
    print(f"Data Valor:      20/06/2026 ✅")
    print(f"Descrição:       Google One Dublin ✅")
    print(f"País:            IRL ✅")
    print(f"Moeda Original:  1,99 EUR ✅")
    print(f"Taxa Câmbio:     (vazio)")
    print(f"Débito EUR:      1,99 ✅")
    print(f"Crédito EUR:     (vazio)")

    print("\n✅ Transação 1 reescrita com sucesso na Sheet!\n")

except Exception as e:
    print(f"❌ ERRO ao reescrever: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*200 + "\n")
