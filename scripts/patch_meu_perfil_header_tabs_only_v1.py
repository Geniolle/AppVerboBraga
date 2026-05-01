from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PAGE_PY = PROJECT_ROOT / "appverbo" / "services" / "page.py"
NEW_USER_HTML = PROJECT_ROOT / "templates" / "new_user.html"
NEW_USER_JS = PROJECT_ROOT / "static" / "js" / "new_user.js"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def replace_between_v1(content: str, start: str, end: str, replacement: str) -> str:
    start_index = content.find(start)
    if start_index < 0:
        raise RuntimeError(f"Marcador inicial não encontrado: {start}")

    end_index = content.find(end, start_index)
    if end_index < 0:
        raise RuntimeError(f"Marcador final não encontrado: {end}")

    return content[:start_index] + replacement + content[end_index:]


####################################################################################
# (3) PATCH appverbo/services/page.py
####################################################################################

def patch_page_py_v1() -> None:
    content = read_text_v1(PAGE_PY)

    if "APPVERBO_MEU_PERFIL_HEADER_TABS_ONLY_V1_START" not in content:
        old_start = '    profile_personal_sections: list[dict[str, str]] = [{"key": "geral", "label": "Geral"}]'
        old_end = '    required_profile_fields = ["nome", "telefone", "email", "pais"]'

        new_block = '''    # APPVERBO_MEU_PERFIL_HEADER_TABS_ONLY_V1_START
    profile_personal_sections: list[dict[str, str]] = []
    profile_personal_field_section_map: dict[str, str] = {}
    header_section_order: list[str] = []
    header_section_seen: set[str] = set()

    profile_header_field_keys = {
        clean_key
        for clean_key, meta in profile_personal_custom_field_meta.items()
        if clean_key.startswith("custom_")
        and str((meta or {}).get("field_type") or "").strip().lower() == "header"
    }

    def append_profile_header_section_v1(raw_header_key: Any) -> None:
        clean_header_key = str(raw_header_key or "").strip().lower()

        if not clean_header_key:
            return

        if clean_header_key in header_section_seen:
            return

        if clean_header_key not in profile_header_field_keys:
            return

        section_label = profile_personal_field_labels.get(clean_header_key, "Aba")

        profile_personal_sections.append(
            {
                "key": clean_header_key,
                "label": section_label,
            }
        )
        header_section_order.append(clean_header_key)
        header_section_seen.add(clean_header_key)

    for field_key in profile_personal_visible_fields:
        clean_field_key = str(field_key or "").strip().lower()
        append_profile_header_section_v1(clean_field_key)

    for header_key in profile_personal_field_header_map.values():
        append_profile_header_section_v1(header_key)

    first_profile_header_key = header_section_order[0] if header_section_order else ""

    for field_key in profile_personal_visible_fields:
        clean_field_key = str(field_key or "").strip().lower()

        if not clean_field_key:
            continue

        field_type = str(profile_personal_field_types.get(clean_field_key) or "").strip().lower()

        if field_type == "header":
            continue

        configured_header_key = str(
            profile_personal_field_header_map.get(clean_field_key) or ""
        ).strip().lower()

        if configured_header_key in header_section_seen:
            profile_personal_field_section_map[clean_field_key] = configured_header_key
            continue

        profile_personal_field_section_map[clean_field_key] = first_profile_header_key
    # APPVERBO_MEU_PERFIL_HEADER_TABS_ONLY_V1_END


'''
        content = replace_between_v1(content, old_start, old_end, new_block + old_end)

    if "APPVERBO_MEU_PERFIL_REQUIRED_SECTION_MAP_V1_START" not in content:
        old_required_map = '''    if "pais" not in profile_personal_field_section_map:
        profile_personal_field_section_map["pais"] = profile_personal_field_section_map.get("telefone", "geral")

    if "nome" not in profile_personal_field_section_map:
        profile_personal_field_section_map["nome"] = "geral"

    if "telefone" not in profile_personal_field_section_map:
        profile_personal_field_section_map["telefone"] = profile_personal_field_section_map.get("nome", "geral")

    if "email" not in profile_personal_field_section_map:
        profile_personal_field_section_map["email"] = profile_personal_field_section_map.get("telefone", "geral")
'''

        new_required_map = '''    # APPVERBO_MEU_PERFIL_REQUIRED_SECTION_MAP_V1_START
    default_profile_header_section_v1 = header_section_order[0] if header_section_order else ""

    if "pais" not in profile_personal_field_section_map:
        profile_personal_field_section_map["pais"] = profile_personal_field_section_map.get(
            "telefone",
            default_profile_header_section_v1,
        )

    if "nome" not in profile_personal_field_section_map:
        profile_personal_field_section_map["nome"] = default_profile_header_section_v1

    if "telefone" not in profile_personal_field_section_map:
        profile_personal_field_section_map["telefone"] = profile_personal_field_section_map.get(
            "nome",
            default_profile_header_section_v1,
        )

    if "email" not in profile_personal_field_section_map:
        profile_personal_field_section_map["email"] = profile_personal_field_section_map.get(
            "telefone",
            default_profile_header_section_v1,
        )
    # APPVERBO_MEU_PERFIL_REQUIRED_SECTION_MAP_V1_END
'''

        if old_required_map not in content:
            raise RuntimeError("Bloco antigo de mapeamento obrigatório não encontrado em page.py.")

        content = content.replace(old_required_map, new_required_map, 1)

    write_text_v1(PAGE_PY, content)
    print("OK: page.py ajustado para abas do Meu perfil somente por Cabeçalho.")


####################################################################################
# (4) PATCH templates/new_user.html
####################################################################################

def patch_new_user_html_v1() -> None:
    content = read_text_v1(NEW_USER_HTML)

    content = re.sub(
        r"profile_personal_field_section_map\.get\(([^,\n]+),\s*'geral'\)",
        r"profile_personal_field_section_map.get(\1, '')",
        content,
    )

    content = re.sub(
        r'profile_personal_field_section_map\.get\(([^,\n]+),\s*"geral"\)',
        r'profile_personal_field_section_map.get(\1, "")',
        content,
    )

    write_text_v1(NEW_USER_HTML, content)
    print("OK: new_user.html ajustado para não usar fallback Geral nas abas do Meu perfil.")


####################################################################################
# (5) PATCH static/js/new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS)

    replacements = {
        'profileSection: String(section.key || "geral")': 'profileSection: String(section.key || "")',
        ': [{ label: "Dados pessoais", target: "#perfil-pessoal-card", profileSection: "geral" }]': ': []',
        'String(profilePersonalSections[0].key || "geral")': 'String(profilePersonalSections[0].key || "")',
    }

    for old_value, new_value in replacements.items():
        content = content.replace(old_value, new_value)

    content = re.sub(
        r'(\?\s*String\(profilePersonalSections\[0\]\.key \|\| ""\)\s*:\s*)"geral"',
        r'\1""',
        content,
    )

    write_text_v1(NEW_USER_JS, content)
    print("OK: new_user.js ajustado para não criar aba fallback Dados pessoais/Geral.")


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    patch_page_py_v1()
    patch_new_user_html_v1()
    patch_new_user_js_v1()
    print("OK: patch concluído.")


if __name__ == "__main__":
    main()