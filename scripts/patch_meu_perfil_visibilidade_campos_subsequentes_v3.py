from __future__ import annotations

####################################################################################
# (1) IMPORTS
####################################################################################

from pathlib import Path
from datetime import datetime


####################################################################################
# (2) CAMINHOS
####################################################################################

ROOT = Path.cwd()
PAGE_SERVICE_PATH = ROOT / "appverbo" / "services" / "page.py"


####################################################################################
# (3) FUNÇÕES AUXILIARES
####################################################################################

def backup_file_v3(path: Path) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".bak_{timestamp}")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"OK: backup criado: {backup_path}")


####################################################################################
# (4) VALIDAR FICHEIRO
####################################################################################

if not PAGE_SERVICE_PATH.exists():
    raise SystemExit(f"ERRO: ficheiro não encontrado: {PAGE_SERVICE_PATH}")

backup_file_v3(PAGE_SERVICE_PATH)

content = PAGE_SERVICE_PATH.read_text(encoding="utf-8")


####################################################################################
# (5) VALIDAR SE A FUNÇÃO V2 EXISTE
####################################################################################

if "_apply_meu_perfil_subsequent_visibility_v2(" not in content:
    raise SystemExit(
        "ERRO: função V2 não encontrada em page.py. Execute primeiro o patch V2."
    )

print("OK: função V2 encontrada em page.py.")


####################################################################################
# (6) TROCAR TODAS AS REFERÊNCIAS V1 PARA V2
####################################################################################

old_call = "_apply_meu_perfil_subsequent_visibility_v1("
new_call = "_apply_meu_perfil_subsequent_visibility_v2("

count_before = content.count(old_call)

if count_before == 0:
    print("INFO: nenhuma referência V1 encontrada. Nada para substituir.")
else:
    content = content.replace(old_call, new_call)
    print(f"OK: referências V1 substituídas por V2: {count_before}")


####################################################################################
# (7) VALIDAR QUE NÃO SOBROU CHAMADA V1
####################################################################################

if old_call in content:
    raise SystemExit("ERRO: ainda existe chamada V1 em page.py.")

print("OK: nenhuma chamada V1 restante.")


####################################################################################
# (8) GRAVAR FICHEIRO
####################################################################################

PAGE_SERVICE_PATH.write_text(content, encoding="utf-8")

print("OK: patch V3 concluído.")
