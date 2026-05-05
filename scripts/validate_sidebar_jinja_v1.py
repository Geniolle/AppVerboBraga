from pathlib import Path
import sys

try:
    from jinja2 import Environment
except Exception as exc:
    print(f"AVISO: jinja2 não disponível para validação sintática: {exc}")
    sys.exit(0)

template_path = Path("templates/partials/new_user_sidebar.html")

content = template_path.read_text(encoding="utf-8")

try:
    Environment().parse(content)
except Exception as exc:
    print(f"ERRO: template Jinja inválido: {exc}")
    sys.exit(1)

print("OK: template Jinja válido.")
