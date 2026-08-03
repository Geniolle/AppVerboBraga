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

result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range='EXTRATO_CARTÃO!A:D'
).execute()

rows = result.get('values', [])

print('\n' + '='*150)
print('ESTADO ATUAL: EXTRATO_CARTÃO')
print('='*150 + '\n')

for i, row in enumerate(rows[:10], 1):
    if i == 1:
        print(f'[CABEÇALHO] {" | ".join(row)}\n')
    else:
        print(f'[Linha {i}] {" | ".join(row) if row else "(vazia)"}')

print('\n' + '='*150 + '\n')
