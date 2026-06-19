from __future__ import annotations

from pathlib import Path
import py_compile
import re
import sys


ROOT = Path.cwd()
PAGE_HANDLER = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"


####################################################################################
# (1) HELPERS
####################################################################################

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def strip_trailing_whitespace(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


def compile_or_fail(path: Path) -> None:
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        raise RuntimeError(str(exc)) from exc


####################################################################################
# (2) REMOVER BLOCO ISOLADO COLOCADO NO LOCAL ERRADO
####################################################################################

def remove_bad_utilizador_state_blocks(text: str) -> tuple[str, bool]:
    pattern = re.compile(
        r"\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_START"
        r"[\s\S]*?"
        r"\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_END",
        re.MULTILINE,
    )

    new_text, count = pattern.subn("", text)

    if count:
        print(f"Blocos ISOLADO_V1 removidos do local incorreto: {count}")

    return new_text, bool(count)


####################################################################################
# (3) RESTAURAR _resolve_initial_menu_target
####################################################################################

def restore_initial_menu_target(text: str) -> tuple[str, bool]:
    pattern = re.compile(
        r"(?P<indent>\s*)admin_subprocess_state_utilizador_v1 = None\n"
        r"(?P=indent)if resolved_admin_tab == \"utilizador\":\n"
        r"(?P=indent)    admin_subprocess_state_utilizador_v1 = montar_estado_pagina_utilizador_v1\(\n"
        r"(?P=indent)        db=db,\n"
        r"(?P=indent)        request=request,\n"
        r"(?P=indent)    \)\n",
        re.MULTILINE,
    )

    def replacement(match: re.Match[str]) -> str:
        indent = match.group("indent")
        return (
            f'{indent}if resolved_admin_tab == "utilizador":\n'
            f'{indent}    return "#create-user-card", ""\n'
        )

    text, count = pattern.subn(replacement, text)

    if count:
        print("Helper _resolve_initial_menu_target restaurado.")

    if 'if resolved_admin_tab == "utilizador":\n            return "#create-user-card", ""' not in text:
        alt_pattern = re.compile(
            r"(?P<indent>\s*)if resolved_admin_tab == \"utilizador\":\n"
            r"(?P=indent)    admin_subprocess_state_utilizador_v1 = montar_estado_pagina_utilizador_v1\([\s\S]*?\n"
            r"(?P=indent)return \"#create-entity-card\", \"\"",
            re.MULTILINE,
        )

        def alt_replacement(match: re.Match[str]) -> str:
            indent = match.group("indent")
            return (
                f'{indent}if resolved_admin_tab == "utilizador":\n'
                f'{indent}    return "#create-user-card", ""\n'
                f'{indent}return "#create-entity-card", ""'
            )

        text, alt_count = alt_pattern.subn(alt_replacement, text, count=1)

        if alt_count:
            print("Helper _resolve_initial_menu_target restaurado por fallback.")
            count += alt_count

    return text, bool(count)


####################################################################################
# (4) GARANTIR IMPORT ISOLADO
####################################################################################

def ensure_import(text: str) -> tuple[str, bool]:
    import_line = (
        "from appverbo.admin_subprocesses.utilizador.pagina "
        "import montar_estado_pagina_utilizador_v1"
    )

    if import_line in text:
        return text, False

    lines = text.splitlines()
    insert_index = 0

    if lines and lines[0].strip() == "from __future__ import annotations":
        insert_index = 1
    else:
        for index, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_index = index + 1

    lines.insert(insert_index, import_line)

    print("Import montar_estado_pagina_utilizador_v1 adicionado.")
    return "\n".join(lines) + "\n", True


####################################################################################
# (5) INSERIR ESTADO ISOLADO DO UTILIZADOR NO LOCAL CERTO
####################################################################################

def ensure_isolated_state_block(text: str) -> tuple[str, bool]:
    marker_start = "# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_START"
    marker_end = "# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_END"

    if marker_start in text and marker_end in text:
        print("Bloco isolado V2 já existe.")
        return text, False

    text = re.sub(
        r"\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_START[\s\S]*?\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_END",
        "",
        text,
    )

    anchor = "    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_END\n"

    if anchor not in text:
        raise RuntimeError("ERRO: marcador final do bloco shadow do Utilizador não encontrado.")

    block = """    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_START
    admin_subprocess_state_utilizador_v1 = None

    if resolved_admin_tab == "utilizador":
        with SessionLocal() as utilizador_subprocess_session_v1:
            admin_subprocess_state_utilizador_v1 = montar_estado_pagina_utilizador_v1(
                session=utilizador_subprocess_session_v1,
                user_edit_id=clean_user_edit_id,
                user_view=user_view,
                selected_entity_id=selected_entity_id,
                allowed_entity_ids=entity_permissions["allowed_entity_ids"],
                success=success or "",
                error=error or "",
            )
    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_END

"""

    text = text.replace(anchor, anchor + "\n" + block, 1)
    print("Bloco isolado V2 inserido após o shadow state.")
    return text, True


####################################################################################
# (6) GARANTIR CONTEXT DO TEMPLATE
####################################################################################

def ensure_context_key(text: str) -> tuple[str, bool]:
    key_line = '"admin_subprocess_state_utilizador_v1": admin_subprocess_state_utilizador_v1,'

    if key_line in text:
        return text, False

    anchor_candidates = [
        '"admin_subprocess_shadow_state_v1": admin_subprocess_shadow_state_v1,',
        '"admin_subprocess_state_sessoes_v2": admin_subprocess_state_sessoes_v2,',
        '"admin_subprocess_state_menu_v1": admin_subprocess_state_menu_v1,',
    ]

    for anchor in anchor_candidates:
        if anchor in text:
            text = text.replace(anchor, anchor + "\n        " + key_line, 1)
            print("Chave admin_subprocess_state_utilizador_v1 adicionada ao context.")
            return text, True

    context_anchor = "    context = {\n"

    if context_anchor not in text:
        raise RuntimeError("ERRO: context principal não encontrado.")

    text = text.replace(context_anchor, context_anchor + "        " + key_line + "\n", 1)
    print("Chave admin_subprocess_state_utilizador_v1 adicionada no início do context.")
    return text, True


####################################################################################
# (7) VALIDAR LOCALIZAÇÃO DO BLOCO
####################################################################################

def validate_structure(text: str) -> None:
    bad_pattern = re.compile(
        r"build_admin_subprocess_state_from_repository\([\s\S]{0,2500}"
        r"APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO",
        re.MULTILINE,
    )

    if bad_pattern.search(text):
        raise RuntimeError(
            "ERRO: ainda existe bloco isolado dentro da chamada build_admin_subprocess_state_from_repository."
        )

    if "# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_START" in text:
        raise RuntimeError("ERRO: marcador ISOLADO_V1 antigo ainda existe.")

    if "# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_START" not in text:
        raise RuntimeError("ERRO: marcador ISOLADO_V2 não foi criado.")

    if 'if resolved_admin_tab == "utilizador":\n            return "#create-user-card", ""' not in text:
        raise RuntimeError("ERRO: _resolve_initial_menu_target não foi restaurado corretamente.")

    if '"admin_subprocess_state_utilizador_v1": admin_subprocess_state_utilizador_v1,' not in text:
        raise RuntimeError("ERRO: context não recebeu admin_subprocess_state_utilizador_v1.")


####################################################################################
# (8) EXECUÇÃO
####################################################################################

def main() -> None:
    original = read_text(PAGE_HANDLER)
    text = strip_trailing_whitespace(original)

    text, _ = remove_bad_utilizador_state_blocks(text)
    text, _ = restore_initial_menu_target(text)
    text, _ = ensure_import(text)
    text, _ = ensure_isolated_state_block(text)
    text, _ = ensure_context_key(text)

    validate_structure(text)

    write_text(PAGE_HANDLER, text)

    compile_or_fail(PAGE_HANDLER)

    print("OK: page_handler.py corrigido e compilado com sucesso.")


if __name__ == "__main__":
    main()
