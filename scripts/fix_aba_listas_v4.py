from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import shutil
import subprocess
import sys


# ###################################################################################
# (1) CONFIGURAÇÃO
# ###################################################################################

ROOT = Path.cwd()
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"


# ###################################################################################
# (2) FUNÇÕES AUXILIARES
# ###################################################################################

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def backup_file(path: Path) -> None:
    if path.exists():
        backup_path = path.with_name(f"{path.name}.bak_fix_aba_listas_v4_{TIMESTAMP}")
        shutil.copy2(path, backup_path)
        print(f"BACKUP: {backup_path}")


def run_command(command: list[str]) -> None:
    print("EXEC:", " ".join(command))
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Comando falhou: {' '.join(command)}")


def remover_script_tag(content: str, script_name: str) -> str:
    return re.sub(
        rf'\s*<script\b[^>]*{re.escape(script_name)}[^>]*></script>\s*',
        "\n",
        content,
        flags=re.IGNORECASE,
    )


# ###################################################################################
# (3) VALIDAR PROJETO
# ###################################################################################

def validar_projeto_v4() -> None:
    if not (ROOT / "appverbo").exists():
        raise FileNotFoundError("Execute dentro da raiz do AppVerboBraga.")

    for path in [TEMPLATE_PATH, SETTINGS_HANDLERS_PATH, MENU_SETTINGS_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Não encontrado: {path}")

    print("OK: projeto validado.")


# ###################################################################################
# (4) CORRIGIR settings_handlers.py
# ###################################################################################

def corrigir_settings_handlers_v4() -> None:
    content = read_file(SETTINGS_HANDLERS_PATH)

    original = content

    content = content.replace(
        '"adicionais": "campos-adicionais",, "lista"}',
        '"adicionais": "campos-adicionais", "lista": "lista"}',
    )

    content = re.sub(
        r'("adicionais"\s*:\s*"campos-adicionais")\s*,\s*,\s*"lista"\s*\}',
        r'\1, "lista": "lista"}',
        content,
    )

    content = content.replace(
        '{"geral", "campos-config", "campos-adicionais"}',
        '{"geral", "campos-config", "campos-adicionais", "lista"}',
    )

    content = content.replace(
        '["geral", "campos-config", "campos-adicionais"]',
        '["geral", "campos-config", "campos-adicionais", "lista"]',
    )

    if content != original:
        write_file(SETTINGS_HANDLERS_PATH, content)
        print("OK: settings_handlers.py corrigido.")
    else:
        print("AVISO: settings_handlers.py não precisava de correção.")


# ###################################################################################
# (5) CORRIGIR TEMPLATE new_user.html
# ###################################################################################

def corrigir_template_v4() -> None:
    content = read_file(TEMPLATE_PATH)

    original = content

# ###################################################################################
# (5.1) REMOVER SCRIPTS ANTIGOS QUE ESTÃO A INTERFERIR
# ###################################################################################

    scripts_antigos = [
        "force_lista_tab_v1.js",
        "process_lists_v1.js",
        "process_lists_runtime_v2.js",
    ]

    for script_name in scripts_antigos:
        content = remover_script_tag(content, script_name)

# ###################################################################################
# (5.2) GARANTIR QUE SÓ FICA O RUNTIME ATUAL
# ###################################################################################

    runtime_tag = '<script src="/static/js/modules/process_lists_runtime_v3.js?v=20260428c"></script>'

    if "process_lists_runtime_v3.js" not in content:
        marker = '<script src="/static/js/new_user.js'
        marker_index = content.find(marker)

        if marker_index >= 0:
            insert_at = content.find("</script>", marker_index)
            insert_at += len("</script>")
            content = content[:insert_at] + "\n  " + runtime_tag + content[insert_at:]
        else:
            endblock_index = content.rfind("{% endblock %}")
            if endblock_index >= 0:
                content = content[:endblock_index] + "  " + runtime_tag + "\n" + content[endblock_index:]
            else:
                content = content + "\n" + runtime_tag + "\n"

# ###################################################################################
# (5.3) CORRIGIR TAGS DE ABAS
# ###################################################################################

    tab_pattern = re.compile(
        r'<(?P<tag>a|button)\b(?P<attrs>[^>]*)>(?P<body>[\s\S]*?Campos adicionais[\s\S]*?)</(?P=tag)>',
        flags=re.IGNORECASE,
    )

    matches = list(tab_pattern.finditer(content))

    if len(matches) >= 2:
        replacements: list[tuple[int, int, str]] = []

        for match in matches[1:]:
            tag_name = match.group("tag")
            attrs = match.group("attrs")

            attrs = attrs.replace("campos-adicionais", "lista")
            attrs = attrs.replace("campos_adicionais", "lista")
            attrs = attrs.replace("Campos adicionais", "Listas")
            attrs = attrs.replace("campos adicionais", "Listas")

            new_tag = f"<{tag_name}{attrs}>Listas</{tag_name}>"
            replacements.append((match.start(), match.end(), new_tag))

        for start, end, new_value in reversed(replacements):
            content = content[:start] + new_value + content[end:]

        print(f"OK: {len(matches) - 1} aba(s) duplicada(s) corrigida(s) para Listas.")

    elif len(matches) == 1 and "settings_tab=lista" not in content and 'data-settings-tab="lista"' not in content:
        match = matches[0]
        tag_name = match.group("tag")
        attrs = match.group("attrs")

        lista_attrs = attrs.replace("campos-adicionais", "lista")
        lista_attrs = lista_attrs.replace("campos_adicionais", "lista")
        lista_attrs = lista_attrs.replace("Campos adicionais", "Listas")
        lista_attrs = lista_attrs.replace("campos adicionais", "Listas")

        lista_tag = f"<{tag_name}{lista_attrs}>Listas</{tag_name}>"
        content = content[:match.end()] + "\n              " + lista_tag + content[match.end()]

        print("OK: aba Listas criada após Campos adicionais.")

    else:
        print("AVISO: não encontrei duplicação de aba Campos adicionais no template.")

# ###################################################################################
# (5.4) CORRIGIR QUALQUER TAG QUE JÁ TENHA settings_tab=lista MAS TEXTO ERRADO
# ###################################################################################

    def corrigir_tag_lista(match: re.Match[str]) -> str:
        tag = match.group(0)

        tag = re.sub(
            r">(.*?)</a>",
            ">Listas</a>",
            tag,
            flags=re.IGNORECASE | re.DOTALL,
        )

        tag = re.sub(
            r">(.*?)</button>",
            ">Listas</button>",
            tag,
            flags=re.IGNORECASE | re.DOTALL,
        )

        tag = tag.replace("Campos adicionais", "Listas")
        tag = tag.replace("campos adicionais", "Listas")

        return tag

    content = re.sub(
        r"<a\b[^>]*(?:settings_tab=lista|data-settings-tab=['\"]lista['\"])[\s\S]*?</a>",
        corrigir_tag_lista,
        content,
        flags=re.IGNORECASE,
    )

    content = re.sub(
        r"<button\b[^>]*(?:settings_tab=lista|data-settings-tab=['\"]lista['\"])[\s\S]*?</button>",
        corrigir_tag_lista,
        content,
        flags=re.IGNORECASE,
    )

# ###################################################################################
# (5.5) GRAVAR
# ###################################################################################

    if content != original:
        write_file(TEMPLATE_PATH, content)
        print("OK: templates/new_user.html corrigido.")
    else:
        print("AVISO: template não sofreu alterações.")


# ###################################################################################
# (6) DIAGNÓSTICO DAS ABAS NO TEMPLATE
# ###################################################################################

def diagnosticar_abas_v4() -> None:
    content = read_file(TEMPLATE_PATH)

    print("")
    print("DIAGNÓSTICO DAS ABAS NO TEMPLATE:")

    for termo in [
        "settings_tab=campos-adicionais",
        "settings_tab=lista",
        "force_lista_tab_v1.js",
        "process_lists_v1.js",
        "process_lists_runtime_v3.js",
        "APPVERBO_LISTA_PANEL_V3",
    ]:
        print(f"{termo}: {termo in content}")

    print("")
    print("TAGS COM CAMPOS ADICIONAIS OU LISTAS:")

    for match in re.finditer(
        r"<(?:a|button)\b[^>]*(?:Campos adicionais|Listas|settings_tab=lista|settings_tab=campos-adicionais)[\s\S]*?</(?:a|button)>",
        content,
        flags=re.IGNORECASE,
    ):
        snippet = " ".join(match.group(0).split())
        print("-", snippet[:300])


# ###################################################################################
# (7) EXECUÇÃO
# ###################################################################################

def main() -> None:
    validar_projeto_v4()

    backup_file(TEMPLATE_PATH)
    backup_file(SETTINGS_HANDLERS_PATH)
    backup_file(MENU_SETTINGS_PATH)

    corrigir_settings_handlers_v4()
    corrigir_template_v4()

    run_command([sys.executable, "-m", "py_compile", "appverbo/routes/profile/settings_handlers.py"])
    run_command([sys.executable, "-m", "py_compile", "appverbo/menu_settings.py"])

    diagnosticar_abas_v4()

    print("")
    print("OK: correção V4 aplicada.")


if __name__ == "__main__":
    main()