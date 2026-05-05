from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END -->"

TEMPLATE_MARKER_START = "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V29_START -->"
TEMPLATE_MARKER_END = "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V29_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START"
JS_MARKER_END = "// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-corrigir-v28-remover-duplicados-v29"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-corrigir-v28-remover-duplicados-v29"


def fail_v29(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v29() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) REMOVER SECTION POR ID
####################################################################################

def remove_section_by_id_v29(content: str, section_id: str) -> str:
    pattern = re.compile(
        r"<section\b[^>]*\bid=[\"']" + re.escape(section_id) + r"[\"'][^>]*>",
        re.IGNORECASE,
    )

    while True:
        match = pattern.search(content)

        if not match:
            return content

        start = match.start()
        cursor = match.end()
        depth = 1
        token_pattern = re.compile(r"</?section\b[^>]*>", re.IGNORECASE)

        for token in token_pattern.finditer(content, cursor):
            token_text = token.group(0).lower()

            if token_text.startswith("</section"):
                depth -= 1

                if depth == 0:
                    end = token.end()
                    content = content[:start] + content[end:]
                    break
            else:
                depth += 1
        else:
            fail_v29(f"não consegui encontrar fechamento da section #{section_id}")


####################################################################################
# (3) REMOVER BLOCOS POR MARCADORES
####################################################################################

def remove_marked_block_v29(content: str, start_marker: str, end_marker: str) -> str:
    while start_marker in content and end_marker in content:
        content = re.sub(
            re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
            "",
            content,
            count=1,
        )

    return content


def disable_js_block_v29(content: str, start_marker: str, end_marker: str, reason: str) -> str:
    if start_marker not in content or end_marker not in content:
        return content

    replacement = f"""{start_marker}
// Desativado pelo fluxo único server-render V29.
// Motivo: {reason}
{end_marker}"""

    return re.sub(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        replacement,
        content,
        count=1,
    )


####################################################################################
# (4) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v29(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (5) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v29()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra definitiva de Sessões sem duplicação

Na aba **Sessões**:

1. Só pode existir um conjunto de cards:
   - `admin-sidebar-sections-form-card`;
   - `admin-sidebar-sections-card`;
   - `admin-sidebar-sections-inactive-card`.
2. Os cards de Sessões só podem aparecer quando `admin_tab=sessoes`.
3. Quando `admin_tab=menu`, `admin_tab=entidade`, `admin_tab=utilizador` ou qualquer outro, os cards de Sessões devem ficar ocultos.
4. O template renderiza as listas, igual ao subprocesso Entidade.
5. JavaScript não pode recriar listas, formulários ou linhas.
6. JavaScript só pode controlar visibilidade e botão visualizar.
7. Não usar `MutationObserver`.
{AGENTS_MARKER_END}"""

agents_content = remove_marked_block_v29(
    agents_content,
    AGENTS_MARKER_START,
    AGENTS_MARKER_END,
).rstrip() + "\n\n" + agents_rule + "\n"

agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: AGENTS.md atualizado em {agents_path}")


####################################################################################
# (6) RECRIAR UM UNICO BLOCO SERVER-RENDER NO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

for start_marker, end_marker in [
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END -->"),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_END -->"),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V29_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V29_END -->"),
]:
    template_content = remove_marked_block_v29(template_content, start_marker, end_marker)

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-create-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    template_content = remove_section_by_id_v29(template_content, section_id)

template_block = """__TEMPLATE_MARKER_START__
        {% set sessoes_return_url = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card" %}
        {% set sessoes_edit = sidebar_section_edit_data if sidebar_section_edit_data else none %}
        {% set sessoes_edit_scope = sessoes_edit.get("visibility_scope_mode", "all") if sessoes_edit else "all" %}
        {% set sessoes_edit_status = "inativo" if sessoes_edit and (sessoes_edit.get("is_active") == false or sessoes_edit.get("status") == "inativo") else "ativo" %}

        <section
          id="admin-sidebar-sections-form-card"
          class="card appverbo-sessoes-card-v29 appverbo-sessoes-form-card-v29"
          data-menu-scope="administrativo"
          data-admin-tab-pane="sessoes"
        >
          {% if settings_success and admin_tab == "sessoes" %}
            <div class="alert ok">{{ settings_success }}</div>
          {% endif %}
          {% if settings_error and admin_tab == "sessoes" %}
            <div class="alert error">{{ settings_error }}</div>
          {% endif %}

          {% if sessoes_edit %}
            <h2 class="appverbo-sessoes-form-title-v29">Editar sessão</h2>

            <form method="post" action="/settings/menu/sidebar-section-save" class="appverbo-sessoes-form-v29">
              <input type="hidden" name="section_mode" value="edit">
              <input type="hidden" name="original_section_key" value="{{ sessoes_edit.get('key', '') }}">
              <input type="hidden" name="sidebar_section_return_url" value="{{ sessoes_return_url }}">

              <div class="appverbo-sessoes-grid-v29">
                <div class="field">
                  <label for="edit_sidebar_section_label_v29">Nome da sessão *</label>
                  <input
                    id="edit_sidebar_section_label_v29"
                    name="section_label"
                    required
                    maxlength="80"
                    value="{{ sessoes_edit.get('label', '') }}"
                  >
                </div>

                <div class="field">
                  <label for="edit_sidebar_section_scope_v29">Sistema *</label>
                  <select id="edit_sidebar_section_scope_v29" name="section_visibility_scope_mode">
                    <option value="all" {% if sessoes_edit_scope == "all" %}selected{% endif %}>Owner e Legado</option>
                    <option value="owner" {% if sessoes_edit_scope == "owner" %}selected{% endif %}>Owner</option>
                    <option value="legado" {% if sessoes_edit_scope == "legado" %}selected{% endif %}>Legado</option>
                  </select>
                </div>

                <div class="field">
                  <label for="edit_sidebar_section_status_v29">Estado *</label>
                  <select id="edit_sidebar_section_status_v29" name="section_status">
                    <option value="ativo" {% if sessoes_edit_status == "ativo" %}selected{% endif %}>Ativo</option>
                    <option value="inativo" {% if sessoes_edit_status == "inativo" %}selected{% endif %}>Inativo</option>
                  </select>
                </div>
              </div>

              <div class="form-action-row appverbo-sessoes-actions-v29">
                <button type="submit" class="action-btn">Guardar</button>
                <a class="action-btn-cancel appverbo-sessoes-cancel-link-v29" href="{{ sessoes_return_url }}">Cancelar</a>
              </div>
            </form>
          {% else %}
            <details id="create-sidebar-section-collapse-v29" class="entity-create-collapse appverbo-sessoes-create-collapse-v29">
              <summary>
                <span>Criar sessão</span>
              </summary>

              <div class="entity-create-body">
                <form method="post" action="/settings/menu/sidebar-section-save" class="appverbo-sessoes-form-v29">
                  <input type="hidden" name="section_mode" value="create">
                  <input type="hidden" name="original_section_key" value="">
                  <input type="hidden" name="sidebar_section_return_url" value="{{ sessoes_return_url }}">

                  <div class="appverbo-sessoes-grid-v29">
                    <div class="field">
                      <label for="create_sidebar_section_label_v29">Nome da sessão *</label>
                      <input
                        id="create_sidebar_section_label_v29"
                        name="section_label"
                        required
                        maxlength="80"
                        placeholder="Informe o nome da sessão"
                      >
                    </div>

                    <div class="field">
                      <label for="create_sidebar_section_scope_v29">Sistema *</label>
                      <select id="create_sidebar_section_scope_v29" name="section_visibility_scope_mode">
                        <option value="all" selected>Owner e Legado</option>
                        <option value="owner">Owner</option>
                        <option value="legado">Legado</option>
                      </select>
                    </div>

                    <div class="field">
                      <label for="create_sidebar_section_status_v29">Estado *</label>
                      <select id="create_sidebar_section_status_v29" name="section_status">
                        <option value="ativo" selected>Ativo</option>
                        <option value="inativo">Inativo</option>
                      </select>
                    </div>
                  </div>

                  <div class="form-action-row appverbo-sessoes-actions-v29">
                    <button type="submit" class="action-btn">Guardar</button>
                    <button
                      type="button"
                      class="action-btn-cancel"
                      onclick="const form=this.closest('form'); const details=this.closest('details'); if(form){form.reset();} if(details){details.open=false;}"
                    >Cancelar</button>
                  </div>
                </form>
              </div>
            </details>
          {% endif %}
        </section>

        <section
          id="admin-sidebar-sections-card"
          class="card appverbo-sessoes-card-v29 appverbo-sessoes-list-card-v29"
          data-menu-scope="administrativo"
          data-admin-tab-pane="sessoes"
        >
          <h2>Sessões ativas</h2>

          {% if active_sidebar_sections %}
            <div class="appverbo-sessoes-table-wrap-v29">
              <table class="appverbo-sessoes-table-v29">
                <thead>
                  <tr>
                    <th>MENU LATERAL</th>
                    <th>SISTEMA</th>
                    <th>ESTADO</th>
                    <th>AÇÕES</th>
                  </tr>
                </thead>
                <tbody>
                  {% for row in active_sidebar_sections %}
                    <tr>
                      <td>{{ row.label }}</td>
                      <td>{{ row.visibility_scope_label or "Owner e Legado" }}</td>
                      <td><span class="appverbo-sessoes-badge-v29 appverbo-sessoes-badge-ativo-v29">Ativo</span></td>
                      <td>
                        <div class="appverbo-sessoes-row-actions-v29">
                          <form method="post" action="/settings/menu/sidebar-section-move-one" class="appverbo-sessoes-inline-form-v29">
                            <input type="hidden" name="section_key" value="{{ row.key }}">
                            <input type="hidden" name="direction" value="up">
                            <input type="hidden" name="sidebar_section_return_url" value="{{ sessoes_return_url }}">
                            <button type="submit" class="appverbo-sessoes-action-btn-v29" title="Subir sessão" aria-label="Subir sessão">↑</button>
                          </form>

                          <form method="post" action="/settings/menu/sidebar-section-move-one" class="appverbo-sessoes-inline-form-v29">
                            <input type="hidden" name="section_key" value="{{ row.key }}">
                            <input type="hidden" name="direction" value="down">
                            <input type="hidden" name="sidebar_section_return_url" value="{{ sessoes_return_url }}">
                            <button type="submit" class="appverbo-sessoes-action-btn-v29" title="Descer sessão" aria-label="Descer sessão">↓</button>
                          </form>

                          <button
                            type="button"
                            class="appverbo-sessoes-action-btn-v29"
                            title="Visualizar detalhes"
                            aria-label="Visualizar detalhes"
                            data-sessao-view-v29
                            data-sessao-label="{{ row.label }}"
                            data-sessao-sistema="{{ row.visibility_scope_label or 'Owner e Legado' }}"
                            data-sessao-estado="Ativo"
                          >👁</button>

                          <a
                            class="appverbo-sessoes-action-btn-v29 appverbo-sessoes-action-link-v29"
                            title="Editar sessão"
                            aria-label="Editar sessão"
                            href="/users/new?menu=administrativo&amp;admin_tab=sessoes&amp;sidebar_sections_tab=sessoes&amp;target=admin-sidebar-sections-form-card&amp;sidebar_section_edit_key={{ row.key }}#admin-sidebar-sections-form-card"
                          >✎</a>
                        </div>
                      </td>
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          {% else %}
            <p class="empty">Sem sessões ativas.</p>
          {% endif %}
        </section>

        <section
          id="admin-sidebar-sections-inactive-card"
          class="card appverbo-sessoes-card-v29 appverbo-sessoes-inactive-card-v29"
          data-menu-scope="administrativo"
          data-admin-tab-pane="sessoes"
        >
          <h2>Sessões inativas</h2>

          {% if inactive_sidebar_sections %}
            <div class="appverbo-sessoes-table-wrap-v29">
              <table class="appverbo-sessoes-table-v29">
                <thead>
                  <tr>
                    <th>MENU LATERAL</th>
                    <th>SISTEMA</th>
                    <th>ESTADO</th>
                    <th>AÇÕES</th>
                  </tr>
                </thead>
                <tbody>
                  {% for row in inactive_sidebar_sections %}
                    <tr>
                      <td>{{ row.label }}</td>
                      <td>{{ row.visibility_scope_label or "Owner e Legado" }}</td>
                      <td><span class="appverbo-sessoes-badge-v29 appverbo-sessoes-badge-inativo-v29">Inativo</span></td>
                      <td>
                        <div class="appverbo-sessoes-row-actions-v29">
                          <button
                            type="button"
                            class="appverbo-sessoes-action-btn-v29"
                            title="Visualizar detalhes"
                            aria-label="Visualizar detalhes"
                            data-sessao-view-v29
                            data-sessao-label="{{ row.label }}"
                            data-sessao-sistema="{{ row.visibility_scope_label or 'Owner e Legado' }}"
                            data-sessao-estado="Inativo"
                          >👁</button>

                          <a
                            class="appverbo-sessoes-action-btn-v29 appverbo-sessoes-action-link-v29"
                            title="Editar sessão"
                            aria-label="Editar sessão"
                            href="/users/new?menu=administrativo&amp;admin_tab=sessoes&amp;sidebar_sections_tab=sessoes&amp;target=admin-sidebar-sections-form-card&amp;sidebar_section_edit_key={{ row.key }}#admin-sidebar-sections-form-card"
                          >✎</a>
                        </div>
                      </td>
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          {% else %}
            <p class="empty">Sem sessões inativas.</p>
          {% endif %}
        </section>
        __TEMPLATE_MARKER_END__
"""

template_block = template_block.replace("__TEMPLATE_MARKER_START__", TEMPLATE_MARKER_START)
template_block = template_block.replace("__TEMPLATE_MARKER_END__", TEMPLATE_MARKER_END)

anchor = '<section id="dynamic-process-card"'

if anchor not in template_content:
    fail_v29("não encontrei âncora dynamic-process-card no template.")

template_content = template_content.replace(anchor, template_block + "\n" + anchor, 1)

template_content = re.sub(
    r"/static/js/modules/sidebar_sections_layout_v1\.js(?:\?v=[^\"']+)?",
    JS_CACHE,
    template_content,
)

template_content = re.sub(
    r"/static/css/modules/sidebar_sections_layout_v1\.css(?:\?v=[^\"']+)?",
    CSS_CACHE,
    template_content,
)

if JS_CACHE not in template_content:
    fail_v29("não consegui atualizar cache do JS no template.")

if CSS_CACHE not in template_content:
    fail_v29("não consegui atualizar cache do CSS no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: template refeito com apenas um conjunto de cards de Sessões.")


####################################################################################
# (7) DESATIVAR JS ANTIGO E CRIAR CONTROLADOR V29
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

for start_marker, end_marker, reason in [
    ("// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START", "// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END", "renderizava card antigo."),
    ("// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START", "// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END", "controlava card antigo."),
    ("// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START", "// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END", "recriava lista antiga."),
    ("// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START", "// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END", "forçava contexto antigo."),
    ("// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START", "// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END", "renderizava cards por JS."),
    ("// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START", "// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END", "recriava cards por JS."),
    ("// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START", "// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END", "hidratava ações antigas."),
    ("// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START", "// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END", "controlador antigo de visibilidade."),
    ("// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START", "// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END", "mostrava Sessões em admin_tab incorreta."),
    ("// APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_START", "// APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_END", "versão anterior substituída pela V29."),
]:
    js_content = disable_js_block_v29(js_content, start_marker, end_marker, reason)

js_block = r'''// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoV29(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function adminTabAtualV29() {
    const url = new URL(window.location.href);
    return normalizarTextoV29(url.searchParams.get("admin_tab") || "");
  }

  function getCardsSessoesV29() {
    return Array.from(document.querySelectorAll('[data-admin-tab-pane="sessoes"]'));
  }

  //###################################################################################
  // (2) CONTROLAR VISIBILIDADE
  //###################################################################################

  function abaSessoesAtivaV29() {
    return adminTabAtualV29() === "sessoes";
  }

  function aplicarVisibilidadeV29() {
    const mostrar = abaSessoesAtivaV29();

    document.body.classList.toggle("appverbo-sessoes-tab-active-v29", mostrar);

    getCardsSessoesV29().forEach(function (card) {
      if (mostrar) {
        card.hidden = false;
        card.removeAttribute("hidden");
        card.setAttribute("aria-hidden", "false");
        card.style.display = "";
        card.style.visibility = "";
      }
      else {
        card.hidden = true;
        card.setAttribute("aria-hidden", "true");
        card.style.display = "none";
      }
    });
  }

  function agendarVisibilidadeV29() {
    window.setTimeout(aplicarVisibilidadeV29, 30);
    window.setTimeout(aplicarVisibilidadeV29, 120);
    window.setTimeout(aplicarVisibilidadeV29, 300);
  }

  //###################################################################################
  // (3) VISUALIZAR DETALHES
  //###################################################################################

  function instalarEventosV29() {
    if (window.__appverboSessoesSemDuplicadosV29 === true) {
      return;
    }

    window.__appverboSessoesSemDuplicadosV29 = true;

    document.addEventListener("click", function (event) {
      const botaoView = event.target.closest("[data-sessao-view-v29]");

      if (botaoView) {
        event.preventDefault();

        alert(
          "Nome da sessão: " + (botaoView.dataset.sessaoLabel || "") +
          "\nSistema: " + (botaoView.dataset.sessaoSistema || "") +
          "\nEstado: " + (botaoView.dataset.sessaoEstado || "")
        );

        return;
      }

      agendarVisibilidadeV29();
    }, true);

    window.addEventListener("hashchange", agendarVisibilidadeV29);
    window.addEventListener("popstate", agendarVisibilidadeV29);
    window.addEventListener("pageshow", agendarVisibilidadeV29);
  }

  //###################################################################################
  // (4) INICIAR
  //###################################################################################

  function iniciarV29() {
    instalarEventosV29();
    agendarVisibilidadeV29();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarV29);
  }
  else {
    iniciarV29();
  }
})();
// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END
'''

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    js_content = re.sub(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END),
        js_block,
        js_content,
        count=1,
    )
else:
    js_content = js_content.rstrip() + "\n\n" + js_block + "\n"

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS antigo desativado e controlador V29 aplicado.")


####################################################################################
# (8) CSS V29
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = """__CSS_MARKER_START__

[data-admin-tab-pane="sessoes"] {
  display: none !important;
}

body.appverbo-sessoes-tab-active-v29 [data-admin-tab-pane="sessoes"] {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.appverbo-sessoes-card-v29 {
  width: 100% !important;
  box-sizing: border-box !important;
}

.appverbo-sessoes-form-card-v29 {
  background: #f3f6fb !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  padding: 16px !important;
  margin-bottom: 12px !important;
  min-height: 58px !important;
}

.appverbo-sessoes-list-card-v29,
.appverbo-sessoes-inactive-card-v29 {
  background: #ffffff !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  padding: 16px !important;
  margin-bottom: 12px !important;
}

.appverbo-sessoes-form-title-v29,
.appverbo-sessoes-card-v29 h2 {
  margin: 0 0 12px !important;
  color: #12213a !important;
  font-size: 22px !important;
  font-weight: 800 !important;
}

.appverbo-sessoes-create-collapse-v29 > summary {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-width: 112px !important;
  min-height: 38px !important;
  padding: 0 16px !important;
  border-radius: 7px !important;
  background: #0f56c5 !important;
  color: #ffffff !important;
  font-weight: 800 !important;
  cursor: pointer !important;
  list-style: none !important;
}

.appverbo-sessoes-create-collapse-v29 > summary::-webkit-details-marker {
  display: none !important;
}

.appverbo-sessoes-create-collapse-v29[open] > summary {
  margin-bottom: 14px !important;
}

.appverbo-sessoes-grid-v29 {
  display: grid !important;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px) !important;
  gap: 12px !important;
  align-items: end !important;
  width: 100% !important;
}

.appverbo-sessoes-grid-v29 .field label {
  display: block !important;
  margin-bottom: 6px !important;
  color: #12213a !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
}

.appverbo-sessoes-grid-v29 .field input,
.appverbo-sessoes-grid-v29 .field select {
  width: 100% !important;
  min-height: 38px !important;
  border: 1px solid #c6d0e2 !important;
  border-radius: 7px !important;
  background: #ffffff !important;
  color: #12213a !important;
  padding: 8px 10px !important;
  box-sizing: border-box !important;
  font-size: 13px !important;
}

.appverbo-sessoes-actions-v29 {
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
  margin-top: 12px !important;
}

.appverbo-sessoes-actions-v29 .action-btn,
.appverbo-sessoes-actions-v29 .action-btn-cancel,
.appverbo-sessoes-cancel-link-v29 {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-width: 112px !important;
  width: 112px !important;
  height: 38px !important;
  min-height: 38px !important;
  box-sizing: border-box !important;
  text-decoration: none !important;
}

.appverbo-sessoes-table-wrap-v29,
.appverbo-sessoes-table-v29 {
  width: 100% !important;
}

.appverbo-sessoes-table-v29 {
  border-collapse: collapse !important;
}

.appverbo-sessoes-table-v29 th,
.appverbo-sessoes-table-v29 td {
  padding: 10px 12px !important;
  border-bottom: 1px solid #e3e8f2 !important;
  text-align: left !important;
  vertical-align: middle !important;
}

.appverbo-sessoes-table-v29 th {
  color: #12213a !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
}

.appverbo-sessoes-table-v29 th:last-child,
.appverbo-sessoes-table-v29 td:last-child {
  text-align: right !important;
}

.appverbo-sessoes-row-actions-v29 {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 6px !important;
}

.appverbo-sessoes-inline-form-v29 {
  display: inline-flex !important;
  margin: 0 !important;
  padding: 0 !important;
}

.appverbo-sessoes-action-btn-v29 {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 30px !important;
  min-width: 30px !important;
  height: 30px !important;
  min-height: 30px !important;
  padding: 0 !important;
  border: 1px solid #b9cdf5 !important;
  border-radius: 7px !important;
  background: #eef5ff !important;
  color: #174ea6 !important;
  font-size: 15px !important;
  font-weight: 800 !important;
  line-height: 1 !important;
  text-align: center !important;
  text-decoration: none !important;
  cursor: pointer !important;
}

.appverbo-sessoes-action-btn-v29:hover {
  background: #dfeaff !important;
  border-color: #7fa8f2 !important;
}

.appverbo-sessoes-badge-v29 {
  display: inline-flex !important;
  align-items: center !important;
  min-height: 24px !important;
  padding: 3px 9px !important;
  border: 1px solid transparent !important;
  border-radius: 999px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
}

.appverbo-sessoes-badge-ativo-v29 {
  border-color: #badbcc !important;
  background: #e9f7ef !important;
  color: #0f5132 !important;
}

.appverbo-sessoes-badge-inativo-v29 {
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}

@media (max-width: 1100px) {
  .appverbo-sessoes-grid-v29 {
    grid-template-columns: 1fr !important;
  }
}

__CSS_MARKER_END__"""

css_block = css_block.replace("__CSS_MARKER_START__", CSS_MARKER_START)
css_block = css_block.replace("__CSS_MARKER_END__", CSS_MARKER_END)

if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
    css_content = re.sub(
        re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
        css_block,
        css_content,
        count=1,
    )
else:
    css_content = css_content.rstrip() + "\n\n" + css_block + "\n"

CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS V29 aplicado.")


####################################################################################
# (9) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START": agents_validado,
    "APPVERBO_SESSOES_SERVER_RENDER_UNICO_V29_START": template_validado,
    "admin-sidebar-sections-form-card": template_validado,
    "admin-sidebar-sections-card": template_validado,
    "admin-sidebar-sections-inactive-card": template_validado,
    "appverbo-sessoes-card-v29": template_validado,
    "20260505-sessoes-corrigir-v28-remover-duplicados-v29": template_validado,
    "APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START": js_validado,
    "abaSessoesAtivaV29": js_validado,
    "APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START": css_validado,
    "appverbo-sessoes-tab-active-v29": css_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v29(f"validação falhou, termo ausente: {termo}")

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    count = len(re.findall(r'id=[\"\']' + re.escape(section_id) + r'[\"\']', template_validado))

    if count != 1:
        fail_v29(f"esperado exatamente 1 #{section_id}, encontrado: {count}")

for forbidden in [
    "APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START\n(function",
    "APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START\n(function",
    "APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START\n(function",
    "APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START\n(function",
    "APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_START\n(function",
]:
    if forbidden in js_validado:
        fail_v29(f"controlador antigo ainda ativo: {forbidden.splitlines()[0]}")

print("OK: patch_sessoes_corrigir_v28_e_remover_duplicados_v29 concluído.")
