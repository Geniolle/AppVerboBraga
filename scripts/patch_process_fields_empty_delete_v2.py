from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MENU_SETTINGS_PATH = PROJECT_ROOT / "appverbo" / "menu_settings.py"
HTML_PATH = PROJECT_ROOT / "templates" / "new_user.html"
V6_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v6.js"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v2(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v2(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def list_matching_functions_v2(content: str, keyword: str) -> list[str]:
    found: list[str] = []

    for match in re.finditer(r"^def\s+([a-zA-Z0-9_]+)\s*\(", content, flags=re.MULTILINE):
        function_name = match.group(1)

        if keyword.lower() in function_name.lower():
            found.append(function_name)

    return found


def replace_top_level_function_v2(content: str, function_name: str, replacement: str) -> str:
    lines = content.splitlines(keepends=True)
    start_index: int | None = None

    for index, line in enumerate(lines):
        if re.match(rf"^def\s+{re.escape(function_name)}\s*\(", line):
            start_index = index
            break

    if start_index is None:
        process_functions = list_matching_functions_v2(content, "process")
        visible_functions = list_matching_functions_v2(content, "visible")
        update_functions = list_matching_functions_v2(content, "update")

        raise RuntimeError(
            "Função não encontrada: "
            + function_name
            + "\nFunções com 'process': "
            + ", ".join(process_functions[:80])
            + "\nFunções com 'visible': "
            + ", ".join(visible_functions[:80])
            + "\nFunções com 'update': "
            + ", ".join(update_functions[:80])
        )

    end_index = len(lines)

    for index in range(start_index + 1, len(lines)):
        if re.match(r"^(def|class)\s+", lines[index]):
            end_index = index
            break

    return "".join(lines[:start_index]) + replacement.rstrip() + "\n\n" + "".join(lines[end_index:])


####################################################################################
# (3) PATCH appverbo/menu_settings.py
####################################################################################

def patch_menu_settings_v2() -> None:
    content = read_text_v2(MENU_SETTINGS_PATH)

    visible_fields_function = '''
def get_menu_process_visible_fields(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    # APPVERBO_PROCESS_FIELDS_EMPTY_DELETE_V2_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    clean_menu_config = menu_config if isinstance(menu_config, dict) else {}

    options = get_menu_process_field_options(clean_menu_key, clean_menu_config)
    available_option_keys = {
        str(item.get("key") or "").strip().lower()
        for item in options
        if str(item.get("key") or "").strip()
    }

    raw_visible_fields = clean_menu_config.get("process_visible_fields")
    has_explicit_process_fields_config = (
        "process_visible_fields" in clean_menu_config
        or bool(clean_menu_config.get("process_visible_fields_configured"))
    )

    normalized_visible_fields: list[str] = []
    seen_fields: set[str] = set()

    if isinstance(raw_visible_fields, str):
        raw_items = [
            chunk
            for chunk in re.split(r"[,;\\n\\r]+", raw_visible_fields)
            if str(chunk or "").strip()
        ]
    elif isinstance(raw_visible_fields, (list, tuple, set)):
        raw_items = list(raw_visible_fields)
    else:
        raw_items = []

    for raw_field_key in raw_items:
        field_key = str(raw_field_key or "").strip().lower()

        if not field_key:
            continue

        if field_key in seen_fields:
            continue

        if available_option_keys and field_key not in available_option_keys:
            continue

        seen_fields.add(field_key)
        normalized_visible_fields.append(field_key)

    if has_explicit_process_fields_config:
        return normalized_visible_fields

    return get_menu_process_default_visible_fields(clean_menu_key, clean_menu_config)
    # APPVERBO_PROCESS_FIELDS_EMPTY_DELETE_V2_END
'''

    content = replace_top_level_function_v2(
        content,
        "get_menu_process_visible_fields",
        visible_fields_function,
    )

    update_fields_function = '''
def update_sidebar_menu_process_fields(
    session: Session,
    menu_key: str,
    visible_fields: list[str],
    visible_headers: list[str] | None = None,
) -> tuple[bool, str]:
    # APPVERBO_PROCESS_FIELDS_EMPTY_DELETE_SAVE_V2_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if not clean_menu_key:
        return False, "Menu inválido."

    raw_menu_config = session.execute(
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

    if raw_menu_config is None:
        return False, "Menu não encontrado."

    if isinstance(raw_menu_config, dict):
        menu_config = dict(raw_menu_config)
    else:
        try:
            parsed_config = json.loads(raw_menu_config or "{}")
        except (TypeError, ValueError):
            parsed_config = {}

        menu_config = parsed_config if isinstance(parsed_config, dict) else {}

    field_options = get_menu_process_field_options(clean_menu_key, menu_config)
    available_field_keys = {
        str(item.get("key") or "").strip().lower()
        for item in field_options
        if str(item.get("key") or "").strip()
    }

    header_options = get_menu_process_header_options(clean_menu_key, menu_config)
    available_header_keys = {
        str(item.get("key") or "").strip().lower()
        for item in header_options
        if str(item.get("key") or "").strip()
    }

    raw_visible_headers = visible_headers if isinstance(visible_headers, list) else []

    clean_visible_fields: list[str] = []
    clean_visible_headers: list[str] = []
    seen_fields: set[str] = set()

    for row_index, raw_field_key in enumerate(visible_fields or []):
        field_key = str(raw_field_key or "").strip().lower()

        if not field_key:
            continue

        if field_key in seen_fields:
            continue

        if available_field_keys and field_key not in available_field_keys:
            continue

        seen_fields.add(field_key)
        clean_visible_fields.append(field_key)

        raw_header_key = (
            raw_visible_headers[row_index]
            if row_index < len(raw_visible_headers)
            else ""
        )
        header_key = str(raw_header_key or "").strip().lower()

        if header_key not in available_header_keys:
            header_key = ""

        clean_visible_headers.append(header_key)

    process_visible_field_header_map: dict[str, str] = {}
    process_visible_field_rows: list[dict[str, str]] = []

    for row_index, field_key in enumerate(clean_visible_fields):
        header_key = (
            clean_visible_headers[row_index]
            if row_index < len(clean_visible_headers)
            else ""
        )

        if header_key:
            process_visible_field_header_map[field_key] = header_key

        process_visible_field_rows.append(
            {
                "field_key": field_key,
                "header_key": header_key,
            }
        )

    menu_config["process_visible_fields"] = clean_visible_fields
    menu_config["process_visible_field_header_map"] = process_visible_field_header_map
    menu_config["process_visible_field_rows"] = process_visible_field_rows
    menu_config["process_visible_fields_configured"] = True

    refresh_token = str(uuid4())
    menu_config["process_visible_fields_refresh_version"] = refresh_token
    menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = refresh_token

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
    session.commit()

    return True, ""
    # APPVERBO_PROCESS_FIELDS_EMPTY_DELETE_SAVE_V2_END
'''

    content = replace_top_level_function_v2(
        content,
        "update_sidebar_menu_process_fields",
        update_fields_function,
    )

    write_text_v2(MENU_SETTINGS_PATH, content)


####################################################################################
# (4) PATCH templates/new_user.html
####################################################################################

def patch_template_v2() -> None:
    content = read_text_v2(HTML_PATH)

    content = content.replace("</script>\\n  <script", "</script>\r\n  <script")
    content = content.replace("</script>\\r\\n  <script", "</script>\r\n  <script")

    obsolete_patterns = [
        r'(?m)^[ \t]*<script src="/static/js/modules/process_fields_config_manager_v4\.js\?v=[^"]*"></script>[ \t]*\r?\n?',
        r'(?m)^[ \t]*<script src="/static/js/modules/process_fields_action_buttons_fallback_v1\.js\?v=[^"]*"></script>[ \t]*\r?\n?',
        r'(?m)^[ \t]*<script src="/static/js/modules/process_fields_config_manager_v6\.js\?v=[^"]*"></script>[ \t]*\r?\n?',
    ]

    for pattern in obsolete_patterns:
        content = re.sub(pattern, "", content)

    script_tag = '  <script src="/static/js/modules/process_fields_config_manager_v6.js?v=20260501-process-fields-config-v6-empty-delete-v2"></script>'

    block_pattern = re.compile(
        r"(?s)({%\s*block\s+scripts\s*%})(.*?)(\r?\n[ \t]*{%\s*endblock\s*%})"
    )

    if not block_pattern.search(content):
        raise RuntimeError("Bloco scripts não encontrado em new_user.html.")

    content = block_pattern.sub(
        lambda item: item.group(1) + item.group(2).rstrip() + "\r\n" + script_tag + item.group(3),
        content,
        count=1,
    )

    write_text_v2(HTML_PATH, content)


####################################################################################
# (5) VALIDAR JS V6
####################################################################################

def validate_v6_v2() -> None:
    content = read_text_v2(V6_PATH)

    required_markers = [
        "APPVERBO_PROCESS_FIELDS_V6_ACTION_BUTTONS_V2_START",
        "garantirBotoesFormulario_v6(form, elements)",
    ]

    missing_markers = [
        marker
        for marker in required_markers
        if marker not in content
    ]

    if missing_markers:
        raise RuntimeError(
            "Marcadores esperados não encontrados no process_fields_config_manager_v6.js: "
            + ", ".join(missing_markers)
        )


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    patch_menu_settings_v2()
    patch_template_v2()
    validate_v6_v2()

    print("OK: menu_settings.py ajustado para tratar lista vazia como configuração válida.")
    print("OK: update_sidebar_menu_process_fields agora grava lista vazia e marcador explicitamente.")
    print("OK: template limpo e cache bust atualizado para o gestor v6.")


if __name__ == "__main__":
    main()