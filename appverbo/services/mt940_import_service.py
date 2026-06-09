from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from appverbo.services.mt940_parser import MT940Transaction, parse_mt940_content
from appverbo.services.profile import (
    build_menu_process_records_storage_key,
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_member_profile_fields,
    serialize_menu_process_records,
)

logger = logging.getLogger(__name__)

# ─── field-label matchers ─────────────────────────────────────────────────────

def _norm(text: str) -> str:
    """Lowercase + strip accents (for fuzzy label matching)."""
    nfd = unicodedata.normalize("NFD", str(text or "").strip())
    ascii_only = nfd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[\s_]+", " ", ascii_only).strip().lower()


_LABEL_PATTERNS: dict[str, list[str]] = {
    "data_mov":        ["data mov", "data do mov", "data movimento"],
    "data_valor":      ["data valor", "valor date"],
    "descricao":       ["descricao", "descr", "historico"],
    "valor":           ["valor", "importancia", "import", "montante", "debito credito"],
    "saldo":           ["saldo contab", "saldo"],
    "tipo":            ["tipo"],
    "numero_extrato":   ["n extrato", "num extrato", "numero extrato", "nr extrato", "n. extrato"],
    "numero_entidade":  ["n entidade", "num entidade", "numero entidade", "nr entidade", "n. entidade", "entidade"],
}


def _match_field_key(label: str) -> Optional[str]:
    norm_label = _norm(label)
    for semantic_key, patterns in _LABEL_PATTERNS.items():
        for p in patterns:
            if p in norm_label:
                return semantic_key
    return None


def _resolve_field_keys(section_fields: list[dict]) -> dict[str, str]:
    """
    Walk the sectionFields and return a mapping:
        semantic_key → actual DB field key
    e.g. {"data_mov": "custom_data_do_movimento", "valor": "custom_valor", ...}
    """
    resolved: dict[str, str] = {}
    for f in section_fields:
        fkey = str(f.get("key") or "").strip().lower()
        flabel = str(f.get("label") or "").strip()
        semantic = _match_field_key(flabel) or _match_field_key(fkey)
        if semantic and semantic not in resolved:
            resolved[semantic] = fkey
    return resolved


# ─── result dataclass ─────────────────────────────────────────────────────────

@dataclass
class MT940ImportResult:
    linhas_inseridas: int = 0
    duplicadas_ignoradas: int = 0
    ficheiros_processados: int = 0
    errors: list[str] = field(default_factory=list)
    status: str = "ok"


# ─── helpers ─────────────────────────────────────────────────────────────────

def _get_section_key(additional_fields: list[dict]) -> str:
    """
    Find the first header field — its key is used as section_key for new records.
    Falls back to 'dados_de_extrato'.
    """
    for f in additional_fields:
        if str(f.get("field_type") or f.get("type") or "").lower() == "header":
            key = str(f.get("key") or "").strip().lower()
            if key:
                return key
    return "dados_de_extrato"


def _load_existing_dedup_keys(
    existing_records: list[dict],
    field_keys: dict[str, str],
) -> set[str]:
    """
    Build the same dedup key as the parser: "data_mov|desc_norm|valor".
    Uses the actual DB field keys resolved from the label matcher.
    """
    keys: set[str] = set()
    fk_data = field_keys.get("data_mov", "")
    fk_desc = field_keys.get("descricao", "")
    fk_valor = field_keys.get("valor", "")

    def norm_val(v: str) -> str:
        nfd = unicodedata.normalize("NFD", str(v or "").strip())
        ascii_only = nfd.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", ascii_only).strip().lower()

    for rec in existing_records:
        values = rec.get("values") or {}
        data = str(values.get(fk_data) or "").strip()
        desc = norm_val(values.get(fk_desc) or "")
        valor = str(values.get(fk_valor) or "").strip()
        if data or desc or valor:
            keys.add(f"{data}|{desc}|{valor}")
    return keys


def _build_record(
    tx: MT940Transaction,
    field_keys: dict[str, str],
    section_key: str,
    timestamp_label: str,
    entity_internal_number: Optional[str],
    numero_extrato: str = "",
) -> dict:
    values: dict[str, str] = {}
    if fk := field_keys.get("data_mov"):
        values[fk] = tx.data_mov
    if fk := field_keys.get("data_valor"):
        values[fk] = tx.data_valor
    if fk := field_keys.get("descricao"):
        values[fk] = tx.descricao
    if fk := field_keys.get("valor"):
        values[fk] = tx.valor
    if fk := field_keys.get("tipo"):
        values[fk] = tx.tipo
    if numero_extrato:
        if fk := field_keys.get("numero_extrato"):
            values[fk] = numero_extrato
    values["__estado"] = "ativo"
    if entity_internal_number:
        # Always store as internal key for entity filtering (multi-tenant)
        values["numero_entidade"] = entity_internal_number
        # Also store under configured field key if the user added a "Nº Entidade" field
        if fk := field_keys.get("numero_entidade"):
            values[fk] = entity_internal_number
    return {
        "record_id": uuid4().hex,
        "created_at": timestamp_label,
        "section_key": section_key,
        "values": values,
    }


# ─── main entry point ─────────────────────────────────────────────────────────

def import_mt940_content(
    *,
    session: Session,
    member,                            # appverbo.models.member.Member
    content: str,                      # raw MT940 text
    menu_key: str = "extrato",
    additional_fields: list[dict] | None = None,
    entity_internal_number: Optional[str] = None,
    last_record_gets_saldo: bool = True,
) -> MT940ImportResult:
    """
    Parse an MT940 string and append new records to member.profile_custom_fields.
    Returns an MT940ImportResult summary.
    """
    result = MT940ImportResult()

    # ── resolve field keys from process additional_fields ─────────────────
    af = additional_fields or []
    field_keys = _resolve_field_keys(af)
    section_key = _get_section_key(af)

    logger.info("MT940 import — field_keys=%s section_key=%s", field_keys, section_key)

    # ── load existing records ─────────────────────────────────────────────
    storage_key = build_menu_process_records_storage_key(menu_key)
    existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
    existing_records = parse_menu_process_records(existing_profile_fields.get(storage_key))

    dedup_keys = _load_existing_dedup_keys(existing_records, field_keys)

    # ── parse MT940 ───────────────────────────────────────────────────────
    parse_result = parse_mt940_content(content)
    result.errors.extend(parse_result.errors)

    timestamp_label = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    new_records: list[dict] = []

    for tx in parse_result.transactions:
        if tx.chave_dedup in dedup_keys:
            result.duplicadas_ignoradas += 1
            continue
        new_records.append(_build_record(
            tx, field_keys, section_key, timestamp_label, entity_internal_number,
            numero_extrato=parse_result.numero_extrato,
        ))
        dedup_keys.add(tx.chave_dedup)

    if not new_records:
        logger.info("MT940 import — 0 new records (all duplicates or empty)")
        result.linhas_inseridas = 0
        return result

    # ── calculate saldo backwards from closing balance ────────────────────
    if parse_result.saldo_contabilistico and new_records:
        fk_saldo = field_keys.get("saldo")
        fk_valor = field_keys.get("valor")
        if fk_saldo and fk_valor:
            try:
                current_saldo = float(
                    parse_result.saldo_contabilistico.replace(",", ".")
                )
                for rec in reversed(new_records):
                    rec["values"][fk_saldo] = f"{current_saldo:.2f}".replace(".", ",")
                    valor_str = str(rec["values"].get(fk_valor) or "0").replace(",", ".")
                    current_saldo -= float(valor_str)
            except (ValueError, AttributeError):
                if fk_saldo:
                    new_records[-1]["values"][fk_saldo] = parse_result.saldo_contabilistico
        elif fk_saldo:
            new_records[-1]["values"][fk_saldo] = parse_result.saldo_contabilistico

    existing_records.extend(new_records)
    result.linhas_inseridas = len(new_records)

    # ── save ──────────────────────────────────────────────────────────────
    serialized = serialize_menu_process_records(existing_records)
    if serialized:
        existing_profile_fields[storage_key] = serialized
    else:
        existing_profile_fields.pop(storage_key, None)

    member.profile_custom_fields = serialize_member_profile_fields(existing_profile_fields)
    session.commit()

    logger.info(
        "MT940 import done — inserted=%d duplicates=%d errors=%d",
        result.linhas_inseridas,
        result.duplicadas_ignoradas,
        len(result.errors),
    )
    result.status = "ok"
    return result


def import_mt940_from_drive(
    *,
    session: Session,
    member,
    service_account_json: str,
    folder_id: str,
    backup_folder_name: str,
    menu_key: str = "extrato",
    additional_fields: list[dict] | None = None,
    entity_internal_number: Optional[str] = None,
) -> MT940ImportResult:
    """
    Pull all .txt files from the Drive folder, import them, then move to backup.
    """
    from appverbo.services.google_drive_service import (
        download_file_content,
        list_txt_files_in_folder,
        move_file_to_folder,
    )

    combined = MT940ImportResult()

    files = list_txt_files_in_folder(service_account_json, folder_id)
    if not files:
        logger.info("MT940 Drive import — no .txt files found in folder %s", folder_id)
        return combined

    for drive_file in files:
        file_id = drive_file["id"]
        file_name = drive_file.get("name", file_id)
        try:
            logger.info("MT940 Drive import — processing %s", file_name)
            content = download_file_content(service_account_json, file_id)
            res = import_mt940_content(
                session=session,
                member=member,
                content=content,
                menu_key=menu_key,
                additional_fields=additional_fields,
                entity_internal_number=entity_internal_number,
            )
            combined.linhas_inseridas += res.linhas_inseridas
            combined.duplicadas_ignoradas += res.duplicadas_ignoradas
            combined.errors.extend(res.errors)
            combined.ficheiros_processados += 1

            move_file_to_folder(service_account_json, file_id, backup_folder_name, folder_id)
            logger.info("MT940 Drive import — %s done: +%d rows", file_name, res.linhas_inseridas)

        except Exception as exc:
            msg = f"{file_name}: {exc}"
            combined.errors.append(msg)
            logger.exception("MT940 Drive import — error processing %s", file_name)

    if combined.errors:
        combined.status = "partial" if combined.linhas_inseridas else "error"
    return combined
