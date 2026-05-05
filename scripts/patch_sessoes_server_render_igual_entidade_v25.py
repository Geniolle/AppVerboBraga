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

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END -->"

TEMPLATE_MARKER_START = "<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START -->"
TEMPLATE_MARKER_END = "<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END -->"

SETTINGS_MARKER_START = "# APPVERBO_SESSOES_SERVER_MOVE_ONE_V25_START"
SETTINGS_MARKER_END = "# APPVERBO_SESSOES_SERVER_MOVE_ONE_V25_END"

JS_MARKER_START = "// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START"
JS_MARKER_END = "// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-server-render-igual-entidade-v25"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-server-render-igual-entidade-v25"


def fail_v25(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v25() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) REMOVER SECTION POR ID COM SCANNER SIMPLES
####################################################################################

def remove_section_by_id_v25(content: str, section_id: str) -> str:
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
            fail_v25(f"não consegui encontrar fechamento da section #{section_id}")


####################################################################################
# (3) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, PAGE_HANDLER_PATH, SETTINGS_HANDLERS_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v25(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (4) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v25()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra definitiva: Sessões igual ao subprocesso Entidade

A aba **Sessões** deve seguir o mesmo procedimento do subprocesso **Entidade**.

Fluxo obrigatório:

1. A ação **Editar** navega para `/users/new` com:
   - `menu=administrativo`;
   - `admin_tab=sessoes`;
   - `sidebar_sections_tab=sessoes`;
   - `sidebar_section_edit_key=<key>`.
2. O `page_handler.py` carrega `sidebar_section_edit_data` no backend.
3. O template `new_user.html` renderiza o formulário de edição diretamente no HTML, como acontece com `entity_edit_data`.
4. O formulário envia para `/settings/menu/sidebar-section-save`.
5. O backend grava no BD/JSON `sidebar_menu_settings.menu_config.sidebar_sections`.
6. Depois do commit, redireciona para a aba **Sessões**.
7. O backend separa e entrega:
   - `active_sidebar_sections`;
   - `inactive_sidebar_sections`.
8. O template renderiza diretamente:
   - card de criar/editar sessão;
   - card **Sessões do sidebar**;
   - card **Sessões inativas**.
9. JavaScript não pode reconstruir listas nem formulários de Sessões.
10. JavaScript só pode atuar em comportamento auxiliar, como visualizar detalhes ou controlar visibilidade da aba.
{AGENTS_MARKER_END}"""

if AGENTS_MARKER_START in agents_content and AGENTS_MARKER_END in agents_content:
    agents_content = re.sub(
        re.escape(AGENTS_MARKER_START) + r"[\s\S]*?" + re.escape(AGENTS_MARKER_END),
        agents_rule,
        agents_content,
        count=1,
    )
else:
    agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: AGENTS.md atualizado em {agents_path}")


####################################################################################
# (5) AJUSTAR PAGE_HANDLER PARA TARGET DE EDICAO DE SESSOES
####################################################################################

page_content = PAGE_HANDLER_PATH.read_text(encoding="utf-8-sig")

if 'sidebar_section_edit_key: str = "",' not in page_content:
    old_param = '''    section_key: str = "",
    appverbo_after_save: str = "",
'''
    new_param = '''    section_key: str = "",
    sidebar_section_edit_key: str = "",
    appverbo_after_save: str = "",
'''

    if old_param not in page_content:
        fail_v25("não encontrei local para inserir sidebar_section_edit_key no page_handler.py.")

    page_content = page_content.replace(old_param, new_param, 1)

if 'resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes"}' not in page_content:
    page_content = page_content.replace(
        'resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes"}',
        'resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes"}',
        1,
    )

if "active_sidebar_sections_v22" not in page_content:
    fail_v25("split backend V22 ainda não existe no page_handler.py. Execute primeiro o patch de split backend ou peça-me para reconstruir do zero.")

old_sessoes_target = '''    if resolved_admin_tab == "sessoes":
        initial_menu_target = "#admin-sidebar-sections-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
'''

new_sessoes_target = '''    if resolved_admin_tab == "sessoes":
        if str(sidebar_section_edit_key or "").strip():
            initial_menu_target = "#admin-sidebar-sections-form-card"
        else:
            initial_menu_target = "#admin-sidebar-sections-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
'''

if old_sessoes_target in page_content:
    page_content = page_content.replace(old_sessoes_target, new_sessoes_target, 1)
elif 'if resolved_admin_tab == "sessoes":' in page_content and "#admin-sidebar-sections-form-card" not in page_content:
    page_content = page_content.replace(
        'initial_menu_target = "#admin-sidebar-sections-card"',
        'initial_menu_target = "#admin-sidebar-sections-form-card" if str(sidebar_section_edit_key or "").strip() else "#admin-sidebar-sections-card"',
        1,
    )

try:
    ast.parse(page_content)
except SyntaxError as exc:
    fail_v25(f"page_handler.py ficaria inválido: {exc}")

PAGE_HANDLER_PATH.write_text(page_content, encoding="utf-8")

print("OK: page_handler.py ajustado para edição server-render de Sessões.")


####################################################################################
# (6) ADICIONAR ENDPOINT SERVER-SIDE PARA MOVER SESSAO
####################################################################################

settings_content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

settings_block = f'''{SETTINGS_MARKER_START}

# ###################################################################################
# (SIDEBAR_SECTION_MOVE_ONE_V25) MOVER SESSAO COM FLUXO SERVER-SIDE
# ###################################################################################

@router.post("/settings/menu/sidebar-section-move-one", response_class=HTMLResponse)
def move_one_sidebar_section_v25(
    request: Request,
    section_key: str = Form(""),
    direction: str = Form(""),
    sidebar_section_return_url: str = Form(""),
) -> RedirectResponse:
    safe_return_url = _sanitize_sidebar_section_return_url_v19(sidebar_section_return_url)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Apenas administradores podem alterar sessões do sidebar.",
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Apenas Owner pode alterar sessões do sidebar.",
            )

        clean_section_key = _slugify_sidebar_section_key_v19(section_key)
        clean_direction = str(direction or "").strip().lower()

        if clean_direction not in {{"up", "down"}}:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Direção inválida para mover a sessão.",
            )

        current_sections = _read_sidebar_sections_for_save_one_v19(session)
        payload_sections: list[dict[str, str]] = []

        for section in current_sections:
            payload_sections.append(
                {{
                    "key": _slugify_sidebar_section_key_v19(section.get("key")),
                    "label": _normalize_sidebar_section_text_v19(section.get("label")),
                    "visibility_scope_mode": _normalize_sidebar_section_scope_v19(
                        section.get("visibility_scope_mode")
                    ),
                    "status": _normalize_sidebar_section_status_v19(section.get("status")),
                }}
            )

        current_index = next(
            (
                index
                for index, section in enumerate(payload_sections)
                if _slugify_sidebar_section_key_v19(section.get("key")) == clean_section_key
            ),
            -1,
        )

        if current_index < 0:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Sessão não encontrada para mover.",
            )

        target_index = current_index - 1 if clean_direction == "up" else current_index + 1

        if target_index < 0 or target_index >= len(payload_sections):
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "success",
                "Sessão já está no limite da hierarquia.",
            )

        payload_sections[current_index], payload_sections[target_index] = (
            payload_sections[target_index],
            payload_sections[current_index],
        )

        ok, error_message = update_sidebar_sections_v2(
            session,
            payload_sections,
        )

        if not ok:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                error_message or "Não foi possível mover a sessão.",
            )

        target_status = payload_sections[target_index].get("status", "ativo")
        _persist_sidebar_sections_status_v19(
            session=session,
            payload_sections=payload_sections,
            target_section_key=clean_section_key,
            target_status=target_status,
        )

        return _redirect_sidebar_section_message_v19(
            safe_return_url,
            "success",
            "Hierarquia da sessão atualizada com sucesso.",
        )

{SETTINGS_MARKER_END}
'''

if SETTINGS_MARKER_START in settings_content and SETTINGS_MARKER_END in settings_content:
    settings_content = re.sub(
        re.escape(SETTINGS_MARKER_START) + r"[\s\S]*?" + re.escape(SETTINGS_MARKER_END),
        settings_block,
        settings_content,
        count=1,
    )
else:
    anchor = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START"

    if anchor not in settings_content:
        fail_v25("não encontrei âncora para inserir endpoint move_one_sidebar_section_v25.")

    settings_content = settings_content.replace(anchor, settings_block + "\n\n" + anchor, 1)

try:
    ast.parse(settings_content)
except SyntaxError as exc:
    fail_v25(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_content, encoding="utf-8")

print("OK: endpoint server-side de mover sessão criado.")


####################################################################################
# (7) SERVER-RENDER NO TEMPLATE IGUAL AO PADRAO ENTIDADE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if TEMPLATE_MARKER_START in template_content and TEMPLATE_MARKER_END in template_content:
    template_content = re.sub(
        re.escape(TEMPLATE_MARKER_START) + r"[\s\S]*?" + re.escape(TEMPLATE_MARKER_END),
        "",
        template_content,
        count=1,
    )

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-create-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    template_content = remove_section_by_id_v25(template_content, section_id)

template_block = f'''{TEMPLATE_MARKER_START}
        {{% set sessoes_return_url = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card" %}}
        {{% set sessoes_edit = sidebar_section_edit_data if sidebar_section_edit_data else none %}}
        {{% set sessoes_edit_scope = sessoes_edit.get("visibility_scope_mode", "all") if sessoes_edit else "all" %}}
        {{% set sessoes_edit_status = "inativo" if sessoes_edit and (sessoes_edit.get("is_active") == false or sessoes_edit.get("status") == "inativo") else "ativo" %}}

        <section
          id="admin-sidebar-sections-form-card"
          class="card appverbo-sessoes-card-v25 appverbo-sessoes-form-card-v25"
          data-menu-scope="administrativo"
          data-admin-tab-pane="sessoes"
        >
          {{% if settings_success and admin_tab == "sessoes" %}}
            <div class="alert ok">{{{{ settings_success }}}}</div>
          {{% endif %}}
          {{% if settings_error and admin_tab == "sessoes" %}}
            <div class="alert error">{{{{ settings_error }}}}</div>
          {{% endif %}}

          {{% if sessoes_edit %}}
            <h2 class="appverbo-sessoes-form-title-v25">Editar sessão</h2>
            <form method="post" action="/settings/menu/sidebar-section-save" class="appverbo-sessoes-form-v25">
              <input type="hidden" name="section_mode" value="edit">
              <input type="hidden" name="original_section_key" value="{{{{ sessoes_edit.get('key', '') }}}}">
              <input type="hidden" name="sidebar_section_return_url" value="{{{{ sessoes_return_url }}}}">

              <div class="appverbo-sessoes-grid-v25">
                <div class="field">
                  <label for="edit_sidebar_section_label_v25">Nome da sessão *</label>
                  <input
                    id="edit_sidebar_section_label_v25"
                    name="section_label"
                    required
                    maxlength="80"
                    value="{{{{ sessoes_edit.get('label', '') }}}}"
                  >
                </div>

                <div class="field">
                  <label for="edit_sidebar_section_scope_v25">Sistema *</label>
                  <select id="edit_sidebar_section_scope_v25" name="section_visibility_scope_mode">
                    <option value="all" {{% if sessoes_edit_scope == "all" %}}selected{{% endif %}}>Owner e Legado</option>
                    <option value="owner" {{% if sessoes_edit_scope == "owner" %}}selected{{% endif %}}>Owner</option>
                    <option value="legado" {{% if sessoes_edit_scope == "legado" %}}selected{{% endif %}}>Legado</option>
                  </select>
                </div>

                <div class="field">
                  <label for="edit_sidebar_section_status_v25">Estado *</label>
                  <select id="edit_sidebar_section_status_v25" name="section_status">
                    <option value="ativo" {{% if sessoes_edit_status == "ativo" %}}selected{{% endif %}}>Ativo</option>
                    <option value="inativo" {{% if sessoes_edit_status == "inativo" %}}selected{{% endif %}}>Inativo</option>
                  </select>
                </div>
              </div>

              <div class="form-action-row appverbo-sessoes-actions-v25">
                <button type="submit" class="action-btn">Guardar</button>
                <a class="action-btn-cancel appverbo-sessoes-cancel-link-v25" href="{{{{ sessoes_return_url }}}}">Cancelar</a>
              </div>
            </form>
          {{% else %}}
            <details id="create-sidebar-section-collapse-v25" class="entity-create-collapse appverbo-sessoes-create-collapse-v25">
              <summary>
                <span>Criar sessão</span>
              </summary>

              <div class="entity-create-body">
                <form method="post" action="/settings/menu/sidebar-section-save" class="appverbo-sessoes-form-v25">
                  <input type="hidden" name="section_mode" value="create">
                  <input type="hidden" name="original_section_key" value="">
                  <input type="hidden" name="sidebar_section_return_url" value="{{{{ sessoes_return_url }}}}">

                  <div class="appverbo-sessoes-grid-v25">
                    <div class="field">
                      <label for="create_sidebar_section_label_v25">Nome da sessão *</label>
                      <input
                        id="create_sidebar_section_label_v25"
                        name="section_label"
                        required
                        maxlength="80"
                        placeholder="Informe o nome da sessão"
                      >
                    </div>

                    <div class="field">
                      <label for="create_sidebar_section_scope_v25">Sistema *</label>
                      <select id="create_sidebar_section_scope_v25" name="section_visibility_scope_mode">
                        <option value="all" selected>Owner e Legado</option>
                        <option value="owner">Owner</option>
                        <option value="legado">Legado</option>
                      </select>
                    </div>

                    <div class="field">
                      <label for="create_sidebar_section_status_v25">Estado *</label>
                      <select id="create_sidebar_section_status_v25" name="section_status">
                        <option value="ativo" selected>Ativo</option>
                        <option value="inativo">Inativo</option>
                      </select>
                    </div>
                  </div>

                  <div class="form-action-row appverbo-sessoes-actions-v25">
                    <button type="submit" class="action-btn">Guardar</button>
                    <button
                      type="button"
                      class="action-btn-cancel"
                      onclick="const form=this.closest('form'); const details=this.closest('details'); if(form){{form.reset();}} if(details){{details.open=false;}}"
                    >Cancelar</button>
                  </div>
                </form>
              </div>
            </details>
          {{% endif %}}
        </section>

        <section
          id="admin-sidebar-sections-card"
          class="card appverbo-sessoes-card-v25 appverbo-sessoes-list-card-v25"
          data-menu-scope="administrativo"
          data-admin-tab-pane="sessoes"
        >
          <h2>Sessões do sidebar</h2>
          <p class="appverbo-sessoes-card-description-v25">Defina e organize apenas as sessões do menu lateral.</p>

          {{% if active_sidebar_sections %}}
            <div class="appverbo-sessoes-table-wrap-v25">
              <table class="appverbo-sessoes-table-v25">
                <thead>
                  <tr>
                    <th>MENU LATERAL</th>
                    <th>SISTEMA</th>
                    <th>ESTADO</th>
                    <th>AÇÕES</th>
                  </tr>
                </thead>
                <tbody>
                  {{% for row in active_sidebar_sections %}}
                    <tr>
                      <td>{{{{ row.label }}}}</td>
                      <td>{{{{ row.visibility_scope_label or "Owner e Legado" }}}}</td>
                      <td><span class="appverbo-sessoes-badge-v25 appverbo-sessoes-badge-ativo-v25">Ativo</span></td>
                      <td>
                        <div class="appverbo-sessoes-row-actions-v25">
                          <form method="post" action="/settings/menu/sidebar-section-move-one" class="appverbo-sessoes-inline-form-v25">
                            <input type="hidden" name="section_key" value="{{{{ row.key }}}}">
                            <input type="hidden" name="direction" value="up">
                            <input type="hidden" name="sidebar_section_return_url" value="{{{{ sessoes_return_url }}}}">
                            <button type="submit" class="appverbo-sessoes-action-btn-v25" title="Subir sessão" aria-label="Subir sessão">↑</button>
                          </form>

                          <form method="post" action="/settings/menu/sidebar-section-move-one" class="appverbo-sessoes-inline-form-v25">
                            <input type="hidden" name="section_key" value="{{{{ row.key }}}}">
                            <input type="hidden" name="direction" value="down">
                            <input type="hidden" name="sidebar_section_return_url" value="{{{{ sessoes_return_url }}}}">
                            <button type="submit" class="appverbo-sessoes-action-btn-v25" title="Descer sessão" aria-label="Descer sessão">↓</button>
                          </form>

                          <button
                            type="button"
                            class="appverbo-sessoes-action-btn-v25"
                            title="Visualizar detalhes"
                            aria-label="Visualizar detalhes"
                            data-sessao-view-v25
                            data-sessao-label="{{{{ row.label }}}}"
                            data-sessao-sistema="{{{{ row.visibility_scope_label or 'Owner e Legado' }}}}"
                            data-sessao-estado="Ativo"
                          >👁</button>

                          <a
                            class="appverbo-sessoes-action-btn-v25 appverbo-sessoes-action-link-v25"
                            title="Editar sessão"
                            aria-label="Editar sessão"
                            href="/users/new?menu=administrativo&amp;admin_tab=sessoes&amp;sidebar_sections_tab=sessoes&amp;target=admin-sidebar-sections-form-card&amp;sidebar_section_edit_key={{{{ row.key }}}}#admin-sidebar-sections-form-card"
                          >✎</a>
                        </div>
                      </td>
                    </tr>
                  {{% endfor %}}
                </tbody>
              </table>
            </div>
          {{% else %}}
            <p class="empty">Sem sessões ativas.</p>
          {{% endif %}}
        </section>

        <section
          id="admin-sidebar-sections-inactive-card"
          class="card appverbo-sessoes-card-v25 appverbo-sessoes-inactive-card-v25"
          data-menu-scope="administrativo"
          data-admin-tab-pane="sessoes"
        >
          <h2>Sessões inativas</h2>

          {{% if inactive_sidebar_sections %}}
            <div class="appverbo-sessoes-table-wrap-v25">
              <table class="appverbo-sessoes-table-v25">
                <thead>
                  <tr>
                    <th>MENU LATERAL</th>
                    <th>SISTEMA</th>
                    <th>ESTADO</th>
                    <th>AÇÕES</th>
                  </tr>
                </thead>
                <tbody>
                  {{% for row in inactive_sidebar_sections %}}
                    <tr>
                      <td>{{{{ row.label }}}}</td>
                      <td>{{{{ row.visibility_scope_label or "Owner e Legado" }}}}</td>
                      <td><span class="appverbo-sessoes-badge-v25 appverbo-sessoes-badge-inativo-v25">Inativo</span></td>
                      <td>
                        <div class="appverbo-sessoes-row-actions-v25">
                          <button
                            type="button"
                            class="appverbo-sessoes-action-btn-v25"
                            title="Visualizar detalhes"
                            aria-label="Visualizar detalhes"
                            data-sessao-view-v25
                            data-sessao-label="{{{{ row.label }}}}"
                            data-sessao-sistema="{{{{ row.visibility_scope_label or 'Owner e Legado' }}}}"
                            data-sessao-estado="Inativo"
                          >👁</button>

                          <a
                            class="appverbo-sessoes-action-btn-v25 appverbo-sessoes-action-link-v25"
                            title="Editar sessão"
                            aria-label="Editar sessão"
                            href="/users/new?menu=administrativo&amp;admin_tab=sessoes&amp;sidebar_sections_tab=sessoes&amp;target=admin-sidebar-sections-form-card&amp;sidebar_section_edit_key={{{{ row.key }}}}#admin-sidebar-sections-form-card"
                          >✎</a>
                        </div>
                      </td>
                    </tr>
                  {{% endfor %}}
                </tbody>
              </table>
            </div>
          {{% else %}}
            <p class="empty">Sem sessões inativas.</p>
          {{% endif %}}
        </section>
        {TEMPLATE_MARKER_END}
'''

anchor = '<section id="dynamic-process-card"'

if anchor not in template_content:
    fail_v25("não encontrei âncora dynamic-process-card para inserir blocos server-render de Sessões.")

template_content = template_content.replace(anchor, template_block + "\n" + anchor, 1)

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v25("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v25("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: template atualizado com Sessões server-render igual Entidade.")


####################################################################################
# (8) DESATIVAR JS RENDERIZADOR ANTIGO E DEIXAR APENAS AUXILIAR
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

def disable_block_v25(content: str, start_marker: str, end_marker: str, reason: str) -> str:
    if start_marker not in content or end_marker not in content:
        return content

    replacement = f"""{start_marker}
// Desativado pelo fluxo server-render V25.
// Motivo: {reason}
{end_marker}"""

    return re.sub(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        replacement,
        content,
        count=1,
    )

for start_marker, end_marker, reason in [
    ("// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START", "// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END", "renderizava card por JS."),
    ("// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START", "// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END", "controlava fluxo visual por JS."),
    ("// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START", "// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END", "reconstruía listas por fetch."),
    ("// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START", "// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END", "forçava URL da aba Sessões."),
    ("// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START", "// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END", "reconstruía cards por JS."),
    ("// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START", "// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END", "renderizava formulário/listas por JS."),
    ("// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START", "// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END", "hidratava ações que agora vêm do template."),
]:
    js_content = disable_block_v25(js_content, start_marker, end_marker, reason)

js_block = r'''// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START
(function () {
  "use strict";

  //###################################################################################
  // (1) UTILITARIOS
  //###################################################################################

  function normalizarTextoV25(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function getSessoesCardsV25() {
    return Array.from(document.querySelectorAll('[data-admin-tab-pane="sessoes"]'));
  }

  function tabSessoesAtivaV25() {
    const url = new URL(window.location.href);

    if (
      url.searchParams.get("admin_tab") === "sessoes" ||
      url.searchParams.get("sidebar_sections_tab") === "sessoes" ||
      url.searchParams.has("sidebar_section_edit_key")
    ) {
      return true;
    }

    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab]"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoV25(elemento.textContent);
      const classe = normalizarTextoV25(elemento.className);
      const ariaSelected = elemento.getAttribute("aria-selected") === "true";

      return texto === "sessoes" &&
        (ariaSelected || classe.includes("active") || classe.includes("selected") || classe.includes("ativo"));
    });
  }

  //###################################################################################
  // (2) CONTROLAR VISIBILIDADE SEM RENDERIZAR CONTEUDO
  //###################################################################################

  function aplicarVisibilidadeSessoesV25() {
    const mostrar = tabSessoesAtivaV25();

    getSessoesCardsV25().forEach(function (card) {
      if (mostrar) {
        card.hidden = false;
        card.style.display = "";
        card.style.visibility = "";
      }
      else {
        card.hidden = true;
        card.style.display = "none";
      }
    });
  }

  //###################################################################################
  // (3) VISUALIZAR DETALHES
  //###################################################################################

  function instalarVisualizarV25() {
    if (window.__appverboSessoesServerRenderV25 === true) {
      return;
    }

    window.__appverboSessoesServerRenderV25 = true;

    document.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sessao-view-v25]");

      if (!botao) {
        window.setTimeout(aplicarVisibilidadeSessoesV25, 120);
        window.setTimeout(aplicarVisibilidadeSessoesV25, 350);
        return;
      }

      event.preventDefault();

      alert(
        "Nome da sessão: " + (botao.dataset.sessaoLabel || "") +
        "\nSistema: " + (botao.dataset.sessaoSistema || "") +
        "\nEstado: " + (botao.dataset.sessaoEstado || "")
      );
    }, true);

    window.addEventListener("hashchange", aplicarVisibilidadeSessoesV25);
    window.addEventListener("popstate", aplicarVisibilidadeSessoesV25);
  }

  //###################################################################################
  // (4) INICIAR
  //###################################################################################

  function iniciarV25() {
    instalarVisualizarV25();

    window.setTimeout(aplicarVisibilidadeSessoesV25, 80);
    window.setTimeout(aplicarVisibilidadeSessoesV25, 250);
    window.setTimeout(aplicarVisibilidadeSessoesV25, 700);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarV25);
  }
  else {
    iniciarV25();
  }
})();
// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END
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

print("OK: JS de render antigo desativado. V25 deixou apenas comportamento auxiliar.")


####################################################################################
# (9) CSS SERVER-RENDER
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

[data-admin-tab-pane="sessoes"] {{
  display: none;
}}

.appverbo-sessoes-card-v25 {{
  width: 100% !important;
  box-sizing: border-box !important;
}}

.appverbo-sessoes-form-card-v25 {{
  background: #f3f6fb !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  padding: 16px !important;
  margin-bottom: 12px !important;
}}

.appverbo-sessoes-list-card-v25,
.appverbo-sessoes-inactive-card-v25 {{
  background: #ffffff !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  padding: 16px !important;
  margin-bottom: 12px !important;
}}

.appverbo-sessoes-form-title-v25,
.appverbo-sessoes-card-v25 h2 {{
  margin: 0 0 12px !important;
  color: #12213a !important;
  font-size: 22px !important;
  font-weight: 800 !important;
}}

.appverbo-sessoes-card-description-v25 {{
  margin: 0 0 12px !important;
  color: #52607a !important;
  font-size: 13px !important;
}}

.appverbo-sessoes-create-collapse-v25 > summary {{
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
}}

.appverbo-sessoes-create-collapse-v25 > summary::-webkit-details-marker {{
  display: none !important;
}}

.appverbo-sessoes-create-collapse-v25[open] > summary {{
  margin-bottom: 14px !important;
}}

.appverbo-sessoes-grid-v25 {{
  display: grid !important;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px) !important;
  gap: 12px !important;
  align-items: end !important;
  width: 100% !important;
}}

.appverbo-sessoes-grid-v25 .field label {{
  display: block !important;
  margin-bottom: 6px !important;
  color: #12213a !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
}}

.appverbo-sessoes-grid-v25 .field input,
.appverbo-sessoes-grid-v25 .field select {{
  width: 100% !important;
  min-height: 38px !important;
  border: 1px solid #c6d0e2 !important;
  border-radius: 7px !important;
  background: #ffffff !important;
  color: #12213a !important;
  padding: 8px 10px !important;
  box-sizing: border-box !important;
  font-size: 13px !important;
}}

.appverbo-sessoes-actions-v25 {{
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
  margin-top: 12px !important;
}}

.appverbo-sessoes-actions-v25 .action-btn,
.appverbo-sessoes-actions-v25 .action-btn-cancel,
.appverbo-sessoes-cancel-link-v25 {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-width: 112px !important;
  width: 112px !important;
  height: 38px !important;
  min-height: 38px !important;
  box-sizing: border-box !important;
  text-decoration: none !important;
}}

.appverbo-sessoes-table-wrap-v25,
.appverbo-sessoes-table-v25 {{
  width: 100% !important;
}}

.appverbo-sessoes-table-v25 {{
  border-collapse: collapse !important;
}}

.appverbo-sessoes-table-v25 th,
.appverbo-sessoes-table-v25 td {{
  padding: 10px 12px !important;
  border-bottom: 1px solid #e3e8f2 !important;
  text-align: left !important;
  vertical-align: middle !important;
}}

.appverbo-sessoes-table-v25 th {{
  color: #12213a !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
}}

.appverbo-sessoes-table-v25 th:last-child,
.appverbo-sessoes-table-v25 td:last-child {{
  text-align: right !important;
}}

.appverbo-sessoes-row-actions-v25 {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 6px !important;
}}

.appverbo-sessoes-inline-form-v25 {{
  display: inline-flex !important;
  margin: 0 !important;
  padding: 0 !important;
}}

.appverbo-sessoes-action-btn-v25 {{
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
}}

.appverbo-sessoes-action-btn-v25:hover {{
  background: #dfeaff !important;
  border-color: #7fa8f2 !important;
}}

.appverbo-sessoes-badge-v25 {{
  display: inline-flex !important;
  align-items: center !important;
  min-height: 24px !important;
  padding: 3px 9px !important;
  border: 1px solid transparent !important;
  border-radius: 999px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
}}

.appverbo-sessoes-badge-ativo-v25 {{
  border-color: #badbcc !important;
  background: #e9f7ef !important;
  color: #0f5132 !important;
}}

.appverbo-sessoes-badge-inativo-v25 {{
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}}

@media (max-width: 1100px) {{
  .appverbo-sessoes-grid-v25 {{
    grid-template-columns: 1fr !important;
  }}
}}

{CSS_MARKER_END}'''

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

print("OK: CSS V25 aplicado.")


####################################################################################
# (10) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
page_validado = PAGE_HANDLER_PATH.read_text(encoding="utf-8")
settings_validado = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START": agents_validado,
    "#admin-sidebar-sections-form-card": page_validado,
    "active_sidebar_sections": page_validado,
    "inactive_sidebar_sections": page_validado,
    "move_one_sidebar_section_v25": settings_validado,
    "/settings/menu/sidebar-section-move-one": settings_validado,
    "APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START": template_validado,
    "admin-sidebar-sections-form-card": template_validado,
    "active_sidebar_sections": template_validado,
    "inactive_sidebar_sections": template_validado,
    "APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START": js_validado,
    "aplicarVisibilidadeSessoesV25": js_validado,
    "APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START": css_validado,
    "appverbo-sessoes-card-v25": css_validado,
    "20260505-sessoes-server-render-igual-entidade-v25": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v25(f"validação falhou, termo ausente: {termo}")

for forbidden in [
    "APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START\n(function",
    "APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START\n(function",
    "APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START\n(function",
    "APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START\n(function",
]:
    if forbidden in js_validado:
        fail_v25(f"controlador JS antigo ainda ativo: {forbidden.splitlines()[0]}")

try:
    ast.parse(page_validado)
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v25(f"Python final inválido: {exc}")

print("OK: patch_sessoes_server_render_igual_entidade_v25 concluído.")
