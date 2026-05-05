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

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END -->"

PY_MARKER_START = "# APPVERBO_SESSOES_SAVE_ONE_V18_START"
PY_MARKER_END = "# APPVERBO_SESSOES_SAVE_ONE_V18_END"

JS_MARKER_START = "// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START"
JS_MARKER_END = "// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-padrao-entidade-v18"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-padrao-entidade-v18"


def fail_v18(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v18() -> Path:
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
        fail_v18(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v18()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra definitiva do subprocesso Sessões no padrão Entidade

O subprocesso **Sessões** deve seguir o mesmo padrão funcional do subprocesso **Entidade**.

Regras:

1. O botão **Editar** da linha não deve editar inline.
2. Ao clicar em **Editar**, a página deve navegar/recarregar para a mesma aba **Sessões** com o parâmetro `sidebar_section_edit_key`.
3. Depois do reload, o bloco superior deve abrir em modo **Editar sessão**, com os campos preenchidos.
4. Os campos editáveis são:
   - **Nome da sessão**;
   - **Sistema**;
   - **Estado**.
5. O botão **Guardar** deve enviar um formulário dedicado para o backend.
6. O botão **Cancelar** deve remover o modo edição e voltar para a lista da aba **Sessões**.
7. O botão **Criar sessão** permanece no mesmo bloco superior, quando não houver sessão em edição.
8. O endpoint dedicado deve gravar somente a sessão criada/editada, preservando as demais sessões existentes.
9. Não usar `settings_edit_key`, `settings_action` ou `settings_tab` para editar Sessões, pois esses parâmetros pertencem ao fluxo do subprocesso Menu.
10. A listagem de ativos e o card de **Sessões inativas** continuam separados.
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

print(f"OK: regra definitiva V18 atualizada em {agents_path}")


####################################################################################
# (4) REFATORAR BACKEND: ENDPOINT DEDICADO CRIAR/EDITAR UMA SESSAO
####################################################################################

settings_content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

py_block = r'''# APPVERBO_SESSOES_SAVE_ONE_V18_START

# ###################################################################################
# (SIDEBAR_SECTION_SAVE_ONE_V18) CRIAR/EDITAR SESSAO NO PADRAO ENTIDADE
# ###################################################################################

def _normalize_sidebar_section_text_v18(value: object) -> str:
    return str(value or "").strip()


def _slugify_sidebar_section_key_v18(value: object) -> str:
    import re
    import unicodedata

    raw_value = _normalize_sidebar_section_text_v18(value).lower()
    raw_value = unicodedata.normalize("NFD", raw_value)
    raw_value = "".join(char for char in raw_value if unicodedata.category(char) != "Mn")
    raw_value = re.sub(r"[^a-z0-9]+", "_", raw_value)
    raw_value = re.sub(r"_+", "_", raw_value).strip("_")
    return raw_value or "nova_sessao"


def _normalize_sidebar_section_status_v18(value: object) -> str:
    clean_value = _normalize_sidebar_section_text_v18(value).lower()

    if clean_value in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def _normalize_sidebar_section_scope_v18(value: object) -> str:
    clean_value = _normalize_sidebar_section_text_v18(value).lower()

    if clean_value in {"owner", "legado"}:
        return clean_value

    return "all"


def _sanitize_sidebar_section_return_url_v18(return_url: object) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    fallback = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
    raw_url = _normalize_sidebar_section_text_v18(return_url)

    if not raw_url:
        raw_url = fallback

    if raw_url.startswith("http://") or raw_url.startswith("https://") or raw_url.startswith("//"):
        raw_url = fallback

    if not raw_url.startswith("/users/new"):
        raw_url = fallback

    parts = urlsplit(raw_url)
    clean_params = []

    blocked_params = {
        "settings_edit_key",
        "settings_action",
        "settings_tab",
        "sidebar_section_edit_key",
        "sidebar_section_return_url",
        "success",
        "error",
    }

    found_menu = False
    found_admin_tab = False
    found_sidebar_tab = False
    found_target = False

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key in blocked_params:
            continue

        if key == "menu":
            found_menu = True
            clean_params.append(("menu", "administrativo"))
            continue

        if key == "admin_tab":
            found_admin_tab = True
            clean_params.append(("admin_tab", "sessoes"))
            continue

        if key == "sidebar_sections_tab":
            found_sidebar_tab = True
            clean_params.append(("sidebar_sections_tab", "sessoes"))
            continue

        if key == "target":
            found_target = True
            clean_params.append(("target", "admin-sidebar-sections-card"))
            continue

        clean_params.append((key, value))

    if not found_menu:
        clean_params.append(("menu", "administrativo"))

    if not found_admin_tab:
        clean_params.append(("admin_tab", "sessoes"))

    if not found_sidebar_tab:
        clean_params.append(("sidebar_sections_tab", "sessoes"))

    if not found_target:
        clean_params.append(("target", "admin-sidebar-sections-card"))

    clean_query = urlencode(clean_params)
    return urlunsplit(("", "", "/users/new", clean_query, "admin-sidebar-sections-card"))


def _append_sidebar_section_message_v18(return_url: str, message_key: str, message: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    parts = urlsplit(return_url)
    params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {"success", "error"}
    ]
    params.append((message_key, message))

    return urlunsplit(("", "", parts.path or "/users/new", urlencode(params), parts.fragment or "admin-sidebar-sections-card"))


def _make_unique_sidebar_section_key_v18(base_key: str, used_keys: set[str]) -> str:
    clean_base_key = _slugify_sidebar_section_key_v18(base_key)

    if clean_base_key not in used_keys:
        return clean_base_key

    counter = 2
    candidate = f"{clean_base_key}_{counter}"

    while candidate in used_keys:
        counter += 1
        candidate = f"{clean_base_key}_{counter}"

    return candidate


def _read_sidebar_sections_for_save_one_v18(session) -> list[dict[str, str]]:
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


def _redirect_sidebar_section_message_v18(
    return_url: str,
    message_key: str,
    message: str,
) -> RedirectResponse:
    safe_return_url = _sanitize_sidebar_section_return_url_v18(return_url)
    return RedirectResponse(
        url=_append_sidebar_section_message_v18(safe_return_url, message_key, message),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/settings/menu/sidebar-section-save", response_class=HTMLResponse)
def save_one_sidebar_section_v18(
    request: Request,
    section_mode: str = Form("create"),
    original_section_key: str = Form(""),
    section_label: str = Form(""),
    section_visibility_scope_mode: str = Form("all"),
    section_status: str = Form("ativo"),
    sidebar_section_return_url: str = Form(""),
) -> RedirectResponse:
    safe_return_url = _sanitize_sidebar_section_return_url_v18(sidebar_section_return_url)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return _redirect_sidebar_section_message_v18(
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
            return _redirect_sidebar_section_message_v18(
                safe_return_url,
                "error",
                "Apenas Owner pode alterar sessões do sidebar.",
            )

        clean_mode = _normalize_sidebar_section_text_v18(section_mode).lower()
        clean_original_key = _slugify_sidebar_section_key_v18(original_section_key)
        clean_label = _normalize_sidebar_section_text_v18(section_label)
        clean_scope = _normalize_sidebar_section_scope_v18(section_visibility_scope_mode)
        clean_status = _normalize_sidebar_section_status_v18(section_status)

        if not clean_label:
            return _redirect_sidebar_section_message_v18(
                safe_return_url,
                "error",
                "Informe o nome da sessão.",
            )

        current_sections = _read_sidebar_sections_for_save_one_v18(session)
        payload_sections: list[dict[str, str]] = []

        if clean_mode == "edit":
            found_section = False

            for section in current_sections:
                section_key = _slugify_sidebar_section_key_v18(section.get("key"))

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
                            "label": _normalize_sidebar_section_text_v18(section.get("label")),
                            "visibility_scope_mode": _normalize_sidebar_section_scope_v18(
                                section.get("visibility_scope_mode")
                            ),
                            "status": _normalize_sidebar_section_status_v18(section.get("status")),
                        }
                    )

            if not found_section:
                return _redirect_sidebar_section_message_v18(
                    safe_return_url,
                    "error",
                    "Sessão não encontrada para edição.",
                )
        else:
            used_keys = {
                _slugify_sidebar_section_key_v18(section.get("key"))
                for section in current_sections
            }
            new_key = _make_unique_sidebar_section_key_v18(clean_label, used_keys)

            for section in current_sections:
                payload_sections.append(
                    {
                        "key": _slugify_sidebar_section_key_v18(section.get("key")),
                        "label": _normalize_sidebar_section_text_v18(section.get("label")),
                        "visibility_scope_mode": _normalize_sidebar_section_scope_v18(
                            section.get("visibility_scope_mode")
                        ),
                        "status": _normalize_sidebar_section_status_v18(section.get("status")),
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
            return _redirect_sidebar_section_message_v18(
                safe_return_url,
                "error",
                error_message or "Não foi possível gravar a sessão.",
            )

        return _redirect_sidebar_section_message_v18(
            safe_return_url,
            "success",
            (
                "Sessão atualizada com sucesso."
                if clean_mode == "edit"
                else "Sessão criada com sucesso."
            ),
        )

# APPVERBO_SESSOES_SAVE_ONE_V18_END
'''

old_endpoint_markers = [
    ("# APPVERBO_SESSOES_SAVE_ONE_V16_START", "# APPVERBO_SESSOES_SAVE_ONE_V16_END"),
    ("# APPVERBO_SESSOES_SAVE_ONE_V18_START", "# APPVERBO_SESSOES_SAVE_ONE_V18_END"),
]

replaced_backend = False

for start_marker, end_marker in old_endpoint_markers:
    if start_marker in settings_content and end_marker in settings_content:
        pattern = re.compile(
            re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
            re.S,
        )
        settings_content = pattern.sub(py_block, settings_content, count=1)
        replaced_backend = True
        break

if not replaced_backend:
    anchor = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START"

    if anchor not in settings_content:
        fail_v18("não encontrei APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START para inserir endpoint V18.")

    settings_content = settings_content.replace(anchor, py_block + "\n\n" + anchor, 1)

try:
    ast.parse(settings_content)
except SyntaxError as exc:
    fail_v18(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_content, encoding="utf-8")

print("OK: endpoint dedicado V18 criado/atualizado sem usar fluxo do Menu.")


####################################################################################
# (5) REFATORAR JAVASCRIPT: DESATIVAR FLUXOS CONFLITANTES E INSTALAR V18
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

def disable_js_block_v18(content: str, start_marker: str, end_marker: str, reason: str) -> str:
    if start_marker not in content or end_marker not in content:
        return content

    replacement = f"""{start_marker}
// Desativado pela refatoração V18.
// Motivo: {reason}
{end_marker}"""

    pattern = re.compile(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        re.S,
    )
    return pattern.sub(replacement, content, count=1)


js_content = disable_js_block_v18(
    js_content,
    "// APPVERBO_SESSOES_RELOAD_ON_TAB_RETURN_V13_START",
    "// APPVERBO_SESSOES_RELOAD_ON_TAB_RETURN_V13_END",
    "V18 controla a recriação do bloco superior ao retornar para a aba Sessões."
)

js_content = disable_js_block_v18(
    js_content,
    "// APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START",
    "// APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_END",
    "V18 controla o card Criar/Editar sessão no padrão Entidade."
)

js_content = disable_js_block_v18(
    js_content,
    "// APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START",
    "// APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_END",
    "V16 criava conflito de URL com o subprocesso Menu."
)

js_content = disable_js_block_v18(
    js_content,
    "// APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START",
    "// APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_END",
    "V17 era apenas interceptador; V18 passa a ser o controlador único do fluxo."
)

js_block = r'''// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV18(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesV18(valor) {
    return normalizarTextoSessoesV18(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesV18(valor) {
    const cleanValor = normalizarTextoSessoesV18(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  function normalizarSistemaSessoesV18(valor) {
    const cleanValor = normalizarTextoSessoesV18(valor);

    if (["owner", "legado"].includes(cleanValor)) {
      return cleanValor;
    }

    return "all";
  }

  //###################################################################################
  // (2) URL DA ABA SESSOES SEM PARAMETROS DO MENU
  //###################################################################################

  function limparParametrosMenuSessoesV18(url) {
    url.searchParams.delete("settings_edit_key");
    url.searchParams.delete("settings_action");
    url.searchParams.delete("settings_tab");
    url.searchParams.delete("sidebar_section_return_url");
    url.searchParams.delete("success");
    url.searchParams.delete("error");
    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.hash = "admin-sidebar-sections-card";
    return url;
  }

  function obterUrlBaseSessaoV18() {
    const url = new URL(window.location.href);
    limparParametrosMenuSessoesV18(url);
    return url;
  }

  function obterUrlRetornoSessaoV18() {
    const url = obterUrlBaseSessaoV18();
    url.searchParams.delete("sidebar_section_edit_key");
    return url.pathname + url.search + url.hash;
  }

  function obterEditKeySessaoV18() {
    const url = new URL(window.location.href);
    return criarChaveSessoesV18(url.searchParams.get("sidebar_section_edit_key") || "");
  }

  function navegarEditarSessaoV18(chave) {
    const cleanChave = criarChaveSessoesV18(chave);

    if (!cleanChave) {
      return;
    }

    const url = obterUrlBaseSessaoV18();
    url.searchParams.set("sidebar_section_edit_key", cleanChave);
    window.location.href = url.pathname + url.search + url.hash;
  }

  function cancelarEdicaoSessaoV18() {
    window.location.href = obterUrlRetornoSessaoV18();
  }

  //###################################################################################
  // (3) DETETAR E FORCAR ABA SESSOES
  //###################################################################################

  function elementoVisivelSessoesV18(elemento) {
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

  function elementoAtivoSessoesV18(elemento) {
    const className = normalizarTextoSessoesV18(elemento.className || "");
    const parentClass = elemento.parentElement
      ? normalizarTextoSessoesV18(elemento.parentElement.className || "")
      : "";

    return elemento.getAttribute("aria-selected") === "true" ||
      className.includes("active") ||
      className.includes("ativo") ||
      className.includes("selected") ||
      className.includes("current") ||
      className.includes("is-active") ||
      parentClass.includes("active") ||
      parentClass.includes("ativo") ||
      parentClass.includes("selected") ||
      parentClass.includes("current") ||
      parentClass.includes("is-active");
  }

  function encontrarTabPorTextoSessoesV18(textoEsperado) {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.find(function (elemento) {
      return normalizarTextoSessoesV18(elemento.textContent) === textoEsperado &&
        elementoVisivelSessoesV18(elemento);
    }) || null;
  }

  function tabAtivaPorTextoSessoesV18(textoEsperado) {
    const tab = encontrarTabPorTextoSessoesV18(textoEsperado);
    return Boolean(tab && elementoAtivoSessoesV18(tab));
  }

  function outraAbaAdministrativaAtivaSessoesV18() {
    return ["entidade", "utilizador", "menu"].some(function (texto) {
      return tabAtivaPorTextoSessoesV18(texto);
    });
  }

  function cardListaSessoesVisivelV18() {
    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card || !elementoVisivelSessoesV18(card)) {
      return false;
    }

    const textoCard = normalizarTextoSessoesV18(card.textContent);

    return textoCard.includes("sessoes do sidebar") ||
      textoCard.includes("menu lateral") ||
      Boolean(card.querySelector(".appverbo-sidebar-section-row-v10, .appverbo-sidebar-section-row-v9, .appverbo-sidebar-section-row-v6, .appverbo-sidebar-section-row-v2"));
  }

  function deveForcarAbaSessoesV18() {
    const url = new URL(window.location.href);
    return Boolean(
      url.searchParams.get("sidebar_section_edit_key") ||
      url.searchParams.get("sidebar_sections_tab") === "sessoes" ||
      url.searchParams.get("admin_tab") === "sessoes"
    );
  }

  function abaSessoesAtivaV18() {
    if (tabAtivaPorTextoSessoesV18("sessoes")) {
      return true;
    }

    if (outraAbaAdministrativaAtivaSessoesV18()) {
      return false;
    }

    if (deveForcarAbaSessoesV18()) {
      return true;
    }

    return cardListaSessoesVisivelV18();
  }

  function forcarAbaSessoesV18() {
    if (!deveForcarAbaSessoesV18()) {
      return;
    }

    const tabSessoes = encontrarTabPorTextoSessoesV18("sessoes");

    if (tabSessoes && !elementoAtivoSessoesV18(tabSessoes)) {
      tabSessoes.click();
    }

    document.body.classList.add("appverbo-admin-sessoes-active-v18");
    document.body.classList.remove("appverbo-admin-sessoes-inactive-v18");
  }

  //###################################################################################
  // (4) LER SESSOES DO BD/TEMPLATE
  //###################################################################################

  function lerSessoesTemplateV18() {
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

  async function carregarSessoesV18() {
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
      console.warn("APPVERBO V18: falha ao carregar sessões do BD.", error);
    }

    return lerSessoesTemplateV18();
  }

  function normalizarSessaoV18(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesV18(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    return {
      key: key,
      label: label,
      visibility_scope_mode: normalizarSistemaSessoesV18(sessao.visibility_scope_mode || sessao.scope_mode || "all"),
      status: normalizarEstadoSessoesV18(sessao.status || (sessao.is_active === false ? "inativo" : "ativo"))
    };
  }

  async function obterSessaoPorChaveV18(chave) {
    const cleanChave = criarChaveSessoesV18(chave);
    const sessoes = await carregarSessoesV18();

    return sessoes
      .map(normalizarSessaoV18)
      .filter(Boolean)
      .find(function (sessao) {
        return criarChaveSessoesV18(sessao.key) === cleanChave;
      }) || null;
  }

  //###################################################################################
  // (5) CARD SUPERIOR PADRAO ENTIDADE
  //###################################################################################

  function obterCardListaSessoesV18() {
    return document.getElementById("admin-sidebar-sections-card");
  }

  function obterOuCriarCardSuperiorSessoesV18() {
    const cardLista = obterCardListaSessoesV18();

    if (!cardLista || !cardLista.parentElement) {
      return null;
    }

    let cardSuperior = document.getElementById("admin-sidebar-sections-create-card");

    if (!cardSuperior) {
      cardSuperior = document.createElement("section");
      cardSuperior.id = "admin-sidebar-sections-create-card";
      cardLista.parentElement.insertBefore(cardSuperior, cardLista);
    }
    else if (cardSuperior.parentElement !== cardLista.parentElement) {
      cardLista.parentElement.insertBefore(cardSuperior, cardLista);
    }

    cardSuperior.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v18";
    cardSuperior.hidden = false;
    cardSuperior.style.display = "";
    cardSuperior.style.visibility = "";

    return cardSuperior;
  }

  function criarCampoHiddenV18(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  function criarOpcaoV18(valor, texto, valorAtual) {
    const option = document.createElement("option");
    option.value = valor;
    option.textContent = texto;

    if (valor === valorAtual) {
      option.selected = true;
    }

    return option;
  }

  function renderizarFormularioSuperiorSessoesV18(cardSuperior, modo, sessao) {
    const isEdit = modo === "edit";
    const editKey = isEdit && sessao ? sessao.key : "";

    if (
      cardSuperior.dataset.appverboSessoesModeV18 === modo &&
      cardSuperior.dataset.appverboSessoesKeyV18 === editKey &&
      cardSuperior.querySelector(".appverbo-sessoes-form-wrapper-v18")
    ) {
      return;
    }

    cardSuperior.dataset.appverboSessoesModeV18 = modo;
    cardSuperior.dataset.appverboSessoesKeyV18 = editKey;
    cardSuperior.innerHTML = "";

    const container = document.createElement("div");
    container.className = "appverbo-sessoes-form-wrapper-v18";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-sessoes-toolbar-v18";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-sessoes-open-create-v18";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appverbo-sessoes-panel-v18";
    panel.hidden = !isEdit;

    if (isEdit) {
      toolbar.hidden = true;
    }

    const title = document.createElement("h2");
    title.className = "appverbo-sessoes-form-title-v18";
    title.textContent = isEdit ? "Editar sessão" : "Criar sessão";

    const form = document.createElement("form");
    form.method = "post";
    form.action = "/settings/menu/sidebar-section-save";
    form.className = "appverbo-sessoes-form-v18";

    form.appendChild(criarCampoHiddenV18("section_mode", isEdit ? "edit" : "create"));
    form.appendChild(criarCampoHiddenV18("original_section_key", isEdit && sessao ? sessao.key : ""));
    form.appendChild(criarCampoHiddenV18("sidebar_section_return_url", obterUrlRetornoSessaoV18()));

    const grid = document.createElement("div");
    grid.className = "appverbo-sessoes-grid-v18";

    const nomeField = document.createElement("div");
    nomeField.className = "field appverbo-sessoes-field-v18";

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
    sistemaField.className = "field appverbo-sessoes-field-v18";

    const sistemaLabel = document.createElement("label");
    sistemaLabel.textContent = "Sistema *";

    const sistemaSelect = document.createElement("select");
    sistemaSelect.name = "section_visibility_scope_mode";

    const sistemaAtual = sessao ? normalizarSistemaSessoesV18(sessao.visibility_scope_mode) : "all";
    sistemaSelect.appendChild(criarOpcaoV18("all", "Owner e Legado", sistemaAtual));
    sistemaSelect.appendChild(criarOpcaoV18("owner", "Owner", sistemaAtual));
    sistemaSelect.appendChild(criarOpcaoV18("legado", "Legado", sistemaAtual));

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-sessoes-field-v18";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = document.createElement("select");
    estadoSelect.name = "section_status";

    const estadoAtual = sessao ? normalizarEstadoSessoesV18(sessao.status) : "ativo";
    estadoSelect.appendChild(criarOpcaoV18("ativo", "Ativo", estadoAtual));
    estadoSelect.appendChild(criarOpcaoV18("inativo", "Inativo", estadoAtual));

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const actions = document.createElement("div");
    actions.className = "appverbo-sessoes-actions-v18";

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

    panel.appendChild(title);
    panel.appendChild(form);

    container.appendChild(toolbar);
    container.appendChild(panel);
    cardSuperior.appendChild(container);

    abrirBtn.addEventListener("click", function () {
      toolbar.hidden = true;
      panel.hidden = false;
      nomeInput.focus();
    });

    cancelarBtn.addEventListener("click", function () {
      if (isEdit) {
        cancelarEdicaoSessaoV18();
        return;
      }

      form.reset();
      panel.hidden = true;
      toolbar.hidden = false;
    });

    form.addEventListener("submit", function () {
      const returnInput = form.querySelector('[name="sidebar_section_return_url"]');

      if (returnInput) {
        returnInput.value = obterUrlRetornoSessaoV18();
      }
    });

    if (isEdit) {
      window.setTimeout(function () {
        nomeInput.focus();
        nomeInput.select();
      }, 120);
    }
  }

  async function montarCardSuperiorSessoesV18() {
    forcarAbaSessoesV18();

    if (!abaSessoesAtivaV18()) {
      document.body.classList.remove("appverbo-admin-sessoes-active-v18");
      document.body.classList.add("appverbo-admin-sessoes-inactive-v18");
      return;
    }

    document.body.classList.add("appverbo-admin-sessoes-active-v18");
    document.body.classList.remove("appverbo-admin-sessoes-inactive-v18");

    const cardSuperior = obterOuCriarCardSuperiorSessoesV18();

    if (!cardSuperior) {
      return;
    }

    const editKey = obterEditKeySessaoV18();

    if (editKey) {
      const sessao = await obterSessaoPorChaveV18(editKey);

      if (sessao) {
        renderizarFormularioSuperiorSessoesV18(cardSuperior, "edit", sessao);
        return;
      }
    }

    renderizarFormularioSuperiorSessoesV18(cardSuperior, "create", null);
  }

  //###################################################################################
  // (6) CAPTURAR EDITAR E IMPEDIR INLINE
  //###################################################################################

  function obterChaveLinhaSessoesV18(linha) {
    if (!linha) {
      return "";
    }

    const datasetKey = linha.dataset.sectionKeyV10 ||
      linha.dataset.sectionKeyV9 ||
      linha.dataset.sectionKeyV6 ||
      linha.dataset.sectionKeyV2 ||
      "";

    if (datasetKey) {
      return criarChaveSessoesV18(datasetKey);
    }

    const hiddenKey = linha.querySelector('[name="section_key"]');

    if (hiddenKey && hiddenKey.value) {
      return criarChaveSessoesV18(hiddenKey.value);
    }

    const primeiraCelula = linha.querySelector("td");

    return primeiraCelula ? criarChaveSessoesV18(primeiraCelula.textContent) : "";
  }

  function encontrarBotaoEditarSessoesV18(target) {
    if (!target || !target.closest) {
      return null;
    }

    const explicitButton = target.closest(
      '[data-sidebar-section-action-v10="edit"], ' +
      '[data-sidebar-section-action-v9="edit"], ' +
      '[data-sidebar-section-action-v6="edit"], ' +
      '[data-sidebar-section-action-v2="edit"], ' +
      '[data-sidebar-section-action="edit"]'
    );

    if (explicitButton) {
      return explicitButton;
    }

    const possibleButton = target.closest("button, a");

    if (!possibleButton) {
      return null;
    }

    const label = normalizarTextoSessoesV18(
      possibleButton.getAttribute("title") ||
      possibleButton.getAttribute("aria-label") ||
      possibleButton.textContent ||
      ""
    );

    if (label.includes("editar") || label === "✎") {
      return possibleButton;
    }

    return null;
  }

  function instalarCapturaEditarSessoesV18() {
    if (window.__appverboSessoesEditCaptureV18 === true) {
      return;
    }

    window.__appverboSessoesEditCaptureV18 = true;

    document.addEventListener("click", function (event) {
      const botaoEditar = encontrarBotaoEditarSessoesV18(event.target);

      if (!botaoEditar) {
        return;
      }

      const card = botaoEditar.closest("#admin-sidebar-sections-card, #admin-sidebar-sections-inactive-card");

      if (!card) {
        return;
      }

      const linha = botaoEditar.closest("tr");
      const chave = obterChaveLinhaSessoesV18(linha);

      if (!chave) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();

      navegarEditarSessaoV18(chave);
    }, true);
  }

  //###################################################################################
  // (7) INSTALAR OBSERVADORES
  //###################################################################################

  function agendarMontagemSessoesV18() {
    window.setTimeout(montarCardSuperiorSessoesV18, 80);
    window.setTimeout(montarCardSuperiorSessoesV18, 250);
    window.setTimeout(montarCardSuperiorSessoesV18, 600);
    window.setTimeout(montarCardSuperiorSessoesV18, 1200);
  }

  function instalarSessoesPadraoEntidadeV18() {
    instalarCapturaEditarSessoesV18();

    document.addEventListener("click", function () {
      agendarMontagemSessoesV18();
    });

    window.addEventListener("hashchange", agendarMontagemSessoesV18);
    window.addEventListener("popstate", agendarMontagemSessoesV18);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesPadraoEntidadeTimerV18);

      window.__appverboSessoesPadraoEntidadeTimerV18 = window.setTimeout(function () {
        if (abaSessoesAtivaV18() || deveForcarAbaSessoesV18()) {
          montarCardSuperiorSessoesV18();
        }
      }, 140);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "hidden", "style", "aria-selected", "aria-hidden"]
    });

    agendarMontagemSessoesV18();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarSessoesPadraoEntidadeV18);
  }
  else {
    instalarSessoesPadraoEntidadeV18();
  }
})();
// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END
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

print("OK: JS V18 instalado como controlador único do fluxo Criar/Editar sessão.")


####################################################################################
# (6) CSS V18 DO CARD SUPERIOR PADRAO ENTIDADE
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-sessoes-create-card-v18 {{
  display: block !important;
  visibility: visible !important;
  width: 100% !important;
  min-height: 64px !important;
  margin: 0 0 12px !important;
  padding: 16px !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  background: #f3f6fb !important;
  box-sizing: border-box !important;
}}

body.appverbo-admin-sessoes-inactive-v18 #admin-sidebar-sections-create-card {{
  display: none !important;
}}

body.appverbo-admin-sessoes-active-v18 #admin-sidebar-sections-create-card.appverbo-sessoes-create-card-v18 {{
  display: block !important;
  visibility: visible !important;
}}

.appverbo-sessoes-form-wrapper-v18 {{
  width: 100%;
}}

.appverbo-sessoes-toolbar-v18 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  min-height: 32px;
}}

.appverbo-sessoes-toolbar-v18[hidden],
.appverbo-sessoes-panel-v18[hidden] {{
  display: none !important;
}}

.appverbo-sessoes-form-title-v18 {{
  margin: 0 0 14px !important;
  color: #12213a !important;
  font-size: 20px !important;
  font-weight: 800 !important;
}}

.appverbo-sessoes-grid-v18 {{
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px);
  gap: 12px;
  align-items: end;
  width: 100%;
}}

.appverbo-sessoes-field-v18 label {{
  display: block;
  margin-bottom: 6px;
  color: #12213a;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}}

.appverbo-sessoes-field-v18 input,
.appverbo-sessoes-field-v18 select {{
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

.appverbo-sessoes-field-v18 input:focus,
.appverbo-sessoes-field-v18 select:focus {{
  border-color: #2454b0;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}}

.appverbo-sessoes-actions-v18 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}}

.appverbo-sessoes-actions-v18 .action-btn,
.appverbo-sessoes-actions-v18 .action-btn-cancel {{
  min-width: 112px !important;
  width: 112px !important;
  height: 38px !important;
  min-height: 38px !important;
}}

@media (max-width: 1100px) {{
  .appverbo-sessoes-grid-v18 {{
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

print("OK: CSS V18 aplicado.")


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
    fail_v18("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v18("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START": agents_validado,
    "APPVERBO_SESSOES_SAVE_ONE_V18_START": settings_validado,
    "save_one_sidebar_section_v18": settings_validado,
    "_sanitize_sidebar_section_return_url_v18": settings_validado,
    "APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START": js_validado,
    "navegarEditarSessaoV18": js_validado,
    "sidebar_section_edit_key": js_validado,
    "/settings/menu/sidebar-section-save": js_validado,
    "APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START": css_validado,
    "appverbo-sessoes-create-card-v18": css_validado,
    "20260505-sessoes-padrao-entidade-v18": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v18(f"validação falhou, termo ausente: {termo}")

if "APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START\n// Desativado pela refatoração V18." not in js_validado:
    print("AVISO: bloco V16 não encontrado/desativado; pode não existir neste ambiente.")

if "APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START\n// Desativado pela refatoração V18." not in js_validado:
    print("AVISO: bloco V17 não encontrado/desativado; pode não existir neste ambiente.")

try:
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v18(f"Python final inválido: {exc}")

print("OK: patch_sessoes_refatorar_padrao_entidade_v18 concluído.")
