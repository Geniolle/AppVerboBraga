from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_autosave_v1.js"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

for path in [MENU_SETTINGS_PATH, SETTINGS_HANDLERS_PATH, TEMPLATE_PATH]:
    if not path.exists():
        fail(f"ficheiro nao encontrado: {path}")


####################################################################################
# (2) LER FICHEIROS
####################################################################################

menu_settings = MENU_SETTINGS_PATH.read_text(encoding="utf-8")
settings_handlers = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
template = TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) ADICIONAR FUNCAO DE GRAVACAO EM menu_settings.py
####################################################################################

menu_marker_start = "# APPVERBO_SIDEBAR_SECTIONS_UPDATE_V1_START"
menu_marker_end = "# APPVERBO_SIDEBAR_SECTIONS_UPDATE_V1_END"

menu_update_block = f'''
{menu_marker_start}

# ###################################################################################
# (SIDEBAR_SECTIONS_UPDATE_V1) GRAVAR SESSOES DO SIDEBAR
# ###################################################################################

def update_sidebar_sections_v1(
    session: Session,
    raw_sections: list[dict[str, Any]],
) -> tuple[bool, str]:
    payload_sections: list[dict[str, Any]] = []

    for raw_section in raw_sections:
        if not isinstance(raw_section, dict):
            continue

        clean_label = _normalize_sidebar_section_label(raw_section.get("label"))
        if not clean_label:
            continue

        clean_key = _normalize_sidebar_section_key(raw_section.get("key"))
        if not clean_key:
            clean_key = _build_sidebar_section_key_from_label(clean_label)

        if not clean_key:
            continue

        scope_mode = (
            raw_section.get("visibility_scope_mode")
            or raw_section.get("scope_mode")
            or raw_section.get("scope")
            or raw_section.get("visibility")
            or MENU_VISIBILITY_SCOPE_ALL
        )

        payload_sections.append(
            _build_sidebar_section_payload(
                clean_key,
                clean_label,
                _visibility_scope_mode_to_scopes(scope_mode),
            )
        )

    normalized_sections = normalize_sidebar_sections(payload_sections)

    if not normalized_sections:
        return False, "Informe pelo menos uma sessão válida."

    row = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {{"menu_key": "administrativo"}},
    ).mappings().one_or_none()

    if row is None:
        return False, "Menu administrativo não encontrado para gravar as sessões."

    raw_menu_config = row.get("menu_config") or "{{}}"

    try:
        menu_config = json.loads(raw_menu_config)
    except (TypeError, ValueError, json.JSONDecodeError):
        menu_config = {{}}

    if not isinstance(menu_config, dict):
        menu_config = {{}}

    menu_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = normalized_sections

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {{
            "menu_key": "administrativo",
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        }},
    )

    session.commit()

    return True, ""

{menu_marker_end}
'''

menu_pattern = re.compile(
    re.escape(menu_marker_start) + r"[\s\S]*?" + re.escape(menu_marker_end),
    re.S,
)

if menu_marker_start in menu_settings:
    menu_settings = menu_pattern.sub(menu_update_block.strip(), menu_settings)
    print("OK: bloco update_sidebar_sections_v1 substituido em menu_settings.py.")
else:
    menu_settings = menu_settings.rstrip() + "\n\n" + menu_update_block.strip() + "\n"
    print("OK: bloco update_sidebar_sections_v1 adicionado em menu_settings.py.")


####################################################################################
# (4) IMPORTAR FUNCAO EM settings_handlers.py
####################################################################################

if "update_sidebar_sections_v1" not in settings_handlers:
    import_pattern = re.compile(
        r"from appverbo\.menu_settings import \(\n(?P<body>[\s\S]*?)\n\)",
        re.S,
    )

    match = import_pattern.search(settings_handlers)
    if not match:
        fail("nao encontrei o bloco de importacao de appverbo.menu_settings em settings_handlers.py.")

    body = match.group("body")
    body = body.rstrip() + "\n    update_sidebar_sections_v1,"
    settings_handlers = (
        settings_handlers[:match.start("body")]
        + body
        + settings_handlers[match.end("body"):]
    )

    print("OK: update_sidebar_sections_v1 importado em settings_handlers.py.")
else:
    print("OK: update_sidebar_sections_v1 ja estava importado em settings_handlers.py.")


####################################################################################
# (5) ADICIONAR ENDPOINT DE GRAVACAO EM settings_handlers.py
####################################################################################

handler_marker_start = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V1_START"
handler_marker_end = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V1_END"

handler_block = f'''
{handler_marker_start}

# ###################################################################################
# (SIDEBAR_SECTIONS_HANDLER_V1) GRAVAR ALTERACOES DAS SESSOES DO SIDEBAR
# ###################################################################################

@router.post("/settings/menu/sidebar-sections", response_class=HTMLResponse)
def edit_sidebar_sections_v1(
    request: Request,
    section_key: list[str] = Form(default=[]),
    section_label: list[str] = Form(default=[]),
    section_visibility_scope_mode: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
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

        rows_count = max(
            len(section_key),
            len(section_label),
            len(section_visibility_scope_mode),
        )

        payload_sections: list[dict[str, str]] = []

        for row_index in range(rows_count):
            payload_sections.append(
                {{
                    "key": section_key[row_index] if row_index < len(section_key) else "",
                    "label": section_label[row_index] if row_index < len(section_label) else "",
                    "visibility_scope_mode": (
                        section_visibility_scope_mode[row_index]
                        if row_index < len(section_visibility_scope_mode)
                        else ""
                    ),
                }}
            )

        ok, error_message = update_sidebar_sections_v1(
            session,
            payload_sections,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível gravar as sessões do sidebar.",
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
                success_message="Sessões do sidebar atualizadas com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key="administrativo",
                settings_action="edit",
                settings_tab="sessoes",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

{handler_marker_end}
'''

handler_pattern = re.compile(
    re.escape(handler_marker_start) + r"[\s\S]*?" + re.escape(handler_marker_end),
    re.S,
)

if handler_marker_start in settings_handlers:
    settings_handlers = handler_pattern.sub(handler_block.strip(), settings_handlers)
    print("OK: endpoint edit_sidebar_sections_v1 substituido em settings_handlers.py.")
else:
    insert_before = '@router.post("/settings/menu/field-move"'
    insert_index = settings_handlers.find(insert_before)

    if insert_index == -1:
        settings_handlers = settings_handlers.rstrip() + "\n\n" + handler_block.strip() + "\n"
    else:
        settings_handlers = (
            settings_handlers[:insert_index]
            + handler_block.strip()
            + "\n\n"
            + settings_handlers[insert_index:]
        )

    print("OK: endpoint edit_sidebar_sections_v1 adicionado em settings_handlers.py.")


####################################################################################
# (6) CRIAR JAVASCRIPT DE AUTO-GRAVACAO
####################################################################################

js_content = r'''(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizeText(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function buildKeyFromLabel(value) {
    return normalizeText(value)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  //###################################################################################
  // (2) LOCALIZAR CARD DE SESSOES DO SIDEBAR
  //###################################################################################

  function findSidebarSectionsCard() {
    const cards = Array.from(document.querySelectorAll(".card, section"));

    return cards.find((card) => {
      const headings = Array.from(card.querySelectorAll("h1, h2, h3"));
      return headings.some((heading) => {
        const text = normalizeText(heading.textContent);
        return text.includes("sessoes do sidebar") || text.includes("sessoes criadas");
      });
    });
  }

  function findCreatedSectionsArea(card) {
    if (!card) {
      return null;
    }

    const headings = Array.from(card.querySelectorAll("h3, h4, strong, legend"));
    const heading = headings.find((item) => normalizeText(item.textContent).includes("sessoes criadas"));

    if (!heading) {
      return card;
    }

    return (
      heading.closest(".admin-subsection") ||
      heading.closest(".entity-panel-card") ||
      heading.parentElement ||
      card
    );
  }

  //###################################################################################
  // (3) COLETAR LINHAS DAS SESSOES CRIADAS
  //###################################################################################

  function getRowForSelect(selectElement) {
    return (
      selectElement.closest("tr") ||
      selectElement.closest(".sidebar-section-row") ||
      selectElement.closest(".settings-row") ||
      selectElement.closest(".menu-row") ||
      selectElement.parentElement?.parentElement ||
      selectElement.parentElement
    );
  }

  function getLabelInput(row) {
    if (!row) {
      return null;
    }

    return (
      row.querySelector('input[name*="section_label"]') ||
      row.querySelector('input[name*="label"]') ||
      row.querySelector('input[type="text"]') ||
      row.querySelector("input:not([type])")
    );
  }

  function getKeyInput(row) {
    if (!row) {
      return null;
    }

    return (
      row.querySelector('input[name*="section_key"]') ||
      row.querySelector('input[name*="key"][type="hidden"]') ||
      row.querySelector('input[type="hidden"][name*="key"]')
    );
  }

  function collectSectionRows(area) {
    const selects = Array.from(area.querySelectorAll("select"));
    const rows = [];

    selects.forEach((selectElement) => {
      const row = getRowForSelect(selectElement);
      const labelInput = getLabelInput(row);

      if (!row || !labelInput) {
        return;
      }

      const label = String(labelInput.value || "").trim();

      if (!label) {
        return;
      }

      const keyInput = getKeyInput(row);
      const key = String(keyInput?.value || row.dataset.sectionKey || buildKeyFromLabel(label)).trim();

      rows.push({
        key: key,
        label: label,
        visibility: String(selectElement.value || "all").trim() || "all",
      });
    });

    return rows;
  }

  //###################################################################################
  // (4) SUBMETER ALTERACOES
  //###################################################################################

  let submitTimer = null;
  let isSubmitting = false;

  function submitSidebarSections(area) {
    if (isSubmitting) {
      return;
    }

    const rows = collectSectionRows(area);

    if (!rows.length) {
      return;
    }

    isSubmitting = true;

    const form = document.createElement("form");
    form.method = "post";
    form.action = "/settings/menu/sidebar-sections";
    form.style.display = "none";

    function appendField(name, value) {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      input.value = value;
      form.appendChild(input);
    }

    rows.forEach((row) => {
      appendField("section_key", row.key);
      appendField("section_label", row.label);
      appendField("section_visibility_scope_mode", row.visibility);
    });

    appendField("redirect_menu", "administrativo");
    appendField("redirect_target", "#settings-menu-edit-card");

    document.body.appendChild(form);
    form.submit();
  }

  function scheduleSubmit(area) {
    window.clearTimeout(submitTimer);
    submitTimer = window.setTimeout(() => submitSidebarSections(area), 250);
  }

  //###################################################################################
  // (5) INICIALIZAR EVENTOS
  //###################################################################################

  function initSidebarSectionsAutosave() {
    const card = findSidebarSectionsCard();
    const area = findCreatedSectionsArea(card);

    if (!area) {
      return;
    }

    area.addEventListener("change", (event) => {
      const target = event.target;

      if (!(target instanceof HTMLSelectElement) && !(target instanceof HTMLInputElement)) {
        return;
      }

      const row = getRowForSelect(target);
      const labelInput = getLabelInput(row);

      if (!labelInput || !String(labelInput.value || "").trim()) {
        return;
      }

      scheduleSubmit(area);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidebarSectionsAutosave);
  } else {
    initSidebarSectionsAutosave();
  }
})();
'''

JS_PATH.write_text(js_content, encoding="utf-8")
print("OK: JS sidebar_sections_autosave_v1.js criado.")


####################################################################################
# (7) INCLUIR JAVASCRIPT NO TEMPLATE
####################################################################################

script_tag = '<script src="/static/js/modules/sidebar_sections_autosave_v1.js?v=20260430-sidebar-sections-v1"></script>'

if "sidebar_sections_autosave_v1.js" not in template:
    scripts_block_pattern = re.compile(
        r"(?P<start>\{% block scripts %\}[\s\S]*?)(?P<end>\n\{% endblock %\})",
        re.S,
    )

    match = scripts_block_pattern.search(template)

    if match:
        template = (
            template[:match.end("start")]
            + "\n  "
            + script_tag
            + template[match.end("start"):]
        )
    else:
        template = template.rstrip() + "\n\n{% block scripts %}\n  " + script_tag + "\n{% endblock %}\n"

    print("OK: sidebar_sections_autosave_v1.js incluido em new_user.html.")
else:
    template = re.sub(
        r'/static/js/modules/sidebar_sections_autosave_v1\.js\?v=[^"]+',
        '/static/js/modules/sidebar_sections_autosave_v1.js?v=20260430-sidebar-sections-v1',
        template,
    )
    print("OK: sidebar_sections_autosave_v1.js ja estava incluido; cache buster atualizado.")


####################################################################################
# (8) VALIDAR SINTAXE PYTHON
####################################################################################

try:
    ast.parse(menu_settings)
except SyntaxError as exc:
    fail(f"menu_settings.py ficaria com erro de sintaxe: {exc}")

try:
    ast.parse(settings_handlers)
except SyntaxError as exc:
    fail(f"settings_handlers.py ficaria com erro de sintaxe: {exc}")


####################################################################################
# (9) GRAVAR FICHEIROS
####################################################################################

MENU_SETTINGS_PATH.write_text(menu_settings, encoding="utf-8")
SETTINGS_HANDLERS_PATH.write_text(settings_handlers, encoding="utf-8")
TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: menu_settings.py atualizado.")
print("OK: settings_handlers.py atualizado.")
print("OK: new_user.html atualizado.")
print("OK: patch_sidebar_sections_autosave_v1 concluido.")
