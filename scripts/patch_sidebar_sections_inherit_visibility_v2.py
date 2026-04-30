from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not MENU_SETTINGS_PATH.exists():
    fail(f"ficheiro nao encontrado: {MENU_SETTINGS_PATH}")

if not SETTINGS_HANDLERS_PATH.exists():
    fail(f"ficheiro nao encontrado: {SETTINGS_HANDLERS_PATH}")


####################################################################################
# (2) LER FICHEIROS
####################################################################################

menu_settings = MENU_SETTINGS_PATH.read_text(encoding="utf-8")
settings_handlers = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) CRIAR FUNCAO V2 - SESSAO HERDA VISIBILIDADE PARA MENUS
####################################################################################

menu_marker_v1_start = "# APPVERBO_SIDEBAR_SECTIONS_UPDATE_V1_START"
menu_marker_v1_end = "# APPVERBO_SIDEBAR_SECTIONS_UPDATE_V1_END"
menu_marker_v2_start = "# APPVERBO_SIDEBAR_SECTIONS_UPDATE_V2_START"
menu_marker_v2_end = "# APPVERBO_SIDEBAR_SECTIONS_UPDATE_V2_END"

menu_update_block = f'''
{menu_marker_v2_start}

# ###################################################################################
# (SIDEBAR_SECTIONS_UPDATE_V2) GRAVAR SESSOES E PROPAGAR VISIBILIDADE AOS MENUS
# ###################################################################################

def _parse_sidebar_menu_config_v2(raw_menu_config: Any) -> dict[str, Any]:
    try:
        parsed_config = json.loads(raw_menu_config or "{{}}")
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed_config = {{}}

    if not isinstance(parsed_config, dict):
        return {{}}

    return parsed_config


def _resolve_menu_sidebar_section_key_v2(
    menu_key: Any,
    menu_config: dict[str, Any],
    section_keys: set[str],
    ordered_section_keys: list[str],
) -> str:
    raw_section_key = (
        menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY)
        or menu_config.get("menu_section")
        or menu_config.get("section_key")
        or menu_config.get("section")
    )

    clean_section_key = _normalize_sidebar_section_key(raw_section_key)
    if clean_section_key in section_keys:
        return clean_section_key

    normalized_section_key = normalize_menu_section_key(raw_section_key, menu_key)
    if normalized_section_key in section_keys:
        return normalized_section_key

    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    default_system_section = MENU_SECTION_BY_SYSTEM_MENU_KEY.get(clean_menu_key, "")

    if default_system_section in section_keys:
        return default_system_section

    return _resolve_default_sidebar_section_key(
        clean_menu_key,
        section_keys,
        ordered_section_keys,
    )


def update_sidebar_sections_v2(
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

    section_keys = {{
        str(section.get("key") or "").strip().lower()
        for section in normalized_sections
        if str(section.get("key") or "").strip()
    }}
    ordered_section_keys = [
        str(section.get("key") or "").strip().lower()
        for section in normalized_sections
        if str(section.get("key") or "").strip()
    ]
    section_scope_map = {{
        str(section.get("key") or "").strip().lower(): normalize_menu_visibility_scopes(
            section.get("visibility_scopes")
        )
        for section in normalized_sections
        if str(section.get("key") or "").strip()
    }}

    menu_rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).mappings().all()

    if not menu_rows:
        return False, "Não existem menus para atualizar."

    updated_menus_count = 0

    for menu_row in menu_rows:
        clean_menu_key = _normalize_menu_key(menu_row.get("menu_key"))
        if not clean_menu_key:
            continue

        menu_config = _parse_sidebar_menu_config_v2(menu_row.get("menu_config"))
        sidebar_section_key = _resolve_menu_sidebar_section_key_v2(
            clean_menu_key,
            menu_config,
            section_keys,
            ordered_section_keys,
        )

        if sidebar_section_key not in section_scope_map:
            continue

        inherited_scopes = normalize_menu_visibility_scopes(
            section_scope_map.get(sidebar_section_key)
        )
        inherited_scope_mode = _resolve_visibility_scope_mode_from_scopes(inherited_scopes)

        menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = sidebar_section_key
        menu_config["visibility_scopes"] = inherited_scopes
        menu_config["visibility_scope_mode"] = inherited_scope_mode
        menu_config["visibility_scope_label"] = _resolve_visibility_scope_label_from_mode(
            inherited_scope_mode
        )

        if clean_menu_key == "administrativo":
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
                "menu_key": clean_menu_key,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            }},
        )
        updated_menus_count += 1

    session.commit()

    if updated_menus_count <= 0:
        return False, "Nenhum menu foi atualizado com a visibilidade das sessões."

    return True, ""

{menu_marker_v2_end}
'''

menu_block_pattern = re.compile(
    r"(?:" +
    re.escape(menu_marker_v1_start) + r"[\s\S]*?" + re.escape(menu_marker_v1_end) +
    r"|" +
    re.escape(menu_marker_v2_start) + r"[\s\S]*?" + re.escape(menu_marker_v2_end) +
    r")",
    re.S,
)

if menu_block_pattern.search(menu_settings):
    menu_settings = menu_block_pattern.sub(menu_update_block.strip(), menu_settings, count=1)
    print("OK: bloco de atualização das sessões substituído por V2 em menu_settings.py.")
elif "def update_sidebar_sections_v1(" in menu_settings:
    legacy_pattern = re.compile(
        r"def update_sidebar_sections_v1\(\n[\s\S]*?\n\s*return True, \"\"",
        re.S,
    )
    if not legacy_pattern.search(menu_settings):
        fail("encontrei update_sidebar_sections_v1, mas não consegui substituir a função antiga.")

    menu_settings = legacy_pattern.sub(menu_update_block.strip(), menu_settings, count=1)
    print("OK: função antiga update_sidebar_sections_v1 substituída por V2.")
else:
    menu_settings = menu_settings.rstrip() + "\n\n" + menu_update_block.strip() + "\n"
    print("OK: bloco update_sidebar_sections_v2 adicionado em menu_settings.py.")


####################################################################################
# (4) ATUALIZAR IMPORT EM settings_handlers.py
####################################################################################

if "update_sidebar_sections_v1" in settings_handlers:
    settings_handlers = settings_handlers.replace(
        "update_sidebar_sections_v1",
        "update_sidebar_sections_v2",
    )
    print("OK: import/chamadas update_sidebar_sections_v1 alterados para V2.")
elif "update_sidebar_sections_v2" not in settings_handlers:
    import_pattern = re.compile(
        r"from appverbo\.menu_settings import \(\n(?P<body>[\s\S]*?)\n\)",
        re.S,
    )

    match = import_pattern.search(settings_handlers)
    if not match:
        fail("não encontrei o bloco de importação de appverbo.menu_settings.")

    body = match.group("body").rstrip() + "\n    update_sidebar_sections_v2,"
    settings_handlers = (
        settings_handlers[:match.start("body")]
        + body
        + settings_handlers[match.end("body"):]
    )
    print("OK: update_sidebar_sections_v2 importado em settings_handlers.py.")
else:
    print("OK: update_sidebar_sections_v2 já estava importado.")


####################################################################################
# (5) CRIAR ENDPOINT V2
####################################################################################

handler_marker_v1_start = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V1_START"
handler_marker_v1_end = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V1_END"
handler_marker_v2_start = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START"
handler_marker_v2_end = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_END"

handler_block = f'''
{handler_marker_v2_start}

# ###################################################################################
# (SIDEBAR_SECTIONS_HANDLER_V2) GRAVAR SESSOES E PROPAGAR VISIBILIDADE AOS MENUS
# ###################################################################################

@router.post("/settings/menu/sidebar-sections", response_class=HTMLResponse)
def edit_sidebar_sections_v2(
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

        ok, error_message = update_sidebar_sections_v2(
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
                success_message="Sessões do sidebar e visibilidade dos menus atualizadas com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key="administrativo",
                settings_action="edit",
                settings_tab="sessoes",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

{handler_marker_v2_end}
'''

handler_block_pattern = re.compile(
    r"(?:" +
    re.escape(handler_marker_v1_start) + r"[\s\S]*?" + re.escape(handler_marker_v1_end) +
    r"|" +
    re.escape(handler_marker_v2_start) + r"[\s\S]*?" + re.escape(handler_marker_v2_end) +
    r")",
    re.S,
)

if handler_block_pattern.search(settings_handlers):
    settings_handlers = handler_block_pattern.sub(handler_block.strip(), settings_handlers, count=1)
    print("OK: endpoint das sessões substituído por V2.")
elif 'def edit_sidebar_sections_v1(' in settings_handlers:
    legacy_handler_pattern = re.compile(
        r'@router\.post\("/settings/menu/sidebar-sections", response_class=HTMLResponse\)\n'
        r'def edit_sidebar_sections_v1\(\n[\s\S]*?\n'
        r'        \)\n'
        r'(?=\n\n@router\.post|\Z)',
        re.S,
    )
    if not legacy_handler_pattern.search(settings_handlers):
        fail("encontrei edit_sidebar_sections_v1, mas não consegui substituir o endpoint antigo.")

    settings_handlers = legacy_handler_pattern.sub(handler_block.strip() + "\n", settings_handlers, count=1)
    print("OK: endpoint antigo edit_sidebar_sections_v1 substituído por V2.")
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

    print("OK: endpoint edit_sidebar_sections_v2 adicionado.")


####################################################################################
# (6) VALIDAR SINTAXE
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
# (7) GRAVAR FICHEIROS
####################################################################################

MENU_SETTINGS_PATH.write_text(menu_settings, encoding="utf-8")
SETTINGS_HANDLERS_PATH.write_text(settings_handlers, encoding="utf-8")

print("OK: menu_settings.py atualizado com update_sidebar_sections_v2.")
print("OK: settings_handlers.py atualizado com edit_sidebar_sections_v2.")
print("OK: patch_sidebar_sections_inherit_visibility_v2 concluído.")
