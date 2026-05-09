from pathlib import Path
import re

page_path = Path("appverbo/routes/profile/page_handler.py")
text = page_path.read_text(encoding="utf-8")
original_text = text

####################################################################################
# (1) GARANTIR QUE admin_tab=menu É ACEITO PELO BACKEND
####################################################################################

pattern_admin_tab_whitelist = r'if resolved_admin_tab not in \{([^}]*)\}:'

def add_menu_to_admin_tab_whitelist(match: re.Match) -> str:
    values = match.group(1)

    if '"menu"' in values or "'menu'" in values:
        return match.group(0)

    clean_values = values.rstrip()
    if clean_values.endswith(","):
        new_values = clean_values + ' "menu",'
    else:
        new_values = clean_values + ', "menu"'

    return f"if resolved_admin_tab not in {{{new_values}}}:"

text = re.sub(
    pattern_admin_tab_whitelist,
    add_menu_to_admin_tab_whitelist,
    text,
    count=1,
)

####################################################################################
# (2) CORRIGIR TARGET INICIAL DO ADMINISTRATIVO -> MENU
####################################################################################

pattern_admin_target_block = re.compile(
    r'    if clean_menu_key == "administrativo":\n'
    r'.*?'
    r'    if clean_menu_key == "configuracao":',
    flags=re.DOTALL,
)

replacement_admin_target_block = '''    if clean_menu_key == "administrativo":
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        if resolved_admin_tab == "menu":
            return "#settings-card", ""
        if resolved_admin_tab == "sessoes":
            return "#admin-sidebar-sections-card", ""
        if resolved_admin_tab == "contas":
            return "#admin-account-status-card", ""
        if resolved_admin_tab == "utilizador":
            return "#create-user-card", ""
        return "#create-entity-card", ""
    if clean_menu_key == "configuracao":'''

text, replacements = pattern_admin_target_block.subn(
    replacement_admin_target_block,
    text,
    count=1,
)

if replacements != 1:
    raise RuntimeError("Não foi possível substituir o bloco _resolve_initial_menu_target para Administrativo.")

####################################################################################
# (3) REFORÇAR TARGET APÓS RESOLUÇÃO DE CONTEXTO
####################################################################################

marker = "# APPVERBO_ADMIN_MENU_TAB_TARGET_V1_START"

if marker not in text:
    insert_before = "    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START"

    reinforcement_block = '''
    # APPVERBO_ADMIN_MENU_TAB_TARGET_V1_START
    # A aba Administrativo -> Menu usa o bloco legado settings-card.
    # Sem esta normalização, a URL admin_tab=menu pode ficar sem conteúdo
    # porque o backend voltava para o target padrão de Entidade.
    if resolved_admin_tab == "menu":
        if clean_settings_edit_key:
            initial_menu_target = "#settings-menu-edit-card"
        else:
            initial_menu_target = "#settings-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_TAB_TARGET_V1_END

'''

    if insert_before not in text:
        raise RuntimeError("Ponto de inserção do reforço da aba Menu não encontrado.")

    text = text.replace(insert_before, reinforcement_block + insert_before, 1)

####################################################################################
# (4) VALIDAR ALTERAÇÕES
####################################################################################

required_markers = [
    'resolved_admin_tab == "menu"',
    'return "#settings-card", ""',
    "APPVERBO_ADMIN_MENU_TAB_TARGET_V1_START",
    'initial_menu_target = "#settings-card"',
]

for marker_value in required_markers:
    if marker_value not in text:
        raise RuntimeError(f"Validação falhou. Marcador ausente: {marker_value}")

if text == original_text:
    raise RuntimeError("Nenhuma alteração foi aplicada em page_handler.py.")

page_path.write_text(text, encoding="utf-8")

print("OK: page_handler.py atualizado para Administrativo -> Menu.")
