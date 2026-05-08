from pathlib import Path
import re

template_path = Path("templates/new_user.html")
text = template_path.read_text(encoding="utf-8")

script_tag = '  <script src="/static/js/modules/profile_field_order.js?v=20260508-profile-field-order-v3" defer></script>'

text = re.sub(
    r'\s*<script\s+src="/static/js/modules/profile_field_order\.js\?v=[^"]*"\s+defer></script>\s*',
    '\n',
    text,
)

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

print("OK: profile_field_order.js incluído no template.")
