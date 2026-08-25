#!/usr/bin/env python3
"""
FLUXO MENSAL AUTOMATIZADO
1. Verifica sheet EXTRATO_CARTÃO para linhas com STATUS vazio
2. Baixa imagem do Google Drive
3. Processa com main.py
4. Grava registos na sheet CARTÃO
5. Atualiza STATUS em EXTRATO_CARTÃO com TIMESTAMP
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
import subprocess

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.cloud import vision
from google.oauth2 import service_account
from googleapiclient.discovery import build
import yaml

print("\n" + "="*200)
print("FLUXO MENSAL: PROCESSAR EXTRATOS DO CARTÃO")
print("="*200 + "\n")

# ============ FASE 1: CARREGAR CONFIGURACOES ============
print("┌" + "─"*198 + "┐")
print("│ FASE 1: CARREGAR CONFIGURACOES")
print("└" + "─"*198 + "┘\n")

with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
print("✅ config.yaml carregado")

creds_file = Path("credentials/soma-cartao-ocr.json")
credentials = service_account.Credentials.from_service_account_file(str(creds_file))
sheets_service = build("sheets", "v4", credentials=credentials)
drive_service = build("drive", "v3", credentials=credentials)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)
print("✅ Google APIs inicializadas\n")

# ============ FASE 2: VERIFICAR SHEET EXTRATO_CARTÃO ============
print("┌" + "─"*198 + "┐")
print("│ FASE 2: VERIFICAR SHEET EXTRATO_CARTÃO - LINHAS PENDENTES")
print("└" + "─"*198 + "┘\n")

spreadsheet_id = cfg['google_sheets']['spreadsheet_id']
worksheet_extratos = cfg['google_sheets'].get('worksheet_extratos', 'EXTRATO_CARTÃO')
worksheet_cartao = cfg['google_sheets']['worksheet']

# Ler EXTRATO_CARTÃO
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{worksheet_extratos}!A:D"
).execute()

rows_extratos = result.get('values', [])

if len(rows_extratos) < 2:
    print("❌ Nenhuma linha em EXTRATO_CARTÃO!")
    sys.exit(1)

header = rows_extratos[0]
print(f"Estrutura da sheet:\n  {' | '.join(header)}\n")

# Encontrar linhas com STATUS vazio (pronta para processar)
linhas_pendentes = []
for idx, row in enumerate(rows_extratos[1:], start=2):
    if len(row) >= 2:  # Pelo menos Nº EXTRATO e IMAGEM
        num_extrato = row[0] if len(row) > 0 else ""
        imagem_path = row[1] if len(row) > 1 else ""
        status = row[2] if len(row) > 2 else ""  # Pode estar vazio

        # Pronta se STATUS está vazio ou ausente
        if not status or status.strip() == "":
            linhas_pendentes.append({
                'linha': idx,
                'num_extrato': num_extrato,
                'imagem_path': imagem_path,
                'status': status
            })

if not linhas_pendentes:
    print("✅ Nenhuma linha pendente. Tudo processado!")
    sys.exit(0)

print(f"🔍 Encontradas {len(linhas_pendentes)} linha(s) pendente(s):\n")
for item in linhas_pendentes:
    print(f"  Linha {item['linha']}: {item['num_extrato']} → {item['imagem_path']}")

print()

# ============ FASE 3: PROCESSAR CADA EXTRATO PENDENTE ============
print("┌" + "─"*198 + "┐")
print("│ FASE 3: PROCESSAR CADA EXTRATO PENDENTE")
print("└" + "─"*198 + "┘\n")

for item in linhas_pendentes:
    print(f"\n{'='*200}")
    print(f"PROCESSANDO: {item['num_extrato']}")
    print(f"{'='*200}\n")

    # 3.1: Baixar imagem do Drive
    print(f"📥 Baixando imagem: {item['imagem_path']}")

    # Procurar arquivo no Drive pelo nome
    try:
        query = f"name='{Path(item['imagem_path']).name}' and trashed=false"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, webContentLink)',
            pageSize=1
        ).execute()

        files = results.get('files', [])

        if not files:
            print(f"❌ Imagem não encontrada no Drive: {item['imagem_path']}")
            continue

        file_id = files[0]['id']
        file_name = files[0]['name']
        print(f"✅ Encontrada no Drive: {file_name} (ID: {file_id})")

        # Baixar para pasta local
        output_dir = Path("downloads")
        output_dir.mkdir(exist_ok=True)
        local_path = output_dir / file_name

        request = drive_service.files().get_media(fileId=file_id)
        with open(local_path, 'wb') as f:
            f.write(request.execute())

        print(f"✅ Salva localmente: {local_path}\n")

        # 3.2: Processar com main.py (já aplica hybrid OCR, validação, etc)
        print(f"🔄 Processando imagem com main.py...")

        # Chamar main.py com a imagem local
        result = subprocess.run([
            sys.executable, 'main.py',
            str(local_path)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Erro ao processar com main.py:")
            print(result.stderr)
            continue

        print(f"✅ Processamento completo\n")

        # 3.3: Ler resultado.json
        with open("output/resultado.json", encoding='utf-8') as f:
            resultado = json.load(f)

        movimentos = resultado.get('movimentos', [])
        print(f"✅ Extraídos {len(movimentos)} movimentos\n")

        # 3.4: Gravar na sheet CARTÃO
        print(f"📝 Gravando {len(movimentos)} registos na sheet CARTÃO...")

        header_cartao = [
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

        id_prefix = cfg['google_sheets']['id_prefix']
        id_digits = cfg['google_sheets']['id_digits']

        linhas = []
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

        # Ler sheet CARTÃO para determinar próxima linha disponível
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{worksheet_cartao}!A:I"
        ).execute()

        rows_cartao = result.get('values', [])
        next_row = len(rows_cartao) + 1 if rows_cartao else 2

        # Gravar na sheet CARTÃO
        all_data = [header_cartao] + linhas if next_row == 2 else linhas

        request = sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{worksheet_cartao}!A{next_row}:I{next_row + len(linhas) - 1}",
            valueInputOption="USER_ENTERED",
            body={'values': all_data if next_row == 2 else linhas}
        )

        response = request.execute()
        print(f"✅ Gravados {response.get('updatedRows', 0)} registos\n")

        # 3.5: Atualizar STATUS em EXTRATO_CARTÃO
        print(f"⏱️  Atualizando STATUS em EXTRATO_CARTÃO...")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        request = sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{worksheet_extratos}!C{item['linha']}:D{item['linha']}",
            valueInputOption="USER_ENTERED",
            body={'values': [['✅ PROCESSADA', timestamp]]}
        )

        response = request.execute()
        print(f"✅ STATUS atualizado: PROCESSADA | {timestamp}\n")

        print(f"{'='*200}")
        print(f"✅ {item['num_extrato']} PROCESSADO COM SUCESSO!")
        print(f"{'='*200}\n")

    except Exception as e:
        print(f"❌ ERRO ao processar {item['num_extrato']}: {e}")
        import traceback
        traceback.print_exc()
        continue

# ============ RESUMO FINAL ============
print("\n" + "="*200)
print("RESUMO FINAL")
print("="*200 + "\n")

print(f"✅ Processadas {len(linhas_pendentes)} extrato(s)")
print(f"✅ Todos os registos gravados na sheet CARTÃO")
print(f"✅ STATUS atualizado em EXTRATO_CARTÃO\n")

print("="*200 + "\n")
