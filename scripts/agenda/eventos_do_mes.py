"""Lê a aba AppAgendaDepartamentos e devolve os EVENTOS do mês atual com data >= hoje.

Uso: python eventos_do_mes.py
Variáveis de ambiente:
  AGENDA_SPREADSHEET_ID   id do Google Sheet
  AGENDA_SHEET_NAME       aba (default AppAgendaDepartamentos)
  GOOGLE_SERVICE_ACCOUNT_FILE  caminho do JSON da conta de serviço (fora do repo)
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path

COL_TIPO = "TIPO DE AGENDAMENTO"
COL_DATA = "DATA DO AGENDAMENTO"
TIPO_EVENTO = "EVENTO"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def parse_data(valor: str) -> date | None:
    """Aceita dd/mm/aaaa (formato da folha)."""
    try:
        return datetime.strptime(valor.strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        return None


def filtrar_eventos_do_mes(linhas: list[list[str]], hoje: date) -> list[dict]:
    """linhas[0] é o cabeçalho; devolve eventos do mês de `hoje` com data >= `hoje`."""
    if not linhas:
        return []
    cabecalho = [c.strip() for c in linhas[0]]
    i_tipo = cabecalho.index(COL_TIPO)
    i_data = cabecalho.index(COL_DATA)

    resultado = []
    for linha in linhas[1:]:
        if len(linha) <= max(i_tipo, i_data):
            continue
        if linha[i_tipo].strip().upper() != TIPO_EVENTO:
            continue
        data = parse_data(linha[i_data])
        if data is None or data.year != hoje.year or data.month != hoje.month or data < hoje:
            continue
        resultado.append(dict(zip(cabecalho, linha), data=data.isoformat()))
    return sorted(resultado, key=lambda r: r["data"])


def ler_linhas_da_folha() -> list[list[str]]:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"], scopes=SCOPES
    )
    servico = build("sheets", "v4", credentials=creds, cache_discovery=False)
    aba = os.environ.get("AGENDA_SHEET_NAME", "AppAgendaDepartamentos")
    resposta = (
        servico.spreadsheets()
        .values()
        .get(spreadsheetId=os.environ["AGENDA_SPREADSHEET_ID"], range=f"'{aba}'!A:ZZ")
        .execute()
    )
    return resposta.get("values", [])


def escrever_json_atomico(destino: Path, eventos: list[dict]) -> None:
    """Escreve num temporário e substitui; nunca deixa ficheiro meio escrito."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + ".tmp")
    payload = {"atualizado_em": date.today().isoformat(), "eventos": eventos}
    temporario.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(temporario, destino)


if __name__ == "__main__":
    destino = Path(os.environ.get("AGENDA_OUTPUT_FILE", "eventos.json"))
    try:
        eventos = filtrar_eventos_do_mes(ler_linhas_da_folha(), date.today())
    except Exception as erro:  # mantém o último ficheiro bom
        print(f"erro: {type(erro).__name__}; ficheiro anterior mantido", flush=True)
        raise SystemExit(1)
    escrever_json_atomico(destino, eventos)
    print(f"ok: {len(eventos)} eventos -> {destino}", flush=True)
