from pathlib import Path
import re

####################################################################################
# (1) CAMINHOS
####################################################################################

menu_settings_path = Path("appverbo/menu_settings.py")
template_path = Path("templates/new_user.html")

####################################################################################
# (2) LER FICHEIROS
####################################################################################

menu_text = menu_settings_path.read_text(encoding="utf-8")
template_text = template_path.read_text(encoding="utf-8")

####################################################################################
# (3) MANTER CAMPOS DE SISTEMA JUNTO COM CAMPOS ADICIONAIS NO MEU PERFIL
####################################################################################

old_priority = 'MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS = {"home"}'
new_priority = 'MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS = {"home", MENU_MEU_PERFIL_KEY}'

if old_priority not in menu_text and new_priority not in menu_text:
    raise RuntimeError("Linha MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS não encontrada.")

if old_priority in menu_text:
    menu_text = menu_text.replace(old_priority, new_priority, 1)

####################################################################################
# (4) GARANTIR CAMPO DE SISTEMA PAÍS NAS OPÇÕES DO MEU PERFIL
####################################################################################

if '{"key": "pais", "label": "País"}' not in menu_text:
    old_email_line = '        {"key": "email", "label": "Email"},\n        {"key": "data_nascimento", "label": "Data de nascimento"},'
    new_email_line = '        {"key": "email", "label": "Email"},\n        {"key": "pais", "label": "País"},\n        {"key": "data_nascimento", "label": "Data de nascimento"},'

    if old_email_line not in menu_text:
        raise RuntimeError("Ponto de inserção do campo País não encontrado no bloco MENU_MEU_PERFIL_KEY.")

    menu_text = menu_text.replace(old_email_line, new_email_line, 1)

####################################################################################
# (5) AJUSTAR DEFAULT DOS CAMPOS VISÍVEIS DO MEU PERFIL
####################################################################################

old_default_visible = '    MENU_MEU_PERFIL_KEY: ["nome", "telefone", "email"],'
new_default_visible = '    MENU_MEU_PERFIL_KEY: ["nome", "email", "telefone", "pais"],'

if old_default_visible in menu_text:
    menu_text = menu_text.replace(old_default_visible, new_default_visible, 1)

menu_text = re.sub(
    r'MENU_MEU_PERFIL_FIELDS_DEFAULT\s*=\s*\[\s*"nome",\s*"telefone",\s*\n\s*"pais",\s*"email"\s*\]',
    'MENU_MEU_PERFIL_FIELDS_DEFAULT = ["nome", "email", "telefone", "pais"]',
    menu_text,
)

####################################################################################
# (6) REMOVER SCRIPT ANTIGO QUE INSERIA CAMPOS NA ABA ERRADA
####################################################################################

template_text = re.sub(
    r'\s*<script\s+src="/static/js/modules/settings_system_fields_v1\.js\?v=[^"]*"\s+defer></script>\s*',
    '\n',
    template_text,
)

####################################################################################
# (7) VALIDAR E GRAVAR
####################################################################################

required_menu_markers = [
    'MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS = {"home", MENU_MEU_PERFIL_KEY}',
    '{"key": "pais", "label": "País"}',
    'MENU_MEU_PERFIL_KEY: ["nome", "email", "telefone", "pais"]',
]

for marker in required_menu_markers:
    if marker not in menu_text:
        raise RuntimeError(f"Validação falhou em menu_settings.py. Marcador ausente: {marker}")

if "settings_system_fields_v1.js" in template_text:
    raise RuntimeError("Validação falhou: script settings_system_fields_v1.js ainda está referenciado no template.")

menu_settings_path.write_text(menu_text, encoding="utf-8")
template_path.write_text(template_text, encoding="utf-8")

print("OK: código atualizado.")
