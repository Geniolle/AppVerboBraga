#!/usr/bin/env python3
"""Verificar a primeira transação agora gravada na Sheet."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build
import yaml

print("\n" + "="*150)
print("VERIFICACAO: PRIMEIRA TRANSACAO NA SHEET (APOS CORRECAO)")
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

# Ler dados da sheet - ULTIMAS LINHAS (mais recentes)
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{worksheet}!A:H"
).execute()

rows = result.get('values', [])

print(f"📊 DADOS NA SHEET (últimas linhas adicionadas)\n")
print(f"Total de linhas: {len(rows)}\n")

if len(rows) > 1:
    header = rows[0]

    # Mostrar as ULTIMAS 5 linhas (mais recentes)
    print("ÚLTIMAS 5 LINHAS ADICIONADAS:\n")
    start = max(1, len(rows) - 5)
    for row_idx in range(start, len(rows)):
        row = rows[row_idx]
        print(f"Linha {row_idx} (ID: CAR{row_idx:010d}):")
        for col_idx, col_name in enumerate(header):
            value = row[col_idx] if col_idx < len(row) else ""
            print(f"  {col_name:20s} = {value}")
        print()

    # Procurar por "Google" nas últimas transações
    print("\n" + "="*150)
    print("PROCURANDO 'GOOGLE' NAS ULTIMAS TRANSACOES")
    print("="*150 + "\n")

    for row_idx in range(start, len(rows)):
        row = rows[row_idx]
        if len(row) > 2:
            desc = row[2].lower() if row[2] else ""
            if "google" in desc:
                print(f"✅ ENCONTRADO 'Google' na Linha {row_idx}:\n")
                for col_idx, col_name in enumerate(header):
                    value = row[col_idx] if col_idx < len(row) else ""
                    print(f"  {col_name:20s} = {value}")
                print()

    # Verificar primeira linha com "One Dublin"
    print("\n" + "="*150)
    print("PRIMEIRAS TRANSACOES GRAVADAS")
    print("="*150 + "\n")

    for row_idx in range(1, min(6, len(rows))):
        row = rows[row_idx]
        data_mov = row[0] if len(row) > 0 else ""
        data_valor = row[1] if len(row) > 1 else ""
        desc = row[2] if len(row) > 2 else ""
        debito = row[6] if len(row) > 6 else ""

        print(f"Linha {row_idx}: {data_mov:12s} | {data_valor:12s} | {desc:40s} | Débito: {debito}")

print("\n" + "="*150 + "\n")
