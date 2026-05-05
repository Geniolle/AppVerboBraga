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

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_END -->"

PY_MARKER_START = "# APPVERBO_SESSOES_SAVE_ONE_V19_START"
PY_MARKER_END = "# APPVERBO_SESSOES_SAVE_ONE_V19_END"

JS_MARKER_START = "// APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_START"
JS_MARKER_END = "// APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-persistir-estado-v19"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-persistir-estado-v19"


def fail_v19(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v19() -> Path:
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
        fail_v19(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v19()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para persistência do Estado em Sessões

Na aba **Sessões**, quando o campo **Estado** for alterado em modo criação ou edição:

1. O valor selecionado deve ser enviado explicitamente ao backend.
2. O backend deve gravar `status`, `is_active` e `status_label` na configuração da sessão.
3. Ao gravar **Inativo**, a sessão deve voltar como **Inativo** após o reload.
4. Ao gravar **Ativo**, a sessão deve voltar como **Ativo** após o reload.
5. O endpoint dedicado de Sessões deve ser único para `/settings/menu/sidebar-section-save`.
6. A gravação não pode cair no fluxo antigo em lote nem no fluxo do subprocesso Menu.
7. A sessão editada deve preservar a chave técnica original.
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

print(f"OK: regra V19 atualizada em {agents_path}")


####################################################################################
# (4) SUBSTITUIR ENDPOINT DEDICADO PARA FORCAR PERSISTENCIA DO ESTADO
####################################################################################

settings_content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

py_block = r'''# APPVERBO_SESSOES_SAVE_ONE_V19_START

# ###################################################################################
# (SIDEBAR_SECTION_SAVE_ONE_V19) CRIAR/EDITAR SESSAO COM ESTADO PERSISTENTE
# ###################################################################################

def _normalize_sidebar_section_text_v19(value: object) -> str:
    return str(value or "").strip()


def _slugify_sidebar_section_key_v19(value: object) -> str:
    import re
    import unicodedata

    raw_value = _normalize_sidebar_section_text_v19(value).lower()
    raw_value = unicodedata.normalize("NFD", raw_value)
    raw_value = "".join(char for char in raw_value if unicodedata.category(char) != "Mn")
    raw_value = re.sub(r"[^a-z0-9]+", "_", raw_value)
    raw_value = re.sub(r"_+", "_", raw_value).strip("_")

    if raw_value and raw_value[0].isdigit():
        raw_value = f"secao_{raw_value}"

    return raw_value or "nova_sessao"


def _normalize_sidebar_section_status_v19(value: object) -> str:
    clean_value = _normalize_sidebar_section_text_v19(value).lower()

    if clean_value in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def _sidebar_section_status_label_v19(value: object) -> str:
    return "Inativo" if _normalize_sidebar_section_status_v19(value) == "inativo" else "Ativo"


def _normalize_sidebar_section_scope_v19(value: object) -> str:
    clean_value = _normalize_sidebar_section_text_v19(value).lower()

    if clean_value in {"owner", "legado"}:
        return clean_value

    return "all"


def _sidebar_section_scope_to_scopes_v19(value: object) -> list[str]:
    clean_value = _normalize_sidebar_section_scope_v19(value)

    if clean_value in {"owner", "legado"}:
        return [clean_value]

    return ["owner", "legado"]


def _sidebar_section_scope_label_v19(value: object) -> str:
    clean_value = _normalize_sidebar_section_scope_v19(value)

    if clean_value == "owner":
        return "Owner"

    if clean_value == "legado":
        return "Legado"

    return "Owner e Legado"


def _sanitize_sidebar_section_return_url_v19(return_url: object) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    fallback = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
    raw_url = _normalize_sidebar_section_text_v19(return_url) or fallback

    if raw_url.startswith("http://") or raw_url.startswith("https://") or raw_url.startswith("//"):
        raw_url = fallback

    if not raw_url.startswith("/users/new"):
        raw_url = fallback

    parts = urlsplit(raw_url)
    blocked_params = {
        "settings_edit_key",
        "settings_action",
        "settings_tab",
        "sidebar_section_edit_key",
        "sidebar_section_return_url",
        "success",
        "error",
    }

    clean_params = []
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

    return urlunsplit(("", "", "/users/new", urlencode(clean_params), "admin-sidebar-sections-card"))


def _append_sidebar_section_message_v19(return_url: str, message_key: str, message: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    parts = urlsplit(return_url)
    params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {"success", "error"}
    ]
    params.append((message_key, message))

    return urlunsplit(("", "", parts.path or "/users/new", urlencode(params), parts.fragment or "admin-sidebar-sections-card"))


def _redirect_sidebar_section_message_v19(
    return_url: str,
    message_key: str,
    message: str,
) -> RedirectResponse:
    safe_return_url = _sanitize_sidebar_section_return_url_v19(return_url)

    return RedirectResponse(
        url=_append_sidebar_section_message_v19(safe_return_url, message_key, message),
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _make_unique_sidebar_section_key_v19(base_key: str, used_keys: set[str]) -> str:
    clean_base_key = _slugify_sidebar_section_key_v19(base_key)

    if clean_base_key not in used_keys:
        return clean_base_key

    counter = 2
    candidate = f"{clean_base_key}_{counter}"

    while candidate in used_keys:
        counter += 1
        candidate = f"{clean_base_key}_{counter}"

    return candidate


def _read_sidebar_sections_for_save_one_v19(session) -> list[dict[str, str]]:
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


def _persist_sidebar_sections_status_v19(
    session,
    payload_sections: list[dict[str, str]],
    target_section_key: str,
    target_status: str,
) -> None:
    from uuid import uuid4

    from appverbo.menu_settings import (
        MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY,
        MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
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

    clean_target_key = _slugify_sidebar_section_key_v19(target_section_key)
    clean_target_status = _normalize_sidebar_section_status_v19(target_status)

    normalized_payload_sections = []

    for section in payload_sections:
        clean_key = _slugify_sidebar_section_key_v19(section.get("key"))
        clean_label = _normalize_sidebar_section_text_v19(section.get("label"))
        clean_scope = _normalize_sidebar_section_scope_v19(section.get("visibility_scope_mode"))
        clean_status = _normalize_sidebar_section_status_v19(section.get("status"))

        if clean_key == clean_target_key:
            clean_status = clean_target_status

        if not clean_label or not clean_key:
            continue

        normalized_payload_sections.append(
            {
                "key": clean_key,
                "label": clean_label,
                "visibility_scopes": _sidebar_section_scope_to_scopes_v19(clean_scope),
                "visibility_scope_mode": clean_scope,
                "visibility_scope_label": _sidebar_section_scope_label_v19(clean_scope),
                "status": clean_status,
                "is_active": clean_status == "ativo",
                "status_label": _sidebar_section_status_label_v19(clean_status),
            }
        )

    menu_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = normalized_payload_sections
    menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = str(uuid4())

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": "administrativo",
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()


@router.post("/settings/menu/sidebar-section-save", response_class=HTMLResponse)
def save_one_sidebar_section_v19(
    request: Request,
    section_mode: str = Form("create"),
    original_section_key: str = Form(""),
    section_label: str = Form(""),
    section_visibility_scope_mode: str = Form("all"),
    section_status: str = Form("ativo"),
    section_status_override_v19: str = Form(""),
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

        clean_mode = _normalize_sidebar_section_text_v19(section_mode).lower()
        clean_original_key = _slugify_sidebar_section_key_v19(original_section_key)
        clean_label = _normalize_sidebar_section_text_v19(section_label)
        clean_scope = _normalize_sidebar_section_scope_v19(section_visibility_scope_mode)

        effective_status = section_status_override_v19 or section_status
        clean_status = _normalize_sidebar_section_status_v19(effective_status)

        if not clean_label:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Informe o nome da sessão.",
            )

        current_sections = _read_sidebar_sections_for_save_one_v19(session)
        payload_sections: list[dict[str, str]] = []
        target_section_key = clean_original_key

        if clean_mode == "edit":
            found_section = False

            for section in current_sections:
                section_key = _slugify_sidebar_section_key_v19(section.get("key"))

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
                            "label": _normalize_sidebar_section_text_v19(section.get("label")),
                            "visibility_scope_mode": _normalize_sidebar_section_scope_v19(
                                section.get("visibility_scope_mode")
                            ),
                            "status": _normalize_sidebar_section_status_v19(section.get("status")),
                        }
                    )

            if not found_section:
                return _redirect_sidebar_section_message_v19(
                    safe_return_url,
                    "error",
                    "Sessão não encontrada para edição.",
                )
        else:
            used_keys = {
                _slugify_sidebar_section_key_v19(section.get("key"))
                for section in current_sections
            }
            target_section_key = _make_unique_sidebar_section_key_v19(clean_label, used_keys)

            for section in current_sections:
                payload_sections.append(
                    {
                        "key": _slugify_sidebar_section_key_v19(section.get("key")),
                        "label": _normalize_sidebar_section_text_v19(section.get("label")),
                        "visibility_scope_mode": _normalize_sidebar_section_scope_v19(
                            section.get("visibility_scope_mode")
                        ),
                        "status": _normalize_sidebar_section_status_v19(section.get("status")),
                    }
                )

            payload_sections.append(
                {
                    "key": target_section_key,
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
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                error_message or "Não foi possível gravar a sessão.",
            )

        _persist_sidebar_sections_status_v19(
            session=session,
            payload_sections=payload_sections,
            target_section_key=target_section_key,
            target_status=clean_status,
        )

        return _redirect_sidebar_section_message_v19(
            safe_return_url,
            "success",
            (
                "Sessão atualizada com sucesso."
                if clean_mode == "edit"
                else "Sessão criada com sucesso."
            ),
        )

# APPVERBO_SESSOES_SAVE_ONE_V19_END
'''

for start_marker, end_marker in [
    ("# APPVERBO_SESSOES_SAVE_ONE_V16_START", "# APPVERBO_SESSOES_SAVE_ONE_V16_END"),
    ("# APPVERBO_SESSOES_SAVE_ONE_V18_START", "# APPVERBO_SESSOES_SAVE_ONE_V18_END"),
    ("# APPVERBO_SESSOES_SAVE_ONE_V19_START", "# APPVERBO_SESSOES_SAVE_ONE_V19_END"),
]:
    if start_marker in settings_content and end_marker in settings_content:
        pattern = re.compile(
            re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
            re.S,
        )
        settings_content = pattern.sub("", settings_content)

anchor = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START"

if anchor not in settings_content:
    fail_v19("não encontrei APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START para inserir endpoint V19.")

settings_content = settings_content.replace(anchor, py_block + "\n\n" + anchor, 1)

route_count = settings_content.count('@router.post("/settings/menu/sidebar-section-save"')

if route_count != 1:
    fail_v19(f"existem {route_count} endpoints /settings/menu/sidebar-section-save; deveria existir exatamente 1.")

try:
    ast.parse(settings_content)
except SyntaxError as exc:
    fail_v19(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_content, encoding="utf-8")

print("OK: endpoint V19 aplicado com persistência forçada do Estado.")


####################################################################################
# (5) ADICIONAR JS PARA ENVIAR O ESTADO SELECIONADO EXPLICITAMENTE
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesPersistirEstadoV19(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizarEstadoSessoesPersistirEstadoV19(valor) {
    const cleanValor = normalizarTextoSessoesPersistirEstadoV19(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  //###################################################################################
  // (2) URL DE RETORNO SEGURA DA ABA SESSOES
  //###################################################################################

  function obterReturnUrlSessoesPersistirEstadoV19() {
    const url = new URL(window.location.href);

    url.searchParams.delete("settings_edit_key");
    url.searchParams.delete("settings_action");
    url.searchParams.delete("settings_tab");
    url.searchParams.delete("sidebar_section_edit_key");
    url.searchParams.delete("sidebar_section_return_url");
    url.searchParams.delete("success");
    url.searchParams.delete("error");

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (3) FORCAR STATUS NO FORMULARIO DEDICADO
  //###################################################################################

  function prepararFormularioSessaoPersistirEstadoV19(formulario) {
    if (!formulario) {
      return;
    }

    const action = String(formulario.getAttribute("action") || "");

    if (!action.includes("/settings/menu/sidebar-section-save")) {
      return;
    }

    const estadoSelect = formulario.querySelector('select[name="section_status"]');
    const estadoValue = normalizarEstadoSessoesPersistirEstadoV19(
      estadoSelect ? estadoSelect.value : "ativo"
    );

    Array.from(formulario.querySelectorAll('input[name="section_status_override_v19"]')).forEach(function (input) {
      input.remove();
    });

    const estadoOverride = document.createElement("input");
    estadoOverride.type = "hidden";
    estadoOverride.name = "section_status_override_v19";
    estadoOverride.value = estadoValue;
    formulario.appendChild(estadoOverride);

    let returnInput = formulario.querySelector('input[name="sidebar_section_return_url"]');

    if (!returnInput) {
      returnInput = document.createElement("input");
      returnInput.type = "hidden";
      returnInput.name = "sidebar_section_return_url";
      formulario.appendChild(returnInput);
    }

    returnInput.value = obterReturnUrlSessoesPersistirEstadoV19();
  }

  function instalarSubmitPersistirEstadoV19() {
    if (window.__appverboSessoesPersistirEstadoV19 === true) {
      return;
    }

    window.__appverboSessoesPersistirEstadoV19 = true;

    document.addEventListener("submit", function (event) {
      prepararFormularioSessaoPersistirEstadoV19(event.target);
    }, true);

    document.addEventListener("click", function (event) {
      const botaoSubmit = event.target.closest('button[type="submit"], input[type="submit"]');

      if (!botaoSubmit) {
        return;
      }

      const formulario = botaoSubmit.form || botaoSubmit.closest("form");

      prepararFormularioSessaoPersistirEstadoV19(formulario);
    }, true);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarSubmitPersistirEstadoV19);
  }
  else {
    instalarSubmitPersistirEstadoV19();
  }
})();
// APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_END
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

print("OK: JS V19 aplicado para enviar section_status_override_v19.")


####################################################################################
# (6) CSS MARCADOR V19
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-sessoes-create-card-v18 select[name="section_status"] {{
  font-weight: 600;
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

print("OK: CSS V19 aplicado.")


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
    fail_v19("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v19("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_START": agents_validado,
    "APPVERBO_SESSOES_SAVE_ONE_V19_START": settings_validado,
    "save_one_sidebar_section_v19": settings_validado,
    "_persist_sidebar_sections_status_v19": settings_validado,
    "section_status_override_v19": settings_validado,
    '"is_active": clean_status == "ativo"': settings_validado,
    "APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_START": js_validado,
    "prepararFormularioSessaoPersistirEstadoV19": js_validado,
    "section_status_override_v19": js_validado,
    "APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_START": css_validado,
    "20260505-sessoes-persistir-estado-v19": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v19(f"validação falhou, termo ausente: {termo}")

route_count_validado = settings_validado.count('@router.post("/settings/menu/sidebar-section-save"')

if route_count_validado != 1:
    fail_v19(f"validação falhou: existem {route_count_validado} endpoints sidebar-section-save.")

try:
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v19(f"Python final inválido: {exc}")

print("OK: patch_sessoes_persistir_estado_v19 concluído.")
