from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
PAGE_HANDLER_PATH = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END -->"

TEMPLATE_MARKER_START = "<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START -->"
TEMPLATE_MARKER_END = "<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START"
JS_MARKER_END = "// APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-fluxo-nativo-igual-entidade-v30"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-fluxo-nativo-igual-entidade-v30"


def fail_v30(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v30() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) REMOVER BLOCOS MARCADOS
####################################################################################

def remove_marked_block_v30(content: str, start_marker: str, end_marker: str) -> str:
    while start_marker in content and end_marker in content:
        content = re.sub(
            re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
            "",
            content,
            count=1,
        )

    return content


####################################################################################
# (3) REMOVER SECTION POR ID
####################################################################################

def remove_section_by_id_v30(content: str, section_id: str) -> str:
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
            fail_v30(f"não consegui encontrar fechamento da section #{section_id}")


####################################################################################
# (4) DESATIVAR BLOCO JS
####################################################################################

def disable_js_block_v30(content: str, start_marker: str, end_marker: str, reason: str) -> str:
    if start_marker not in content or end_marker not in content:
        return content

    replacement = f"""{start_marker}
// Desativado pelo fluxo nativo V30.
// Motivo: {reason}
{end_marker}"""

    return re.sub(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        replacement,
        content,
        count=1,
    )


####################################################################################
# (5) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, PAGE_HANDLER_PATH, SETTINGS_HANDLERS_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v30(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (6) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v30()
agents_content = agents_path.read_text(encoding="utf-8")

for start_marker, end_marker in [
    ("<!-- APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_START -->", "<!-- APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_END -->"),
    ("<!-- APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START -->", "<!-- APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END -->"),
    (AGENTS_MARKER_START, AGENTS_MARKER_END),
]:
    agents_content = remove_marked_block_v30(agents_content, start_marker, end_marker)

agents_rule = f"""{AGENTS_MARKER_START}
## Regra definitiva: Sessões no fluxo nativo igual ao subprocesso Entidade

A aba **Sessões** deve seguir o mesmo padrão de renderização da aba **Entidade**.

Regras obrigatórias:

1. O template só deve renderizar os cards de Sessões quando `admin_tab == "sessoes"`.
2. Não usar `data-admin-tab-pane="sessoes"` como mecanismo paralelo de visibilidade.
3. Não usar JavaScript para forçar aparecer/desaparecer o card **Criar sessão**.
4. O card **Criar sessão** deve existir no HTML apenas quando a aba Sessões for carregada pelo backend.
5. Ao navegar para Entidade/Menu/Utilizador, os cards de Sessões não devem existir no HTML da resposta.
6. Ao voltar para Sessões, o backend deve renderizar novamente:
   - `admin-sidebar-sections-form-card`;
   - `admin-sidebar-sections-card`;
   - `admin-sidebar-sections-inactive-card`.
7. O JavaScript de Sessões só pode tratar ação auxiliar de visualizar detalhes.
8. As listas de sessões ativas e inativas devem ser renderizadas pelo template com dados do backend.
9. A ação **Editar** deve navegar com `sidebar_section_edit_key`, igual ao fluxo da Entidade com `entity_edit_id`.
10. Não usar `MutationObserver` no subprocesso Sessões.
{AGENTS_MARKER_END}"""

agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"
agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: AGENTS.md atualizado em {agents_path}")


####################################################################################
# (7) GARANTIR PAGE_HANDLER COM SESSOES NO FLUXO NATIVO
####################################################################################

page_content = PAGE_HANDLER_PATH.read_text(encoding="utf-8-sig")

if 'resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes"}' not in page_content:
    page_content = page_content.replace(
        'resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes"}',
        'resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes"}',
        1,
    )

if "sidebar_section_edit_data" not in page_content:
    fail_v30("page_handler.py ainda não entrega sidebar_section_edit_data. É necessário manter o split backend já criado.")

if "active_sidebar_sections" not in page_content:
    fail_v30("page_handler.py ainda não entrega active_sidebar_sections. É necessário manter o split backend já criado.")

if "inactive_sidebar_sections" not in page_content:
    fail_v30("page_handler.py ainda não entrega inactive_sidebar_sections. É necessário manter o split backend já criado.")

if 'if resolved_admin_tab == "sessoes":' not in page_content:
    anchor = '''    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query
'''
    insert = '''    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query

    if resolved_admin_tab == "sessoes":
        if str(sidebar_section_edit_key or "").strip():
            initial_menu_target = "#admin-sidebar-sections-form-card"
        else:
            initial_menu_target = "#admin-sidebar-sections-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
'''
    if anchor in page_content:
        page_content = page_content.replace(anchor, insert, 1)

if 'if resolved_admin_tab == "sessoes":' in page_content and "#admin-sidebar-sections-form-card" not in page_content:
    page_content = page_content.replace(
        'initial_menu_target = "#admin-sidebar-sections-card"',
        'initial_menu_target = "#admin-sidebar-sections-form-card" if str(sidebar_section_edit_key or "").strip() else "#admin-sidebar-sections-card"',
        1,
    )

try:
    ast.parse(page_content)
except SyntaxError as exc:
    fail_v30(f"page_handler.py ficaria inválido: {exc}")

PAGE_HANDLER_PATH.write_text(page_content, encoding="utf-8")

print("OK: page_handler.py validado para fluxo nativo de Sessões.")


####################################################################################
# (8) RECRIAR BLOCO NATIVO NO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

for start_marker, end_marker in [
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END -->"),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_END -->"),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V29_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V29_END -->"),
    (TEMPLATE_MARKER_START, TEMPLATE_MARKER_END),
]:
    template_content = remove_marked_block_v30(template_content, start_marker, end_marker)

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-create-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    template_content = remove_section_by_id_v30(template_content, section_id)

template_block = """__TEMPLATE_MARKER_START__
        {% if admin_tab == "sessoes" %}
          {% set sessoes_return_url = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card" %}
          {% set sessoes_edit = sidebar_section_edit_data if sidebar_section_edit_data else none %}
          {% set sessoes_edit_scope = sessoes_edit.get("visibility_scope_mode", "all") if sessoes_edit else "all" %}
          {% set sessoes_edit_status = "inativo" if sessoes_edit and (sessoes_edit.get("is_active") == false or sessoes_edit.get("status") == "inativo") else "ativo" %}

          <section
            id="admin-sidebar-sections-form-card"
            class="card appverbo-sessoes-card-v30 appverbo-sessoes-form-card-v30"
            data-menu-scope="administrativo"
          >
            {% if settings_success %}
              <div class="alert ok">{{ settings_success }}</div>
            {% endif %}
            {% if settings_error %}
              <div class="alert error">{{ settings_error }}</div>
            {% endif %}

            {% if sessoes_edit %}
              <h2 class="appverbo-sessoes-form-title-v30">Editar sessão</h2>

              <form method="post" action="/settings/menu/sidebar-section-save" class="appverbo-sessoes-form-v30">
                <input type="hidden" name="section_mode" value="edit">
                <input type="hidden" name="original_section_key" value="{{ sessoes_edit.get('key', '') }}">
                <input type="hidden" name="sidebar_section_return_url" value="{{ sessoes_return_url }}">

                <div class="appverbo-sessoes-grid-v30">
                  <div class="field">
                    <label for="edit_sidebar_section_label_v30">Nome da sessão *</label>
                    <input
                      id="edit_sidebar_section_label_v30"
                      name="section_label"
                      required
                      maxlength="80"
                      value="{{ sessoes_edit.get('label', '') }}"
                    >
                  </div>

                  <div class="field">
                    <label for="edit_sidebar_section_scope_v30">Sistema *</label>
                    <select id="edit_sidebar_section_scope_v30" name="section_visibility_scope_mode">
                      <option value="all" {% if sessoes_edit_scope == "all" %}selected{% endif %}>Owner e Legado</option>
                      <option value="owner" {% if sessoes_edit_scope == "owner" %}selected{% endif %}>Owner</option>
                      <option value="legado" {% if sessoes_edit_scope == "legado" %}selected{% endif %}>Legado</option>
                    </select>
                  </div>

                  <div class="field">
                    <label for="edit_sidebar_section_status_v30">Estado *</label>
                    <select id="edit_sidebar_section_status_v30" name="section_status">
                      <option value="ativo" {% if sessoes_edit_status == "ativo" %}selected{% endif %}>Ativo</option>
                      <option value="inativo" {% if sessoes_edit_status == "inativo" %}selected{% endif %}>Inativo</option>
                    </select>
                  </div>
                </div>

                <div class="form-action-row appverbo-sessoes-actions-v30">
                  <button type="submit" class="action-btn">Guardar</button>
                  <a class="action-btn-cancel appverbo-sessoes-cancel-link-v30" href="{{ sessoes_return_url }}">Cancelar</a>
                </div>
              </form>
            {% else %}
              <details id="create-sidebar-section-collapse-v30" class="entity-create-collapse appverbo-sessoes-create-collapse-v30">
                <summary>
                  <span>Criar sessão</span>
                </summary>

                <div class="entity-create-body">
                  <form method="post" action="/settings/menu/sidebar-section-save" class="appverbo-sessoes-form-v30">
                    <input type="hidden" name="section_mode" value="create">
                    <input type="hidden" name="original_section_key" value="">
                    <input type="hidden" name="sidebar_section_return_url" value="{{ sessoes_return_url }}">

                    <div class="appverbo-sessoes-grid-v30">
                      <div class="field">
                        <label for="create_sidebar_section_label_v30">Nome da sessão *</label>
                        <input
                          id="create_sidebar_section_label_v30"
                          name="section_label"
                          required
                          maxlength="80"
                          placeholder="Informe o nome da sessão"
                        >
                      </div>

                      <div class="field">
                        <label for="create_sidebar_section_scope_v30">Sistema *</label>
                        <select id="create_sidebar_section_scope_v30" name="section_visibility_scope_mode">
                          <option value="all" selected>Owner e Legado</option>
                          <option value="owner">Owner</option>
                          <option value="legado">Legado</option>
                        </select>
                      </div>

                      <div class="field">
                        <label for="create_sidebar_section_status_v30">Estado *</label>
                        <select id="create_sidebar_section_status_v30" name="section_status">
                          <option value="ativo" selected>Ativo</option>
                          <option value="inativo">Inativo</option>
                        </select>
                      </div>
                    </div>

                    <div class="form-action-row appverbo-sessoes-actions-v30">
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
            class="card appverbo-sessoes-card-v30 appverbo-sessoes-list-card-v30"
            data-menu-scope="administrativo"
          >
            <h2>Sessões ativas</h2>

            {% if active_sidebar_sections %}
              <div class="appverbo-sessoes-table-wrap-v30">
                <table class="appverbo-sessoes-table-v30">
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
                        <td><span class="appverbo-sessoes-badge-v30 appverbo-sessoes-badge-ativo-v30">Ativo</span></td>
                        <td>
                          <div class="appverbo-sessoes-row-actions-v30">
                            <form method="post" action="/settings/menu/sidebar-section-move-one" class="appverbo-sessoes-inline-form-v30">
                              <input type="hidden" name="section_key" value="{{ row.key }}">
                              <input type="hidden" name="direction" value="up">
                              <input type="hidden" name="sidebar_section_return_url" value="{{ sessoes_return_url }}">
                              <button type="submit" class="appverbo-sessoes-action-btn-v30" title="Subir sessão" aria-label="Subir sessão">↑</button>
                            </form>

                            <form method="post" action="/settings/menu/sidebar-section-move-one" class="appverbo-sessoes-inline-form-v30">
                              <input type="hidden" name="section_key" value="{{ row.key }}">
                              <input type="hidden" name="direction" value="down">
                              <input type="hidden" name="sidebar_section_return_url" value="{{ sessoes_return_url }}">
                              <button type="submit" class="appverbo-sessoes-action-btn-v30" title="Descer sessão" aria-label="Descer sessão">↓</button>
                            </form>

                            <button
                              type="button"
                              class="appverbo-sessoes-action-btn-v30"
                              title="Visualizar detalhes"
                              aria-label="Visualizar detalhes"
                              data-sessao-view-v30
                              data-sessao-label="{{ row.label }}"
                              data-sessao-sistema="{{ row.visibility_scope_label or 'Owner e Legado' }}"
                              data-sessao-estado="Ativo"
                            >👁</button>

                            <a
                              class="appverbo-sessoes-action-btn-v30 appverbo-sessoes-action-link-v30"
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
            class="card appverbo-sessoes-card-v30 appverbo-sessoes-inactive-card-v30"
            data-menu-scope="administrativo"
          >
            <h2>Sessões inativas</h2>

            {% if inactive_sidebar_sections %}
              <div class="appverbo-sessoes-table-wrap-v30">
                <table class="appverbo-sessoes-table-v30">
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
                        <td><span class="appverbo-sessoes-badge-v30 appverbo-sessoes-badge-inativo-v30">Inativo</span></td>
                        <td>
                          <div class="appverbo-sessoes-row-actions-v30">
                            <button
                              type="button"
                              class="appverbo-sessoes-action-btn-v30"
                              title="Visualizar detalhes"
                              aria-label="Visualizar detalhes"
                              data-sessao-view-v30
                              data-sessao-label="{{ row.label }}"
                              data-sessao-sistema="{{ row.visibility_scope_label or 'Owner e Legado' }}"
                              data-sessao-estado="Inativo"
                            >👁</button>

                            <a
                              class="appverbo-sessoes-action-btn-v30 appverbo-sessoes-action-link-v30"
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
        {% endif %}
        __TEMPLATE_MARKER_END__
"""

template_block = template_block.replace("__TEMPLATE_MARKER_START__", TEMPLATE_MARKER_START)
template_block = template_block.replace("__TEMPLATE_MARKER_END__", TEMPLATE_MARKER_END)

anchor = '<section id="dynamic-process-card"'

if anchor not in template_content:
    fail_v30("não encontrei âncora dynamic-process-card no template.")

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
    fail_v30("não consegui atualizar cache do JS no template.")

if CSS_CACHE not in template_content:
    fail_v30("não consegui atualizar cache do CSS no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: template renderiza Sessões apenas com admin_tab=sessoes.")


####################################################################################
# (9) DESATIVAR CONTROLADORES JS DE VISIBILIDADE/RENDER E DEIXAR SOMENTE VISUALIZAR
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

for start_marker, end_marker, reason in [
    ("// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START", "// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END", "renderizava card antigo por JS."),
    ("// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START", "// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END", "controlava fluxo visual antigo."),
    ("// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START", "// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END", "recriava lista por fetch."),
    ("// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START", "// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END", "forçava URL/aba de Sessões."),
    ("// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START", "// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END", "reconstruía cards por JS."),
    ("// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START", "// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END", "reconstruía formulários/listas por JS."),
    ("// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START", "// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END", "hidratava ações antigas."),
    ("// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START", "// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END", "controlava visibilidade paralela."),
    ("// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START", "// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END", "forçava reaparecimento por JS."),
    ("// APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_START", "// APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_END", "controlava visibilidade paralela."),
    ("// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START", "// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END", "controlava visibilidade paralela."),
]:
    js_content = disable_js_block_v30(js_content, start_marker, end_marker, reason)

js_block = r'''// APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START
(function () {
  "use strict";

  //###################################################################################
  // (1) VISUALIZAR DETALHES
  //###################################################################################

  function instalarVisualizarSessaoV30() {
    if (window.__appverboSessoesVisualizarV30 === true) {
      return;
    }

    window.__appverboSessoesVisualizarV30 = true;

    document.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sessao-view-v30]");

      if (!botao) {
        return;
      }

      event.preventDefault();

      alert(
        "Nome da sessão: " + (botao.dataset.sessaoLabel || "") +
        "\nSistema: " + (botao.dataset.sessaoSistema || "") +
        "\nEstado: " + (botao.dataset.sessaoEstado || "")
      );
    });
  }

  //###################################################################################
  // (2) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarVisualizarSessaoV30);
  }
  else {
    instalarVisualizarSessaoV30();
  }
})();
// APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END
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

print("OK: JS de Sessões reduzido para ação auxiliar de visualizar.")


####################################################################################
# (10) LIMPAR CSS ANTIGO E APLICAR CSS V30 SEM REGRAS DE OCULTAR ABA
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

for start_marker, end_marker in [
    ("/* APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START */", "/* APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END */"),
    ("/* APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START */", "/* APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_END */"),
    ("/* APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START */", "/* APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END */"),
    ("/* APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_START */", "/* APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_END */"),
    ("/* APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START */", "/* APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END */"),
    (CSS_MARKER_START, CSS_MARKER_END),
]:
    css_content = remove_marked_block_v30(css_content, start_marker, end_marker)

css_block = """__CSS_MARKER_START__

.appverbo-sessoes-card-v30 {
  display: block !important;
  visibility: visible !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

.appverbo-sessoes-form-card-v30 {
  background: #f3f6fb !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  padding: 16px !important;
  margin-bottom: 12px !important;
  min-height: 58px !important;
}

.appverbo-sessoes-list-card-v30,
.appverbo-sessoes-inactive-card-v30 {
  background: #ffffff !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  padding: 16px !important;
  margin-bottom: 12px !important;
}

.appverbo-sessoes-form-title-v30,
.appverbo-sessoes-card-v30 h2 {
  margin: 0 0 12px !important;
  color: #12213a !important;
  font-size: 22px !important;
  font-weight: 800 !important;
}

.appverbo-sessoes-create-collapse-v30 > summary {
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

.appverbo-sessoes-create-collapse-v30 > summary::-webkit-details-marker {
  display: none !important;
}

.appverbo-sessoes-create-collapse-v30[open] > summary {
  margin-bottom: 14px !important;
}

.appverbo-sessoes-grid-v30 {
  display: grid !important;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px) !important;
  gap: 12px !important;
  align-items: end !important;
  width: 100% !important;
}

.appverbo-sessoes-grid-v30 .field label {
  display: block !important;
  margin-bottom: 6px !important;
  color: #12213a !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
}

.appverbo-sessoes-grid-v30 .field input,
.appverbo-sessoes-grid-v30 .field select {
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

.appverbo-sessoes-actions-v30 {
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
  margin-top: 12px !important;
}

.appverbo-sessoes-actions-v30 .action-btn,
.appverbo-sessoes-actions-v30 .action-btn-cancel,
.appverbo-sessoes-cancel-link-v30 {
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

.appverbo-sessoes-table-wrap-v30,
.appverbo-sessoes-table-v30 {
  width: 100% !important;
}

.appverbo-sessoes-table-v30 {
  border-collapse: collapse !important;
}

.appverbo-sessoes-table-v30 th,
.appverbo-sessoes-table-v30 td {
  padding: 10px 12px !important;
  border-bottom: 1px solid #e3e8f2 !important;
  text-align: left !important;
  vertical-align: middle !important;
}

.appverbo-sessoes-table-v30 th {
  color: #12213a !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
}

.appverbo-sessoes-table-v30 th:last-child,
.appverbo-sessoes-table-v30 td:last-child {
  text-align: right !important;
}

.appverbo-sessoes-row-actions-v30 {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 6px !important;
}

.appverbo-sessoes-inline-form-v30 {
  display: inline-flex !important;
  margin: 0 !important;
  padding: 0 !important;
}

.appverbo-sessoes-action-btn-v30 {
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

.appverbo-sessoes-action-btn-v30:hover {
  background: #dfeaff !important;
  border-color: #7fa8f2 !important;
}

.appverbo-sessoes-badge-v30 {
  display: inline-flex !important;
  align-items: center !important;
  min-height: 24px !important;
  padding: 3px 9px !important;
  border: 1px solid transparent !important;
  border-radius: 999px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
}

.appverbo-sessoes-badge-ativo-v30 {
  border-color: #badbcc !important;
  background: #e9f7ef !important;
  color: #0f5132 !important;
}

.appverbo-sessoes-badge-inativo-v30 {
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}

@media (max-width: 1100px) {
  .appverbo-sessoes-grid-v30 {
    grid-template-columns: 1fr !important;
  }
}

__CSS_MARKER_END__"""

css_block = css_block.replace("__CSS_MARKER_START__", CSS_MARKER_START)
css_block = css_block.replace("__CSS_MARKER_END__", CSS_MARKER_END)

css_content = css_content.rstrip() + "\n\n" + css_block + "\n"
CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS V30 aplicado sem regras paralelas de esconder Sessões.")


####################################################################################
# (11) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
page_validado = PAGE_HANDLER_PATH.read_text(encoding="utf-8")
settings_validado = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START": agents_validado,
    "{% if admin_tab == \"sessoes\" %}": template_validado,
    "APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START": template_validado,
    "admin-sidebar-sections-form-card": template_validado,
    "admin-sidebar-sections-card": template_validado,
    "admin-sidebar-sections-inactive-card": template_validado,
    "appverbo-sessoes-card-v30": template_validado,
    "20260505-sessoes-fluxo-nativo-igual-entidade-v30": template_validado,
    "sidebar_section_edit_data": page_validado,
    "active_sidebar_sections": page_validado,
    "inactive_sidebar_sections": page_validado,
    "APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START": js_validado,
    "data-sessao-view-v30": js_validado,
    "APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START": css_validado,
    "appverbo-sessoes-card-v30": css_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v30(f"validação falhou, termo ausente: {termo}")

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    count = len(re.findall(r'id=[\"\']' + re.escape(section_id) + r'[\"\']', template_validado))

    if count != 1:
        fail_v30(f"esperado exatamente 1 #{section_id}, encontrado: {count}")

if 'data-admin-tab-pane="sessoes"' in template_validado:
    fail_v30('template ainda contém data-admin-tab-pane="sessoes", que foi removido no fluxo nativo.')

for forbidden in [
    "APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START\n(function",
    "APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START\n(function",
    "APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START\n(function",
    "APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START\n(function",
    "APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_START\n(function",
    "APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START\n(function",
]:
    if forbidden in js_validado:
        fail_v30(f"controlador antigo ainda ativo: {forbidden.splitlines()[0]}")

try:
    ast.parse(page_validado)
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v30(f"Python final inválido: {exc}")

print("OK: patch_sessoes_fluxo_nativo_igual_entidade_v30 concluído.")
