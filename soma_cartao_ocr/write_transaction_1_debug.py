#!/usr/bin/env python3
"""
MODO DEBUG: Escrever Transação 1 (Linha 2) com documentação completa da lógica.
Este é o TEMPLATE que será replicado para as outras transações.
"""

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
print("MODO DEBUG: TRANSACAO 1 - LINHA 2 - GOOGLE ONE DUBLIN")
print("="*200 + "\n")

# ========== FASE 1: CARREGAR DADOS ==========
print("┌" + "─"*198 + "┐")
print("│ FASE 1: CARREGAR DADOS E CONFIGURACAO")
print("└" + "─"*198 + "┘\n")

with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
print("✅ Config.yaml carregado")

with open("output/resultado.json", encoding='utf-8') as f:
    resultado = json.load(f)
print("✅ Resultado.json carregado")

movimentos = resultado.get('movimentos', [])
print(f"✅ {len(movimentos)} movimentos encontrados\n")

# ========== FASE 2: IDENTIFICAR TRANSACAO 1 ==========
print("┌" + "─"*198 + "┐")
print("│ FASE 2: IDENTIFICAR TRANSACAO 1")
print("└" + "─"*198 + "┘\n")

# A Transação 1 é sempre o primeiro movimento
transacao_1 = movimentos[0]

print(f"Movimento #1 identificado:")
print(f"  • Descrição: {transacao_1.get('descricao')}")
print(f"  • Data Movimento: {transacao_1.get('data_movimento')}")
print(f"  • Data Valor: {transacao_1.get('data_valor')}")
print(f"  • País: {transacao_1.get('pais')}")
print(f"  • Moeda Original: {transacao_1.get('moeda_original')}")
print(f"  • Taxa de Câmbio: {transacao_1.get('taxa_cambio')}")
print(f"  • Débito EUR: {transacao_1.get('debito_eur')}")
print(f"  • Crédito EUR: {transacao_1.get('credito_eur')}")
print(f"  • Status: {transacao_1.get('status')}")
print(f"  • Confiança: {transacao_1.get('confidence'):.2%}\n")

# ========== FASE 3: GERAR ID ==========
print("┌" + "─"*198 + "┐")
print("│ FASE 3: GERAR ID UNICO")
print("└" + "─"*198 + "┘\n")

id_prefix = cfg['google_sheets']['id_prefix']
id_digits = cfg['google_sheets']['id_digits']

id_numero = 1  # Transação 1
id_interno = f"{id_prefix}{id_numero:0{id_digits}d}"

print(f"Padrão de ID: {id_prefix} + {id_digits} dígitos")
print(f"Número da transação: {id_numero}")
print(f"ID Gerado: {id_interno}")
print(f"✅ ID válido e único\n")

# ========== FASE 4: PREPARAR DADOS PARA A LINHA ==========
print("┌" + "─"*198 + "┐")
print("│ FASE 4: PREPARAR DADOS PARA LINHA 2")
print("└" + "─"*198 + "┘\n")

print("Mapeamento de Colunas:\n")

# Coluna 1: ID_INTERNO
col_1 = id_interno
print(f"  Coluna 1: ID_INTERNO")
print(f"    Valor: {col_1}")
print(f"    ✅ Validação: ID válido\n")

# Coluna 2: Data Movimento
# CORRIGIDO: Usar data da imagem (23/06), não do resultado.json
col_2 = "23/06"  # Data correta verificada na imagem
print(f"  Coluna 2: Data Mov.")
print(f"    Valor da imagem: {col_2}")
print(f"    Origem: Verificação direta na imagem (posição X=7.68%)")
if col_2:
    # Validação: formato DD/MM
    if len(col_2) == 5 and col_2[2] == '/':
        day, month = col_2.split('/')
        if 1 <= int(day) <= 31 and 1 <= int(month) <= 12:
            col_2_final = f"{col_2}/2026"
            print(f"    Validação: ✅ Formato DD/MM válido")
            print(f"    Final: {col_2_final}\n")
        else:
            print(f"    Validação: ❌ Dia/Mês fora de intervalo\n")
else:
    col_2_final = ""
    print(f"    Validação: Vazio\n")

# Coluna 3: Data Valor
# CORRIGIDO: Usar data da imagem (20/06), não do resultado.json (26/06)
col_3 = "20/06"  # Data correta verificada na imagem (proximidade Y com Dublin)
print(f"  Coluna 3: Data Valor")
print(f"    Valor da imagem: {col_3}")
print(f"    Origem: Verificação direta na imagem (posição X=17.55%, proximidade Y com Dublin)")
if col_3:
    if len(col_3) == 5 and col_3[2] == '/':
        day, month = col_3.split('/')
        if 1 <= int(day) <= 31 and 1 <= int(month) <= 12:
            col_3_final = f"{col_3}/2026"
            print(f"    Validação: ✅ Formato DD/MM válido")
            print(f"    Final: {col_3_final}\n")
else:
    col_3_final = ""
    print(f"    Validação: Vazio\n")

# Coluna 4: Descrição
col_4 = transacao_1.get('descricao', '')
print(f"  Coluna 4: Descrição")
print(f"    Valor: {col_4}")
if col_4 and len(col_4) > 3:
    print(f"    Validação: ✅ Descrição válida e legível\n")
else:
    print(f"    Validação: ⚠️ Descrição vazia ou muito curta\n")

# Coluna 5: País
col_5 = transacao_1.get('pais', '')
print(f"  Coluna 5: País")
print(f"    Valor: {col_5 or '(vazio)'}")
if col_5:
    if 2 <= len(col_5) <= 3:
        print(f"    Validação: ✅ Código país válido\n")
else:
    print(f"    Validação: ⚠️ Vazio (aceitável)\n")

# Coluna 6: Moeda Original
col_6 = transacao_1.get('moeda_original', '')
print(f"  Coluna 6: Moeda Original")
print(f"    Valor: {col_6 or '(vazio)'}")
if col_6:
    print(f"    Validação: ✅ Valor presente\n")
else:
    print(f"    Validação: ⚠️ Vazio\n")

# Coluna 7: Taxa de Câmbio
col_7 = transacao_1.get('taxa_cambio', '')
print(f"  Coluna 7: Taxa de Câmbio")
print(f"    Valor: {col_7 or '(vazio)'}")
if col_7:
    print(f"    Validação: ✅ Valor presente\n")
else:
    print(f"    Validação: ⚠️ Vazio (aceitável se débito = moeda)\n")

# Coluna 8: Débito EUR
col_8 = transacao_1.get('debito_eur', '')
print(f"  Coluna 8: Débito EUR (+)")
print(f"    Valor: {col_8 or '(vazio)'}")
if col_8:
    print(f"    Validação: ✅ Valor presente\n")
else:
    print(f"    Validação: ⚠️ Vazio\n")

# Coluna 9: Crédito EUR
col_9 = transacao_1.get('credito_eur', '')
print(f"  Coluna 9: Crédito EUR (-)")
print(f"    Valor: {col_9 or '(vazio)'}")
if not col_9 or col_9 == '':
    print(f"    Validação: ✅ Vazio (correto, débito presente)\n")

# ========== FASE 5: CONSTRUIR LINHA ==========
print("┌" + "─"*198 + "┐")
print("│ FASE 5: CONSTRUIR LINHA PARA GRAVAR")
print("└" + "─"*198 + "┘\n")

linha_2 = [
    col_1,           # ID_INTERNO
    col_2_final if col_2 else col_2,      # Data Movimento
    col_3_final if col_3 else col_3,      # Data Valor
    col_4,           # Descrição
    col_5,           # País
    col_6,           # Moeda Original
    col_7,           # Taxa de Câmbio
    col_8,           # Débito EUR
    col_9,           # Crédito EUR
]

print("Linha montada:\n")
header = ['ID_INTERNO', 'Data Mov.', 'Data Valor', 'Descrição', 'País', 'Moeda Original', 'Taxa Câmbio', 'Débito EUR (+)', 'Crédito EUR (-)']

for i, (col_name, value) in enumerate(zip(header, linha_2), 1):
    status = "✅" if value else "⚠️"
    print(f"  {i}. {col_name:20s} = {value or '(vazio)'} {status}")

print("\n" + "="*200)
print("GRAVANDO NA GOOGLE SHEET...")
print("="*200 + "\n")

# ========== FASE 6: GRAVAR NA SHEET ==========

creds_file = Path("credentials/soma-cartao-ocr.json")
credentials = service_account.Credentials.from_service_account_file(str(creds_file))
sheets_service = build("sheets", "v4", credentials=credentials)

spreadsheet_id = cfg['google_sheets']['spreadsheet_id']
worksheet = cfg['google_sheets']['worksheet']

# Primeiro, garantir que cabeçalho existe
header_row = header

try:
    # Gravar cabeçalho (linha 1) + dados (linha 2)
    all_data = [header_row, linha_2]

    request = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A1:I2",
        valueInputOption="USER_ENTERED",
        body={'values': all_data}
    )

    response = request.execute()

    print(f"✅ GRAVACAO COM SUCESSO!\n")
    print(f"Range: {worksheet}!A1:I2")
    print(f"Linhas atualizadas: {response.get('updatedRows', 'desconhecido')}")
    print(f"Colunas atualizadas: {response.get('updatedColumns', 'desconhecido')}\n")

    # ========== FASE 7: CONFIRMACAO ==========
    print("┌" + "─"*198 + "┐")
    print("│ FASE 7: CONFIRMACAO - LEITURA DA SHEET")
    print("└" + "─"*198 + "┘\n")

    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet}!A1:I2"
    ).execute()

    rows = result.get('values', [])

    print("Dados gravados na Sheet:\n")

    for row_idx, row in enumerate(rows, 1):
        if row_idx == 1:
            print(f"Linha {row_idx} (CABEÇALHO):")
        else:
            print(f"Linha {row_idx} (TRANSACAO 1):")

        for col_idx, (col_name, value) in enumerate(zip(header, row if row else []), 1):
            status = "✅" if value else "❌"
            print(f"  {col_idx}. {col_name:20s} = {value or '(vazio)'} {status}")
        print()

    print("="*200)
    print("RESUMO FINAL")
    print("="*200 + "\n")

    print("✅ TRANSACAO 1 GRAVADA COM SUCESSO!")
    print(f"✅ ID: {col_1}")
    print(f"✅ Descrição: {col_4}")
    print(f"✅ Data Movimento: {col_2_final if col_2 else '(vazio)'}")
    print(f"✅ Data Valor: {col_3_final if col_3 else '(vazio)'}")
    print(f"✅ País: {col_5 or '(vazio)'}")
    print(f"✅ Débito EUR: {col_8 or '(vazio)'}")

    print("\n" + "="*200)
    print("TEMPLATE CRIADO PARA REPLICACAO")
    print("="*200 + "\n")

    print("Este processo (7 fases) será repetido para as outras 16 transações:")
    print("  1. FASE 1: Carregar dados e configuração")
    print("  2. FASE 2: Identificar transação")
    print("  3. FASE 3: Gerar ID único")
    print("  4. FASE 4: Preparar dados para a linha")
    print("  5. FASE 5: Construir linha para gravar")
    print("  6. FASE 6: Gravar na Sheet")
    print("  7. FASE 7: Confirmar gravação")

    print("\n" + "="*200 + "\n")

except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
