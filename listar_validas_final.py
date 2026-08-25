#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Listar entradas válidas diretamente via Google Sheets API.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path

service_account_file = Path("AppExtrato/credentials/sheets-service-account.json")
spreadsheet_id = "1poVWJGSBb13_2S1YKEzvFmkB9Ru0ZVzfQ0OEcMkfOZw"

print("\n" + "="*100)
print("LISTAR ENTRADAS VALIDAS - DIZIMOS/OFERTAS")
print("="*100)
print()

try:
    # Autenticar
    creds = service_account.Credentials.from_service_account_file(
        str(service_account_file),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    sheets_service = build("sheets", "v4", credentials=creds)

    print("[1/4] Obtendo estrutura da planilha...")

    # Obter detalhes da planilha
    metadata = sheets_service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()

    # Encontrar sheet DIZIMOS/OFERTAS
    target_sheet = None
    sheet_title_to_use = None

    print("      Sheets disponiveis:")
    for sheet in metadata.get("sheets", []):
        title = sheet["properties"]["title"]
        print(f"        - {title}")
        if "ZIMOS" in title or "DIZAM" in title or "OFERTAS" in title:
            if "/" in title:
                target_sheet = sheet
                sheet_title_to_use = title

    if not target_sheet:
        print("[ERRO] Sheet DÍZIMOS/OFERTAS nao encontrada")
        exit(1)

    sheet_id = target_sheet["properties"]["sheetId"]
    sheet_title = target_sheet["properties"]["title"]
    print(f"      [OK] Sheet encontrada: {sheet_title} (ID: {sheet_id})")
    print()

    print("[2/4] Carregando dados...")

    # Obter dados
    request = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_title}'!A:Z"
    )
    result = request.execute()

    data = result.get("values", [])

    if len(data) < 2:
        print("[ERRO] Nao ha dados suficientes")
        exit(1)

    headers = data[0]
    rows = data[1:]

    print(f"      [OK] {len(headers)} colunas, {len(rows)} linhas carregadas")
    print()

    # Mapear indices
    column_map = {
        str(h).upper().strip(): idx
        for idx, h in enumerate(headers)
    }

    print("[3/4] Filtrando entradas validas...")
    print()

    # Indices
    idx_data = column_map.get("DATA", -1)
    idx_tipo = column_map.get("TIPO", -1)
    idx_doc_soma = column_map.get("DOC. SOMA", -1)
    idx_finance = column_map.get("FINANCE", -1)
    idx_valor = column_map.get("VALOR", -1)
    idx_descricao = column_map.get("DESCRICAO", -1)
    idx_id_interno = column_map.get("ID_INTERNO", -1)

    validas = []
    invalidas = []

    for row_num, row in enumerate(rows, start=2):
        # Extrair dados
        data_val = str(row[idx_data]).strip() if idx_data >= 0 and idx_data < len(row) else ""
        tipo = str(row[idx_tipo]).strip() if idx_tipo >= 0 and idx_tipo < len(row) else ""
        doc_soma = str(row[idx_doc_soma]).strip() if idx_doc_soma >= 0 and idx_doc_soma < len(row) else ""
        finance = str(row[idx_finance]).strip() if idx_finance >= 0 and idx_finance < len(row) else ""
        valor = str(row[idx_valor]).strip() if idx_valor >= 0 and idx_valor < len(row) else ""
        descricao = str(row[idx_descricao]).strip() if idx_descricao >= 0 and idx_descricao < len(row) else ""
        id_interno = str(row[idx_id_interno]).strip() if idx_id_interno >= 0 and idx_id_interno < len(row) else ""

        # Nao processar linhas vazias
        if not tipo or not data_val:
            continue

        # Validar criterios
        tipo_ok = tipo in ["DIZIMOS/OFERTAS", "DIA VERBO MISSOES"]
        doc_soma_ok = not doc_soma or doc_soma == ""
        finance_ok = not finance or finance == ""
        data_ok = bool(data_val)

        # Validar valor
        valor_ok = False
        if valor:
            try:
                valor_num = float(valor.replace(",", "."))
                valor_ok = valor_num > 0
            except:
                valor_ok = False

        # Todos criterios atendidos?
        valido = tipo_ok and doc_soma_ok and finance_ok and valor_ok and data_ok

        registro = {
            "linha": row_num,
            "data": data_val,
            "tipo": tipo,
            "doc_soma": doc_soma,
            "finance": finance,
            "valor": valor,
            "descricao": descricao,
            "id_interno": id_interno,
            "valido": valido
        }

        if valido:
            validas.append(registro)
        else:
            invalidas.append(registro)

    # Resultado
    print("="*100)
    print("[RESULTADO] {} VALIDAS | {} INVALIDAS".format(len(validas), len(invalidas)))
    print("="*100)
    print()

    if validas:
        print("LISTA DE ENTRADAS VALIDAS ({}):".format(len(validas)))
        print("-"*100)
        print("{:<6} {:<12} {:<25} {:<12} {:<30} {:<15}".format(
            "Linha", "Data", "Tipo", "Valor", "Descricao", "ID"
        ))
        print("-"*100)

        total = 0.0
        for e in validas:
            tipo_display = e["tipo"][:22]
            desc_display = e["descricao"][:28] if e["descricao"] else "(sem descricao)"

            try:
                v = float(e["valor"].replace(",", "."))
                total += v
            except:
                pass

            print("{:<6} {:<12} {:<25} {:<12} {:<30} {:<15}".format(
                str(e["linha"]),
                e["data"],
                tipo_display,
                e["valor"],
                desc_display,
                e["id_interno"]
            ))

        print("-"*100)
        print("{:<6} {:<12} {:<25} {:<12.2f} EUR".format(
            "TOTAL", "", "", total
        ))
        print()

        # Detalhes
        print("\nDETALHES DE CADA ENTRADA VALIDA:")
        print()
        for i, e in enumerate(validas, 1):
            print("[{}] LINHA {}".format(i, e["linha"]))
            print("    +" + "-"*98 + "+")
            print("    | Data:              {}".format(e["data"]))
            print("    | Tipo:              {}".format(e["tipo"]))
            print("    | Valor:             {} EUR".format(e["valor"]))
            print("    | Descricao:         {}".format(e["descricao"]))
            print("    | ID_INTERNO:        {}".format(e["id_interno"]))
            print("    | DOC.SOMA:          {}".format(e["doc_soma"] if e["doc_soma"] else "(vazio)"))
            print("    | FINANCE:           {}".format(e["finance"] if e["finance"] else "(vazio)"))
            print("    | Status:            PRONTA PARA TRANSFERENCIA")
            print("    +" + "-"*98 + "+")
            print()

    else:
        print("AVISO: Nenhuma entrada valida encontrada.")
        print()
        print("Criterios requeridos:")
        print("  1. TIPO = 'DIZIMOS/OFERTAS' ou 'DIA VERBO MISSOES'")
        print("  2. DOC.SOMA = vazio")
        print("  3. FINANCE = vazio")
        print("  4. VALOR > 0")
        print("  5. DATA = preenchida")
        print()

    # Mostrar algumas invalidas
    if invalidas:
        print()
        print("AMOSTRAS DE ENTRADAS INVALIDAS (primeiras 10 de {}):".format(len(invalidas)))
        print("-"*100)
        print("{:<6} {:<25} {:<12} {:<50}".format(
            "Linha", "Tipo", "Valor", "Motivo"
        ))
        print("-"*93)

        for e in invalidas[:10]:
            motivos = []
            if e["tipo"] not in ["DIZIMOS/OFERTAS", "DIA VERBO MISSOES"]:
                motivos.append("TIPO='{}'".format(e["tipo"]))
            if e["doc_soma"]:
                motivos.append("DOC.SOMA='{}'".format(e["doc_soma"]))
            if e["finance"]:
                motivos.append("FINANCE='{}'".format(e["finance"]))

            try:
                v = float(e["valor"].replace(",", "."))
                if v <= 0:
                    motivos.append("VALOR<=0")
            except:
                motivos.append("VALOR='{}'".format(e["valor"]))

            if not e["data"]:
                motivos.append("DATA vazia")

            motivo = " + ".join(motivos)[:48]
            tipo = e["tipo"][:22]

            print("{:<6} {:<25} {:<12} {:<50}".format(
                str(e["linha"]),
                tipo,
                e["valor"],
                motivo
            ))

        if len(invalidas) > 10:
            print("... e mais {} invalidas".format(len(invalidas) - 10))

    print()
    print("="*100)
    print()

except Exception as e:
    print("[ERRO] {}".format(e))
    import traceback
    traceback.print_exc()
