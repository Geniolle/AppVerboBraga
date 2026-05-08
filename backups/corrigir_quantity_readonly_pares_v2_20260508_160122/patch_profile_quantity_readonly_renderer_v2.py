from pathlib import Path
import re

template_path = Path("templates/new_user.html")
text = template_path.read_text(encoding="utf-8")

script_tag = '  <script src="/static/js/modules/profile_quantity_readonly_renderer_v2.js?v=20260508-quantity-readonly-renderer-v2" defer></script>'

# Remove scripts antigos/duplicados relacionados ao readonly de quantidade.
patterns = [
    r'\s*<script\s+src="/static/js/modules/profile_quantity_readonly_layout_v1\.js\?v=[^"]*"\s+defer></script>\s*',
    r'\s*<script\s+src="/static/js/modules/profile_quantity_readonly_renderer_v2\.js\?v=[^"]*"\s+defer></script>\s*',
]

for pattern in patterns:
    text = re.sub(pattern, "\n", text)

# Remove scripts/links que tenham sido inseridos por engano dentro do title.
title_pattern = re.compile(
    r'(\{% block title %\})(.*?)(\{% endblock %\})',
    flags=re.DOTALL,
)

match = title_pattern.search(text)

if match:
    title_content = match.group(2)
    title_content = re.sub(r'<script\b[^>]*></script>', '', title_content, flags=re.IGNORECASE)
    title_content = re.sub(r'<link\b[^>]*>', '', title_content, flags=re.IGNORECASE)
    text = text[:match.start()] + match.group(1) + title_content.strip() + match.group(3) + text[match.end():]

head_marker = "{% block head_extra %}"
head_start = text.find(head_marker)

if head_start >= 0:
    head_end = text.find("{% endblock %}", head_start)

    if head_end < 0:
        raise RuntimeError("Fim do bloco head_extra não encontrado em templates/new_user.html")

    text = text[:head_end] + script_tag + "\n" + text[head_end:]
elif "</head>" in text:
    text = text.replace("</head>", script_tag + "\n</head>", 1)
else:
    raise RuntimeError("Não foi possível localizar head_extra nem </head> em templates/new_user.html")

template_path.write_text(text, encoding="utf-8")

print("OK: template atualizado.")
