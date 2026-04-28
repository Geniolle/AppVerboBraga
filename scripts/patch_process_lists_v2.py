from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import shutil
import subprocess
import sys


####################################################################################
# (1) CONFIGURAÇÃO INICIAL
####################################################################################

ROOT = Path.cwd()
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

FILES = {
    "menu_settings": ROOT / "appverbo" / "menu_settings.py",
    "settings_handlers": ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py",
    "admin_tabs": ROOT / "appverbo" / "process_settings" / "admin_tabs.py",
    "template": ROOT / "templates" / "new_user.html",
    "new_user_js": ROOT / "static" / "js" / "new_user.js",
    "settings_process_tabs_js": ROOT / "static" / "js" / "modules" / "settings_process_tabs.js",
    "runtime_js": ROOT / "static" / "js" / "modules" / "process_lists_runtime_v2.js",
    "css": ROOT / "static" / "css" / "new_user.css",
}


####################################################################################
# (2) FUNÇÕES AUXILIARES
####################################################################################

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def backup_file(path: Path) -> None:
    if path.exists():
        backup_path = path.with_name(f"{path.name}.bak_lista_v2_{TIMESTAMP}")
        shutil.copy2(path, backup_path)
        print(f"BACKUP: {backup_path}")


def run_command(command: list[str]) -> None:
    print("EXEC:", " ".join(command))
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Comando falhou: {' '.join(command)}")


def replace_once(content: str, old: str, new: str, label: str) -> str:
    if old not in content:
        print(f"AVISO: trecho não encontrado para {label}. Pode já estar aplicado.")
        return content

    print(f"OK: aplicado {label}.")
    return content.replace(old, new, 1)


####################################################################################
# (3) VALIDAR PROJETO
####################################################################################

def validate_project_v2() -> None:
    required_paths = [
        ROOT / "appverbo",
        FILES["menu_settings"],
        FILES["settings_handlers"],
        FILES["template"],
        FILES["new_user_js"],
        FILES["css"],
    ]

    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(f"Não encontrado: {path}")

    print("OK: projeto validado.")


####################################################################################
# (4) PATCH appverbo/menu_settings.py
####################################################################################

def patch_menu_settings_v2() -> None:
    path = FILES["menu_settings"]
    content = read_file(path)

    if "import re" not in content:
        content = content.replace("import json", "import json\nimport re", 1)

    if '"key": "list", "label": "Lista"' not in content:
        content = replace_once(
            content,
            '    {"key": "header", "label": "Cabeçalho (aba)"},\n)',
            '    {"key": "header", "label": "Cabeçalho (aba)"},\n'
            '    {"key": "list", "label": "Lista"},\n'
            ')',
            "tipo de campo Lista",
        )

    if "def normalize_menu_process_lists_v2" not in content:
        append_block = r'''

####################################################################################
# LISTA V2 - LISTAS REUTILIZÁVEIS DO PROCESSO
####################################################################################

def _normalize_process_list_key_v2(raw_key: Any) -> str:
    clean_key = str(raw_key or "").strip().lower()
    clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
    clean_key = re.sub(r"_+", "_", clean_key).strip("_")

    if not clean_key:
        return ""

    if not clean_key.startswith("list_"):
        clean_key = f"list_{clean_key}"

    return clean_key


def _build_process_list_key_from_label_v2(label: str) -> str:
    base_key = _build_menu_key_from_label(label)

    if not base_key:
        base_key = "lista"

    return _normalize_process_list_key_v2(base_key)


def _normalize_process_list_items_csv_v2(raw_items: Any) -> list[str]:
    if isinstance(raw_items, str):
        raw_values = raw_items.split(",")
    elif isinstance(raw_items, (list, tuple, set)):
        raw_values = []
        for item in raw_items:
            if isinstance(item, str) and "," in item:
                raw_values.extend(item.split(","))
            else:
                raw_values.append(item)
    else:
        raw_values = []

    normalized: list[str] = []
    seen: set[str] = set()

    for raw_value in raw_values:
        clean_value = " ".join(str(raw_value or "").strip().split())

        if not clean_value:
            continue

        lookup_key = clean_value.lower()

        if lookup_key in seen:
            continue

        seen.add(lookup_key)
        normalized.append(clean_value)

    return normalized


def normalize_menu_process_lists_v2(raw_lists: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_lists, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_labels: set[str] = set()

    for raw_item in raw_lists:
        if not isinstance(raw_item, dict):
            continue

        label = _normalize_sentence_case_text(raw_item.get("label", raw_item.get("name")))

        if not label:
            continue

        label_lookup = label.lower()

        if label_lookup in seen_labels:
            continue

        seen_labels.add(label_lookup)

        list_key = (
            _normalize_process_list_key_v2(raw_item.get("key"))
            or _build_process_list_key_from_label_v2(label)
        )

        base_key = list_key
        suffix = 2

        while list_key in seen_keys:
            list_key = f"{base_key}_{suffix}"
            suffix += 1

        seen_keys.add(list_key)

        items = _normalize_process_list_items_csv_v2(
            raw_item.get("items_csv", raw_item.get("items"))
        )

        normalized.append(
            {
                "key": list_key,
                "label": label,
                "items": items,
                "items_csv": ", ".join(items),
            }
        )

    return normalized


def get_menu_process_lists_v2(menu_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not isinstance(menu_config, dict):
        return []

    return normalize_menu_process_lists_v2(menu_config.get("process_lists"))


if "_original_normalize_menu_process_additional_fields_for_list_v2" not in globals():
    _original_normalize_menu_process_additional_fields_for_list_v2 = normalize_menu_process_additional_fields


def normalize_menu_process_additional_fields_v3(raw_fields: Any) -> list[dict[str, Any]]:
    normalized = _original_normalize_menu_process_additional_fields_for_list_v2(raw_fields)

    if not isinstance(raw_fields, (list, tuple, set)):
        return normalized

    raw_by_key: dict[str, dict[str, Any]] = {}
    raw_by_label: dict[str, dict[str, Any]] = {}
    raw_by_index: dict[int, dict[str, Any]] = {}

    for index, raw_item in enumerate(raw_fields):
        if not isinstance(raw_item, dict):
            continue

        raw_by_index[index] = raw_item

        raw_key = _normalize_custom_field_key(str(raw_item.get("key") or ""))

        if raw_key:
            raw_by_key[raw_key] = raw_item

        raw_label = _normalize_additional_field_label(raw_item.get("label"))

        if raw_label:
            raw_by_label[raw_label.lower()] = raw_item

    for index, item in enumerate(normalized):
        if str(item.get("field_type") or "").strip().lower() != "list":
            item.pop("list_key", None)
            continue

        item_key = str(item.get("key") or "").strip().lower()
        item_label = str(item.get("label") or "").strip().lower()

        raw_item = (
            raw_by_key.get(item_key)
            or raw_by_label.get(item_label)
            or raw_by_index.get(index)
            or {}
        )

        item["list_key"] = _normalize_process_list_key_v2(
            raw_item.get("list_key", raw_item.get("process_list_key", raw_item.get("lista")))
        )

    return normalized


normalize_menu_process_additional_fields = normalize_menu_process_additional_fields_v3


if "_original_get_sidebar_menu_settings_for_lists_v2" not in globals():
    _original_get_sidebar_menu_settings_for_lists_v2 = get_sidebar_menu_settings


def get_sidebar_menu_settings_v3(session: Session) -> list[dict[str, Any]]:
    settings = _original_get_sidebar_menu_settings_for_lists_v2(session)

    rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()

    config_by_key = {
        _normalize_menu_key(row.menu_key): _parse_menu_config(row.menu_config)
        for row in rows
        if _normalize_menu_key(row.menu_key)
    }

    for item in settings:
        clean_key = _normalize_menu_key(item.get("key"))
        menu_config = config_by_key.get(clean_key, {})
        process_lists = get_menu_process_lists_v2(menu_config)
        item["process_lists"] = process_lists
        item["process_list_options"] = [
            {"key": process_list["key"], "label": process_list["label"]}
            for process_list in process_lists
        ]

    return settings


get_sidebar_menu_settings = get_sidebar_menu_settings_v3
'''
        content = content.rstrip() + append_block + "\n"

    write_file(path, content)
    print("OK: menu_settings.py atualizado.")


####################################################################################
# (5) PATCH appverbo/process_settings/admin_tabs.py
####################################################################################

def patch_admin_tabs_v2() -> None:
    path = FILES["admin_tabs"]

    if not path.exists():
        print("AVISO: admin_tabs.py não existe. Ignorado.")
        return

    content = read_file(path)

    if '"key": "lista"' in content:
        print("AVISO: aba Lista já existe em admin_tabs.py.")
        return

    content = replace_once(
        content,
        '    {"key": "campos_adicionais", "label": "Campos adicionais"},',
        '    {"key": "campos_adicionais", "label": "Campos adicionais"},\n'
        '    {"key": "lista", "label": "Lista"},',
        "admin_tabs Lista",
    )

    write_file(path, content)
    print("OK: admin_tabs.py atualizado.")


####################################################################################
# (6) PATCH appverbo/routes/profile/settings_handlers.py
####################################################################################

def patch_settings_handlers_v2() -> None:
    path = FILES["settings_handlers"]
    content = read_file(path)

    if '"lista"' not in content or "settings_tab" in content:
        content = re.sub(
            r'\{([^{}]*"campos-adicionais"[^{}]*)\}',
            lambda match: match.group(0)
            if '"lista"' in match.group(0)
            else "{" + match.group(1).rstrip() + ', "lista"' + "}",
            content,
            count=1,
        )

    if "additional_field_list_key: list[str] = Form(default=[])," not in content:
        content = replace_once(
            content,
            '    additional_field_size: list[str] = Form(default=[]),\n'
            '    redirect_menu: str = Form("administrativo"),',
            '    additional_field_size: list[str] = Form(default=[]),\n'
            '    additional_field_list_key: list[str] = Form(default=[]),\n'
            '    redirect_menu: str = Form("administrativo"),',
            "additional_field_list_key",
        )

    if "len(additional_field_list_key)," not in content:
        content = replace_once(
            content,
            '            len(additional_field_key),\n'
            '        )',
            '            len(additional_field_key),\n'
            '            len(additional_field_list_key),\n'
            '        )',
            "rows_count list_key",
        )

    if '"list_key": additional_field_list_key[row_index]' not in content:
        content = replace_once(
            content,
            '                    "size": additional_field_size[row_index] if row_index < len(additional_field_size) else "",\n'
            '                }',
            '                    "size": additional_field_size[row_index] if row_index < len(additional_field_size) else "",\n'
            '                    "list_key": additional_field_list_key[row_index] if row_index < len(additional_field_list_key) else "",\n'
            '                }',
            "payload list_key",
        )

    if "def edit_sidebar_menu_process_lists_v2" not in content:
        append_route = r'''


@router.post("/settings/menu/process-lists", response_class=HTMLResponse)
def edit_sidebar_menu_process_lists_v2(
    request: Request,
    menu_key: str = Form(...),
    process_list_key: list[str] = Form(default=[]),
    process_list_label: list[str] = Form(default=[]),
    process_list_items_csv: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    import json
    import re
    from sqlalchemy import text

    from appverbo.menu_settings import _build_menu_key_from_label

    clean_menu_key = menu_key.strip().lower()

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
                    error_message="Apenas administradores podem alterar listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
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
                    error_message="Apenas Owner pode configurar listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        existing_row = session.execute(
            text(
                """
                SELECT menu_config
                FROM sidebar_menu_settings
                WHERE lower(trim(menu_key)) = :menu_key
                LIMIT 1
                """
            ),
            {"menu_key": clean_menu_key},
        ).mappings().first()

        if existing_row is None:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Processo não encontrado.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        def normalize_list_key_v2(raw_key: str, label: str) -> str:
            clean_key = str(raw_key or "").strip().lower()
            clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
            clean_key = re.sub(r"_+", "_", clean_key).strip("_")

            if not clean_key:
                clean_key = _build_menu_key_from_label(label)

            if not clean_key:
                clean_key = "lista"

            if not clean_key.startswith("list_"):
                clean_key = f"list_{clean_key}"

            return clean_key

        def normalize_items_v2(raw_csv: str) -> list[str]:
            values = []
            seen = set()

            for raw_value in str(raw_csv or "").split(","):
                clean_value = " ".join(raw_value.strip().split())

                if not clean_value:
                    continue

                lookup_key = clean_value.lower()

                if lookup_key in seen:
                    continue

                seen.add(lookup_key)
                values.append(clean_value)

            return values

        rows_count = max(
            len(process_list_key),
            len(process_list_label),
            len(process_list_items_csv),
        )

        process_lists = []
        seen_keys = set()

        for row_index in range(rows_count):
            label = process_list_label[row_index] if row_index < len(process_list_label) else ""
            label = " ".join(str(label or "").strip().split())

            raw_items_csv = (
                process_list_items_csv[row_index]
                if row_index < len(process_list_items_csv)
                else ""
            )
            items = normalize_items_v2(raw_items_csv)

            if not label and not items:
                continue

            if not label:
                return RedirectResponse(
                    url=_build_settings_redirect_url(
                        error_message="Informe o nome da lista.",
                        redirect_menu=redirect_menu,
                        redirect_target=redirect_target,
                        settings_edit_key=clean_menu_key,
                        settings_action="edit",
                        settings_tab="lista",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            if not items:
                return RedirectResponse(
                    url=_build_settings_redirect_url(
                        error_message="Informe os itens da lista separados por vírgula.",
                        redirect_menu=redirect_menu,
                        redirect_target=redirect_target,
                        settings_edit_key=clean_menu_key,
                        settings_action="edit",
                        settings_tab="lista",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            raw_key = process_list_key[row_index] if row_index < len(process_list_key) else ""
            list_key = normalize_list_key_v2(raw_key, label)
            base_key = list_key
            suffix = 2

            while list_key in seen_keys:
                list_key = f"{base_key}_{suffix}"
                suffix += 1

            seen_keys.add(list_key)

            process_lists.append(
                {
                    "key": list_key,
                    "label": label,
                    "items": items,
                    "items_csv": ", ".join(items),
                }
            )

        raw_config = existing_row.get("menu_config")

        if isinstance(raw_config, dict):
            menu_config = dict(raw_config)
        elif isinstance(raw_config, str) and raw_config.strip():
            try:
                menu_config = json.loads(raw_config)
            except json.JSONDecodeError:
                menu_config = {}
        else:
            menu_config = {}

        menu_config["process_lists"] = process_lists

        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": clean_menu_key,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            },
        )
        session.commit()

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Listas do processo atualizadas com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="lista",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
'''
        content = content.rstrip() + append_route + "\n"

    write_file(path, content)
    print("OK: settings_handlers.py atualizado.")


####################################################################################
# (7) PATCH templates/new_user.html
####################################################################################

def patch_template_v2() -> None:
    path = FILES["template"]
    content = read_file(path)

    content = re.sub(
        r'\s*<script[^>]+force_lista_tab_v1\.js[^>]*></script>\s*',
        "\n",
        content,
        flags=re.IGNORECASE,
    )

    if "settings_tab=lista" not in content:
        anchor_pattern = re.compile(
            r'(<a\b[^>]*settings_tab=campos-adicionais[^>]*>[\s\S]*?</a>)',
            re.IGNORECASE,
        )

        match = anchor_pattern.search(content)

        if match:
            original_anchor = match.group(1)
            lista_anchor = original_anchor
            lista_anchor = lista_anchor.replace("campos-adicionais", "lista")
            lista_anchor = lista_anchor.replace("campos_adicionais", "lista")
            lista_anchor = lista_anchor.replace("Campos adicionais", "Lista")
            lista_anchor = lista_anchor.replace("campos adicionais", "Lista")
            content = content[:match.end()] + "\n              " + lista_anchor + content[match.end()]
            print("OK: aba Lista adicionada junto às outras abas.")
        else:
            raise RuntimeError(
                "Não encontrei a aba Campos adicionais no template. "
                "Procure por settings_tab=campos-adicionais em templates/new_user.html."
            )

    if "APPVERBO_PROCESS_LISTS_PANEL_V2" not in content:
        panel_block = r'''
              <!-- APPVERBO_PROCESS_LISTS_PANEL_V2 -->
              {% if settings_tab == "lista" %}
              {% set process_lists = settings_edit_data.process_lists|default([]) %}
              <div class="admin-subsection process-lists-panel-v2" id="settings-process-lists-card">
                <h3>Lista</h3>
                <p class="muted">
                  Crie listas reutilizáveis para usar no tipo de campo Lista.
                  Separe os itens por vírgula. Ex.: Ativo, Inativo, Pendente, Em acompanhamento.
                </p>

                <form method="post" action="/settings/menu/process-lists">
                  <input type="hidden" name="menu_key" value="{{ settings_edit_data.key }}">
                  <input type="hidden" name="redirect_menu" value="administrativo">
                  <input type="hidden" name="redirect_target" value="#settings-menu-edit-card">

                  <div class="process-lists-rows-v2">
                    {% for process_list in process_lists %}
                    <div class="process-list-row-v2">
                      <input type="hidden" name="process_list_key" value="{{ process_list.key }}">
                      <div class="field">
                        <label>Nome da lista</label>
                        <input
                          name="process_list_label"
                          value="{{ process_list.label }}"
                          placeholder="Ex.: Estado"
                        >
                      </div>
                      <div class="field full">
                        <label>Itens da lista separados por vírgula</label>
                        <input
                          name="process_list_items_csv"
                          value="{{ process_list.items_csv }}"
                          placeholder="Ativo, Inativo, Pendente, Em acompanhamento"
                        >
                      </div>
                      <div class="field process-list-actions-v2">
                        <button type="button" class="action-btn-cancel" onclick="this.closest('.process-list-row-v2').remove()">Remover</button>
                      </div>
                    </div>
                    {% endfor %}

                    <div class="process-list-row-v2">
                      <input type="hidden" name="process_list_key" value="">
                      <div class="field">
                        <label>Nome da lista</label>
                        <input name="process_list_label" placeholder="Ex.: Estado">
                      </div>
                      <div class="field full">
                        <label>Itens da lista separados por vírgula</label>
                        <input name="process_list_items_csv" placeholder="Ativo, Inativo, Pendente, Em acompanhamento">
                      </div>
                      <div class="field process-list-actions-v2">
                        <button type="button" class="action-btn-cancel" onclick="this.closest('.process-list-row-v2').remove()">Remover</button>
                      </div>
                    </div>
                  </div>

                  <div class="form-action-row">
                    <button type="button" class="action-btn-secondary" id="add-process-list-row-v2">Adicionar lista</button>
                    <button type="submit" class="action-btn">Guardar listas</button>
                  </div>
                </form>
              </div>
              {% endif %}
              <!-- /APPVERBO_PROCESS_LISTS_PANEL_V2 -->
'''

        insert_index = content.find("<h3>Campos Adicionais")
        if insert_index < 0:
            insert_index = content.find("<h3>Campos adicionais")

        if insert_index >= 0:
            block_start = content.rfind("{% if", 0, insert_index)
            if block_start >= 0 and "campos" in content[block_start:insert_index].lower():
                content = content[:block_start] + panel_block + "\n" + content[block_start:]
            else:
                content = content[:insert_index] + panel_block + "\n" + content[insert_index:]
            print("OK: painel da aba Lista inserido no template.")
        else:
            raise RuntimeError(
                "Não encontrei o bloco Campos Adicionais para inserir o painel Lista."
            )

    script_tag = '<script src="/static/js/modules/process_lists_runtime_v2.js?v=20260428b"></script>'
    if "process_lists_runtime_v2.js" not in content:
        marker = '<script src="/static/js/new_user.js'
        marker_index = content.find(marker)

        if marker_index >= 0:
            insert_at = content.find("</script>", marker_index)
            insert_at += len("</script>")
            content = content[:insert_at] + "\n  " + script_tag + content[insert_at:]
        else:
            endblock_index = content.rfind("{% endblock %}")
            content = content[:endblock_index] + "  " + script_tag + "\n" + content[endblock_index:]

        print("OK: process_lists_runtime_v2.js injetado no template.")

    write_file(path, content)
    print("OK: new_user.html atualizado.")


####################################################################################
# (8) PATCH static/js/new_user.js
####################################################################################

def patch_new_user_js_v2() -> None:
    path = FILES["new_user_js"]
    content = read_file(path)

    if '"lista": "lista"' not in content:
        content = replace_once(
            content,
            '    "adicionais": "campos-adicionais"',
            '    "adicionais": "campos-adicionais",\n'
            '    "lista": "lista"',
            "normalizeSettingsTabKey lista",
        )

    content = content.replace(
        'const processSupportedTypes = new Set(["text", "number", "email", "phone", "date", "flag"]);',
        'const processSupportedTypes = new Set(["text", "number", "email", "phone", "date", "flag", "list"]);',
    )

    if "listKey: normalizeMenuKey(option.list_key || option.listKey)," not in content:
        content = replace_once(
            content,
            '      size: optionSize,\n'
            '      isRequired: normalizeProcessFieldRequired(option.is_required ?? option.required)\n'
            '    });',
            '      size: optionSize,\n'
            '      listKey: normalizeMenuKey(option.list_key || option.listKey),\n'
            '      isRequired: normalizeProcessFieldRequired(option.is_required ?? option.required)\n'
            '    });',
            "option listKey",
        )

    if "listKey: normalizeMenuKey(fieldMeta.listKey)," not in content:
        content = replace_once(
            content,
            '      isRequired: Boolean(fieldMeta.isRequired),\n'
            '      value: typeof fieldValue === "string" ? fieldValue : "",',
            '      isRequired: Boolean(fieldMeta.isRequired),\n'
            '      listKey: normalizeMenuKey(fieldMeta.listKey),\n'
            '      value: typeof fieldValue === "string" ? fieldValue : "",',
            "field listKey",
        )

    write_file(path, content)
    print("OK: new_user.js atualizado.")


####################################################################################
# (9) PATCH static/js/modules/settings_process_tabs.js
####################################################################################

def patch_settings_process_tabs_js_v2() -> None:
    path = FILES["settings_process_tabs_js"]

    if not path.exists():
        print("AVISO: settings_process_tabs.js não existe. Ignorado.")
        return

    content = read_file(path)

    if '"lista": "lista"' not in content:
        content = content.replace(
            '      "adicionais": "campos-adicionais"',
            '      "adicionais": "campos-adicionais",\n'
            '      "lista": "lista"',
        )

    write_file(path, content)
    print("OK: settings_process_tabs.js atualizado.")


####################################################################################
# (10) CRIAR static/js/modules/process_lists_runtime_v2.js
####################################################################################

def create_runtime_js_v2() -> None:
    path = FILES["runtime_js"]

    content = r'''//###################################################################################
// APPVERBOBRAGA - LISTA V2 - RUNTIME DA ABA LISTA E DO TIPO LISTA
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNÇÕES AUXILIARES
  //###################################################################################

  function normalizeKey_v2(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function getBootstrap_v2() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function getUrlParam_v2(name) {
    try {
      return new URL(window.location.href).searchParams.get(name) || "";
    } catch (error) {
      return "";
    }
  }

  function getSettingsEditKey_v2() {
    return normalizeKey_v2(getUrlParam_v2("settings_edit_key") || getBootstrap_v2().settingsEditKey);
  }

  function getCurrentSetting_v2() {
    const key = getSettingsEditKey_v2();
    const settings = Array.isArray(getBootstrap_v2().sidebarMenuSettings)
      ? getBootstrap_v2().sidebarMenuSettings
      : [];

    return settings.find(function (setting) {
      return normalizeKey_v2(setting.key) === key;
    }) || null;
  }

  function getProcessLists_v2() {
    const setting = getCurrentSetting_v2();

    return setting && Array.isArray(setting.process_lists)
      ? setting.process_lists
      : [];
  }

  function getProcessFieldOptions_v2() {
    const setting = getCurrentSetting_v2();

    return setting && Array.isArray(setting.process_field_options)
      ? setting.process_field_options
      : [];
  }

  function getListByKey_v2(listKey) {
    const cleanListKey = normalizeKey_v2(listKey);

    return getProcessLists_v2().find(function (item) {
      return normalizeKey_v2(item.key) === cleanListKey;
    }) || null;
  }

  //###################################################################################
  // (2) ADICIONAR LINHA NA ABA LISTA
  //###################################################################################

  function bindAddProcessListRow_v2() {
    const button = document.getElementById("add-process-list-row-v2");
    const container = document.querySelector(".process-lists-rows-v2");

    if (!button || !container || button.dataset.boundListaV2 === "1") {
      return;
    }

    button.dataset.boundListaV2 = "1";

    button.addEventListener("click", function () {
      const row = document.createElement("div");
      row.className = "process-list-row-v2";
      row.innerHTML = [
        '<input type="hidden" name="process_list_key" value="">',
        '<div class="field">',
        '  <label>Nome da lista</label>',
        '  <input name="process_list_label" placeholder="Ex.: Estado">',
        '</div>',
        '<div class="field full">',
        '  <label>Itens da lista separados por vírgula</label>',
        '  <input name="process_list_items_csv" placeholder="Ativo, Inativo, Pendente, Em acompanhamento">',
        '</div>',
        '<div class="field process-list-actions-v2">',
        '  <button type="button" class="action-btn-cancel" data-remove-list-row-v2>Remover</button>',
        '</div>'
      ].join("");

      row.querySelector("[data-remove-list-row-v2]").addEventListener("click", function () {
        row.remove();
      });

      container.appendChild(row);
    });
  }

  //###################################################################################
  // (3) CRIAR SELECT DE LISTAS NA CONFIGURAÇÃO DE CAMPOS
  //###################################################################################

  function buildListSelect_v2(selectedValue) {
    const select = document.createElement("select");
    select.name = "additional_field_list_key";

    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = getProcessLists_v2().length
      ? "Selecione a lista"
      : "Crie uma lista na aba Lista";
    select.appendChild(emptyOption);

    getProcessLists_v2().forEach(function (item) {
      const option = document.createElement("option");
      option.value = normalizeKey_v2(item.key);
      option.textContent = item.label || item.key;

      if (normalizeKey_v2(selectedValue) === normalizeKey_v2(item.key)) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function enhanceAdditionalFieldsForm_v2() {
    const forms = Array.from(
      document.querySelectorAll("form[action*='/settings/menu/process-additional-fields']")
    );

    if (!forms.length) {
      return;
    }

    const processFields = getProcessFieldOptions_v2();

    forms.forEach(function (form) {
      const typeSelects = Array.from(form.querySelectorAll("select[name='additional_field_type']"));

      typeSelects.forEach(function (typeSelect, index) {
        if (!typeSelect.querySelector("option[value='list']")) {
          const option = document.createElement("option");
          option.value = "list";
          option.textContent = "Lista";
          typeSelect.appendChild(option);
        }

        const row = typeSelect.closest(".additional-field-row-equalized")
          || (typeSelect.closest(".field") ? typeSelect.closest(".field").parentElement : null)
          || typeSelect.parentElement;

        if (!row || row.querySelector("[data-list-picker-v2]")) {
          return;
        }

        const currentMeta = processFields[index] || {};
        const picker = document.createElement("div");
        picker.className = "field additional-field-list-col-v2";
        picker.setAttribute("data-list-picker-v2", "1");

        const label = document.createElement("label");
        label.textContent = "Lista";
        picker.appendChild(label);
        picker.appendChild(buildListSelect_v2(currentMeta.list_key || currentMeta.listKey || ""));

        row.appendChild(picker);

        function refreshPicker_v2() {
          picker.style.display = typeSelect.value === "list" ? "" : "none";
        }

        typeSelect.addEventListener("change", refreshPicker_v2);
        refreshPicker_v2();
      });
    });
  }

  //###################################################################################
  // (4) TRANSFORMAR CAMPO LISTA EM SELECT NO PROCESSO
  //###################################################################################

  function enhanceDynamicProcessListFields_v2() {
    const setting = getCurrentSetting_v2();

    if (!setting) {
      return;
    }

    const menuKey = normalizeKey_v2(setting.key || getUrlParam_v2("menu"));

    if (!menuKey) {
      return;
    }

    const listFields = getProcessFieldOptions_v2().filter(function (field) {
      return normalizeKey_v2(field.field_type || field.fieldType) === "list";
    });

    listFields.forEach(function (field) {
      const fieldKey = normalizeKey_v2(field.key);
      const listKey = normalizeKey_v2(field.list_key || field.listKey);
      const processList = getListByKey_v2(listKey);

      if (!fieldKey || !processList) {
        return;
      }

      const inputName = "process__" + menuKey + "__" + fieldKey;
      const currentInput = document.querySelector('[name="' + inputName + '"]');

      if (!currentInput || currentInput.tagName.toLowerCase() === "select") {
        return;
      }

      const select = document.createElement("select");
      select.name = currentInput.name;
      select.id = currentInput.id;
      select.className = currentInput.className;

      if (currentInput.required) {
        select.required = true;
      }

      const emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = "Selecione";
      select.appendChild(emptyOption);

      const currentValue = String(currentInput.value || "");
      const items = Array.isArray(processList.items) ? processList.items : [];

      items.forEach(function (item) {
        const option = document.createElement("option");
        option.value = String(item || "");
        option.textContent = String(item || "");

        if (String(item || "") === currentValue) {
          option.selected = true;
        }

        select.appendChild(option);
      });

      currentInput.replaceWith(select);
    });
  }

  //###################################################################################
  // (5) INICIALIZAÇÃO
  //###################################################################################

  function inicializarListaV2_v2() {
    bindAddProcessListRow_v2();
    enhanceAdditionalFieldsForm_v2();
    enhanceDynamicProcessListFields_v2();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarListaV2_v2);
  } else {
    inicializarListaV2_v2();
  }

  window.setTimeout(inicializarListaV2_v2, 100);
  window.setTimeout(inicializarListaV2_v2, 400);
  window.setTimeout(inicializarListaV2_v2, 1000);
  window.setTimeout(inicializarListaV2_v2, 1800);
})();
'''

    write_file(path, content)
    print("OK: process_lists_runtime_v2.js criado.")


####################################################################################
# (11) PATCH CSS
####################################################################################

def patch_css_v2() -> None:
    path = FILES["css"]
    content = read_file(path)

    if "Processo Lista V2" in content:
        print("AVISO: CSS da Lista V2 já existe.")
        return

    css_block = r'''

/* ###################################################################################
   Processo Lista V2
################################################################################### */

.process-lists-panel-v2 {
  margin-top: 16px;
}

.process-lists-rows-v2 {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.process-list-row-v2 {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(320px, 2fr) auto;
  gap: 12px;
  align-items: end;
  width: 100%;
}

.process-list-actions-v2 {
  display: flex;
  align-items: end;
  justify-content: flex-start;
}

.additional-field-list-col-v2 {
  min-width: 180px;
}

@media (max-width: 900px) {
  .process-list-row-v2 {
    grid-template-columns: 1fr;
  }
}
'''

    content = content.rstrip() + "\n" + css_block
    write_file(path, content)
    print("OK: CSS atualizado.")


####################################################################################
# (12) EXECUÇÃO PRINCIPAL
####################################################################################

def main() -> None:
    validate_project_v2()

    for path in FILES.values():
        backup_file(path)

    patch_menu_settings_v2()
    patch_admin_tabs_v2()
    patch_settings_handlers_v2()
    patch_template_v2()
    patch_new_user_js_v2()
    patch_settings_process_tabs_js_v2()
    create_runtime_js_v2()
    patch_css_v2()

    run_command([sys.executable, "-m", "py_compile", "appverbo/menu_settings.py"])
    run_command([sys.executable, "-m", "py_compile", "appverbo/routes/profile/settings_handlers.py"])

    print("OK: patch Processo Lista V2 aplicado.")


if __name__ == "__main__":
    main()