#!/usr/bin/env python3
"""Testar em múltiplos extratos para validar consistência."""

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
print("TESTE: Múltiplos Extratos")
print("="*150 + "\n")

# Carregar configuração
with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# Carregar credenciais
creds_file = Path("credentials/soma-cartao-ocr.json")
credentials = service_account.Credentials.from_service_account_file(str(creds_file))
drive_service = build("drive", "v3", credentials=credentials)

# Folder ID
folder_id = cfg["drive"]["folder_id"]

print(f"Procurando extratos em: {folder_id}\n")

# Listar arquivos
results = drive_service.files().list(
    q=f"'{folder_id}' in parents and mimeType='image/jpeg'",
    spaces='drive',
    fields='files(id, name, createdTime)',
    pageSize=50
).execute()

files = results.get('files', [])

if not files:
    print("Nenhum extrato encontrado!")
    sys.exit(1)

print(f"Total de extratos encontrados: {len(files)}\n")

# Mostrar lista
print("EXTRATOS DISPONÍVEIS:")
print("-" * 150)
for file in files:
    print(f"  • {file['name']:<50} (ID: {file['id'][:20]}...)")

print("\n" + "="*150)
print("ANÁLISE DE EXTRATOS")
print("="*150 + "\n")

# Informações sobre cada extrato
for i, file in enumerate(files[:5], 1):
    print(f"{i}. {file['name']}")
    print(f"   ID: {file['id']}")
    print(f"   Data: {file['createdTime']}")
    print()

print("="*150)
print("RECOMENDACAO PARA PROXIMOS TESTES")
print("="*150 + "\n")

print("""
Para testar em múltiplos extratos:

1. Modificar config.yaml ou adicionar CLI arg para selecionar extrato
   Opção A: filename field com filtro
   Opção B: CLI: python main.py --extract "05-2026"

2. Executar em cada extrato:
   python main.py --extract 07-2026  # Atual (já testado)
   python main.py --extract 06-2026  # Anterior
   python main.py --extract 05-2026  # 2 meses atrás
   python main.py --extract 04-2026  # 3 meses atrás

3. Comparar métricas:
   - Taxa de sucesso (esperado: >50%)
   - Confiança média (esperado: >80%)
   - Padrões de rejeição (procurar por consistência)

4. Validar se "Google One" aparece em outros extratos:
   - Procurar por "Google" em resultados.json
   - Se aparecer, verificar se tem mesmo problema

Próxima Sprint:
- Implementar CLI --extract
- Criar script de batch testing
- Gerar relatório comparativo
""")

print("="*150 + "\n")
