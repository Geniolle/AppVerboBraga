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
from datetime import date, datetime, timedelta
from pathlib import Path

COL_TIPO = "TIPO DE AGENDAMENTO"
COL_DATA = "DATA DO AGENDAMENTO"
TIPO_EVENTO = "EVENTO"
# Só estes campos vão para o JSON público (sem IDUSER, morada, detalhes).
CAMPOS_PUBLICOS = ("TÍTULO DA AGENDA", "DATA DO AGENDAMENTO", "HORA DE INÍCIO", "HORA DE FIM", "LOCALIZAÇÃO", "ID_DA_IMAGEM")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SCOPES_DRIVE = ["https://www.googleapis.com/auth/drive.readonly"]


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

    proximo_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
    meses_validos = {(hoje.year, hoje.month), (proximo_mes.year, proximo_mes.month)}

    resultado = []
    for linha in linhas[1:]:
        if len(linha) <= max(i_tipo, i_data):
            continue
        if linha[i_tipo].strip().upper() != TIPO_EVENTO:
            continue
        data = parse_data(linha[i_data])
        if data is None or (data.year, data.month) not in meses_validos or data < hoje:
            continue
        linha_dict = dict(zip(cabecalho, linha))
        resultado.append({c: linha_dict.get(c, "") for c in CAMPOS_PUBLICOS} | {"data": data.isoformat()})
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


def mapa_imagens_da_pasta(pasta_id: str) -> dict[str, str]:
    """Nome do ficheiro -> URL pública (lh3) para as imagens da pasta do Drive."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"], scopes=SCOPES_DRIVE
    )
    servico = build("drive", "v3", credentials=creds, cache_discovery=False)
    mapa: dict[str, str] = {}
    token = None
    while True:
        resposta = (
            servico.files()
            .list(
                q=f"'{pasta_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name)",
                pageSize=1000,
                pageToken=token,
            )
            .execute()
        )
        for ficheiro in resposta.get("files", []):
            mapa.setdefault(ficheiro["name"], f"https://lh3.googleusercontent.com/d/{ficheiro['id']}")
        token = resposta.get("nextPageToken")
        if not token:
            return mapa


def anexar_imagens(eventos: list[dict], mapa: dict[str, str]) -> None:
    """Põe imagem_url em cada evento e retira o caminho interno do Drive."""
    for evento in eventos:
        nome = evento.pop("ID_DA_IMAGEM", "").split("/")[-1]
        evento["imagem_url"] = mapa.get(nome, "")


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
    try:  # sem imagens os eventos continuam a sair
        mapa = mapa_imagens_da_pasta(os.environ["AGENDA_IMAGENS_FOLDER_ID"])
    except Exception as erro:
        print(f"aviso: imagens não lidas ({type(erro).__name__})", flush=True)
        mapa = {}
    anexar_imagens(eventos, mapa)
    escrever_json_atomico(destino, eventos)
    print(f"ok: {len(eventos)} eventos -> {destino}", flush=True)
