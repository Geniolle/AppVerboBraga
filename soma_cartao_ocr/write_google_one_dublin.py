#!/usr/bin/env python3
"""Gravar a transação Google One Dublin na Google Sheet com os dados que temos."""

import sys
import os
from pathlib import Path
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build
import yaml

print("\n" + "="*150)
print("GRAVACAO: TRANSACAO GOOGLE ONE DUBLIN")
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

# Dados da transação
transacao = {
    'Data Mov.': '23/06/2026',
    'Data Valor': '20/06/2026',
    'Descrição': 'Google One Dublin',
    'País': 'IRL',
    'Moeda Original': '',
    'Taxa de Câmbio': '',
    'Débito EUR (+)': '',
    'Crédito EUR (-)': '',
}

print("📋 DADOS A GRAVAR:\n")
for campo, valor in transacao.items():
    print(f"  {campo:20s} = {valor or '(vazio)'}")

print("\n" + "="*150)
print("GRAVANDO NA GOOGLE SHEET...")
print("="*150 + "\n")

# Preparar linha para adicionar
row_values = [
    transacao['Data Mov.'],
    transacao['Data Valor'],
    transacao['Descrição'],
    transacao['País'],
    transacao['Moeda Original'],
    transacao['Taxa de Câmbio'],
    transacao['Débito EUR (+)'],
    transacao['Crédito EUR (-)'],
]

# Gravar na sheet
try:
    request = sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A:H",
        valueInputOption="USER_ENTERED",
        body={
            'values': [row_values]
        }
    )

    response = request.execute()

    print(f"✅ GRAVADO COM SUCESSO!\n")
    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"Worksheet: {worksheet}")
    print(f"Linha adicionada: {response.get('updates', {}).get('updatedRows', 'desconhecido')}")
    print(f"Colunas atualizadas: {response.get('updates', {}).get('updatedColumns', 'desconhecido')}")

    # Ler a sheet para confirmar
    print("\n" + "="*150)
    print("CONFIRMACAO: ULTIMAS LINHAS NA SHEET")
    print("="*150 + "\n")

    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A:H"
    ).execute()

    rows = result.get('values', [])

    if len(rows) > 1:
        header = rows[0]
        print("Cabeçalho:")
        for i, col in enumerate(header):
            print(f"  Col {i}: {col}")

        print("\nÚltimas 3 linhas:")
        for row in rows[-3:]:
            print(f"  {row}")

    print("\n✅ Transação 'Google One Dublin' gravada com sucesso na Sheet!")

except Exception as e:
    print(f"❌ ERRO ao gravar: {e}")
    sys.exit(1)

print("\n" + "="*150 + "\n")
