#!/usr/bin/env python3
"""
Restore meu_perfil custom config: dados_pessoais / dados_de_morada / dados_de_agregados
with their sub-fields, process_lists and 7 subsequent_fields rules.

Applies to the top-level config (no entity scope), which is read by all
legado entities (including entity 1000 / Igreja Braga).
"""

import sys, os, json, uuid
from pathlib import Path

sys.path.insert(0, str(Path("c:/workspace/AppVerboBraga")))
from dotenv import load_dotenv
load_dotenv("c:/workspace/AppVerboBraga/.env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    sys.exit("ERROR: DATABASE_URL not set")

engine = create_engine(DATABASE_URL)

# ---------------------------------------------------------------------------
# Configuration to restore
# ---------------------------------------------------------------------------

# New additional_fields headers + sub-fields to PREPEND before dept fields
FIELDS_TO_PREPEND = [
    {"key": "custom_dados_pessoais",    "label": "Dados pessoais",    "field_type": "header"},
    {"key": "custom_estado_civil",       "label": "Estado civil",      "field_type": "list",   "list_key": "lista_estado_civil"},
    {"key": "custom_tem_filhos",         "label": "Tem filhos",        "field_type": "list",   "list_key": "lista_sim_nao"},
    {"key": "custom_dados_de_morada",    "label": "Dados de morada",   "field_type": "header"},
    {"key": "custom_dados_de_agregados", "label": "Dados de agregados","field_type": "header"},
    {"key": "custom_nome_do_conjuge",    "label": "Nome do cônjuge",   "field_type": "text",   "size": 150},
    {"key": "custom_data_do_matrimonio", "label": "Data do matrimônio","field_type": "date"},
    {"key": "custom_data_da_uniao",      "label": "Data da união",     "field_type": "date"},
    {"key": "custom_quantos_filhos_tens","label": "Quantos filhos tens?","field_type": "number","size": 10},
]

# Process lists for the new list-type fields
NEW_PROCESS_LISTS = [
    {
        "key": "lista_estado_civil",
        "label": "Estado civil",
        "items": ["Solteiro", "Casado", "União de Facto", "Separado", "Divorciado", "Viúvo"],
        "items_csv": "Solteiro, Casado, União de Facto, Separado, Divorciado, Viúvo",
        "source_key": "manual",
        "source_label": "Configuração manual",
    },
    {
        "key": "lista_sim_nao",
        "label": "Sim/Não",
        "items": ["Sim", "Não"],
        "items_csv": "Sim, Não",
        "source_key": "manual",
        "source_label": "Configuração manual",
    },
]

# 7 subsequent rules from the screenshot, plus 1 extra for quantos_filhos_tens
# (must be in dados_pessoais and hidden unless tem_filhos=Sim, so the
#  dados_de_agregados tab is never forced visible through an unconstrained child)
SUBSEQUENT_RULES = [
    {"trigger_field": "custom_tem_filhos",  "field_key": "custom_dados_de_agregados",  "operator": "equals", "trigger_value": "Sim"},
    {"trigger_field": "custom_estado_civil", "field_key": "custom_nome_do_conjuge",     "operator": "equals", "trigger_value": "Casado"},
    {"trigger_field": "custom_estado_civil", "field_key": "custom_nome_do_conjuge",     "operator": "equals", "trigger_value": "União de Facto"},
    {"trigger_field": "custom_estado_civil", "field_key": "custom_data_do_matrimonio",  "operator": "equals", "trigger_value": "Casado"},
    {"trigger_field": "custom_estado_civil", "field_key": "custom_data_da_uniao",       "operator": "equals", "trigger_value": "União de facto"},
    {"trigger_field": "custom_estado_civil", "field_key": "custom_dados_de_agregados",  "operator": "equals", "trigger_value": "Casado"},
    {"trigger_field": "custom_estado_civil", "field_key": "custom_dados_de_agregados",  "operator": "equals", "trigger_value": "União de Facto"},
    # Extra rule: quantos_filhos_tens lives in dados_pessoais but only makes sense when has children
    {"trigger_field": "custom_tem_filhos",  "field_key": "custom_quantos_filhos_tens", "operator": "equals", "trigger_value": "Sim"},
]

# Header assignment for built-in and new custom fields
BUILTIN_HEADER_MAP = {
    "nome":               "custom_dados_pessoais",
    "telefone":           "custom_dados_pessoais",
    "email":              "custom_dados_pessoais",
    "data_nascimento":    "custom_dados_pessoais",
    "whatsapp":           "custom_dados_pessoais",
    "autorizacao_whatsapp": "custom_dados_pessoais",
    "pais":               "custom_dados_de_morada",
}
CUSTOM_HEADER_MAP = {
    "custom_estado_civil":       "custom_dados_pessoais",
    "custom_tem_filhos":         "custom_dados_pessoais",
    # quantos_filhos_tens belongs to dados_pessoais: if it were under dados_de_agregados
    # (with no subsequent rule) it would force that tab permanently visible even for
    # Estado civil=Solteiro / Tem filhos=Nao, because the JS un-hides a header whenever
    # any of its children is visible.
    "custom_quantos_filhos_tens":"custom_dados_pessoais",
    "custom_nome_do_conjuge":    "custom_dados_de_agregados",
    "custom_data_do_matrimonio": "custom_dados_de_agregados",
    "custom_data_da_uniao":      "custom_dados_de_agregados",
}

# New selectable (non-header) fields to add BETWEEN built-ins and dept fields
# They will be inserted after their header's last built-in field
NEW_SELECTABLE_KEYS = [
    "custom_estado_civil",
    "custom_tem_filhos",
    "custom_nome_do_conjuge",
    "custom_data_do_matrimonio",
    "custom_data_da_uniao",
    "custom_quantos_filhos_tens",
]


def build_new_visible_rows(old_rows: list[dict]) -> list[dict]:
    """
    Rebuild process_visible_field_rows:
    - Assign built-in fields to custom header sections
    - Insert new custom fields after the built-in fields they follow
    - Keep department field rows unchanged
    """
    # Determine existing keys so we don't duplicate
    old_keys = {str(r.get("field_key") or "").strip().lower() for r in old_rows}

    new_rows: list[dict] = []

    # Reconstruct ordering: built-ins first (with new headers), then new custom fields, then dept fields
    # Order for built-in block (those that go in custom_dados_pessoais):
    personal_builtins = [k for k in ["nome", "telefone", "email", "data_nascimento", "whatsapp", "autorizacao_whatsapp"] if k in old_keys]
    morada_builtins   = [k for k in ["pais"] if k in old_keys]
    # Remaining built-ins without header
    all_assigned_builtins = set(personal_builtins + morada_builtins)
    other_builtins = [
        r for r in old_rows
        if str(r.get("field_key") or "").strip().lower() not in all_assigned_builtins
        and str(r.get("field_key") or "").strip().lower() not in {k for k in old_keys if k.startswith("custom_")}
    ]

    # Dept custom fields (existing)
    dept_rows = [
        r for r in old_rows
        if str(r.get("field_key") or "").strip().lower().startswith("custom_")
        and str(r.get("field_key") or "").strip().lower() not in CUSTOM_HEADER_MAP
        and str(r.get("field_key") or "").strip().lower() not in {str(f["key"]).strip().lower() for f in FIELDS_TO_PREPEND if f.get("field_type") != "header"}
    ]

    # 1. Personal built-in fields
    for k in personal_builtins:
        new_rows.append({"field_key": k, "header_key": "custom_dados_pessoais"})

    # 2. New custom personal fields
    for k in ["custom_estado_civil", "custom_tem_filhos"]:
        new_rows.append({"field_key": k, "header_key": "custom_dados_pessoais"})

    # 3. Morada built-in
    for k in morada_builtins:
        new_rows.append({"field_key": k, "header_key": "custom_dados_de_morada"})

    # 4. New custom dados_pessoais overflow (quantos_filhos_tens)
    for k in ["custom_quantos_filhos_tens"]:
        new_rows.append({"field_key": k, "header_key": "custom_dados_pessoais"})

    # 5. New custom agregados fields
    for k in ["custom_nome_do_conjuge", "custom_data_do_matrimonio", "custom_data_da_uniao"]:
        new_rows.append({"field_key": k, "header_key": "custom_dados_de_agregados"})

    # 6. Other built-ins with no header
    for r in other_builtins:
        fk = str(r.get("field_key") or "").strip().lower()
        new_rows.append({"field_key": fk, "header_key": str(r.get("header_key") or "").strip().lower()})

    # 7. Existing dept custom rows
    for r in dept_rows:
        fk = str(r.get("field_key") or "").strip().lower()
        hk = str(r.get("header_key") or "").strip().lower()
        new_rows.append({"field_key": fk, "header_key": hk})

    return new_rows


def build_legacy_visible_fields(rows: list[dict]) -> list[str]:
    """Build the legacy visible_fields list (interleaves header keys as separators)."""
    seen: set[str] = set()
    result: list[str] = []
    active_header = ""
    for r in rows:
        fk = str(r.get("field_key") or "").strip().lower()
        hk = str(r.get("header_key") or "").strip().lower()
        if hk and hk != active_header:
            if hk not in seen:
                result.append(hk)
                seen.add(hk)
            active_header = hk
        if not hk:
            active_header = ""
        if fk not in seen:
            result.append(fk)
            seen.add(fk)
    return result


def main(dry_run: bool = False) -> None:
    with Session(engine) as sess:
        row = sess.execute(
            text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = 'meu_perfil'")
        ).one_or_none()

        if row is None:
            sys.exit("ERROR: meu_perfil not found")

        raw = row[0]
        cfg: dict = json.loads(raw) if isinstance(raw, str) else (dict(raw) if raw else {})

        # ---- additional_fields ----
        cur_af: list[dict] = list(cfg.get("additional_fields") or [])
        existing_keys = {str(f.get("key") or "").strip().lower() for f in cur_af}
        fields_to_add = [f for f in FIELDS_TO_PREPEND if str(f.get("key") or "").strip().lower() not in existing_keys]
        new_af = fields_to_add + cur_af
        print(f"additional_fields: {len(cur_af)} → {len(new_af)} (+{len(fields_to_add)} new)")

        # ---- process_visible_field_rows ----
        cur_rows: list[dict] = list(cfg.get("process_visible_field_rows") or [])
        new_rows = build_new_visible_rows(cur_rows)
        new_pvf = [str(r["field_key"]) for r in new_rows]
        new_pvf_header_map = {
            str(r["field_key"]): str(r["header_key"])
            for r in new_rows
            if str(r.get("header_key") or "").strip()
        }
        new_visible_headers: list[str] = []
        seen_hdr: set[str] = set()
        for r in new_rows:
            hk = str(r.get("header_key") or "").strip().lower()
            if hk and hk not in seen_hdr:
                new_visible_headers.append(hk)
                seen_hdr.add(hk)
        legacy_vf = build_legacy_visible_fields(new_rows)
        print(f"process_visible_fields: {len(cfg.get('process_visible_fields', []))} → {len(new_pvf)}")
        print(f"process_visible_headers: {new_visible_headers}")

        # ---- process_lists ----
        cur_pl: list[dict] = list(cfg.get("process_lists") or [])
        existing_list_keys = {str(l.get("key") or "").strip().lower() for l in cur_pl}
        lists_to_add = [l for l in NEW_PROCESS_LISTS if l["key"] not in existing_list_keys]
        new_pl = cur_pl + lists_to_add
        print(f"process_lists: {len(cur_pl)} → {len(new_pl)} (+{len(lists_to_add)} new)")

        # ---- subsequent_fields ----
        print(f"subsequent_fields: {len(cfg.get('subsequent_fields', []))} → {len(SUBSEQUENT_RULES)} (replace)")

        if dry_run:
            print("\n[DRY RUN] No changes written.")
            return

        refresh_token = str(uuid.uuid4())
        updated = dict(cfg)
        updated["additional_fields"]                = new_af
        updated["process_visible_fields"]           = new_pvf
        updated["process_visible_field_rows"]       = new_rows
        updated["process_visible_field_header_map"] = new_pvf_header_map
        updated["process_visible_headers"]          = new_visible_headers
        updated["visible_fields"]                   = legacy_vf
        updated["visible_field_headers"]            = new_pvf_header_map
        updated["process_visible_fields_configured"]= True
        updated["subsequent_fields"]                = SUBSEQUENT_RULES
        updated["process_lists"]                    = new_pl
        updated["process_additional_fields_refresh_version"] = refresh_token
        updated["sidebar_global_refresh_version"]   = refresh_token
        updated["_restore_meu_perfil_v1"]           = refresh_token

        sess.execute(
            text("UPDATE sidebar_menu_settings SET menu_config = :cfg WHERE menu_key = 'meu_perfil'"),
            {"cfg": json.dumps(updated, ensure_ascii=False, default=str)},
        )
        sess.commit()
        print("\nSUCCESS — meu_perfil config updated.")
        print(f"  additional_fields : {len(new_af)}")
        print(f"  process_visible   : {len(new_pvf)}")
        print(f"  subsequent_fields : {len(SUBSEQUENT_RULES)}")
        print(f"  process_lists     : {len(new_pl)}")


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    main(dry_run=dry)
