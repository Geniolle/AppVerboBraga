from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-botoes-v3"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-botoes-v3"

HELPER_MARKER_START = "// APPVERBO_SESSOES_BOTOES_V3_START"
HELPER_MARKER_END = "// APPVERBO_SESSOES_BOTOES_V3_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_BOTOES_V3_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_BOTOES_V3_END */"


def fail_v3(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail_v3(f"ficheiro não encontrado: {TEMPLATE_PATH}")

if not JS_PATH.exists():
    fail_v3(f"ficheiro não encontrado: {JS_PATH}")

if not CSS_PATH.exists():
    fail_v3(f"ficheiro não encontrado: {CSS_PATH}")


####################################################################################
# (2) ATUALIZAR TEXTO DO BOTAO GRAVAR E ADICIONAR CANCELAR
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

if 'gravar.textContent = "Gravar alterações";' in js_content:
    js_content = js_content.replace(
        'gravar.textContent = "Gravar alterações";',
        'gravar.textContent = "Gravar";',
    )
elif 'gravar.textContent = "Gravar";' not in js_content:
    fail_v3('não encontrei o texto do botão "Gravar alterações" para substituir.')

cancel_button_block = '''    const cancelar = document.createElement("button");
    cancelar.type = "button";
    cancelar.className = "action-btn-cancel appverbo-sidebar-section-cancel-btn-v3";
    cancelar.textContent = "Cancelar";
    cancelar.addEventListener("click", function () {
      window.location.assign("/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card");
    });

'''

if "appverbo-sidebar-section-cancel-btn-v3" not in js_content:
    target_gravar_block = '''    const gravar = document.createElement("button");
    gravar.type = "submit";
    gravar.className = "action-btn";
    gravar.textContent = "Gravar";

'''

    if target_gravar_block not in js_content:
        fail_v3("não encontrei o bloco do botão Gravar para inserir o botão Cancelar.")

    js_content = js_content.replace(
        target_gravar_block,
        target_gravar_block + cancel_button_block,
        1,
    )

    if '''footer.appendChild(nota);
    footer.appendChild(gravar);''' in js_content:
        js_content = js_content.replace(
            '''footer.appendChild(nota);
    footer.appendChild(gravar);''',
            '''footer.appendChild(nota);
    footer.appendChild(cancelar);
    footer.appendChild(gravar);''',
            1,
        )
    else:
        fail_v3("não encontrei footer.appendChild(gravar) para posicionar o botão Cancelar.")
else:
    print("AVISO: botão Cancelar V3 já existe no JS.")


####################################################################################
# (3) REMOVER BOTAO SUPERIOR VOLTAR A LISTA
####################################################################################

helper_block = f'''  {HELPER_MARKER_START}
  function removerBotaoVoltarListaSessoes_v3(card) {{
    if (!card) {{
      return;
    }}

    const candidatos = Array.from(card.querySelectorAll("button, a"));

    candidatos.forEach(function (elemento) {{
      const texto = normalizarTextoSessoesLayout_v2(elemento.textContent);

      if (texto === "voltar a lista" || texto === "voltar lista") {{
        elemento.remove();
      }}
    }});
  }}
  {HELPER_MARKER_END}

'''

if HELPER_MARKER_START not in js_content:
    anchor = "  //###################################################################################\n  // (6) INSTALAR LAYOUT\n  //###################################################################################\n\n"

    if anchor not in js_content:
        fail_v3("não encontrei o bloco de instalação do layout para inserir helper V3.")

    js_content = js_content.replace(anchor, helper_block + anchor, 1)
else:
    pattern = re.compile(
        re.escape(HELPER_MARKER_START) + r"[\s\S]*?" + re.escape(HELPER_MARKER_END),
        re.S,
    )
    js_content = pattern.sub(helper_block.strip(), js_content, count=1)

old_install_guard = '''    if (!card || card.dataset.sidebarSectionsLayoutV2 === "1") {
      return;
    }
'''

new_install_guard = '''    if (!card) {
      return;
    }

    removerBotaoVoltarListaSessoes_v3(card);

    if (card.dataset.sidebarSectionsLayoutV2 === "1") {
      return;
    }
'''

if old_install_guard in js_content:
    js_content = js_content.replace(old_install_guard, new_install_guard, 1)
elif "removerBotaoVoltarListaSessoes_v3(card);" not in js_content:
    fail_v3("não consegui inserir a chamada para remover o botão Voltar a lista.")


####################################################################################
# (4) ATUALIZAR CSS DO BOTAO CANCELAR
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''
{CSS_MARKER_START}

.appverbo-sidebar-section-cancel-btn-v3 {{
  border: 1px solid #c2d4f7;
  background: #eef5ff;
  color: #1d4f9f;
  border-radius: 7px;
  font-weight: 700;
  padding: 9px 14px;
  cursor: pointer;
}}

.appverbo-sidebar-section-cancel-btn-v3:hover {{
  background: #dceaff;
}}

{CSS_MARKER_END}
'''

if CSS_MARKER_START in css_content:
    css_pattern = re.compile(
        re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
        re.S,
    )
    css_content = css_pattern.sub(css_block.strip(), css_content, count=1)
else:
    css_content = css_content.rstrip() + "\n\n" + css_block.strip() + "\n"


####################################################################################
# (5) ATUALIZAR CACHE BUSTER NO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v3("não encontrei sidebar_sections_layout_v1.js no template.")

if "sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v3("não encontrei sidebar_sections_layout_v1.css no template.")


####################################################################################
# (6) GRAVAR FICHEIROS
####################################################################################

JS_PATH.write_text(js_content, encoding="utf-8")
CSS_PATH.write_text(css_content, encoding="utf-8")
TEMPLATE_PATH.write_text(template_content, encoding="utf-8")


####################################################################################
# (7) VALIDAR CONTEUDO
####################################################################################

js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    'gravar.textContent = "Gravar";': js_validado,
    "appverbo-sidebar-section-cancel-btn-v3": js_validado,
    "removerBotaoVoltarListaSessoes_v3": js_validado,
    "window.location.assign": js_validado,
    CSS_MARKER_START: css_validado,
    JS_CACHE: template_validado,
    CSS_CACHE: template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v3(f"validação falhou, termo ausente: {termo}")

if 'gravar.textContent = "Gravar alterações";' in js_validado:
    fail_v3('texto antigo "Gravar alterações" ainda existe no JS principal.')

print("OK: botão Gravar alterações alterado para Gravar.")
print("OK: botão Cancelar adicionado ao rodapé da tela Sessões.")
print("OK: botão superior Voltar a lista será removido da tela Sessões.")
print("OK: cache buster do template atualizado.")
