from pathlib import Path

template_path = Path("templates/new_user.html")
text = template_path.read_text(encoding="utf-8")

script_tag = '  <script src="/static/js/modules/settings_system_fields_v1.js?v=20260506-meu-perfil-system-fields-v1" defer></script>'

if "settings_system_fields_v1.js" not in text:
    head_marker = "{% block head_extra %}"
    head_start = text.find(head_marker)

    if head_start < 0:
        raise RuntimeError("Bloco head_extra nao encontrado em templates/new_user.html")

    head_end = text.find("{% endblock %}", head_start)

    if head_end < 0:
        raise RuntimeError("Fim do bloco head_extra nao encontrado em templates/new_user.html")

    text = text[:head_end] + script_tag + "\n" + text[head_end:]
    template_path.write_text(text, encoding="utf-8")

print("OK: template validado/atualizado.")
