from __future__ import annotations

from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_HANDLERS = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
PAGE_PY = PROJECT_ROOT / "appverbo" / "services" / "page.py"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


####################################################################################
# (3) PATCH DE IMPORTS
####################################################################################

def patch_imports_v1(content: str) -> str:
    if "import json" not in content:
        content = content.replace(
            "from fastapi import APIRouter, Request, Form, status\n",
            "import json\n\nfrom fastapi import APIRouter, Request, Form, status\n",
            1,
        )

    if "from sqlalchemy import text" not in content:
        content = content.replace(
            "from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse\n",
            "from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse\nfrom sqlalchemy import text\n",
            1,
        )

    return content


####################################################################################
# (4) HELPER PARA PRESERVAR CAMPO -> CABECALHO
####################################################################################

def patch_helper_v1(content: str) -> str:
    marker = "APPVERBO_PRESERVE_HEADER_ASSIGNMENTS_V1_START"

    if marker in content:
        return content

    helper_block = r'''

# APPVERBO_PRESERVE_HEADER_ASSIGNMENTS_V1_START

# ###################################################################################
# (PRESERVE_HEADER_ASSIGNMENTS_V1) PRESERVAR ATRIBUICAO CAMPO -> CABECALHO
# ###################################################################################

def _normalize_menu_key_local_v1(value: object) -> str:
    return str(value or "").strip().lower()


def _read_sidebar_menu_config_v1(session, menu_key: str) -> dict:
    clean_menu_key = _normalize_menu_key_local_v1(menu_key)

    raw_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": clean_menu_key},
    ).scalar_one_or_none()

    if not raw_config:
        return {}

    try:
        parsed_config = json.loads(raw_config)
    except (TypeError, ValueError):
        return {}

    return parsed_config if isinstance(parsed_config, dict) else {}


def _write_sidebar_menu_config_v1(session, menu_key: str, menu_config: dict) -> None:
    clean_menu_key = _normalize_menu_key_local_v1(menu_key)

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )


def _get_header_assignments_from_config_v1(menu_config: dict) -> dict[str, str]:
    assignments: dict[str, str] = {}

    raw_rows = menu_config.get("process_visible_field_rows")
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue

            field_key = _normalize_menu_key_local_v1(raw_row.get("field_key"))
            header_key = _normalize_menu_key_local_v1(raw_row.get("header_key"))

            if not field_key or not header_key:
                continue

            assignments[field_key] = header_key

    raw_header_map = menu_config.get("process_visible_field_header_map")
    if isinstance(raw_header_map, dict):
        for raw_field_key, raw_header_key in raw_header_map.items():
            field_key = _normalize_menu_key_local_v1(raw_field_key)
            header_key = _normalize_menu_key_local_v1(raw_header_key)

            if not field_key or not header_key:
                continue

            assignments[field_key] = header_key

    return assignments


def _get_header_keys_from_config_v1(menu_config: dict) -> set[str]:
    header_keys: set[str] = set()

    raw_fields = menu_config.get("additional_fields")
    if not isinstance(raw_fields, list):
        return header_keys

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue

        field_key = _normalize_menu_key_local_v1(raw_field.get("key"))
        field_type = _normalize_menu_key_local_v1(raw_field.get("field_type") or raw_field.get("type"))

        if field_key and field_type == "header":
            header_keys.add(field_key)

    return header_keys


def _get_visible_fields_from_config_v1(menu_config: dict) -> list[str]:
    visible_fields: list[str] = []
    seen_fields: set[str] = set()

    raw_visible_fields = menu_config.get("process_visible_fields")
    if isinstance(raw_visible_fields, list):
        for raw_field_key in raw_visible_fields:
            field_key = _normalize_menu_key_local_v1(raw_field_key)

            if not field_key or field_key in seen_fields:
                continue

            seen_fields.add(field_key)
            visible_fields.append(field_key)

    raw_rows = menu_config.get("process_visible_field_rows")
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue

            field_key = _normalize_menu_key_local_v1(raw_row.get("field_key"))

            if not field_key or field_key in seen_fields:
                continue

            seen_fields.add(field_key)
            visible_fields.append(field_key)

    return visible_fields


def _restore_menu_header_assignments_after_additional_fields_v1(
    session,
    menu_key: str,
    old_menu_config: dict,
) -> None:
    old_assignments = _get_header_assignments_from_config_v1(old_menu_config)

    if not old_assignments:
        return

    current_config = _read_sidebar_menu_config_v1(session, menu_key)
    if not current_config:
        return

    current_header_keys = _get_header_keys_from_config_v1(current_config)
    current_visible_fields = _get_visible_fields_from_config_v1(current_config)

    if not current_visible_fields:
        current_visible_fields = _get_visible_fields_from_config_v1(old_menu_config)

    if not current_visible_fields:
        return

    restored_header_map: dict[str, str] = {}
    restored_rows: list[dict[str, str]] = []

    for field_key in current_visible_fields:
        if field_key in current_header_keys:
            continue

        header_key = old_assignments.get(field_key, "")
        if header_key not in current_header_keys:
            header_key = ""

        if header_key:
            restored_header_map[field_key] = header_key

        restored_rows.append(
            {
                "field_key": field_key,
                "header_key": header_key,
            }
        )

    current_config["process_visible_field_header_map"] = restored_header_map
    current_config["process_visible_field_rows"] = restored_rows

    _write_sidebar_menu_config_v1(session, menu_key, current_config)
    session.commit()


def _update_sidebar_menu_additional_fields_preserve_headers_v1(
    session,
    menu_key: str,
    payload_fields: list[dict[str, str]],
) -> tuple[bool, str]:
    old_menu_config = _read_sidebar_menu_config_v1(session, menu_key)

    ok, error_message = update_sidebar_menu_additional_fields_v1(
        session,
        menu_key,
        payload_fields,
    )

    if not ok:
        return ok, error_message

    _restore_menu_header_assignments_after_additional_fields_v1(
        session,
        menu_key,
        old_menu_config,
    )

    return ok, error_message

# APPVERBO_PRESERVE_HEADER_ASSIGNMENTS_V1_END
'''

    insert_before = '@router.post("/settings/menu/process-additional-fields", response_class=HTMLResponse)'
    if insert_before not in content:
        raise RuntimeError("Endpoint process-additional-fields não encontrado para inserir helper.")

    return content.replace(insert_before, helper_block + "\n\n" + insert_before, 1)


####################################################################################
# (5) TROCAR CHAMADA DO HANDLER
####################################################################################

def patch_handler_call_v1(content: str) -> str:
    old_call = '''        ok, error_message = update_sidebar_menu_additional_fields_v1(
            session,
            clean_menu_key,
            payload_fields,
        )'''

    new_call = '''        ok, error_message = _update_sidebar_menu_additional_fields_preserve_headers_v1(
            session,
            clean_menu_key,
            payload_fields,
        )'''

    if new_call in content:
        return content

    if old_call not in content:
        raise RuntimeError("Chamada antiga update_sidebar_menu_additional_fields_v1 não encontrada.")

    return content.replace(old_call, new_call, 1)


####################################################################################
# (6) CORRIGIR MOJIBAKE EM page.py
####################################################################################

def patch_page_mojibake_v1() -> None:
    content = read_text_v1(PAGE_PY)
    content = content.replace('"pais": "PaÃs"', '"pais": "País"')
    content = content.replace("'pais': 'PaÃs'", "'pais': 'País'")
    write_text_v1(PAGE_PY, content)


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    content = read_text_v1(SETTINGS_HANDLERS)

    content = patch_imports_v1(content)
    content = patch_helper_v1(content)
    content = patch_handler_call_v1(content)

    write_text_v1(SETTINGS_HANDLERS, content)
    patch_page_mojibake_v1()

    print("OK: settings_handlers.py ajustado para preservar atribuições campo -> cabeçalho.")
    print("OK: page.py validado para corrigir PaÃs -> País.")


if __name__ == "__main__":
    main()