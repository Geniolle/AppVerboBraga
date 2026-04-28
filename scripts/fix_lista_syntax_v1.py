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

SETTINGS_HANDLERS = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
MENU_SETTINGS = ROOT / "appverbo" / "menu_settings.py"


####################################################################################
# (2) FUNÇÕES AUXILIARES
####################################################################################

def backup_file(path: Path) -> None:
    backup_path = path.with_name(f"{path.name}.bak_fix_lista_syntax_v1_{TIMESTAMP}")
    shutil.copy2(path, backup_path)
    print(f"BACKUP: {backup_path}")


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


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

    if not SETTINGS_HANDLERS.exists():
        raise FileNotFoundError("appverbo/routes/profile/settings_handlers.py não encontrado.")

    if not MENU_SETTINGS.exists():
        raise FileNotFoundError("appverbo/menu_settings.py não encontrado.")

    print("OK: projeto validado.")


####################################################################################
# (4) CORRIGIR SINTAXE DA ABA LISTA
####################################################################################

def corrigir_settings_handlers_v1() -> None:
    content = read_file(SETTINGS_HANDLERS)

    original = content

    # Corrige exatamente o erro visto no log:
    # "adicionais": "campos-adicionais",, "lista"}
    content = re.sub(
        r'("adicionais"\s*:\s*"campos-adicionais")\s*,\s*,\s*"lista"\s*\}',
        r'\1, "lista": "lista"}',
        content,
    )

    # Corrige variação com aspas simples, se existir.
    content = re.sub(
        r"('adicionais'\s*:\s*'campos-adicionais')\s*,\s*,\s*'lista'\s*\}",
        r"\1, 'lista': 'lista'}",
        content,
    )

    # Se por acaso ficou apenas "lista" perdido dentro de dicionário, normaliza.
    content = content.replace(
        '"adicionais": "campos-adicionais", "lista"}',
        '"adicionais": "campos-adicionais", "lista": "lista"}',
    )

    content = content.replace(
        "'adicionais': 'campos-adicionais', 'lista'}",
        "'adicionais': 'campos-adicionais', 'lista': 'lista'}",
    )

    if content == original:
        print("AVISO: não encontrei o padrão exato do erro. Vou mostrar as linhas 50-70 para análise.")
        lines = content.splitlines()
        for number in range(50, min(70, len(lines)) + 1):
            print(f"{number}: {lines[number - 1]}")
    else:
        write_file(SETTINGS_HANDLERS, content)
        print("OK: settings_handlers.py corrigido.")


####################################################################################
# (5) EXECUÇÃO
####################################################################################

def main() -> None:
    validar_projeto_v1()

    backup_file(SETTINGS_HANDLERS)
    backup_file(MENU_SETTINGS)

    corrigir_settings_handlers_v1()

    run_command([sys.executable, "-m", "py_compile", "appverbo/routes/profile/settings_handlers.py"])
    run_command([sys.executable, "-m", "py_compile", "appverbo/menu_settings.py"])

    print("OK: sintaxe Python validada.")


if __name__ == "__main__":
    main()