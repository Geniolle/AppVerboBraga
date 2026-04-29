from pathlib import Path

ROOT = Path.cwd()
path = ROOT / "appverbo" / "menu_settings.py"

content = path.read_text(encoding="utf-8")

target = '        if operator not in allowed_operators:\n'

insert = '''        allowed_operators = {
            "preenchido",
            "vazio",
            "igual",
            "diferente",
            "contem",
            "nao_contem",
            "maior",
            "menor",
            "maior_igual",
            "menor_igual",
        }

'''

if target not in content:
    raise RuntimeError("Não encontrei a linha: if operator not in allowed_operators:")

if insert.strip() not in content:
    content = content.replace(target, insert + target, 1)

path.write_text(content, encoding="utf-8")

print("OK: allowed_operators corrigido em appverbo/menu_settings.py")
