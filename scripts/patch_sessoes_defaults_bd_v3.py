from pathlib import Path
import ast
import json
import os
import re
import sys
import time

from sqlalchemy import text

ROOT = Path.cwd()

MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"

BACKUP_NAME = os.environ.get("APPVERBO_SESSOES_FIX_BACKUP_NAME", "corrigir_sessoes_defaults_bd_v3_manual")
BACKUP_ROOT = ROOT / "backups" / BACKUP_NAME
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

EXPECTED_SECTION_KEYS = [
    "sistema",
    "geral",
    "dados_gerais",
    "igreja",
    "tesouraria",
]

EXPECTED_SECTION_LABELS = {
    "sistema": "Sistema",
    "geral": "Geral",
    "dados_gerais": "Dados gerais",
    "igreja": "Igreja",
    "tesouraria": "Tesouraria",
}


def fail_v3(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not MENU_SETTINGS_PATH.exists():
    fail_v3(f"ficheiro não encontrado: {MENU_SETTINGS_PATH}")

if not TEMPLATE_PATH.exists():
    fail_v3(f"ficheiro não encontrado: {TEMPLATE_PATH}")


####################################################################################
# (2) CORRIGIR DEFAULTS EM appverbo/menu_settings.py
####################################################################################

menu_settings = MENU_SETTINGS_PATH.read_text(encoding="utf-8")

new_defaults_block = '''SIDEBAR_SECTION_DEFAULTS: tuple[dict[str, Any], ...] = (
    {"key": "sistema", "label": "Sistema", "visibility_scopes": ["owner", "legado"]},
    {"key": "geral", "label": "Geral", "visibility_scopes": ["owner", "legado"]},
    {"key": "dados_gerais", "label": "Dados gerais", "visibility_scopes": ["owner", "legado"]},
    {"key": "igreja", "label": "Igreja", "visibility_scopes": ["owner", "legado"]},
    {"key": "tesouraria", "label": "Tesouraria", "visibility_scopes": ["owner", "legado"]},
)
SIDEBAR_SECTION_DEFAULTS_BY_KEY'''

defaults_pattern = re.compile(
    r'SIDEBAR_SECTION_DEFAULTS: tuple\[dict\[str, Any\], \.\.\.\] = \(\n[\s\S]*?\n\)\nSIDEBAR_SECTION_DEFAULTS_BY_KEY',
    re.S,
)

if not defaults_pattern.search(menu_settings):
    fail_v3("não encontrei o bloco SIDEBAR_SECTION_DEFAULTS para substituir.")

menu_settings = defaults_pattern.sub(new_defaults_block, menu_settings)

new_resolve_function = '''def _resolve_default_sidebar_section_key(menu_key: str, section_keys: set[str], ordered_section_keys: list[str]) -> str:
    if not ordered_section_keys:
        return ""

    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    preferred_section_key = MENU_SECTION_BY_SYSTEM_MENU_KEY.get(clean_menu_key, "")

    if preferred_section_key in section_keys:
        return preferred_section_key

    if clean_menu_key in {"home", "administrativo"} and "geral" in section_keys:
        return "geral"

    if clean_menu_key not in {"home", "administrativo"} and "igreja" in section_keys:
        return "igreja"

    return ordered_section_keys[0]
'''

resolve_pattern = re.compile(
    r'def _resolve_default_sidebar_section_key\(menu_key: str, section_keys: set\[str\], ordered_section_keys: list\[str\]\) -> str:\n[\s\S]*?\n\n\nPT_PT_LABEL_REPLACEMENTS',
    re.S,
)

if not resolve_pattern.search(menu_settings):
    fail_v3("não encontrei a função _resolve_default_sidebar_section_key para substituir.")

menu_settings = resolve_pattern.sub(new_resolve_function + "\n\n\nPT_PT_LABEL_REPLACEMENTS", menu_settings)

try:
    ast.parse(menu_settings)
except SyntaxError as exc:
    fail_v3(f"menu_settings.py ficaria com erro de sintaxe: {exc}")

MENU_SETTINGS_PATH.write_text(menu_settings, encoding="utf-8")

print("OK: SIDEBAR_SECTION_DEFAULTS agora contém Sistema, Geral, Dados gerais, Igreja e Tesouraria.")
print("OK: _resolve_default_sidebar_section_key agora usa MENU_SECTION_BY_SYSTEM_MENU_KEY antes do fallback.")


####################################################################################
# (3) GARANTIR CACHE BUSTER NO TEMPLATE
####################################################################################

template = TEMPLATE_PATH.read_text(encoding="utf-8")

if "sidebar_sections_layout_v1.css" in template:
    template = re.sub(
        r'/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^"]+',
        '/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-defaults-bd-v3',
        template,
    )

if "sidebar_sections_layout_v1.js" in template:
    template = re.sub(
        r'/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^"]+',
        '/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-defaults-bd-v3',
        template,
    )

if "appverbo-sidebar-section-options-v2" not in template:
    marker_start = "<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_START -->"
    marker_end = "<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_END -->"
    json_block = f'''        {marker_start}
        <script id="appverbo-sidebar-section-options-v2" type="application/json">{{{{ sidebar_section_options|default([])|tojson }}}}</script>
        {marker_end}
'''
    anchor = '<section id="dynamic-process-card"'
    if anchor in template:
        template = template.replace(anchor, json_block + "        " + anchor, 1)
    else:
        fail_v3("não encontrei local para inserir JSON sidebar_section_options no template.")

TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: template validado com JSON/cache buster das sessões.")


####################################################################################
# (4) IMPORTAR APP E SINCRONIZAR BD
####################################################################################

sys.path.insert(0, str(ROOT))

from appverbo.core import SessionLocal
from appverbo.menu_settings import (
    MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY,
    MENU_CONFIG_SIDEBAR_SECTION_KEY,
    MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
    MENU_SECTION_BY_SYSTEM_MENU_KEY,
    MENU_SECTION_OPTIONS,
    normalize_menu_section_key,
    normalize_sidebar_sections,
)


def parse_menu_config_v3(raw_value):
    if isinstance(raw_value, dict):
        return raw_value

    try:
        parsed = json.loads(raw_value or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = {}

    return parsed if isinstance(parsed, dict) else {}


def build_expected_sections_v3():
    expected_sections = []

    for item in MENU_SECTION_OPTIONS:
        section_key = str(item.get("key") or "").strip().lower()
        section_label = str(item.get("label") or "").strip()

        if section_key not in EXPECTED_SECTION_KEYS:
            continue

        expected_sections.append(
            {
                "key": section_key,
                "label": section_label or EXPECTED_SECTION_LABELS.get(section_key, section_key),
                "visibility_scope_mode": "all",
                "visibility_scopes": ["owner", "legado"],
                "visibility_scope_label": "Owner e Legado",
            }
        )

    for section_key in EXPECTED_SECTION_KEYS:
        if any(item["key"] == section_key for item in expected_sections):
            continue

        expected_sections.append(
            {
                "key": section_key,
                "label": EXPECTED_SECTION_LABELS[section_key],
                "visibility_scope_mode": "all",
                "visibility_scopes": ["owner", "legado"],
                "visibility_scope_label": "Owner e Legado",
            }
        )

    return expected_sections


def merge_sections_v3(raw_sections):
    current_sections = normalize_sidebar_sections(raw_sections)
    expected_sections = normalize_sidebar_sections(build_expected_sections_v3())

    current_by_key = {
        str(item.get("key") or "").strip().lower(): dict(item)
        for item in current_sections
        if str(item.get("key") or "").strip()
    }

    merged_sections = []
    seen_keys = set()

    for expected in expected_sections:
        section_key = str(expected.get("key") or "").strip().lower()
        if not section_key:
            continue

        if section_key in current_by_key:
            item = dict(current_by_key[section_key])
            item["label"] = item.get("label") or expected.get("label")
            item["visibility_scopes"] = item.get("visibility_scopes") or ["owner", "legado"]
            item["visibility_scope_mode"] = item.get("visibility_scope_mode") or "all"
            item["visibility_scope_label"] = item.get("visibility_scope_label") or "Owner e Legado"
        else:
            item = dict(expected)

        merged_sections.append(item)
        seen_keys.add(section_key)

    for current in current_sections:
        section_key = str(current.get("key") or "").strip().lower()
        if not section_key or section_key in seen_keys:
            continue
        merged_sections.append(dict(current))
        seen_keys.add(section_key)

    return normalize_sidebar_sections(merged_sections)


def sync_database_v3():
    report = {
        "timestamp": int(time.time()),
        "admin_row_found": False,
        "before_sidebar_sections": [],
        "after_sidebar_sections": [],
        "menu_rows_before": [],
        "menu_rows_after": [],
        "updated_menu_rows": [],
    }

    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT menu_key, menu_label, menu_config
                FROM sidebar_menu_settings
                ORDER BY id
                """
            )
        ).mappings().all()

        admin_config = None

        for row in rows:
            menu_key = str(row.get("menu_key") or "").strip().lower()
            menu_label = str(row.get("menu_label") or "").strip()
            menu_config = parse_menu_config_v3(row.get("menu_config"))

            report["menu_rows_before"].append(
                {
                    "menu_key": menu_key,
                    "menu_label": menu_label,
                    "sidebar_section": menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY),
                }
            )

            if menu_key == "administrativo":
                report["admin_row_found"] = True
                admin_config = menu_config

        if admin_config is None:
            fail_v3("menu administrativo não encontrado no BD.")

        report["before_sidebar_sections"] = admin_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY) or []

        merged_sections = merge_sections_v3(admin_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY))
        valid_section_keys = {
            str(item.get("key") or "").strip().lower()
            for item in merged_sections
            if str(item.get("key") or "").strip()
        }

        admin_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = merged_sections
        admin_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = str(int(time.time() * 1000))

        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": "administrativo",
                "menu_config": json.dumps(admin_config, ensure_ascii=False),
            },
        )

        for row in rows:
            menu_key = str(row.get("menu_key") or "").strip().lower()
            if not menu_key:
                continue

            menu_config = parse_menu_config_v3(row.get("menu_config"))
            current_section = normalize_menu_section_key(
                menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY),
                menu_key,
            )
            preferred_section = MENU_SECTION_BY_SYSTEM_MENU_KEY.get(menu_key, current_section)

            if preferred_section not in valid_section_keys:
                preferred_section = current_section if current_section in valid_section_keys else "igreja"

            if menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY) != preferred_section:
                menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = preferred_section

                session.execute(
                    text(
                        """
                        UPDATE sidebar_menu_settings
                        SET menu_config = :menu_config
                        WHERE lower(trim(menu_key)) = :menu_key
                        """
                    ),
                    {
                        "menu_key": menu_key,
                        "menu_config": json.dumps(menu_config, ensure_ascii=False),
                    },
                )

                report["updated_menu_rows"].append(
                    {
                        "menu_key": menu_key,
                        "sidebar_section": preferred_section,
                    }
                )

        session.commit()

        rows_after = session.execute(
            text(
                """
                SELECT menu_key, menu_label, menu_config
                FROM sidebar_menu_settings
                ORDER BY id
                """
            )
        ).mappings().all()

        for row in rows_after:
            menu_key = str(row.get("menu_key") or "").strip().lower()
            menu_label = str(row.get("menu_label") or "").strip()
            menu_config = parse_menu_config_v3(row.get("menu_config"))

            report["menu_rows_after"].append(
                {
                    "menu_key": menu_key,
                    "menu_label": menu_label,
                    "sidebar_section": menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY),
                }
            )

            if menu_key == "administrativo":
                report["after_sidebar_sections"] = menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY) or []

    report_path = BACKUP_ROOT / "diagnostico_sessoes_defaults_bd_v3.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print("")
    print("===== DIAGNOSTICO BD SESSOES V3 =====")
    print(f"Relatório: {report_path}")
    print(f"Menu administrativo encontrado: {report['admin_row_found']}")
    print("Sessões antes:")
    for item in report["before_sidebar_sections"]:
        print(f" - {item.get('key')} | {item.get('label')}")
    print("Sessões depois:")
    for item in report["after_sidebar_sections"]:
        print(f" - {item.get('key')} | {item.get('label')}")
    print("Menus atualizados:")
    for item in report["updated_menu_rows"]:
        print(f" - {item.get('menu_key')} -> {item.get('sidebar_section')}")
    print("===== FIM DIAGNOSTICO BD SESSOES V3 =====")
    print("")


sync_database_v3()


####################################################################################
# (5) VALIDACAO FINAL
####################################################################################

menu_settings_validado = MENU_SETTINGS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

for expected_key in EXPECTED_SECTION_KEYS:
    if f'"key": "{expected_key}"' not in menu_settings_validado:
        fail_v3(f"default ausente em menu_settings.py: {expected_key}")

if "appverbo-sidebar-section-options-v2" not in template_validado:
    fail_v3("template não contém appverbo-sidebar-section-options-v2.")

try:
    ast.parse(menu_settings_validado)
except SyntaxError as exc:
    fail_v3(f"menu_settings.py final ficou com erro de sintaxe: {exc}")

print("OK: patch_sessoes_defaults_bd_v3 concluído.")
