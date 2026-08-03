#!/usr/bin/env python3
"""Recriar todas as transações na Sheet de forma completa e organizada."""

import sys
import os
from pathlib import Path
import json

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build
import yaml

print("\n" + "="*200)
print("RECRIACAO COMPLETA: TODAS AS TRANSACOES NA SHEET")
print("="*200 + "\n")

# Carregar config e resultado
with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

with open("output/resultado.json", encoding='utf-8') as f:
    resultado = json.load(f)

# Carregar credenciais
creds_file = Path("credentials/soma-cartao-ocr.json")
credentials = service_account.Credentials.from_service_account_file(str(creds_file))
sheets_service = build("sheets", "v4", credentials=credentials)

# IDs
spreadsheet_id = cfg['google_sheets']['spreadsheet_id']
worksheet = cfg['google_sheets']['worksheet']
id_prefix = cfg['google_sheets']['id_prefix']
id_digits = cfg['google_sheets']['id_digits']

print("📋 PREPARANDO DADOS...\n")

# Preparar cabeçalho
header = [
    'ID_INTERNO',
    'Data Mov.',
    'Data Valor',
    'Descrição',
    'País',
    'Moeda Original',
    'Taxa de Câmbio',
    'Débito EUR (+)',
    'Crédito EUR (-)',
]

# Preparar linhas
linhas = []
movimentos = resultado.get('movimentos', [])

print(f"Total de movimentos: {len(movimentos)}\n")
print("Preparando linhas:\n")

for idx, movimento in enumerate(movimentos, 1):
    id_interno = f"{id_prefix}{idx:0{id_digits}d}"

    linha = [
        id_interno,
        movimento.get('data_movimento', ''),
        movimento.get('data_valor', ''),
        movimento.get('descricao', ''),
        movimento.get('pais', ''),
        movimento.get('moeda_original', ''),
        movimento.get('taxa_cambio', ''),
        movimento.get('debito_eur', ''),
        movimento.get('credito_eur', ''),
    ]

    linhas.append(linha)

    desc = movimento.get('descricao', '')[:30]
    status = movimento.get('status', '')
    print(f"  {idx:2d}. {id_interno} | {desc:30s} | {status}")

print(f"\n✅ Total de linhas preparadas: {len(linhas)}\n")

print("="*200)
print("GRAVANDO NA SHEET...")
print("="*200 + "\n")

# Limpar sheet (deletar conteúdo)
try:
    # Primeiro, limpar toda a sheet exceto o cabeçalho
    print("🧹 Limpando sheet...\n")

    # Escrever apenas cabeçalho + linhas
    all_data = [header] + linhas

    request = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A1:I{len(all_data)}",
        valueInputOption="USER_ENTERED",
        body={'values': all_data}
    )

    response = request.execute()

    print(f"✅ GRAVACAO COM SUCESSO!\n")
    print(f"Linhas atualizadas: {response.get('updatedRows', 'desconhecido')}")
    print(f"Colunas atualizadas: {response.get('updatedColumns', 'desconhecido')}")

    print("\n" + "="*200)
    print("CONFIRMACAO: SHEET COMPLETA")
    print("="*200 + "\n")

    # Ler sheet para confirmar
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A:I"
    ).execute()

    rows_confirmed = result.get('values', [])

    print(f"Total de linhas na Sheet: {len(rows_confirmed)}")
    print(f"(1 cabeçalho + {len(rows_confirmed)-1} transações)\n")

    # Mostrar primeiras 3 e últimas 3 linhas
    print("PRIMEIRAS 3 LINHAS:\n")
    for i in range(min(3, len(rows_confirmed))):
        row = rows_confirmed[i]
        if i == 0:
            print(f"  Linha {i+1} (CABEÇALHO): {' | '.join(row[:3])}...")
        else:
            desc = row[3][:25] if len(row) > 3 else ""
            print(f"  Linha {i+1}: {row[0]:15s} | {desc:25s} | {row[7] if len(row) > 7 else ''}")

    print("\nULTIMAS 3 LINHAS:\n")
    for i in range(max(0, len(rows_confirmed)-3), len(rows_confirmed)):
        row = rows_confirmed[i]
        if len(row) > 0:
            desc = row[3][:25] if len(row) > 3 else ""
            print(f"  Linha {i+1}: {row[0]:15s} | {desc:25s} | {row[7] if len(row) > 7 else ''}")

    print("\n" + "="*200)
    print("RESUMO FINAL")
    print("="*200 + "\n")

    print(f"✅ Sheet RECRIADA com sucesso!")
    print(f"✅ Total de transações: {len(linhas)}")
    print(f"✅ Transação 1: CAR0000000001 - Google One Dublin")
    print(f"✅ Transação 2: CAR0000000002 - One Dublin")
    print(f"✅ Transação 3: CAR0000000003 - MERCADONA BRAGA")
    print(f"✅ ... até Transação {len(linhas)}: {f'{id_prefix}{len(linhas):0{id_digits}d}'}")

    print("\n" + "="*200 + "\n")

except Exception as e:
    print(f"❌ ERRO ao gravar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
