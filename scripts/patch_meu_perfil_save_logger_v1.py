from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()
PROFILE_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"


####################################################################################
# (2) FUNCOES AUXILIARES DO PATCH
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def upsert_block_v1(
    content: str,
    start_marker: str,
    end_marker: str,
    block: str,
    anchor: str,
    insert_after: bool,
) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\n?",
        flags=re.DOTALL,
    )

    if pattern.search(content):
        return pattern.sub(block, content, count=1)

    if anchor not in content:
        raise RuntimeError(f"Ancora nao encontrada: {anchor[:120]}")

    if insert_after:
        return content.replace(anchor, anchor + block, 1)

    return content.replace(anchor, block + anchor, 1)


def update_update_personal_profile_section_v1(content: str, transform_func):
    start_anchor = '@router.post("/users/profile/personal")'
    start_index = content.find(start_anchor)

    if start_index < 0:
        raise RuntimeError("Endpoint /users/profile/personal nao encontrado.")

    next_router_index = content.find("\n@router.", start_index + len(start_anchor))

    if next_router_index < 0:
        next_router_index = len(content)

    section = content[start_index:next_router_index]
    new_section = transform_func(section)

    return content[:start_index] + new_section + content[next_router_index:]


####################################################################################
# (3) BLOCO LOGGER
####################################################################################

LOGGER_HELPER_START = "# APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1_START"
LOGGER_HELPER_END = "# APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1_END"

LOGGER_HELPER_BLOCK = r'''
# APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1_START
def _safe_meu_perfil_logger_value_v1(raw_value: Any, max_size: int = 1200) -> Any:
    clean_value = str(raw_value or "")

    if len(clean_value) > max_size:
        return clean_value[:max_size] + "...[TRUNCATED]"

    return clean_value


def _append_meu_perfil_logger_value_v1(target: dict[str, Any], key: str, value: Any) -> None:
    clean_key = str(key or "").strip()

    if not clean_key:
        return

    if clean_key in target:
        if not isinstance(target[clean_key], list):
            target[clean_key] = [target[clean_key]]
        target[clean_key].append(value)
        return

    target[clean_key] = value


def _build_meu_perfil_form_debug_snapshot_v1(submitted_form: Any) -> dict[str, Any]:
    import json

    blocked_fragments = (
        "password",
        "senha",
        "token",
        "csrf",
        "secret",
        "cookie",
        "authorization",
    )

    if hasattr(submitted_form, "multi_items"):
        raw_items = list(submitted_form.multi_items())
    elif hasattr(submitted_form, "items"):
        raw_items = list(submitted_form.items())
    else:
        raw_items = []

    general_fields: dict[str, Any] = {}
    custom_fields: dict[str, Any] = {}
    quantity_payloads: dict[str, Any] = {}
    quantity_live_fields: dict[str, Any] = {}

    for raw_name, raw_value in raw_items:
        clean_name = str(raw_name or "").strip()
        clean_name_lower = clean_name.lower()

        if not clean_name:
            continue

        if any(fragment in clean_name_lower for fragment in blocked_fragments):
            clean_value = "[FILTERED]"
        else:
            clean_value = _safe_meu_perfil_logger_value_v1(raw_value)

        if clean_name.startswith("process_quantity_payload__"):
            parsed_payload: Any = None
            parsed_error = ""

            try:
                parsed_payload = json.loads(str(raw_value or "[]"))
            except Exception as exc:
                parsed_error = repr(exc)

            _append_meu_perfil_logger_value_v1(
                quantity_payloads,
                clean_name,
                {
                    "raw": clean_value,
                    "parsed": parsed_payload,
                    "parse_error": parsed_error,
                },
            )
            continue

        if clean_name.startswith("process_quantity_field__"):
            _append_meu_perfil_logger_value_v1(
                quantity_live_fields,
                clean_name,
                clean_value,
            )
            continue

        if clean_name.startswith("custom_field__"):
            _append_meu_perfil_logger_value_v1(
                custom_fields,
                clean_name,
                clean_value,
            )
            continue

        _append_meu_perfil_logger_value_v1(
            general_fields,
            clean_name,
            clean_value,
        )

    return {
        "general_fields": general_fields,
        "custom_fields": custom_fields,
        "quantity_payloads": quantity_payloads,
        "quantity_live_fields": quantity_live_fields,
        "all_field_names": [
            str(raw_name or "").strip()
            for raw_name, _raw_value in raw_items
            if str(raw_name or "").strip()
        ],
    }


def _write_meu_perfil_save_debug_log_v1(
    request: Request,
    submitted_form: Any,
    stage: str,
    data: dict[str, Any] | None = None,
) -> None:
    import json
    import os
    from pathlib import Path
    from datetime import datetime, timezone

    try:
        log_dir = Path(
            os.environ.get(
                "APPVERBO_PROFILE_SAVE_LOG_DIR",
                "appverbo_runtime_logs",
            )
        )
        log_dir.mkdir(parents=True, exist_ok=True)

        request_url = ""
        request_path = ""
        request_method = ""
        request_client = ""

        try:
            request_url = str(request.url)
            request_path = str(request.url.path)
            request_method = str(request.method)
            request_client = str(getattr(request.client, "host", "") or "")
        except Exception:
            pass

        log_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "logger": "APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1",
            "stage": str(stage or "").strip(),
            "request": {
                "method": request_method,
                "path": request_path,
                "url": request_url,
                "client": request_client,
            },
            "form_snapshot": _build_meu_perfil_form_debug_snapshot_v1(submitted_form),
            "data": data or {},
        }

        log_line = json.dumps(
            log_entry,
            ensure_ascii=False,
            default=str,
            sort_keys=True,
        )

        log_path = log_dir / "meu_perfil_save_debug.log"

        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(log_line + "\n")

        print("APPVERBO_MEU_PERFIL_SAVE_DEBUG " + log_line, flush=True)

    except Exception as exc:
        print(
            "APPVERBO_MEU_PERFIL_SAVE_DEBUG_ERROR " + repr(exc),
            flush=True,
        )
# APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1_END

'''


####################################################################################
# (4) BLOCOS DE CHAMADA DO LOGGER
####################################################################################

FORM_RECEIVED_START = "    # APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1_START"
FORM_RECEIVED_END = "    # APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1_END"

FORM_RECEIVED_BLOCK = r'''    # APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1_START
    _write_meu_perfil_save_debug_log_v1(
        request,
        submitted_form,
        "01_form_received",
        {
            "message": "Formulario recebido no endpoint /users/profile/personal antes de qualquer processamento.",
        },
    )
    # APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1_END

'''


QUANTITY_CONTEXT_START = "        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1_START"
QUANTITY_CONTEXT_END = "        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1_END"

QUANTITY_CONTEXT_BLOCK = r'''        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1_START
        _write_meu_perfil_save_debug_log_v1(
            request,
            submitted_form,
            "02_quantity_context_loaded",
            {
                "current_user_id": current_user.get("id") if isinstance(current_user, dict) else None,
                "member_id": getattr(member, "id", None),
                "quantity_rules": quantity_rules,
                "quantity_repeated_field_keys": sorted(list(quantity_repeated_field_keys)),
                "process_options_count": len(process_options),
            },
        )
        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1_END

'''


BEFORE_UPDATE_START = "        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1_START"
BEFORE_UPDATE_END = "        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1_END"

BEFORE_UPDATE_BLOCK = r'''        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1_START
        _write_meu_perfil_save_debug_log_v1(
            request,
            submitted_form,
            "03_before_member_update",
            {
                "current_user_id": current_user.get("id") if isinstance(current_user, dict) else None,
                "member_id": getattr(member, "id", None),
                "existing_quantity_values": existing_quantity_values,
                "updated_quantity_values": updated_quantity_values,
                "updated_custom_fields": updated_custom_fields,
                "visible_custom_keys": visible_custom_keys,
                "active_custom_keys": active_custom_keys,
                "hidden_meu_perfil_targets": hidden_meu_perfil_targets,
                "missing_required_custom_labels": missing_required_custom_labels,
            },
        )
        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1_END

'''


AFTER_COMMIT_START = "        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1_START"
AFTER_COMMIT_END = "        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1_END"

AFTER_COMMIT_BLOCK = r'''        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1_START
        _write_meu_perfil_save_debug_log_v1(
            request,
            submitted_form,
            "04_after_session_commit",
            {
                "current_user_id": current_user.get("id") if isinstance(current_user, dict) else None,
                "member_id": getattr(member, "id", None),
                "stored_profile_custom_fields": getattr(member, "profile_custom_fields", None),
                "stored_full_name": getattr(member, "full_name", None),
                "stored_primary_phone": getattr(member, "primary_phone", None),
                "stored_email": getattr(member, "email", None),
            },
        )
        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1_END

'''


####################################################################################
# (5) APLICAR PATCH
####################################################################################

def patch_profile_handlers_v1() -> None:
    content = read_text_v1(PROFILE_HANDLERS_PATH)

    helper_anchor = "\n\ndef _normalize_process_field_type"
    content = upsert_block_v1(
        content,
        LOGGER_HELPER_START,
        LOGGER_HELPER_END,
        LOGGER_HELPER_BLOCK,
        helper_anchor,
        insert_after=False,
    )

    def transform_profile_section_v1(section: str) -> str:
        section = upsert_block_v1(
            section,
            FORM_RECEIVED_START,
            FORM_RECEIVED_END,
            FORM_RECEIVED_BLOCK,
            "    submitted_form = await request.form()\n",
            insert_after=True,
        )

        section = upsert_block_v1(
            section,
            QUANTITY_CONTEXT_START,
            QUANTITY_CONTEXT_END,
            QUANTITY_CONTEXT_BLOCK,
            "        quantity_repeated_field_keys = get_menu_process_quantity_repeated_field_keys(quantity_rules)\n",
            insert_after=True,
        )

        section = upsert_block_v1(
            section,
            BEFORE_UPDATE_START,
            BEFORE_UPDATE_END,
            BEFORE_UPDATE_BLOCK,
            '        previous_phone = (member.primary_phone or "").strip()\n',
            insert_after=False,
        )

        if AFTER_COMMIT_START in section and AFTER_COMMIT_END in section:
            pattern = re.compile(
                re.escape(AFTER_COMMIT_START) + r".*?" + re.escape(AFTER_COMMIT_END) + r"\n?",
                flags=re.DOTALL,
            )
            section = pattern.sub(AFTER_COMMIT_BLOCK, section, count=1)
        else:
            commit_anchor = "        session.commit()\n"
            if commit_anchor not in section:
                raise RuntimeError("session.commit() nao encontrado dentro de update_personal_profile.")

            section = section.replace(
                commit_anchor,
                commit_anchor + AFTER_COMMIT_BLOCK,
                1,
            )

        return section

    content = update_update_personal_profile_section_v1(
        content,
        transform_profile_section_v1,
    )

    required_markers = [
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1_START",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1_START",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1_START",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1_START",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1_START",
        "APPVERBO_MEU_PERFIL_SAVE_DEBUG",
        "process_quantity_payload__",
        "updated_quantity_values",
        "stored_profile_custom_fields",
    ]

    missing_markers = [
        marker
        for marker in required_markers
        if marker not in content
    ]

    if missing_markers:
        raise RuntimeError("Marcadores ausentes depois do patch: " + ", ".join(missing_markers))

    write_text_v1(PROFILE_HANDLERS_PATH, content)


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    if not PROFILE_HANDLERS_PATH.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {PROFILE_HANDLERS_PATH}")

    patch_profile_handlers_v1()

    print("OK: logger APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1 inserido em profile_handlers.py")
    print("OK: o log sera escrito em appverbo_runtime_logs/meu_perfil_save_debug.log")
    print("OK: o log tambem aparece em docker compose logs com prefixo APPVERBO_MEU_PERFIL_SAVE_DEBUG")


if __name__ == "__main__":
    main()
