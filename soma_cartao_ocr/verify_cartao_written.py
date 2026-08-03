#!/usr/bin/env python3
import sys, os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build

creds_file = Path('credentials/soma-cartao-ocr.json')
credentials = service_account.Credentials.from_service_account_file(str(creds_file))
sheets_service = build('sheets', 'v4', credentials=credentials)

spreadsheet_id = '1poVWJGSBb13_2S1YKEzvFmkB9Ru0ZVzfQ0OEcMkfOZw'

# Verificar CARTÃO
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range='CARTÃO!A:I'
).execute()

rows_cartao = result.get('values', [])

print('\n' + '='*150)
print('DADOS NA SHEET CARTÃO')
print('='*150)
print(f'\nTotal de linhas: {len(rows_cartao)} (1 cabeçalho + {len(rows_cartao)-1} transações)\n')

print('PRIMEIRAS 3 LINHAS:\n')
for i in range(min(3, len(rows_cartao))):
    row = rows_cartao[i]
    if i == 0:
        print(f'[Cabeçalho] {" | ".join(row[:4])}...')
    else:
        print(f'[Linha {i+1}] ID: {row[0] if len(row) > 0 else ""} | Data: {row[1] if len(row) > 1 else ""}/{row[2] if len(row) > 2 else ""} | Desc: {row[3] if len(row) > 3 else ""}')

print('\nÚLTIMAS 3 LINHAS:\n')
for i in range(max(0, len(rows_cartao)-3), len(rows_cartao)):
    row = rows_cartao[i]
    if i > 0:
        print(f'[Linha {i+1}] ID: {row[0] if len(row) > 0 else ""} | Desc: {row[3] if len(row) > 3 else ""}')

print('\n' + '='*150 + '\n')

# Verificar EXTRATO_CARTÃO
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range='EXTRATO_CARTÃO!A:D'
).execute()

rows_extratos = result.get('values', [])

print('='*150)
print('ESTADO DA SHEET EXTRATO_CARTÃO')
print('='*150 + '\n')

for i, row in enumerate(rows_extratos[:5], 1):
    if i == 1:
        print(f'[CABEÇALHO] {" | ".join(row)}\n')
    else:
        print(f'[Linha {i}] {" | ".join(row) if row else "(vazia)"}')

print('\n' + '='*150 + '\n')
