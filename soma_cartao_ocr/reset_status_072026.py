#!/usr/bin/env python3
"""Script para resetar o status do extrato 07/2026."""

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

# Ler a sheet EXTRATO_CARTÃO
sheet_name = "EXTRATO_CARTÃO"
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{sheet_name}!A:D"
).execute()

values = result.get("values", [])

# Encontrar a linha com 07/2026
print("\n" + "="*80)
print("RESETANDO STATUS DO EXTRATO 07/2026")
print("="*80 + "\n")

for idx, row in enumerate(values, 1):
    if len(row) > 0 and "07/2026" in str(row[0]):
        print(f"Encontrada na linha {idx}: {row}")

        # Limpar o STATUS (coluna 3, índice 2)
        update_range = f"{sheet_name}!C{idx}"

        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=update_range,
            valueInputOption="RAW",
            body={"values": [[""]]}
        ).execute()

        print(f"✓ STATUS resetado na linha {idx}")
        print(f"✓ Pronto para reprocessamento\n")
        break
else:
    print("✗ Extrato 07/2026 não encontrado\n")

print("="*80 + "\n")
