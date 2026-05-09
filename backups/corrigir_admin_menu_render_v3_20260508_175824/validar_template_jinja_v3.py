from pathlib import Path
from jinja2 import Environment

template_text = Path("templates/new_user.html").read_text(encoding="utf-8")
Environment().parse(template_text)
print("OK: template Jinja válido.")
