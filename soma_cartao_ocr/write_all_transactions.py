#!/usr/bin/env python3
"""Escrever todas as 17 transações na Sheet com dados do resultado.json + correções da imagem."""

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
print("ESCRITA COMPLETA: TODAS AS 17 TRANSACOES")
print("="*200 + "\n")

# Carregar config
with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# Carregar resultado
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

    # CORRECAO: Transação 1 tem datas erradas em resultado.json
    # Usar datas verificadas na imagem: 23/06 (movimento) e 20/06 (valor)
    if idx == 1:
        data_movimento = "23/06"  # Corrigido da imagem
        data_valor = "20/06"       # Corrigido da imagem
    else:
        data_movimento = movimento.get('data_movimento', '')
        data_valor = movimento.get('data_valor', '')

    linha = [
        id_interno,
        data_movimento,
        data_valor,
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

    # Marcar Transação 1 como corrigida
    marker = " [DATAS CORRIGIDAS DA IMAGEM]" if idx == 1 else ""
    print(f"  {idx:2d}. {id_interno} | {desc:30s} | {status}{marker}")

print(f"\n✅ Total de linhas preparadas: {len(linhas)}\n")

print("="*200)
print("GRAVANDO NA SHEET...")
print("="*200 + "\n")

try:
    # Escrever cabeçalho + linhas
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

    # Mostrar primeiras 3 linhas
    print("PRIMEIRAS 3 LINHAS:\n")
    for i in range(min(3, len(rows_confirmed))):
        row = rows_confirmed[i]
        if i == 0:
            print(f"  Linha 1 (CABEÇALHO):")
            print(f"    {' | '.join(row)}")
        else:
            print(f"  Linha {i+1}:")
            print(f"    ID: {row[0] if len(row) > 0 else ''}")
            print(f"    Data Mov: {row[1] if len(row) > 1 else ''}")
            print(f"    Data Valor: {row[2] if len(row) > 2 else ''}")
            print(f"    Descrição: {row[3] if len(row) > 3 else ''}")
            if i == 1:
                print(f"    ✅ CORRIGIDO COM DATAS DA IMAGEM")
            print()

    print("\nULTIMAS 3 LINHAS:\n")
    for i in range(max(0, len(rows_confirmed)-3), len(rows_confirmed)):
        row = rows_confirmed[i]
        if len(row) > 0 and i > 0:  # Skip header
            print(f"  Linha {i+1}:")
            print(f"    ID: {row[0]}")
            print(f"    Descrição: {row[3] if len(row) > 3 else ''}")

    print("\n" + "="*200)
    print("RESUMO FINAL")
    print("="*200 + "\n")

    print(f"✅ Sheet COMPLETA com TODAS as transações!")
    print(f"✅ Total de transações: {len(linhas)}")
    print(f"✅ Transação 1: CAR0000000001 - Google One Dublin [DATAS CORRIGIDAS: 23/06 → 20/06]")
    print(f"✅ Transações 2-{len(linhas)}: Usando dados de resultado.json")

    print("\n" + "="*200 + "\n")

except Exception as e:
    print(f"❌ ERRO ao gravar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
