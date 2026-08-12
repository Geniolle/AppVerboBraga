#!/usr/bin/env python3
"""Comparar dados extraídos com dados na Google Sheet CARTÃO."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build
import yaml

print("\n" + "="*150)
print("COMPARACAO: DADOS EXTRAIDOS vs GOOGLE SHEET")
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

print(f"📊 Lendo Google Sheet: {worksheet}\n")
print(f"Spreadsheet ID: {spreadsheet_id}\n")

# Ler dados da sheet
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{worksheet}!A:H"
).execute()

rows = result.get('values', [])

print("="*150)
print("DADOS NA GOOGLE SHEET CARTÃO")
print("="*150 + "\n")

if len(rows) > 0:
    # Mostrar cabeçalho
    if len(rows) > 0:
        print("CABEÇALHO:")
        header = rows[0] if rows else []
        for i, col in enumerate(header):
            print(f"  Col {i}: {col}")
        print()

    # Mostrar primeiras 5 linhas
    print("PRIMEIRAS LINHAS DE DADOS:\n")
    for row_idx, row in enumerate(rows[1:6], 1):
        print(f"Linha {row_idx}:")
        for col_idx, value in enumerate(row if row else []):
            col_name = header[col_idx] if col_idx < len(header) else f"Col{col_idx}"
            print(f"  {col_name:20s} = {value}")
        print()

    # Filtrar por "Google" para encontrar a transação
    print("="*150)
    print("PROCURANDO TRANSACOES COM 'GOOGLE'")
    print("="*150 + "\n")

    google_rows = []
    for row_idx, row in enumerate(rows[1:], 1):  # Pula cabeçalho
        if len(row) > 2:  # Tem descrição
            desc = row[2].lower() if row[2] else ""
            if "google" in desc:
                google_rows.append((row_idx, row))

    if google_rows:
        print(f"Encontradas {len(google_rows)} transação(ções) com 'Google':\n")
        for row_idx, row in google_rows[:3]:  # Mostrar primeiras 3
            print(f"Linha {row_idx} da Sheet:")
            print(f"  Data Movimento: {row[0] if len(row) > 0 else '(vazio)'}")
            print(f"  Data Valor:     {row[1] if len(row) > 1 else '(vazio)'}")
            print(f"  Descrição:      {row[2] if len(row) > 2 else '(vazio)'}")
            print(f"  País:           {row[3] if len(row) > 3 else '(vazio)'}")
            print(f"  Moeda Original: {row[4] if len(row) > 4 else '(vazio)'}")
            print(f"  Taxa Câmbio:    {row[5] if len(row) > 5 else '(vazio)'}")
            print(f"  Débito EUR:     {row[6] if len(row) > 6 else '(vazio)'}")
            print(f"  Crédito EUR:    {row[7] if len(row) > 7 else '(vazio)'}")
            print()
    else:
        print("❌ Nenhuma transação com 'Google' encontrada na sheet")

else:
    print("❌ Sheet vazia ou sem acesso")

print("\n" + "="*150)
print("COMPARACAO: EXTRAIDO vs SHEET")
print("="*150 + "\n")

extracted = {
    "Data Movimento": "23/06",
    "Data Valor": "20/06",
    "Descrição": "Google One Dublin",
    "País": "IRL",
    "Moeda Original": "1,99",
    "Débito EUR": "1,99"
}

print("O que foi EXTRAÍDO da imagem:")
print("-" * 150)
for key, value in extracted.items():
    print(f"  {key:20s} = {value}")

print("\nO que está NA SHEET:")
print("-" * 150)
if google_rows:
    row_idx, row = google_rows[0]
    sheet_data = {
        "Data Movimento": row[0] if len(row) > 0 else "",
        "Data Valor": row[1] if len(row) > 1 else "",
        "Descrição": row[2] if len(row) > 2 else "",
        "País": row[3] if len(row) > 3 else "",
        "Moeda Original": row[4] if len(row) > 4 else "",
        "Débito EUR": row[6] if len(row) > 6 else "",
    }
    for key, value in sheet_data.items():
        print(f"  {key:20s} = {value}")

    print("\nDIFERENÇAS:")
    print("-" * 150)
    for key in extracted:
        ext = extracted.get(key, "")
        sheet = sheet_data.get(key, "")
        if ext != sheet:
            print(f"  ❌ {key:20s}")
            print(f"     Extraído: {ext}")
            print(f"     Sheet:    {sheet}")
        else:
            print(f"  ✅ {key:20s} (igual)")

print("\n" + "="*150 + "\n")
