#!/usr/bin/env python3
"""Contar linhas preenchidas na sheet CARTÃO."""

import os
import yaml
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Carregar configuração
with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# Autenticar
service_account_file = os.path.expanduser(cfg["google"]["service_account_file"])
credentials = service_account.Credentials.from_service_account_file(
    service_account_file,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
sheets_service = build("sheets", "v4", credentials=credentials)

# Obter ID da spreadsheet
spreadsheet_id = str(cfg["google_sheets"]["spreadsheet_id"]).strip()

# Ler a sheet CARTÃO
sheet_name = "CARTÃO"
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{sheet_name}!A:L"
).execute()

values = result.get("values", [])

print("\n" + "="*80)
print(f"ANÁLISE DA SHEET '{sheet_name}'")
print("="*80 + "\n")

total_linhas = len(values)
linhas_preenchidas = sum(1 for row in values if any(cell for cell in row))
linhas_dados = total_linhas - 1  # Excluir cabeçalho

print(f"Total de linhas (incluindo cabeçalho): {total_linhas}")
print(f"Total de linhas com dados: {linhas_dados}")
print(f"Linhas preenchidas (com algum conteúdo): {linhas_preenchidas}")

# Mostrar algumas linhas para validação
print(f"\nPrimeiras 5 linhas:")
print("-" * 80)
for idx, row in enumerate(values[:5], 1):
    print(f"Linha {idx}: {row[:5]}...")  # Mostrar primeiras 5 colunas

print(f"\nÚltimas 5 linhas:")
print("-" * 80)
for idx, row in enumerate(values[-5:], len(values)-4):
    print(f"Linha {idx}: {row[:5]}...")

print("\n" + "="*80 + "\n")
