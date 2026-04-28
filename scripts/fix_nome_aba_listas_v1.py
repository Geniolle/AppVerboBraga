from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import shutil
import subprocess
import sys


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

ROOT = Path.cwd()
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
ADMIN_TABS_PATH = ROOT / "appverbo" / "process_settings" / "admin_tabs.py"
RUNTIME_JS_PATH = ROOT / "static" / "js" / "modules" / "process_lists_runtime_v3.js"


####################################################################################
# (2) FUNÇÕES AUXILIARES
####################################################################################

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def backup_file(path: Path) -> None:
    if path.exists():
        backup_path = path.with_name(f"{path.name}.bak_fix_nome_aba_listas_v1_{TIMESTAMP}")
        shutil.copy2(path, backup_path)
        print(f"BACKUP: {backup_path}")


def run_command(command: list[str]) -> None:
    print("EXEC:", " ".join(command))
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Comando falhou: {' '.join(command)}")


####################################################################################
# (3) VALIDAR PROJETO
####################################################################################

def validar_projeto_v1() -> None:
    if not (ROOT / "appverbo").exists():
        raise FileNotFoundError("Execute dentro da raiz do AppVerboBraga.")

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError("templates/new_user.html não encontrado.")

    print("OK: projeto validado.")


####################################################################################
# (4) CORRIGIR LABEL DA ABA NO TEMPLATE
####################################################################################

def corrigir_template_v1() -> None:
    content = read_file(TEMPLATE_PATH)

    original = content

    def corrigir_tag(match: re.Match[str]) -> str:
        tag = match.group(0)

        if "settings_tab=lista" not in tag and 'data-settings-tab="lista"' not in tag and "data-settings-tab='lista'" not in tag:
            return tag

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

        return tag

    content = re.sub(
        r"<a\b[^>]*(?:settings_tab=lista|data-settings-tab=['\"]lista['\"])[\s\S]*?</a>",
        corrigir_tag,
        content,
        flags=re.IGNORECASE,
    )

    content = re.sub(
        r"<button\b[^>]*(?:settings_tab=lista|data-settings-tab=['\"]lista['\"])[\s\S]*?</button>",
        corrigir_tag,
        content,
        flags=re.IGNORECASE,
    )

    content = content.replace(">Lista</a>", ">Listas</a>")
    content = content.replace(">Lista</button>", ">Listas</button>")

    if content == original:
        print("AVISO: não encontrei tag da aba lista no template.")
    else:
        write_file(TEMPLATE_PATH, content)
        print("OK: template corrigido para aba Listas.")


####################################################################################
# (5) CORRIGIR admin_tabs.py, SE EXISTIR
####################################################################################

def corrigir_admin_tabs_v1() -> None:
    if not ADMIN_TABS_PATH.exists():
        print("AVISO: admin_tabs.py não existe. Ignorado.")
        return

    content = read_file(ADMIN_TABS_PATH)

    content = content.replace(
        '{"key": "lista", "label": "Lista"}',
        '{"key": "lista", "label": "Listas"}',
    )

    content = content.replace(
        "'key': 'lista', 'label': 'Lista'",
        "'key': 'lista', 'label': 'Listas'",
    )

    write_file(ADMIN_TABS_PATH, content)
    print("OK: admin_tabs.py corrigido para Listas.")


####################################################################################
# (6) CORRIGIR TEXTOS DO RUNTIME, SE EXISTIR
####################################################################################

def corrigir_runtime_js_v1() -> None:
    if not RUNTIME_JS_PATH.exists():
        print("AVISO: process_lists_runtime_v3.js não existe. Ignorado.")
        return

    content = read_file(RUNTIME_JS_PATH)

    content = content.replace(
        "Crie uma lista na aba Lista",
        "Crie uma lista na aba Listas",
    )

    write_file(RUNTIME_JS_PATH, content)
    print("OK: runtime JS corrigido.")


####################################################################################
# (7) EXECUÇÃO
####################################################################################

def main() -> None:
    validar_projeto_v1()

    backup_file(TEMPLATE_PATH)
    backup_file(ADMIN_TABS_PATH)
    backup_file(RUNTIME_JS_PATH)

    corrigir_template_v1()
    corrigir_admin_tabs_v1()
    corrigir_runtime_js_v1()

    run_command([sys.executable, "-m", "py_compile", "appverbo/routes/profile/settings_handlers.py"])
    run_command([sys.executable, "-m", "py_compile", "appverbo/menu_settings.py"])

    print("OK: nome da aba corrigido para Listas.")


if __name__ == "__main__":
    main()
    