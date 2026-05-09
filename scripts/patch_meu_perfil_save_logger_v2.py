from __future__ import annotations

import re
import sys
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()
PROFILE_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"

CLEAN_BACKUP_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else None


####################################################################################
# (2) FUNCOES AUXILIARES DO PATCH
####################################################################################

def read_text_v2(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v2(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_marked_block_v2(content: str, start_marker: str, end_marker: str) -> str:
    pattern = re.compile(
        r"^[^\S\r\n]*#\s*" + re.escape(start_marker) + r".*?"
        + r"^[^\S\r\n]*#\s*" + re.escape(end_marker) + r"[^\r\n]*(?:\r?\n)?",
        flags=re.DOTALL | re.MULTILINE,
    )

    return pattern.sub("", content)


def remove_previous_logger_blocks_v2(content: str) -> str:
    marker_pairs = [
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V2_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V2_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V2_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V2_END"),
    ]

    for start_marker, end_marker in marker_pairs:
        content = remove_marked_block_v2(content, start_marker, end_marker)

    return content


def update_update_personal_profile_section_v2(content: str, transform_func):
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
# (3) BLOCO LOGGER SEGURO
####################################################################################

LOGGER_HELPER_BLOCK = r'''
# APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2_START
def _safe_meu_perfil_logger_value_v2(raw_value: Any, max_size: int = 1500) -> Any:
    clean_value = str(raw_value or "")

    if len(clean_value) > max_size:
        return clean_value[:max_size] + "...[TRUNCATED]"

    return clean_value


def _append_meu_perfil_logger_value_v2(target: dict[str, Any], key: str, value: Any) -> None:
    clean_key = str(key or "").strip()

    if not clean_key:
        return

    if clean_key in target:
        if not isinstance(target[clean_key], list):
            target[clean_key] = [target[clean_key]]
        target[clean_key].append(value)
        return

    target[clean_key] = value


def _build_meu_perfil_form_debug_snapshot_v2(submitted_form: Any) -> dict[str, Any]:
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
            clean_value = _safe_meu_perfil_logger_value_v2(raw_value)

        if clean_name.startswith("process_quantity_payload__"):
            parsed_payload: Any = None
            parsed_error = ""

            try:
                parsed_payload = json.loads(str(raw_value or "[]"))
            except Exception as exc:
                parsed_error = repr(exc)

            _append_meu_perfil_logger_value_v2(
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
            _append_meu_perfil_logger_value_v2(
                quantity_live_fields,
                clean_name,
                clean_value,
            )
            continue

        if clean_name.startswith("custom_field__"):
            _append_meu_perfil_logger_value_v2(
                custom_fields,
                clean_name,
                clean_value,
            )
            continue

        _append_meu_perfil_logger_value_v2(
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


def _write_meu_perfil_save_debug_log_v2(
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
            "logger": "APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2",
            "stage": str(stage or "").strip(),
            "request": {
                "method": request_method,
                "path": request_path,
                "url": request_url,
                "client": request_client,
            },
            "form_snapshot": _build_meu_perfil_form_debug_snapshot_v2(submitted_form),
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
# APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2_END

'''


FORM_RECEIVED_BLOCK = r'''    # APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V2_START
    _write_meu_perfil_save_debug_log_v2(
        request,
        submitted_form,
        "01_form_received",
        {
            "message": "Formulario recebido no endpoint /users/profile/personal antes de qualquer processamento.",
        },
    )
    # APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V2_END

'''


QUANTITY_CONTEXT_BLOCK = r'''        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V2_START
        _write_meu_perfil_save_debug_log_v2(
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
        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V2_END

'''


####################################################################################
# (4) APLICAR PATCH
####################################################################################

def patch_profile_handlers_v2() -> None:
    content = read_text_v2(PROFILE_HANDLERS_PATH)

    clean_content = remove_previous_logger_blocks_v2(content)

    if CLEAN_BACKUP_PATH is not None:
        CLEAN_BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        write_text_v2(CLEAN_BACKUP_PATH, clean_content)

    helper_anchor = "\ndef _normalize_process_field_type"

    if helper_anchor not in clean_content:
        raise RuntimeError("Ancora para inserir helper nao encontrada: def _normalize_process_field_type")

    content = clean_content.replace(
        helper_anchor,
        "\n" + LOGGER_HELPER_BLOCK + "\ndef _normalize_process_field_type",
        1,
    )

    def transform_profile_section_v2(section: str) -> str:
        form_anchor = "    submitted_form = await request.form()\n"

        if form_anchor not in section:
            raise RuntimeError("Ancora submitted_form nao encontrada no endpoint update_personal_profile.")

        section = section.replace(
            form_anchor,
            form_anchor + FORM_RECEIVED_BLOCK,
            1,
        )

        context_anchor = "        quantity_repeated_field_keys = get_menu_process_quantity_repeated_field_keys(quantity_rules)\n"

        if context_anchor not in section:
            raise RuntimeError("Ancora quantity_repeated_field_keys nao encontrada no endpoint update_personal_profile.")

        section = section.replace(
            context_anchor,
            context_anchor + QUANTITY_CONTEXT_BLOCK,
            1,
        )

        return section

    content = update_update_personal_profile_section_v2(
        content,
        transform_profile_section_v2,
    )

    required_markers = [
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2_START",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V2_START",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V2_START",
        "APPVERBO_MEU_PERFIL_SAVE_DEBUG",
        "process_quantity_payload__",
        "process_quantity_field__",
        "quantity_rules",
        "quantity_repeated_field_keys",
    ]

    missing_markers = [
        marker
        for marker in required_markers
        if marker not in content
    ]

    if missing_markers:
        raise RuntimeError("Marcadores ausentes depois do patch: " + ", ".join(missing_markers))

    write_text_v2(PROFILE_HANDLERS_PATH, content)


####################################################################################
# (5) EXECUCAO
####################################################################################

def main() -> None:
    if not PROFILE_HANDLERS_PATH.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {PROFILE_HANDLERS_PATH}")

    patch_profile_handlers_v2()

    print("OK: logger quebrado removido.")
    print("OK: logger APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2 inserido com pontos seguros.")
    print("OK: backup limpo sem logger gravado em:", CLEAN_BACKUP_PATH)


if __name__ == "__main__":
    main()
