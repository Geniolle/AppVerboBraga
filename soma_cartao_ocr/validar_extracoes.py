#!/usr/bin/env python3
"""Validar extrações na sheet CARTÃO vs imagem do extrato."""

import os
import yaml
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Carregar config
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
    range=f"{sheet_name}!A:H"
).execute()

values = result.get("values", [])

print("\n" + "="*120)
print("VALIDAÇÃO DE EXTRAÇÕES - SHEET CARTÃO vs IMAGEM DO EXTRATO")
print("="*120 + "\n")

print("DADOS EXTRAÍDOS NA SHEET CARTÃO:")
print("-" * 120)
print(f"{'LN':<3} {'Data Mov':<12} {'Data Valor':<12} {'Descrição':<35} {'País':<8} {'Moeda Orig':<12} {'Taxa Câmbio':<12} {'Débito EUR':<12}")
print("-" * 120)

# Ignorar cabeçalho e primeira linha vazia
for idx, row in enumerate(values[1:], 1):
    if len(row) < 8:
        row = row + [""] * (8 - len(row))

    data_mov = row[0] if len(row) > 0 else ""
    data_val = row[1] if len(row) > 1 else ""
    desc = row[2][:33] if len(row) > 2 else ""
    pais = row[3] if len(row) > 3 else ""
    moeda = row[4][:10] if len(row) > 4 else ""
    taxa = row[5] if len(row) > 5 else ""
    debito = row[6] if len(row) > 6 else ""

    print(f"{idx:<3} {data_mov:<12} {data_val:<12} {desc:<35} {pais:<8} {moeda:<12} {taxa:<12} {debito:<12}")

print("\n" + "="*120)
print("DADOS CORRETOS DA IMAGEM DO EXTRATO:")
print("="*120 + "\n")

dados_esperados = [
    ("23/06", "20/06", "Google One Dublin", "IRL", "", "", "1,99"),
    ("26/06", "25/06", "MERCADONA BRAGA", "", "", "", "35,15"),
    ("26/06", "26/06", "FACEBK 8HJ84THS72 Dublin", "IRL", "", "5,90", "5,90"),
    ("27/06", "26/06", "OPUS CLIP OPUS.PRO", "USA", "29,00", "", "29,00"),
    ("27/06", "26/06", "COMISSAO ESTRANGEIRO", "", "", "", "1,09"),
    ("27/06", "26/06", "IS-TGIS 17.3.4.", "", "", "", "0,04"),
    ("27/06", "27/06", "LEVANT. NUMERÁRIO A CRÉDITO", "", "", "", "0,04"),
    ("27/06", "27/06", "COMISSAO CASH", "", "", "", "160,00"),
    ("27/06", "27/06", "IS-TGIS 17.3.4.", "", "", "", "11,20"),
    ("27/06", "27/06", "CANVA 104920-25183857 CANVA.CO", "USA", "12,00", "", "12,00"),
    ("27/06", "27/06", "COMISSAO ESTRANGEIRO", "", "", "", "0,45"),
    ("27/06", "27/06", "IS-TGIS 17.3.4.", "", "", "", "0,02"),
    ("27/06", "27/06", "RECHEIO CASH & CARRYBRAGA", "", "", "", "31,08"),
    ("01/07", "30/06", "NO-IP 7758531883", "USA", "2,45 USD", "87,75500", "2,15"),
    ("01/07", "30/06", "COMISSAO ESTRANGEIRO", "", "", "", "0,08"),
    ("02/07", "01/07", "Google Workspace verbodavDubli", "IRL", "32,40", "", "32,40"),
    ("02/07", "01/07", "GOOGLE CLOUD HZ55XQ 8888888888", "IRL", "0,62", "", "0,62"),
]

print(f"{'LN':<3} {'Data Mov':<12} {'Data Valor':<12} {'Descrição':<35} {'País':<8} {'Moeda Orig':<12} {'Taxa Câmbio':<12} {'Débito EUR':<12}")
print("-" * 120)

for idx, (dm, dv, desc, pais, moeda, taxa, debito) in enumerate(dados_esperados, 1):
    print(f"{idx:<3} {dm:<12} {dv:<12} {desc:<35} {pais:<8} {moeda:<12} {taxa:<12} {debito:<12}")

print("\n" + "="*120)
print("ANÁLISE DE DISCREPÂNCIAS:")
print("="*120 + "\n")

discrepancias = []

for idx, (dm_esp, dv_esp, desc_esp, pais_esp, moeda_esp, taxa_esp, debito_esp) in enumerate(dados_esperados, 1):
    if idx < len(values):
        row = values[idx]
        if len(row) < 8:
            row = row + [""] * (8 - len(row))

        dm_obs = row[0]
        dv_obs = row[1]
        desc_obs = row[2]
        pais_obs = row[3] if len(row) > 3 else ""
        moeda_obs = row[4] if len(row) > 4 else ""
        taxa_obs = row[5] if len(row) > 5 else ""
        debito_obs = row[6] if len(row) > 6 else ""

        # Comparar
        if desc_obs != desc_esp:
            discrepancias.append(f"Linha {idx}: Descrição")
            print(f"⚠ Linha {idx} - DESCRIÇÃO:")
            print(f"  Esperado: '{desc_esp}'")
            print(f"  Observado: '{desc_obs}'")
            print()

        if pais_obs != pais_esp:
            discrepancias.append(f"Linha {idx}: País")
            print(f"⚠ Linha {idx} - PAÍS:")
            print(f"  Esperado: '{pais_esp}'")
            print(f"  Observado: '{pais_obs}'")
            print()

        if moeda_obs != moeda_esp:
            discrepancias.append(f"Linha {idx}: Moeda Original")
            print(f"⚠ Linha {idx} - MOEDA ORIGINAL:")
            print(f"  Esperado: '{moeda_esp}'")
            print(f"  Observado: '{moeda_obs}'")
            print()

        if taxa_obs != taxa_esp:
            discrepancias.append(f"Linha {idx}: Taxa Câmbio")
            print(f"⚠ Linha {idx} - TAXA CÂMBIO:")
            print(f"  Esperado: '{taxa_esp}'")
            print(f"  Observado: '{taxa_obs}'")
            print()

        if debito_obs != debito_esp:
            discrepancias.append(f"Linha {idx}: Débito")
            print(f"⚠ Linha {idx} - DÉBITO EUR:")
            print(f"  Esperado: '{debito_esp}'")
            print(f"  Observado: '{debito_obs}'")
            print()

if not discrepancias:
    print("✓ NENHUMA DISCREPÂNCIA ENCONTRADA - Todas as extrações estão corretas!")
else:
    print(f"\nTotal de discrepâncias: {len(discrepancias)}")

print("\n" + "="*120 + "\n")
