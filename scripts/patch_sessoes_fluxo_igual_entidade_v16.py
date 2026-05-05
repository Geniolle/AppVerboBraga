from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_END -->"

PY_MARKER_START = "# APPVERBO_SESSOES_SAVE_ONE_V16_START"
PY_MARKER_END = "# APPVERBO_SESSOES_SAVE_ONE_V16_END"

JS_MARKER_START = "// APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START"
JS_MARKER_END = "// APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-fluxo-entidade-v16"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-fluxo-entidade-v16"


def fail_v16(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v16() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, SETTINGS_HANDLERS_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v16(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v16()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra do subprocesso Sessões igual ao fluxo da Entidade

Na aba **Sessões**, a ação **Editar** deve seguir o mesmo padrão funcional da aba **Entidade**.

Regras:

1. O botão **Editar** da linha não deve editar inline.
2. Ao clicar em **Editar**, deve navegar/recarregar para a aba **Sessões** com o parâmetro técnico da sessão em edição.
3. Após o reload, o bloco superior da aba deve abrir em modo **Editar sessão**, com os campos preenchidos.
4. Os campos editáveis são:
   - **Nome da sessão**;
   - **Sistema**;
   - **Estado**.
5. O botão **Guardar** deve submeter um formulário dedicado para backend, semelhante ao fluxo de atualização da Entidade.
6. O botão **Cancelar** deve sair do modo edição e retornar para a lista da aba **Sessões**.
7. O botão **Criar sessão** continua pertencendo ao bloco superior da aba **Sessões**.
8. O bloco **Sessões inativas** deve permanecer separado abaixo, como card próprio.
9. A chave técnica da sessão deve ser preservada na edição.
{AGENTS_MARKER_END}"""

if AGENTS_MARKER_START in agents_content and AGENTS_MARKER_END in agents_content:
    agents_pattern = re.compile(
        re.escape(AGENTS_MARKER_START) + r"[\s\S]*?" + re.escape(AGENTS_MARKER_END),
        re.S,
    )
    agents_content = agents_pattern.sub(agents_rule, agents_content, count=1)
else:
    agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: regra do fluxo igual à Entidade atualizada em {agents_path}")


####################################################################################
# (4) ADICIONAR ENDPOINT DEDICADO PARA CRIAR/EDITAR UMA SESSAO
####################################################################################

settings_content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

py_block = r'''# APPVERBO_SESSOES_SAVE_ONE_V16_START

# ###################################################################################
# (SIDEBAR_SECTION_SAVE_ONE_V16) CRIAR/EDITAR UMA SESSAO COM FLUXO IGUAL ENTIDADE
# ###################################################################################

def _normalize_sidebar_section_text_v16(value: object) -> str:
    return str(value or "").strip()


def _slugify_sidebar_section_key_v16(value: object) -> str:
    import re
    import unicodedata

    raw_value = _normalize_sidebar_section_text_v16(value).lower()
    raw_value = unicodedata.normalize("NFD", raw_value)
    raw_value = "".join(char for char in raw_value if unicodedata.category(char) != "Mn")
    raw_value = re.sub(r"[^a-z0-9]+", "_", raw_value)
    raw_value = re.sub(r"_+", "_", raw_value).strip("_")
    return raw_value or "nova_sessao"


def _normalize_sidebar_section_status_v16(value: object) -> str:
    clean_value = _normalize_sidebar_section_text_v16(value).lower()

    if clean_value in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def _normalize_sidebar_section_scope_v16(value: object) -> str:
    clean_value = _normalize_sidebar_section_text_v16(value).lower()

    if clean_value in {"owner", "legado"}:
        return clean_value

    return "all"


def _make_unique_sidebar_section_key_v16(base_key: str, used_keys: set[str]) -> str:
    clean_base_key = _slugify_sidebar_section_key_v16(base_key)

    if clean_base_key not in used_keys:
        return clean_base_key

    counter = 2
    candidate = f"{clean_base_key}_{counter}"

    while candidate in used_keys:
        counter += 1
        candidate = f"{clean_base_key}_{counter}"

    return candidate


def _read_sidebar_sections_for_save_one_v16(session) -> list[dict[str, str]]:
    from appverbo.menu_settings import (
        MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
        normalize_sidebar_sections,
    )

    raw_menu_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": "administrativo"},
    ).scalar_one_or_none()

    try:
        menu_config = json.loads(raw_menu_config or "{}")
    except (TypeError, ValueError):
        menu_config = {}

    if not isinstance(menu_config, dict):
        menu_config = {}

    return normalize_sidebar_sections(
        menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )


@router.post("/settings/menu/sidebar-section-save", response_class=HTMLResponse)
def save_one_sidebar_section_v16(
    request: Request,
    section_mode: str = Form("create"),
    original_section_key: str = Form(""),
    section_label: str = Form(""),
    section_visibility_scope_mode: str = Form("all"),
    section_status: str = Form("ativo"),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-sidebar-sections-card"),
) -> RedirectResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar sessões do sidebar.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode alterar sessões do sidebar.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        clean_mode = _normalize_sidebar_section_text_v16(section_mode).lower()
        clean_original_key = _slugify_sidebar_section_key_v16(original_section_key)
        clean_label = _normalize_sidebar_section_text_v16(section_label)
        clean_scope = _normalize_sidebar_section_scope_v16(section_visibility_scope_mode)
        clean_status = _normalize_sidebar_section_status_v16(section_status)

        if not clean_label:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Informe o nome da sessão.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        current_sections = _read_sidebar_sections_for_save_one_v16(session)
        payload_sections: list[dict[str, str]] = []

        if clean_mode == "edit":
            found_section = False

            for section in current_sections:
                section_key = _slugify_sidebar_section_key_v16(section.get("key"))

                if section_key == clean_original_key:
                    found_section = True
                    payload_sections.append(
                        {
                            "key": section_key,
                            "label": clean_label,
                            "visibility_scope_mode": clean_scope,
                            "status": clean_status,
                        }
                    )
                else:
                    payload_sections.append(
                        {
                            "key": section_key,
                            "label": _normalize_sidebar_section_text_v16(section.get("label")),
                            "visibility_scope_mode": _normalize_sidebar_section_scope_v16(
                                section.get("visibility_scope_mode")
                            ),
                            "status": _normalize_sidebar_section_status_v16(section.get("status")),
                        }
                    )

            if not found_section:
                return RedirectResponse(
                    url=_build_settings_redirect_url(
                        error_message="Sessão não encontrada para edição.",
                        redirect_menu=redirect_menu,
                        redirect_target=redirect_target,
                        settings_edit_key="administrativo",
                        settings_action="edit",
                        settings_tab="sessoes",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
        else:
            used_keys = {
                _slugify_sidebar_section_key_v16(section.get("key"))
                for section in current_sections
            }
            new_key = _make_unique_sidebar_section_key_v16(clean_label, used_keys)

            for section in current_sections:
                payload_sections.append(
                    {
                        "key": _slugify_sidebar_section_key_v16(section.get("key")),
                        "label": _normalize_sidebar_section_text_v16(section.get("label")),
                        "visibility_scope_mode": _normalize_sidebar_section_scope_v16(
                            section.get("visibility_scope_mode")
                        ),
                        "status": _normalize_sidebar_section_status_v16(section.get("status")),
                    }
                )

            payload_sections.append(
                {
                    "key": new_key,
                    "label": clean_label,
                    "visibility_scope_mode": clean_scope,
                    "status": clean_status,
                }
            )

        ok, error_message = update_sidebar_sections_v2(
            session,
            payload_sections,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível gravar a sessão.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message=(
                    "Sessão atualizada com sucesso."
                    if clean_mode == "edit"
                    else "Sessão criada com sucesso."
                ),
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key="administrativo",
                settings_action="edit",
                settings_tab="sessoes",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

# APPVERBO_SESSOES_SAVE_ONE_V16_END
'''

if PY_MARKER_START in settings_content and PY_MARKER_END in settings_content:
    py_pattern = re.compile(
        re.escape(PY_MARKER_START) + r"[\s\S]*?" + re.escape(PY_MARKER_END),
        re.S,
    )
    settings_content = py_pattern.sub(py_block, settings_content, count=1)
else:
    anchor = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START"

    if anchor not in settings_content:
        fail_v16("não encontrei âncora APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START.")

    settings_content = settings_content.replace(anchor, py_block + "\n\n" + anchor, 1)

try:
    ast.parse(settings_content)
except SyntaxError as exc:
    fail_v16(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_content, encoding="utf-8")

print("OK: endpoint dedicado /settings/menu/sidebar-section-save criado/atualizado.")


####################################################################################
# (5) ADICIONAR JS PARA FLUXO CRIAR/EDITAR IGUAL ENTIDADE
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV16(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesV16(valor) {
    return normalizarTextoSessoesV16(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesV16(valor) {
    const cleanValor = normalizarTextoSessoesV16(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  function normalizarSistemaSessoesV16(valor) {
    const cleanValor = normalizarTextoSessoesV16(valor);

    if (["owner", "legado"].includes(cleanValor)) {
      return cleanValor;
    }

    return "all";
  }

  //###################################################################################
  // (2) DETETAR ABA SESSOES
  //###################################################################################

  function elementoVisivelSessoesV16(elemento) {
    if (!elemento) {
      return false;
    }

    if (elemento.hidden || elemento.getAttribute("aria-hidden") === "true") {
      return false;
    }

    const estilo = window.getComputedStyle(elemento);

    if (estilo.display === "none" || estilo.visibility === "hidden") {
      return false;
    }

    return Boolean(elemento.offsetWidth || elemento.offsetHeight || elemento.getClientRects().length);
  }

  function elementoAtivoSessoesV16(elemento) {
    const className = normalizarTextoSessoesV16(elemento.className || "");
    const parentClass = elemento.parentElement
      ? normalizarTextoSessoesV16(elemento.parentElement.className || "")
      : "";

    return elemento.getAttribute("aria-selected") === "true" ||
      className.includes("active") ||
      className.includes("ativo") ||
      className.includes("selected") ||
      className.includes("current") ||
      parentClass.includes("active") ||
      parentClass.includes("ativo") ||
      parentClass.includes("selected") ||
      parentClass.includes("current");
  }

  function tabAtivaPorTextoSessoesV16(textoEsperado) {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      return normalizarTextoSessoesV16(elemento.textContent) === textoEsperado &&
        elementoVisivelSessoesV16(elemento) &&
        elementoAtivoSessoesV16(elemento);
    });
  }

  function abaSessoesAtivaV16() {
    if (tabAtivaPorTextoSessoesV16("sessoes")) {
      return true;
    }

    if (
      tabAtivaPorTextoSessoesV16("entidade") ||
      tabAtivaPorTextoSessoesV16("utilizador") ||
      tabAtivaPorTextoSessoesV16("menu")
    ) {
      return false;
    }

    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card || !elementoVisivelSessoesV16(card)) {
      return false;
    }

    const textoCard = normalizarTextoSessoesV16(card.textContent);

    return textoCard.includes("sessoes do sidebar") ||
      textoCard.includes("menu lateral") ||
      Boolean(card.querySelector(".appverbo-sidebar-section-row-v10, .appverbo-sidebar-section-row-v9, .appverbo-sidebar-section-row-v6, .appverbo-sidebar-section-row-v2"));
  }

  //###################################################################################
  // (3) LER SESSOES
  //###################################################################################

  function lerSessoesTemplateV16() {
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    }
    catch (error) {
      return [];
    }
  }

  async function carregarSessoesV16() {
    try {
      const response = await fetch("/settings/menu/sidebar-sections-data", {
        headers: {
          Accept: "application/json"
        },
        credentials: "same-origin"
      });

      if (response.ok) {
        const payload = await response.json();

        if (payload && Array.isArray(payload.sections)) {
          return payload.sections;
        }
      }
    }
    catch (error) {
      console.warn("APPVERBO V16: falha ao carregar sessões do BD.", error);
    }

    return lerSessoesTemplateV16();
  }

  function normalizarSessaoV16(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesV16(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    return {
      key: key,
      label: label,
      visibility_scope_mode: normalizarSistemaSessoesV16(sessao.visibility_scope_mode || sessao.scope_mode || "all"),
      status: normalizarEstadoSessoesV16(sessao.status || (sessao.is_active === false ? "inativo" : "ativo"))
    };
  }

  async function obterSessaoPorChaveV16(chave) {
    const cleanChave = criarChaveSessoesV16(chave);
    const sessoes = await carregarSessoesV16();

    return sessoes
      .map(normalizarSessaoV16)
      .filter(Boolean)
      .find(function (sessao) {
        return criarChaveSessoesV16(sessao.key) === cleanChave;
      }) || null;
  }

  //###################################################################################
  // (4) URLS
  //###################################################################################

  function obterParametroV16(nome) {
    const params = new URLSearchParams(window.location.search);
    return params.get(nome) || "";
  }

  function urlBaseSessoesV16() {
    return "/users/new?menu=administrativo&admin_tab=sessoes&settings_edit_key=administrativo&settings_action=edit&settings_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card";
  }

  function navegarParaEditarSessaoV16(chave) {
    const cleanChave = criarChaveSessoesV16(chave);

    if (!cleanChave) {
      return;
    }

    window.location.href = "/users/new?menu=administrativo&admin_tab=sessoes&settings_edit_key=administrativo&settings_action=edit&settings_tab=sessoes&sidebar_section_edit_key=" +
      encodeURIComponent(cleanChave) +
      "&target=admin-sidebar-sections-card#admin-sidebar-sections-card";
  }

  function cancelarEdicaoSessaoV16() {
    window.location.href = urlBaseSessoesV16();
  }

  //###################################################################################
  // (5) CARD SUPERIOR CRIAR/EDITAR
  //###################################################################################

  function obterCardListaSessoesV16() {
    return document.getElementById("admin-sidebar-sections-card");
  }

  function obterOuCriarCardSuperiorSessoesV16() {
    const cardLista = obterCardListaSessoesV16();

    if (!cardLista || !cardLista.parentElement) {
      return null;
    }

    let cardSuperior = document.getElementById("admin-sidebar-sections-create-card");

    if (!cardSuperior) {
      cardSuperior = document.createElement("section");
      cardSuperior.id = "admin-sidebar-sections-create-card";
      cardLista.parentElement.insertBefore(cardSuperior, cardLista);
    }

    cardSuperior.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v16";
    cardSuperior.hidden = false;
    cardSuperior.style.display = "";
    cardSuperior.style.visibility = "";

    return cardSuperior;
  }

  function criarOpcaoV16(valor, texto, valorAtual) {
    const option = document.createElement("option");
    option.value = valor;
    option.textContent = texto;

    if (valor === valorAtual) {
      option.selected = true;
    }

    return option;
  }

  function criarCampoHiddenV16(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  function renderizarFormularioSessoesV16(cardSuperior, modo, sessao) {
    const isEdit = modo === "edit";

    cardSuperior.innerHTML = "";
    cardSuperior.dataset.appverboSessoesServerModeV16 = isEdit ? "edit" : "create";

    const container = document.createElement("div");
    container.className = "appverbo-sessoes-server-form-container-v16";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-sessoes-server-toolbar-v16";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-sessoes-server-open-btn-v16";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const formWrap = document.createElement("div");
    formWrap.className = "appverbo-sessoes-server-form-wrap-v16";
    formWrap.hidden = !isEdit;

    if (isEdit) {
      toolbar.hidden = true;
    }

    const title = document.createElement("h2");
    title.className = "appverbo-sessoes-server-form-title-v16";
    title.textContent = isEdit ? "Editar sessão" : "Criar sessão";

    const form = document.createElement("form");
    form.method = "post";
    form.action = "/settings/menu/sidebar-section-save";
    form.className = "appverbo-sessoes-server-form-v16";

    form.appendChild(criarCampoHiddenV16("section_mode", isEdit ? "edit" : "create"));
    form.appendChild(criarCampoHiddenV16("original_section_key", isEdit && sessao ? sessao.key : ""));
    form.appendChild(criarCampoHiddenV16("redirect_menu", "administrativo"));
    form.appendChild(criarCampoHiddenV16("redirect_target", "#admin-sidebar-sections-card"));

    const grid = document.createElement("div");
    grid.className = "appverbo-sessoes-server-grid-v16";

    const nomeField = document.createElement("div");
    nomeField.className = "field appverbo-sessoes-server-field-v16";

    const nomeLabel = document.createElement("label");
    nomeLabel.textContent = "Nome da sessão *";

    const nomeInput = document.createElement("input");
    nomeInput.name = "section_label";
    nomeInput.required = true;
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";
    nomeInput.value = sessao ? sessao.label : "";

    nomeField.appendChild(nomeLabel);
    nomeField.appendChild(nomeInput);

    const sistemaField = document.createElement("div");
    sistemaField.className = "field appverbo-sessoes-server-field-v16";

    const sistemaLabel = document.createElement("label");
    sistemaLabel.textContent = "Sistema *";

    const sistemaSelect = document.createElement("select");
    sistemaSelect.name = "section_visibility_scope_mode";

    const sistemaAtual = sessao ? normalizarSistemaSessoesV16(sessao.visibility_scope_mode) : "all";
    sistemaSelect.appendChild(criarOpcaoV16("all", "Owner e Legado", sistemaAtual));
    sistemaSelect.appendChild(criarOpcaoV16("owner", "Owner", sistemaAtual));
    sistemaSelect.appendChild(criarOpcaoV16("legado", "Legado", sistemaAtual));

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-sessoes-server-field-v16";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = document.createElement("select");
    estadoSelect.name = "section_status";

    const estadoAtual = sessao ? normalizarEstadoSessoesV16(sessao.status) : "ativo";
    estadoSelect.appendChild(criarOpcaoV16("ativo", "Ativo", estadoAtual));
    estadoSelect.appendChild(criarOpcaoV16("inativo", "Inativo", estadoAtual));

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const actions = document.createElement("div");
    actions.className = "appverbo-sessoes-server-actions-v16";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "submit";
    guardarBtn.className = "action-btn";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    form.appendChild(grid);
    form.appendChild(actions);

    formWrap.appendChild(title);
    formWrap.appendChild(form);

    container.appendChild(toolbar);
    container.appendChild(formWrap);
    cardSuperior.appendChild(container);

    abrirBtn.addEventListener("click", function () {
      toolbar.hidden = true;
      formWrap.hidden = false;
      nomeInput.focus();
    });

    cancelarBtn.addEventListener("click", function () {
      if (isEdit) {
        cancelarEdicaoSessaoV16();
        return;
      }

      form.reset();
      formWrap.hidden = true;
      toolbar.hidden = false;
    });

    if (isEdit) {
      window.setTimeout(function () {
        nomeInput.focus();
        nomeInput.select();
      }, 120);
    }
  }

  async function montarCardSuperiorSessoesV16() {
    if (!abaSessoesAtivaV16()) {
      return;
    }

    const cardSuperior = obterOuCriarCardSuperiorSessoesV16();

    if (!cardSuperior) {
      return;
    }

    const editKey = obterParametroV16("sidebar_section_edit_key");

    if (editKey) {
      const sessao = await obterSessaoPorChaveV16(editKey);

      if (sessao) {
        renderizarFormularioSessoesV16(cardSuperior, "edit", sessao);
        return;
      }
    }

    renderizarFormularioSessoesV16(cardSuperior, "create", null);
  }

  //###################################################################################
  // (6) CAPTURAR EDITAR E TROCAR INLINE POR NAVEGACAO
  //###################################################################################

  function obterChaveDaLinhaSessoesV16(linha) {
    if (!linha) {
      return "";
    }

    const datasetKey = linha.dataset.sectionKeyV10 ||
      linha.dataset.sectionKeyV9 ||
      linha.dataset.sectionKeyV6 ||
      linha.dataset.sectionKeyV2 ||
      "";

    if (datasetKey) {
      return criarChaveSessoesV16(datasetKey);
    }

    const hiddenKey = linha.querySelector('[name="section_key"]');

    if (hiddenKey && hiddenKey.value) {
      return criarChaveSessoesV16(hiddenKey.value);
    }

    const primeiraCelula = linha.querySelector("td");

    return primeiraCelula ? criarChaveSessoesV16(primeiraCelula.textContent) : "";
  }

  function instalarCapturaEditarSessoesV16() {
    if (window.__appverboSessoesEditServerCaptureV16 === true) {
      return;
    }

    window.__appverboSessoesEditServerCaptureV16 = true;

    document.addEventListener("click", function (event) {
      const botaoEditar = event.target.closest(
        '[data-sidebar-section-action-v10="edit"], ' +
        '[data-sidebar-section-action-v9="edit"], ' +
        '[data-sidebar-section-action-v6="edit"], ' +
        '[data-sidebar-section-action="edit"]'
      );

      if (!botaoEditar) {
        return;
      }

      if (!abaSessoesAtivaV16()) {
        return;
      }

      const linha = botaoEditar.closest("tr");
      const chave = obterChaveDaLinhaSessoesV16(linha);

      if (!chave) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();

      navegarParaEditarSessaoV16(chave);
    }, true);
  }

  //###################################################################################
  // (7) OBSERVAR NAVEGACAO ENTRE ABAS
  //###################################################################################

  function agendarMontagemSessoesV16() {
    window.setTimeout(montarCardSuperiorSessoesV16, 80);
    window.setTimeout(montarCardSuperiorSessoesV16, 250);
    window.setTimeout(montarCardSuperiorSessoesV16, 600);
    window.setTimeout(montarCardSuperiorSessoesV16, 1200);
  }

  function instalarFluxoSessoesV16() {
    instalarCapturaEditarSessoesV16();

    document.addEventListener("click", function () {
      agendarMontagemSessoesV16();
    });

    window.addEventListener("hashchange", agendarMontagemSessoesV16);
    window.addEventListener("popstate", agendarMontagemSessoesV16);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesServerModeTimerV16);

      window.__appverboSessoesServerModeTimerV16 = window.setTimeout(function () {
        if (abaSessoesAtivaV16()) {
          const cardSuperior = document.getElementById("admin-sidebar-sections-create-card");

          if (!cardSuperior || !cardSuperior.dataset.appverboSessoesServerModeV16) {
            montarCardSuperiorSessoesV16();
          }
        }
      }, 150);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "hidden", "style", "aria-selected", "aria-hidden"]
    });

    agendarMontagemSessoesV16();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarFluxoSessoesV16);
  }
  else {
    instalarFluxoSessoesV16();
  }
})();
// APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_END
'''

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    js_pattern = re.compile(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END),
        re.S,
    )
    js_content = js_pattern.sub(js_block, js_content, count=1)
else:
    js_content = js_content.rstrip() + "\n\n" + js_block + "\n"

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS V16 aplicado para Editar Sessão por navegação/reload e formulário dedicado.")


####################################################################################
# (6) ADICIONAR CSS V16
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-sessoes-create-card-v16 {{
  display: block !important;
  visibility: visible !important;
  min-height: 64px !important;
  margin-bottom: 12px !important;
  padding: 16px !important;
  border: 1px solid #d5dceb !important;
  border-radius: 8px !important;
  background: #f3f6fb !important;
  box-sizing: border-box !important;
}}

.appverbo-sessoes-server-form-container-v16 {{
  width: 100%;
}}

.appverbo-sessoes-server-toolbar-v16 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
}}

.appverbo-sessoes-server-toolbar-v16[hidden],
.appverbo-sessoes-server-form-wrap-v16[hidden] {{
  display: none !important;
}}

.appverbo-sessoes-server-form-title-v16 {{
  margin: 0 0 14px !important;
  color: #12213a !important;
  font-size: 20px !important;
  font-weight: 800 !important;
}}

.appverbo-sessoes-server-grid-v16 {{
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px);
  gap: 12px;
  align-items: end;
  width: 100%;
  padding-top: 12px;
  border-top: 1px solid #d5dceb;
}}

.appverbo-sessoes-server-field-v16 label {{
  display: block;
  margin-bottom: 6px;
  color: #12213a;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}}

.appverbo-sessoes-server-field-v16 input,
.appverbo-sessoes-server-field-v16 select {{
  width: 100%;
  min-height: 38px;
  border: 1px solid #c6d0e2;
  border-radius: 7px;
  background: #ffffff;
  color: #12213a;
  padding: 8px 10px;
  box-sizing: border-box;
  font-size: 13px;
}}

.appverbo-sessoes-server-field-v16 input:focus,
.appverbo-sessoes-server-field-v16 select:focus {{
  border-color: #2454b0;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}}

.appverbo-sessoes-server-actions-v16 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}}

.appverbo-sessoes-server-actions-v16 .action-btn,
.appverbo-sessoes-server-actions-v16 .action-btn-cancel {{
  min-width: 112px !important;
  width: 112px !important;
  height: 38px !important;
  min-height: 38px !important;
}}

@media (max-width: 1100px) {{
  .appverbo-sessoes-server-grid-v16 {{
    grid-template-columns: 1fr;
  }}
}}

{CSS_MARKER_END}'''

if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
    css_pattern = re.compile(
        re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
        re.S,
    )
    css_content = css_pattern.sub(css_block, css_content, count=1)
else:
    css_content = css_content.rstrip() + "\n\n" + css_block + "\n"

CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS V16 aplicado.")


####################################################################################
# (7) ATUALIZAR CACHE BUSTER
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v16("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v16("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado.")


####################################################################################
# (8) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
settings_validado = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START": agents_validado,
    "APPVERBO_SESSOES_SAVE_ONE_V16_START": settings_validado,
    "/settings/menu/sidebar-section-save": settings_validado,
    "save_one_sidebar_section_v16": settings_validado,
    "APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START": js_validado,
    "navegarParaEditarSessaoV16": js_validado,
    "sidebar_section_edit_key": js_validado,
    "/settings/menu/sidebar-section-save": js_validado,
    "APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START": css_validado,
    "appverbo-sessoes-create-card-v16": css_validado,
    "20260505-sessoes-fluxo-entidade-v16": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v16(f"validação falhou, termo ausente: {termo}")

try:
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v16(f"Python final inválido: {exc}")

print("OK: patch_sessoes_fluxo_igual_entidade_v16 concluído.")
