from __future__ import annotations

from pathlib import Path
import ast
import py_compile
import re
import sys


ROOT = Path.cwd()
PAGE_HANDLER = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"


####################################################################################
# (1) HELPERS
####################################################################################

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def strip_trailing_whitespace(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


def compile_or_fail(path: Path) -> None:
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        raise RuntimeError(str(exc)) from exc


def parse_or_fail(text: str) -> None:
    try:
        ast.parse(text)
    except SyntaxError as exc:
        raise RuntimeError(
            f"SyntaxError antes de gravar: linha {exc.lineno}, coluna {exc.offset}: {exc.msg}"
        ) from exc


####################################################################################
# (2) GARANTIR IMPORT DO ESTADO ISOLADO DO UTILIZADOR
####################################################################################

def ensure_utilizador_import(text: str) -> str:
    import_line = (
        "from appverbo.admin_subprocesses.utilizador.pagina "
        "import montar_estado_pagina_utilizador_v1"
    )

    text = re.sub(
        r"\nfrom appverbo\.admin_subprocesses\.utilizador\.pagina import montar_estado_pagina_utilizador_v1\n",
        "\n",
        text,
    )

    marker = "# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_END\n"

    if marker in text:
        text = text.replace(marker, marker + import_line + "\n", 1)
        print("Import do estado isolado inserido após os imports de subprocessos.")
        return text

    future_line = "from __future__ import annotations\n"

    if text.startswith(future_line):
        text = text.replace(future_line, future_line + import_line + "\n", 1)
        print("Import do estado isolado inserido após __future__.")
        return text

    text = import_line + "\n" + text
    print("Import do estado isolado inserido no topo do ficheiro.")
    return text


####################################################################################
# (3) RESTAURAR _resolve_initial_menu_target
####################################################################################

def restore_initial_menu_target(text: str) -> str:
    broken_pattern = re.compile(
        r"(?P<indent>        )admin_subprocess_state_utilizador_v1 = None\n"
        r"(?P=indent)if resolved_admin_tab == \"utilizador\":\n"
        r"(?P=indent)    admin_subprocess_state_utilizador_v1 = montar_estado_pagina_utilizador_v1\(\n"
        r"(?P=indent)        db=db,\n"
        r"(?P=indent)        request=request,\n"
        r"(?P=indent)    \)\n",
        re.MULTILINE,
    )

    replacement = (
        '        if resolved_admin_tab == "utilizador":\n'
        '            return "#create-user-card", ""\n'
    )

    text, count = broken_pattern.subn(replacement, text)

    if count:
        print("Target do subprocesso Utilizador restaurado no helper _resolve_initial_menu_target.")
        return text

    if 'if resolved_admin_tab == "utilizador":\n            return "#create-user-card", ""' in text:
        print("Target do subprocesso Utilizador já estava correto.")
        return text

    anchor = '        if resolved_admin_tab in {"menu", "contas", "definicoes"}:\n            return "#admin-account-status-card", ""\n'

    if anchor in text:
        text = text.replace(anchor, anchor + replacement, 1)
        print("Target do subprocesso Utilizador inserido por fallback.")
        return text

    raise RuntimeError("ERRO: não foi possível restaurar o target default do Utilizador.")


####################################################################################
# (4) REESCREVER BLOCO SHADOW DO UTILIZADOR
####################################################################################

def rewrite_shadow_block(text: str) -> str:
    start_marker = "    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_START"
    end_marker = "    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_END"

    start_index = text.find(start_marker)
    end_index = text.find(end_marker)

    if start_index == -1 or end_index == -1:
        raise RuntimeError("ERRO: marcadores do bloco shadow do Utilizador não encontrados.")

    if end_index <= start_index:
        raise RuntimeError("ERRO: ordem dos marcadores do bloco shadow do Utilizador está inválida.")

    end_index = text.find("\n", end_index)
    if end_index == -1:
        end_index = len(text)
    else:
        end_index += 1

    clean_block = '''    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_START
    # Estado nativo em paralelo para validar o subprocesso Utilizador sem trocar a tela legada.
    # O bloco usa sessão própria para ficar isolado da estrutura legada da página.
    admin_subprocess_shadow_state_v1 = None

    if resolved_admin_tab == "utilizador":
        utilizador_subprocess_config_v1 = get_admin_subprocess_config("utilizador")

        if utilizador_subprocess_config_v1 is not None:
            with SessionLocal() as admin_subprocess_shadow_session_v1:
                admin_subprocess_shadow_state_v1 = build_admin_subprocess_state_from_repository(
                    config=utilizador_subprocess_config_v1,
                    session=admin_subprocess_shadow_session_v1,
                    edit_key=clean_user_edit_id,
                    success=success or "",
                    error=error or "",
                    return_url="/users/new?menu=administrativo&admin_tab=utilizador",
                    context={
                        "page_state": page_state,
                        "page_state_refresh_home_url": page_state.get("refresh_home_url", "/users/new?menu=home"),
                        "current_user": current_user,
                        "selected_entity_id": selected_entity_id,
                        "allowed_entity_ids": entity_permissions["allowed_entity_ids"],
                        "can_manage_all_entities": entity_permissions["can_manage_all_entities"],
                    },
                )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_END

'''

    text = text[:start_index] + clean_block + text[end_index:]
    print("Bloco shadow do Utilizador reescrito com chamada fechada corretamente.")
    return text


####################################################################################
# (5) REMOVER BLOCOS ISOLADOS ANTIGOS E INSERIR BLOCO ISOLADO V3
####################################################################################

def remove_old_isolated_blocks(text: str) -> str:
    text, count_v1 = re.subn(
        r"\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_START[\s\S]*?\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_END\n?",
        "\n",
        text,
        flags=re.MULTILINE,
    )

    text, count_v2 = re.subn(
        r"\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_START[\s\S]*?\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_END\n?",
        "\n",
        text,
        flags=re.MULTILINE,
    )

    text, count_v3 = re.subn(
        r"\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_START[\s\S]*?\n\s*# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_END\n?",
        "\n",
        text,
        flags=re.MULTILINE,
    )

    total = count_v1 + count_v2 + count_v3

    if total:
        print(f"Blocos isolados antigos removidos: {total}")

    return text


def insert_isolated_state_v3(text: str) -> str:
    marker = "    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_END\n"

    if marker not in text:
        raise RuntimeError("ERRO: marcador final do bloco shadow do Utilizador não encontrado.")

    block = '''    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_START
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
    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_END

'''

    text = text.replace(marker, marker + "\n" + block, 1)
    print("Bloco isolado V3 do Utilizador inserido fora da chamada shadow.")
    return text


####################################################################################
# (6) GARANTIR CHAVE NO CONTEXT PRINCIPAL
####################################################################################

def ensure_context_key(text: str) -> str:
    key_line = '        "admin_subprocess_state_utilizador_v1": admin_subprocess_state_utilizador_v1,\n'

    text = text.replace(key_line, "")

    isolated_marker = "# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_END"
    context_anchor = "    context = {\n"

    start_search = text.find(isolated_marker)
    if start_search == -1:
        raise RuntimeError("ERRO: marcador isolado V3 não encontrado antes do context.")

    context_index = text.find(context_anchor, start_search)
    if context_index == -1:
        raise RuntimeError("ERRO: context principal não encontrado após o bloco isolado V3.")

    insert_at = context_index + len(context_anchor)
    text = text[:insert_at] + key_line + text[insert_at:]

    print("Chave admin_subprocess_state_utilizador_v1 adicionada ao context principal.")
    return text


####################################################################################
# (7) VALIDAÇÃO ESTRUTURAL
####################################################################################

def validate_structure(text: str) -> None:
    if "# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V1_START" in text:
        raise RuntimeError("ERRO: bloco antigo ISOLADO_V1 ainda existe.")

    if "# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V2_START" in text:
        raise RuntimeError("ERRO: bloco antigo ISOLADO_V2 ainda existe.")

    if "# APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_START" not in text:
        raise RuntimeError("ERRO: bloco novo ISOLADO_V3 não foi criado.")

    shadow_start = text.find("# APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_START")
    shadow_end = text.find("# APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_END")

    if shadow_start == -1 or shadow_end == -1:
        raise RuntimeError("ERRO: bloco shadow do Utilizador não foi encontrado.")

    shadow_segment = text[shadow_start:shadow_end]

    if "APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO" in shadow_segment:
        raise RuntimeError("ERRO: bloco isolado ainda está dentro do bloco shadow.")

    if 'if resolved_admin_tab == "utilizador":\n            return "#create-user-card", ""' not in text:
        raise RuntimeError("ERRO: _resolve_initial_menu_target não aponta para #create-user-card.")

    if '"admin_subprocess_state_utilizador_v1": admin_subprocess_state_utilizador_v1,' not in text:
        raise RuntimeError("ERRO: context não contém admin_subprocess_state_utilizador_v1.")

    if "db=db,\n                request=request," in text:
        raise RuntimeError("ERRO: chamada antiga incorreta montar_estado_pagina_utilizador_v1(db=db, request=request) ainda existe.")


####################################################################################
# (8) EXECUÇÃO
####################################################################################

def main() -> None:
    text = read_text(PAGE_HANDLER)
    text = strip_trailing_whitespace(text)

    text = ensure_utilizador_import(text)
    text = restore_initial_menu_target(text)
    text = rewrite_shadow_block(text)
    text = remove_old_isolated_blocks(text)
    text = insert_isolated_state_v3(text)
    text = ensure_context_key(text)

    validate_structure(text)
    parse_or_fail(text)

    write_text(PAGE_HANDLER, text)
    compile_or_fail(PAGE_HANDLER)

    print("OK: page_handler.py corrigido e compilado com sucesso.")


if __name__ == "__main__":
    main()
