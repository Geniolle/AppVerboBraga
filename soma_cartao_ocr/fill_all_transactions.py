#!/usr/bin/env python3
"""Preencher todas as linhas de transações na Google Sheet."""

import sys
import os
from pathlib import Path
import json

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build
import yaml

print("\n" + "="*150)
print("PREENCHIMENTO: TODAS AS TRANSACOES")
print("="*150 + "\n")

# Carregar config
with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# Carregar resultado.json
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

print(f"📋 CONFIGURACAO:\n")
print(f"  Spreadsheet: {spreadsheet_id}")
print(f"  Worksheet: {worksheet}")
print(f"  ID Prefix: {id_prefix}")
print(f"  ID Digits: {id_digits}\n")

# Ler Sheet atual
print("📊 LENDO SHEET ATUAL...\n")

result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{worksheet}!A:I"
).execute()

rows = result.get('values', [])
print(f"Linhas atuais: {len(rows)}\n")

# Extrair movimentos do resultado.json
movimentos = resultado.get('movimentos', [])
print(f"Movimentos extraídos: {len(movimentos)}\n")

# Preparar linhas a adicionar (pulando o Google One Dublin que já existe)
linhas_para_adicionar = []
next_id_num = 2  # Começar de 2, já que CAR0000000001 é o Google One Dublin

print("="*150)
print("PREPARANDO LINHAS A ADICIONAR")
print("="*150 + "\n")

for idx, movimento in enumerate(movimentos, 1):
    # Pular se for a transação Google One Dublin (já gravada)
    if 'Google One Dublin' in movimento.get('descricao', ''):
        print(f"{idx}. ⏭️  PULANDO: {movimento.get('descricao', '')} (já gravada)")
        continue

    # Preparar ID
    id_interno = f"{id_prefix}{next_id_num:0{id_digits}d}"
    next_id_num += 1

    # Preparar dados
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

    linhas_para_adicionar.append(linha)

    status = movimento.get('status', '')
    print(f"{idx}. ✅ {id_interno} | {movimento.get('descricao', '')[:40]:40s} | {status}")

print(f"\n📝 Total de linhas a adicionar: {len(linhas_para_adicionar)}\n")

if not linhas_para_adicionar:
    print("❌ Nenhuma linha para adicionar!")
    sys.exit(1)

print("="*150)
print("GRAVANDO NA SHEET...")
print("="*150 + "\n")

# Gravar todas as linhas de uma vez
try:
    # Começar a partir da linha 3 (linha 1 = cabeçalho, linha 2 = Google One Dublin)
    start_row = len(rows) + 1

    request = sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A{start_row}:I",
        valueInputOption="USER_ENTERED",
        body={
            'values': linhas_para_adicionar
        }
    )

    response = request.execute()

    print(f"✅ GRAVADO COM SUCESSO!\n")
    print(f"Linhas adicionadas: {response.get('updates', {}).get('updatedRows', 'desconhecido')}")
    print(f"Colunas atualizadas: {response.get('updates', {}).get('updatedColumns', 'desconhecido')}")

    print("\n" + "="*150)
    print("CONFIRMACAO: ULTIMAS LINHAS NA SHEET")
    print("="*150 + "\n")

    # Ler Sheet atualizada
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A:I"
    ).execute()

    rows_atualizado = result.get('values', [])

    print(f"Total de linhas na Sheet agora: {len(rows_atualizado)}\n")

    # Mostrar últimas 5 linhas
    print("Últimas 5 linhas adicionadas:\n")
    for row in rows_atualizado[-5:]:
        if row:
            id_col = row[0] if row else ""
            desc_col = row[3] if len(row) > 3 else ""
            debito_col = row[7] if len(row) > 7 else ""
            print(f"  {id_col:15s} | {desc_col:40s} | Débito: {debito_col}")

    print(f"\n✅ Todas as transações gravadas com sucesso na Sheet!\n")

except Exception as e:
    print(f"❌ ERRO ao gravar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*150)
print("RESUMO FINAL")
print("="*150 + "\n")

print(f"✅ Transações gravadas: {len(linhas_para_adicionar)}")
print(f"✅ Google One Dublin (ID: CAR0000000001) - já gravada")
print(f"✅ Outras transações - IDs de CAR{2:0{id_digits}d} a CAR{next_id_num-1:0{id_digits}d}")
print(f"✅ Total de linhas na Sheet: {len(rows_atualizado)}")

print("\n" + "="*150 + "\n")
