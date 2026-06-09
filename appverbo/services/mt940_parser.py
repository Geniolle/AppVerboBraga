from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class MT940Transaction:
    data_mov: str        # DD/MM/YYYY
    data_valor: str      # DD/MM/YYYY
    valor: str           # formatted with comma e.g. "150,00" or "-150,00"
    descricao: str       # raw description
    tipo: str            # Entrada / Saída / MVV / Transferência
    chave_dedup: str     # deduplication key: "data|desc_norm|valor"


@dataclass
class MT940ParseResult:
    transactions: list[MT940Transaction] = field(default_factory=list)
    saldo_contabilistico: Optional[str] = None   # formatted "1234,56"
    data_abertura: str = ""
    numero_extrato: str = ""                      # :28C: statement number/sequence
    errors: list[str] = field(default_factory=list)


# ─── helpers (mirrors GAS helpers) ───────────────────────────────────────────

def _normalizar_texto(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace — mirrors normalizarTexto GAS."""
    clean = str(text or "").strip()
    nfd = unicodedata.normalize("NFD", clean)
    ascii_only = nfd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_only).strip().lower()


def _formatar_valor(raw: str | float) -> str:
    """Return value as string with 2 decimal places and comma separator."""
    clean = str(raw or "").strip().replace(",", ".")
    try:
        num = float(clean)
        return f"{num:.2f}".replace(".", ",")
    except ValueError:
        return str(raw)


def _format_date_mt940(yymmdd: str) -> str:
    """Convert YYMMDD (MT940) → DD/MM/YYYY."""
    try:
        dt = datetime.strptime(yymmdd.strip(), "%y%m%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return yymmdd


def _classify_tipo(descricao_norm: str, is_credito: bool) -> str:
    """Mirrors the tipoFinal classification block from the GAS script."""
    if _normalizar_texto("TRF.PWORLDOFLIFINTMINIST") in descricao_norm:
        return "MVV"
    if _normalizar_texto("ENT.NUMERARIO  CH24 0006774253") in descricao_norm:
        return "Transferência"
    return "Entrada" if is_credito else "Saída"


# ─── main parser ─────────────────────────────────────────────────────────────

def parse_mt940_content(content: str) -> MT940ParseResult:
    """
    Parse a MT940 file string into a list of MT940Transaction objects.
    Logic is a direct port of ImportarFicheiroMT940 Google Apps Script.
    """
    result = MT940ParseResult()
    lines = content.splitlines()

    data_mov_atual = ""

    for idx, line in enumerate(lines):
        line_no = idx + 1

        # ── :28C: statement number / sequence ────────────────────────────
        if line.startswith(":28C:"):
            result.numero_extrato = line[5:].strip()
            continue

        # ── :60F: opening balance date ────────────────────────────────────
        if line.startswith(":60F:"):
            date_part = line[6:12]
            data_mov_atual = _format_date_mt940(date_part)
            result.data_abertura = data_mov_atual
            continue

        # ── :61: transaction ──────────────────────────────────────────────
        if line.startswith(":61:"):
            try:
                is_credito = len(line) > 14 and line[14] == "C"
                sinal = "" if is_credito else "-"

                idx_nmsc = line.find("NMSC")
                if idx_nmsc == -1:
                    result.errors.append(f"Linha {line_no}: NMSC não encontrado — {line[:40]}")
                    continue

                valor_part = line[15:idx_nmsc]
                valor_num_str = f"{sinal}{valor_part.replace(',', '.')}"
                valor_formatado = _formatar_valor(valor_num_str)

                desc_parte = line[idx_nmsc + 4:].strip()
                descricao = desc_parte.replace("/", "").strip()
                descricao_norm = _normalizar_texto(descricao)

                tipo = _classify_tipo(descricao_norm, is_credito)
                chave = f"{data_mov_atual}|{descricao_norm}|{valor_formatado}"

                result.transactions.append(MT940Transaction(
                    data_mov=data_mov_atual,
                    data_valor=data_mov_atual,
                    valor=valor_formatado,
                    descricao=descricao,
                    tipo=tipo,
                    chave_dedup=chave,
                ))
            except Exception as exc:
                result.errors.append(f"Linha {line_no}: {exc}")
            continue

        # ── :62F: closing balance ─────────────────────────────────────────
        if line.startswith(":62F:"):
            parts = line.split("EUR")
            if len(parts) > 1:
                saldo_raw = parts[1].strip()
                result.saldo_contabilistico = _formatar_valor(saldo_raw)
            continue

    return result
