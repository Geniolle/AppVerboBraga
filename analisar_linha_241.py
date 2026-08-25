#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analisar linha 241 corretamente:
1. Ler cabeçalho (linha 1)
2. Encontrar índice de cada coluna pelo NOME
3. Buscar valor na linha 241 usando os índices corretos
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path

service_account_file = Path("AppExtrato/credentials/sheets-service-account.json")
spreadsheet_id = "1poVWJGSBb13_2S1YKEzvFmkB9Ru0ZVzfQ0OEcMkfOZw"

print("\n" + "="*100)
print("ANÁLISE CORRETA DA LINHA 241 - DÍZIMOS/OFERTAS")
print("="*100)
print()

try:
    # Autenticar
    creds = service_account.Credentials.from_service_account_file(
        str(service_account_file),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    sheets_service = build("sheets", "v4", credentials=creds)

    # Obter metadados
    metadata = sheets_service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()

    target_sheet = None
    for sheet in metadata.get("sheets", []):
        if "ZIMOS" in sheet["properties"]["title"]:
            if "/" in sheet["properties"]["title"]:
                target_sheet = sheet
                break

    if not target_sheet:
        print("[ERRO] Sheet DÍZIMOS/OFERTAS nao encontrada")
        exit(1)

    sheet_title = target_sheet["properties"]["title"]
    print(f"[1/3] Sheet encontrada: {sheet_title}")
    print()

    # Carregar TODAS as linhas
    print("[2/3] Carregando dados...")
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_title}'!A:Z"
    ).execute()

    data = result.get("values", [])
    print(f"      Total de linhas: {len(data)}")
    print()

    if len(data) < 2:
        print("[ERRO] Nao ha dados suficientes")
        exit(1)

    # LINHA 1: Cabeçalho
    headers = data[0]
    print("[3/3] Lendo cabeçalho (Linha 1):")
    print()
    print("      Índice | Nome da Coluna")
    print("      " + "-"*50)
    for idx, header in enumerate(headers):
        print(f"      {idx:3d}    | {header}")
    print()

    # Criar mapa de colunas pelo NOME
    column_map = {
        str(h).strip().upper(): idx
        for idx, h in enumerate(headers)
    }

    print("="*100)
    print("MAPA DE COLUNAS (buscadas por NOME, não por posição):")
    print("="*100)
    print()

    # Colunas que queremos analisar
    colunas_importantes = [
        "DATA",
        "TIPO",
        "DOC. SOMA",
        "NÚMERO DOCUMENTO",
        "VALOR",
        "FINANCE"
    ]

    indices = {}
    for col_name in colunas_importantes:
        col_upper = col_name.upper().strip()
        if col_upper in column_map:
            idx = column_map[col_upper]
            indices[col_name] = idx
            print(f"[OK] {col_name:<20} encontrada no indice {idx}")
        else:
            print(f"[NAO] {col_name:<20} NAO encontrada")

    print()
    print("="*100)
    print("ANÁLISE DA LINHA 241:")
    print("="*100)
    print()

    # Linha 241 está no índice 240 (0-based)
    linha_241_idx = 240

    if linha_241_idx < len(data):
        linha_241 = data[linha_241_idx]
        print(f"Linha 241 (índice {linha_241_idx}):")
        print()

        print("VALORES ENCONTRADOS (usando índices corretos do cabeçalho):")
        print("-"*100)

        # Ler cada coluna usando o índice correto
        for col_name in colunas_importantes:
            if col_name in indices:
                idx = indices[col_name]
                valor = linha_241[idx] if idx < len(linha_241) else "(vazio)"
                print(f"  {col_name:<20} (índice {idx:2d}): {str(valor):<50}")
            else:
                print(f"  {col_name:<20} (NÃO ENCONTRADA)")

        print()
        print("="*100)
        print("APLICANDO 5 CRITÉRIOS DE VALIDAÇÃO:")
        print("="*100)
        print()

        # Extrair valores usando índices corretos
        data_valor = linha_241[indices.get("DATA", -1)] if indices.get("DATA", -1) >= 0 and indices.get("DATA", -1) < len(linha_241) else ""
        tipo = linha_241[indices.get("TIPO", -1)] if indices.get("TIPO", -1) >= 0 and indices.get("TIPO", -1) < len(linha_241) else ""
        doc_soma = linha_241[indices.get("DOC. SOMA", -1)] if indices.get("DOC. SOMA", -1) >= 0 and indices.get("DOC. SOMA", -1) < len(linha_241) else ""
        valor = linha_241[indices.get("VALOR", -1)] if indices.get("VALOR", -1) >= 0 and indices.get("VALOR", -1) < len(linha_241) else ""
        finance = linha_241[indices.get("FINANCE", -1)] if indices.get("FINANCE", -1) >= 0 and indices.get("FINANCE", -1) < len(linha_241) else ""

        print(f"[Critério 1] TIPO = 'DÍZIMOS/OFERTAS' ou 'DIA VERBO MISSÔES'")
        print(f"  Valor encontrado: '{tipo}'")
        tipo_ok = tipo in ["DÍZIMOS/OFERTAS", "DIA VERBO MISSÔES"]
        print(f"  Resultado: {'[OK] PASSOU' if tipo_ok else '[NAO] FALHOU'}")
        print()

        print(f"[Critério 2] DOC.SOMA = VAZIO")
        print(f"  Valor encontrado: '{doc_soma}'")
        doc_soma_ok = not doc_soma or doc_soma.strip() == ""
        print(f"  Resultado: {'[OK] PASSOU' if doc_soma_ok else '[NAO] FALHOU (DOC.SOMA nao esta vazio)'}")
        print()

        print(f"[Critério 3] FINANCE = VAZIO")
        print(f"  Valor encontrado: '{finance}'")
        finance_ok = not finance or finance.strip() == ""
        print(f"  Resultado: {'[OK] PASSOU' if finance_ok else '[NAO] FALHOU (FINANCE nao esta vazio)'}")
        print()

        print(f"[Critério 4] VALOR > 0")
        print(f"  Valor encontrado: '{valor}'")
        valor_ok = False
        if valor:
            try:
                valor_num = float(str(valor).replace(",", "."))
                valor_ok = valor_num > 0
            except:
                pass
        print(f"  Resultado: {'[OK] PASSOU' if valor_ok else '[NAO] FALHOU'}")
        print()

        print(f"[Criterio 5] DATA = PREENCHIDA")
        print(f"  Valor encontrado: '{data_valor}'")
        data_ok = bool(data_valor)
        print(f"  Resultado: {'[OK] PASSOU' if data_ok else '[NAO] FALHOU'}")
        print()

        print("="*100)
        print("VEREDITO FINAL:")
        print("="*100)
        print()

        todos_ok = tipo_ok and doc_soma_ok and finance_ok and valor_ok and data_ok

        if todos_ok:
            print("[OK] LINHA 241 E ELEGIVEL PARA TRANSFERENCIA")
        else:
            print("[NAO] LINHA 241 NAO E ELEGIVEL PARA TRANSFERENCIA")

        print()
        print("Motivos de rejeição:")
        if not tipo_ok:
            print(f"  • TIPO inválido: '{tipo}'")
        if not doc_soma_ok:
            print(f"  • DOC.SOMA não está vazio: '{doc_soma}'")
        if not finance_ok:
            print(f"  • FINANCE não está vazio: '{finance}'")
        if not valor_ok:
            print(f"  • VALOR inválido: '{valor}'")
        if not data_ok:
            print(f"  • DATA vazia")

        print()
        print("="*100)

    else:
        print("[ERRO] Linha 241 não existe no dataset")

except Exception as e:
    print(f"[ERRO] {e}")
    import traceback
    traceback.print_exc()
