from pathlib import Path
import sys

ROOT = Path.cwd()

FILES = [
    ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js",
    ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js",
    ROOT / "templates" / "new_user.html",
]


####################################################################################
# (1) UTILITARIOS
####################################################################################

def fail_v33(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v33(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v33(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


####################################################################################
# (2) REMOVER ESPACOS/LINHAS EXTRAS NO FINAL
####################################################################################

for file_path in FILES:
    if not file_path.exists():
        fail_v33(f"ficheiro não encontrado: {file_path}")

    content = read_text_v33(file_path)
    fixed = content.rstrip() + "\n"

    if fixed != content:
        write_text_v33(file_path, fixed)
        print(f"OK: EOF corrigido em {file_path}")
    else:
        print(f"OK: EOF já estava correto em {file_path}")


####################################################################################
# (3) VALIDAR CONTEUDO ESSENCIAL
####################################################################################

top_menu = read_text_v33(ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js")
sidebar = read_text_v33(ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js")
template = read_text_v33(ROOT / "templates" / "new_user.html")

if "admin_tab=sessoes&sidebar_sections_tab=sessoes" not in top_menu:
    fail_v33("URL correta de Sessões ausente em top_menu_active_v1.js")

if "APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V32" not in sidebar:
    fail_v33("guard V32 ausente em sidebar_sections_layout_v1.js")

if "APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V32" not in sidebar:
    fail_v33("guard mover V32 ausente em sidebar_sections_layout_v1.js")

if 'id="menu-tabs-card"' not in template and "id='menu-tabs-card'" not in template:
    fail_v33("menu-tabs-card ausente em templates/new_user.html")

for file_path in FILES:
    content = read_text_v33(file_path)
    if not content.endswith("\n"):
        fail_v33(f"ficheiro sem newline final: {file_path}")
    if content.endswith("\n\n"):
        fail_v33(f"ficheiro com linha em branco extra no EOF: {file_path}")

print("OK: validações V33 concluídas.")
