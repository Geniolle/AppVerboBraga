#!/usr/bin/env python3
"""Carregar a imagem CORRETA do Drive (100149.jpg que foi processada)."""

import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import vision
import yaml

print("\n" + "="*150)
print("CARREGANDO IMAGEM CORRETA DO DRIVE")
print("="*150 + "\n")

# Carregar credenciais e config
creds_file = Path("credentials/soma-cartao-ocr.json")
credentials = service_account.Credentials.from_service_account_file(str(creds_file))

drive_service = build("drive", "v3", credentials=credentials)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)

with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

folder_id = cfg["drive"]["folder_id"]

# Procurar pelos dois arquivos
print("🔍 Procurando arquivos no Drive...\n")

results = drive_service.files().list(
    q=f"'{folder_id}' in parents and mimeType='image/jpeg'",
    spaces='drive',
    fields='files(id, name)',
    pageSize=50
).execute()

files = results.get('files', [])

print(f"Encontrados {len(files)} arquivos:\n")

target_files = {}
for file in files:
    if "100149" in file['name']:
        target_files['100149'] = file
        print(f"✅ ENCONTRADO (foi processado): {file['name']}")
    elif "102342" in file['name']:
        target_files['102342'] = file
        print(f"⚠️  Está configurado: {file['name']}")

print("\n" + "="*150)
print("ANALISANDO 100149.jpg (O QUE FOI GRAVADO NA SHEET)")
print("="*150 + "\n")

if '100149' in target_files:
    file_id = target_files['100149']['id']
    file_name = target_files['100149']['name']

    # Baixar a imagem
    print(f"Baixando: {file_name}\n")
    request = drive_service.files().get_media(fileId=file_id)
    from io import BytesIO
    fh = BytesIO()
    downloader = request.execute()

    # Usar Vision API para processar
    print("Processando com Vision API...\n")

    request = drive_service.files().get_media(fileId=file_id)
    fh = BytesIO()
    request.execute()

    # Recarregar com Vision
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    request = drive_service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    image_content = fh.getvalue()

    # Processar com Vision API
    image = vision.Image(content=image_content)
    response = vision_client.document_text_detection(image=image)

    # Extrair Words
    words = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    text = "".join([symbol.text for symbol in word.symbols])
                    y0 = word.bounding_box.vertices[0].y
                    y1 = word.bounding_box.vertices[2].y
                    x0 = word.bounding_box.vertices[0].x
                    x1 = word.bounding_box.vertices[2].x
                    words.append({
                        'text': text,
                        'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                        'cy': (y0 + y1) // 2,
                    })

    # Agrupar por Y
    y_groups = {}
    for word in words:
        cy = word['cy']
        found_group = False
        for group_y in list(y_groups.keys()):
            if abs(group_y - cy) <= 15:
                y_groups[group_y].append(word)
                found_group = True
                break
        if not found_group:
            y_groups[cy] = [word]

    sorted_y_groups = sorted(y_groups.items())

    # Mostrar primeiras 10 linhas
    print("PRIMEIRAS LINHAS DETECTADAS (Y=ordem de aparição):\n")
    for i, (cy, words_in_line) in enumerate(sorted_y_groups[:15], 1):
        sorted_words = sorted(words_in_line, key=lambda x: x['x0'])
        text_line = " ".join([w['text'] for w in sorted_words])
        print(f"Linha {i:2d} (CY={cy:4d}): {text_line[:100]}")

else:
    print("❌ Arquivo 100149.jpg não encontrado no Drive")

print("\n" + "="*150 + "\n")
