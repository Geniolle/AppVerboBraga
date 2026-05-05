from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
NEW_USER_CSS_PATH = ROOT / "static" / "css" / "new_user.css"
UI_STANDARDS_CSS_PATH = ROOT / "static" / "css" / "ui-standards.css"
SESSOES_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

AGENTS_MARKER_START = "<!-- APPVERBO_SAVE_CANCEL_BUTTON_RULE_V1_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SAVE_CANCEL_BUTTON_RULE_V1_END -->"

CSS_MARKER_START = "/* APPVERBO_SAVE_CANCEL_BUTTON_STANDARD_V1_START */"
CSS_MARKER_END = "/* APPVERBO_SAVE_CANCEL_BUTTON_STANDARD_V1_END */"

NEW_USER_CSS_CACHE = "/static/css/new_user.css?v=20260505-save-cancel-standard-v1"
SESSOES_CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-save-cancel-standard-v1"
SESSOES_JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-save-cancel-standard-v1"


def fail_v1(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v1() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text(
        "# AGENTS.md\n\n",
        encoding="utf-8",
    )
    return AGENTS_UPPER_PATH


####################################################################################
# (2) ATUALIZAR REGRA NO AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v1()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule_block = f"""{AGENTS_MARKER_START}
## Regra geral para botões Guardar e Cancelar

Sempre que existir um par de botões **Guardar** e **Cancelar** no projeto AppVerboBraga:

1. Os botões devem ficar sempre no lado esquerdo da tela ou do bloco/formulário.
2. Os dois botões devem ter a mesma largura, altura, padding e alinhamento vertical.
3. A ordem visual deve ser sempre: **Guardar** primeiro e **Cancelar** depois.
4. O texto do botão principal deve ser **Guardar**.
5. O texto do botão secundário deve ser **Cancelar**.
6. Não usar textos alternativos como "Gravar alterações", "Salvar", "Voltar" ou "Fechar" para esse par padrão, exceto quando existir regra funcional específica documentada.
7. Em formulários administrativos, rodapés de tabelas, subprocessos e telas dinâmicas, usar as classes globais existentes `action-btn` e `action-btn-cancel` sempre que possível.
8. Não posicionar Guardar/Cancelar no lado direito da tela, salvo exceção explícita aprovada.
{AGENTS_MARKER_END}"""

if AGENTS_MARKER_START in agents_content and AGENTS_MARKER_END in agents_content:
    agents_pattern = re.compile(
        re.escape(AGENTS_MARKER_START) + r"[\s\S]*?" + re.escape(AGENTS_MARKER_END),
        re.S,
    )
    agents_content = agents_pattern.sub(agents_rule_block, agents_content, count=1)
else:
    agents_content = agents_content.rstrip() + "\n\n" + agents_rule_block + "\n"

agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: regra Guardar/Cancelar atualizada em {agents_path}")


####################################################################################
# (3) CRIAR CSS GLOBAL DO PADRAO GUARDAR/CANCELAR
####################################################################################

css_standard_block = f"""{CSS_MARKER_START}

:root {{
  --appverbo-save-cancel-button-width-v1: 112px;
  --appverbo-save-cancel-button-height-v1: 38px;
}}

.action-btn,
.action-btn-cancel,
button.action-btn,
button.action-btn-cancel,
input.action-btn,
input.action-btn-cancel,
.profile-edit-actions > button[type="submit"],
.profile-edit-actions > .profile-cancel-btn,
.form-action-row > button[type="submit"],
.form-action-row > .action-btn,
.form-action-row > .action-btn-cancel,
.appverbo-sidebar-sections-footer-v2 > .action-btn,
.appverbo-sidebar-sections-footer-v2 > .action-btn-cancel {{
  min-width: var(--appverbo-save-cancel-button-width-v1) !important;
  width: var(--appverbo-save-cancel-button-width-v1) !important;
  height: var(--appverbo-save-cancel-button-height-v1) !important;
  min-height: var(--appverbo-save-cancel-button-height-v1) !important;
  padding: 0 14px !important;
  box-sizing: border-box !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  line-height: 1 !important;
  white-space: nowrap !important;
  text-align: center !important;
  font-weight: 700 !important;
}}

.profile-edit-actions,
.form-action-row,
.entity-form-actions,
.appverbo-sidebar-sections-footer-v2 {{
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
}}

.appverbo-sidebar-sections-footer-v2 .appverbo-sidebar-section-change-note-v2 {{
  order: 3 !important;
  margin-left: 10px !important;
}}

.appverbo-sidebar-sections-footer-v2 > .action-btn {{
  order: 1 !important;
}}

.appverbo-sidebar-sections-footer-v2 > .action-btn-cancel {{
  order: 2 !important;
}}

{CSS_MARKER_END}"""


def upsert_css_block_v1(css_path: Path) -> None:
    if not css_path.exists():
        print(f"AVISO: CSS não encontrado, ignorado: {css_path}")
        return

    css_content = css_path.read_text(encoding="utf-8")

    if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
        css_pattern = re.compile(
            re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
            re.S,
        )
        css_content = css_pattern.sub(css_standard_block, css_content, count=1)
    else:
        css_content = css_content.rstrip() + "\n\n" + css_standard_block + "\n"

    css_path.write_text(css_content, encoding="utf-8")
    print(f"OK: padrão CSS Guardar/Cancelar aplicado em {css_path}")


upsert_css_block_v1(NEW_USER_CSS_PATH)
upsert_css_block_v1(UI_STANDARDS_CSS_PATH)


####################################################################################
# (4) AJUSTAR BOTÕES DA TELA SESSÕES
####################################################################################

if SESSOES_JS_PATH.exists():
    sessoes_js = SESSOES_JS_PATH.read_text(encoding="utf-8")

    sessoes_js = sessoes_js.replace(
        'gravar.textContent = "Gravar alterações";',
        'gravar.textContent = "Guardar";',
    )

    sessoes_js = sessoes_js.replace(
        'gravar.textContent = "Gravar";',
        'gravar.textContent = "Guardar";',
    )

    sessoes_js = sessoes_js.replace(
        'cancelar.textContent = "Cancelar";',
        'cancelar.textContent = "Cancelar";',
    )

    old_footer_patterns = [
        '''footer.appendChild(nota);
    footer.appendChild(cancelar);
    footer.appendChild(gravar);''',
        '''footer.appendChild(nota);
    footer.appendChild(gravar);
    footer.appendChild(cancelar);''',
        '''footer.appendChild(nota);
    footer.appendChild(gravar);''',
    ]

    new_footer_block = '''footer.appendChild(gravar);
    if (typeof cancelar !== "undefined" && cancelar) {
      footer.appendChild(cancelar);
    }
    footer.appendChild(nota);'''

    replaced_footer = False

    for old_footer_pattern in old_footer_patterns:
        if old_footer_pattern in sessoes_js:
            sessoes_js = sessoes_js.replace(old_footer_pattern, new_footer_block, 1)
            replaced_footer = True
            break

    if not replaced_footer and "footer.appendChild(gravar);" not in sessoes_js:
        fail_v1("não encontrei footer da tela Sessões para ordenar Guardar/Cancelar.")

    if "const cancelar = document.createElement" not in sessoes_js:
        target_gravar_block = '''    const gravar = document.createElement("button");
    gravar.type = "submit";
    gravar.className = "action-btn";
    gravar.textContent = "Guardar";

'''

        cancel_button_block = '''    const cancelar = document.createElement("button");
    cancelar.type = "button";
    cancelar.className = "action-btn-cancel appverbo-sidebar-section-cancel-btn-v3";
    cancelar.textContent = "Cancelar";
    cancelar.addEventListener("click", function () {
      window.location.assign("/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card");
    });

'''

        if target_gravar_block not in sessoes_js:
            fail_v1("não encontrei bloco do botão Guardar para adicionar Cancelar na tela Sessões.")

        sessoes_js = sessoes_js.replace(
            target_gravar_block,
            target_gravar_block + cancel_button_block,
            1,
        )

    if 'gravar.textContent = "Guardar";' not in sessoes_js:
        fail_v1("botão Guardar não ficou com texto Guardar na tela Sessões.")

    if 'cancelar.textContent = "Cancelar";' not in sessoes_js:
        fail_v1("botão Cancelar não foi encontrado na tela Sessões.")

    SESSOES_JS_PATH.write_text(sessoes_js, encoding="utf-8")
    print("OK: tela Sessões ajustada para Guardar/Cancelar à esquerda.")
else:
    print(f"AVISO: JS de Sessões não encontrado: {SESSOES_JS_PATH}")


####################################################################################
# (5) ATUALIZAR CACHE BUSTER NO TEMPLATE
####################################################################################

if TEMPLATE_PATH.exists():
    template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

    if "static/css/new_user.css" in template_content:
        template_content = re.sub(
            r"/static/css/new_user\.css\?v=[^\"]+",
            NEW_USER_CSS_CACHE,
            template_content,
        )

    if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
        template_content = re.sub(
            r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
            SESSOES_CSS_CACHE,
            template_content,
        )

    if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
        template_content = re.sub(
            r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
            SESSOES_JS_CACHE,
            template_content,
        )

    TEMPLATE_PATH.write_text(template_content, encoding="utf-8")
    print("OK: cache buster atualizado em templates/new_user.html")
else:
    fail_v1(f"template não encontrado: {TEMPLATE_PATH}")


####################################################################################
# (6) VALIDAR CONTEUDO FINAL
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

if AGENTS_MARKER_START not in agents_validado:
    fail_v1("marcador da regra Guardar/Cancelar não foi encontrado no AGENTS.md.")

if "Sempre que existir um par de botões **Guardar** e **Cancelar**" not in agents_validado:
    fail_v1("regra Guardar/Cancelar não foi gravada corretamente no AGENTS.md.")

if NEW_USER_CSS_PATH.exists():
    new_user_css_validado = NEW_USER_CSS_PATH.read_text(encoding="utf-8")
    if CSS_MARKER_START not in new_user_css_validado:
        fail_v1("CSS padrão Guardar/Cancelar não foi aplicado em static/css/new_user.css.")

if SESSOES_JS_PATH.exists():
    sessoes_js_validado = SESSOES_JS_PATH.read_text(encoding="utf-8")
    if 'gravar.textContent = "Guardar";' not in sessoes_js_validado:
        fail_v1("texto Guardar não foi aplicado no JS de Sessões.")
    if "action-btn-cancel" not in sessoes_js_validado:
        fail_v1("botão Cancelar não foi validado no JS de Sessões.")

if "save-cancel-standard-v1" not in template_validado:
    print("AVISO: cache buster save-cancel-standard-v1 não apareceu no template. Pode estar usando cache global por outro ficheiro.")

print("OK: patch_padronizar_botoes_guardar_cancelar_v1 concluído.")
