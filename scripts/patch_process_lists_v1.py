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

FILES = {
    "menu_settings": ROOT / "appverbo" / "menu_settings.py",
    "settings_handlers": ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py",
    "settings_process_tabs": ROOT / "static" / "js" / "modules" / "settings_process_tabs.js",
    "new_user_js": ROOT / "static" / "js" / "new_user.js",
    "new_user_html": ROOT / "templates" / "new_user.html",
    "process_lists_js": ROOT / "static" / "js" / "modules" / "process_lists_v1.js",
}

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


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
        backup_path = path.with_name(f"{path.name}.bak_lista_v1_{TIMESTAMP}")
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

    return content.replace(old, new, 1)


####################################################################################
# (3) VALIDAÇÃO DO PROJETO
####################################################################################

def validate_project_v1() -> None:
    required_paths = [
        ROOT / "appverbo",
        FILES["menu_settings"],
        FILES["settings_handlers"],
        FILES["settings_process_tabs"],
        FILES["new_user_js"],
        FILES["new_user_html"],
    ]

    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(f"Não encontrado: {path}")

    print("OK: projeto validado.")


####################################################################################
# (4) PATCH appverbo/menu_settings.py
####################################################################################

def patch_menu_settings_v1() -> None:
    path = FILES["menu_settings"]
    content = read_file(path)

    if '"list", "label": "Lista"' not in content and "'list', 'label': 'Lista'" not in content:
        content = replace_once(
            content,
            '    {"key": "header", "label": "Cabeçalho (aba)"},\n)',
            '    {"key": "header", "label": "Cabeçalho (aba)"},\n'
            '    {"key": "list", "label": "Lista"},\n'
            ')',
            "ADDITIONAL_FIELD_TYPES Lista",
        )

    if '"lista"' not in content:
        content = replace_once(
            content,
            '    "configuracao": ["geral", "configuracao_campos", "campos_adicionais"],',
            '    "configuracao": ["geral", "configuracao_campos", "campos_adicionais", "lista"],',
            "MENU_PROCESS_DEFAULT_VISIBLE_FIELDS_BY_KEY configuracao",
        )

    if "def normalize_menu_process_lists_v1" not in content:
        append_block = r'''

####################################################################################
# LISTA V1 - LISTAS REUTILIZÁVEIS DO PROCESSO
####################################################################################

def _normalize_process_list_key_v1(raw_key: Any) -> str:
    clean_key = str(raw_key or "").strip().lower()
    clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
    clean_key = re.sub(r"_+", "_", clean_key).strip("_")

    if not clean_key:
        return ""

    if not clean_key.startswith("list_"):
        clean_key = f"list_{clean_key}"

    return clean_key


def _build_process_list_key_from_label_v1(label: str) -> str:
    base_key = _build_menu_key_from_label(label)

    if not base_key:
        base_key = "lista"

    return _normalize_process_list_key_v1(base_key)


def _normalize_process_list_items_csv_v1(raw_items: Any) -> list[str]:
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


def normalize_menu_process_lists_v1(raw_lists: Any) -> list[dict[str, Any]]:
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
            _normalize_process_list_key_v1(raw_item.get("key"))
            or _build_process_list_key_from_label_v1(label)
        )

        base_key = list_key
        suffix = 2

        while list_key in seen_keys:
            list_key = f"{base_key}_{suffix}"
            suffix += 1

        seen_keys.add(list_key)

        items = _normalize_process_list_items_csv_v1(
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


def get_menu_process_lists_v1(menu_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not isinstance(menu_config, dict):
        return []

    return normalize_menu_process_lists_v1(menu_config.get("process_lists"))


if "_original_normalize_menu_process_additional_fields_for_list_v1" not in globals():
    _original_normalize_menu_process_additional_fields_for_list_v1 = normalize_menu_process_additional_fields


def normalize_menu_process_additional_fields_v2(raw_fields: Any) -> list[dict[str, Any]]:
    normalized = _original_normalize_menu_process_additional_fields_for_list_v1(raw_fields)

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

        item["list_key"] = _normalize_process_list_key_v1(
            raw_item.get("list_key", raw_item.get("process_list_key", raw_item.get("lista")))
        )

    return normalized


normalize_menu_process_additional_fields = normalize_menu_process_additional_fields_v2


if "_original_get_sidebar_menu_settings_for_lists_v1" not in globals():
    _original_get_sidebar_menu_settings_for_lists_v1 = get_sidebar_menu_settings


def get_sidebar_menu_settings_v2(session: Session) -> list[dict[str, Any]]:
    settings = _original_get_sidebar_menu_settings_for_lists_v1(session)

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
        process_lists = get_menu_process_lists_v1(menu_config)
        item["process_lists"] = process_lists
        item["process_list_options"] = [
            {"key": process_list["key"], "label": process_list["label"]}
            for process_list in process_lists
        ]

    return settings


get_sidebar_menu_settings = get_sidebar_menu_settings_v2
'''
        content = content.rstrip() + append_block + "\n"

    write_file(path, content)
    print("OK: menu_settings.py atualizado.")


####################################################################################
# (5) PATCH appverbo/process_settings/admin_tabs.py
####################################################################################

def patch_admin_tabs_v1() -> None:
    path = ROOT / "appverbo" / "process_settings" / "admin_tabs.py"

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

def patch_settings_handlers_v1() -> None:
    path = FILES["settings_handlers"]
    content = read_file(path)

    content = content.replace(
        'if clean_settings_tab in {"geral", "campos-config", "campos-adicionais"}:',
        'if clean_settings_tab in {"geral", "campos-config", "campos-adicionais", "lista"}:',
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

    if "def edit_sidebar_menu_process_lists_v1" not in content:
        append_route = r'''


@router.post("/settings/menu/process-lists", response_class=HTMLResponse)
def edit_sidebar_menu_process_lists_v1(
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

        def normalize_list_key(raw_key: str, label: str) -> str:
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

        def normalize_items(raw_csv: str) -> list[str]:
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
            items = normalize_items(raw_items_csv)

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
            list_key = normalize_list_key(raw_key, label)
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
# (7) PATCH static/js/modules/settings_process_tabs.js
####################################################################################

def patch_settings_process_tabs_v1() -> None:
    path = FILES["settings_process_tabs"]
    content = read_file(path)

    if '"lista": "lista"' not in content:
        content = replace_once(
            content,
            '      "adicionais": "campos-adicionais"',
            '      "adicionais": "campos-adicionais",\n'
            '      "lista": "lista"',
            "alias lista",
        )

    if 'text === "lista"' not in content:
        content = replace_once(
            content,
            '        element.textContent = "Campos adicionais";\n'
            '      }',
            '        element.textContent = "Campos adicionais";\n'
            '        return;\n'
            '      }\n\n'
            '      if (text === "lista") {\n'
            '        element.textContent = "Lista";\n'
            '      }',
            "label Lista",
        )

    write_file(path, content)
    print("OK: settings_process_tabs.js atualizado.")


####################################################################################
# (8) PATCH static/js/new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    path = FILES["new_user_js"]
    content = read_file(path)

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
# (9) CRIAR static/js/modules/process_lists_v1.js
####################################################################################

def create_process_lists_js_v1() -> None:
    path = FILES["process_lists_js"]

    content = r'''//###################################################################################
// APPVERBOBRAGA - ABA LISTA + TIPO DE CAMPO LISTA
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNÇÕES AUXILIARES
  //###################################################################################

  function normalizeKey(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function getBootstrap() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function getUrlParam(name) {
    try {
      return new URL(window.location.href).searchParams.get(name) || "";
    } catch (error) {
      return "";
    }
  }

  function getSettingsEditKey() {
    return normalizeKey(getUrlParam("settings_edit_key") || getBootstrap().settingsEditKey);
  }

  function getCurrentSettingsTab() {
    return normalizeKey(getUrlParam("settings_tab") || getBootstrap().settingsTab).replace(/_/g, "-");
  }

  function getCurrentSetting() {
    const key = getSettingsEditKey();
    const settings = Array.isArray(getBootstrap().sidebarMenuSettings)
      ? getBootstrap().sidebarMenuSettings
      : [];

    return settings.find(function (setting) {
      return normalizeKey(setting.key) === key;
    }) || null;
  }

  function getProcessLists() {
    const setting = getCurrentSetting();

    return setting && Array.isArray(setting.process_lists)
      ? setting.process_lists
      : [];
  }

  function getListByKey(listKey) {
    const cleanListKey = normalizeKey(listKey);

    return getProcessLists().find(function (item) {
      return normalizeKey(item.key) === cleanListKey;
    }) || null;
  }

  function getProcessFieldOptions() {
    const setting = getCurrentSetting();

    return setting && Array.isArray(setting.process_field_options)
      ? setting.process_field_options
      : [];
  }

  //###################################################################################
  // (2) GARANTIR ABA LISTA
  //###################################################################################

  function buildListaHref() {
    const url = new URL(window.location.href);
    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("settings_action", "edit");
    url.searchParams.set("settings_tab", "lista");

    const key = getSettingsEditKey();

    if (key) {
      url.searchParams.set("settings_edit_key", key);
    }

    url.hash = "settings-menu-edit-card";

    return `${url.pathname}${url.search}${url.hash}`;
  }

  function ensureListaTab() {
    const key = getSettingsEditKey();

    if (!key) {
      return;
    }

    if (document.querySelector("[data-settings-tab='lista'], a[href*='settings_tab=lista']")) {
      return;
    }

    const candidates = Array.from(
      document.querySelectorAll("a[href*='settings_tab='], button[data-settings-tab]")
    );

    if (!candidates.length) {
      return;
    }

    const reference = candidates.find(function (element) {
      return String(element.getAttribute("href") || "").includes("settings_tab=campos-adicionais")
        || String(element.getAttribute("data-settings-tab") || "") === "campos-adicionais";
    }) || candidates[candidates.length - 1];

    const listaTab = reference.cloneNode(true);
    listaTab.textContent = "Lista";
    listaTab.setAttribute("data-settings-tab", "lista");

    if (listaTab.tagName && listaTab.tagName.toLowerCase() === "a") {
      listaTab.setAttribute("href", buildListaHref());
    }

    reference.insertAdjacentElement("afterend", listaTab);
  }

  //###################################################################################
  // (3) RENDERIZAR ABA LISTA
  //###################################################################################

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function buildListRow(item) {
    const row = document.createElement("div");
    row.className = "process-list-row-v1";

    const itemsCsv = item.items_csv || (Array.isArray(item.items) ? item.items.join(", ") : "");

    row.innerHTML = [
      `<input type="hidden" name="process_list_key" value="${escapeHtml(item.key || "")}">`,
      `<div class="field">`,
      `  <label>Nome da lista</label>`,
      `  <input name="process_list_label" value="${escapeHtml(item.label || "")}" placeholder="Ex.: Estado">`,
      `</div>`,
      `<div class="field full">`,
      `  <label>Itens da lista separados por vírgula</label>`,
      `  <input name="process_list_items_csv" value="${escapeHtml(itemsCsv)}" placeholder="Ativo, Inativo, Pendente, Em acompanhamento">`,
      `</div>`,
      `<div class="field process-list-actions-v1">`,
      `  <button type="button" class="action-btn-cancel" data-remove-process-list>Remover</button>`,
      `</div>`
    ].join("");

    row.querySelector("[data-remove-process-list]").addEventListener("click", function () {
      row.remove();
    });

    return row;
  }

  function renderListaTab() {
    if (getCurrentSettingsTab() !== "lista") {
      return;
    }

    const key = getSettingsEditKey();
    const card = document.getElementById("settings-menu-edit-card");

    if (!key || !card) {
      return;
    }

    if (card.querySelector("[data-process-list-pane-v1]")) {
      return;
    }

    Array.from(card.querySelectorAll("form")).forEach(function (form) {
      if (!String(form.getAttribute("action") || "").includes("/settings/menu/process-lists")) {
        form.style.display = "none";
      }
    });

    const pane = document.createElement("section");
    pane.className = "admin-subsection";
    pane.setAttribute("data-process-list-pane-v1", "1");

    const lists = getProcessLists();
    const rows = lists.length ? lists : [{ key: "", label: "", items_csv: "" }];

    pane.innerHTML = [
      `<h3>Lista</h3>`,
      `<p class="muted">Crie listas reutilizáveis. Separe os itens por vírgula. Ex.: Ativo, Inativo, Pendente, Em acompanhamento.</p>`,
      `<form method="post" action="/settings/menu/process-lists" id="process-lists-form-v1">`,
      `  <input type="hidden" name="menu_key" value="${escapeHtml(key)}">`,
      `  <input type="hidden" name="redirect_menu" value="administrativo">`,
      `  <input type="hidden" name="redirect_target" value="#settings-menu-edit-card">`,
      `  <div id="process-lists-rows-v1" class="process-lists-rows-v1"></div>`,
      `  <div class="form-action-row">`,
      `    <button type="button" class="action-btn-secondary" id="add-process-list-v1">Adicionar lista</button>`,
      `    <button type="submit" class="action-btn">Guardar listas</button>`,
      `  </div>`,
      `</form>`
    ].join("");

    const rowsContainer = pane.querySelector("#process-lists-rows-v1");

    rows.forEach(function (item) {
      rowsContainer.appendChild(buildListRow(item));
    });

    pane.querySelector("#add-process-list-v1").addEventListener("click", function () {
      rowsContainer.appendChild(buildListRow({ key: "", label: "", items_csv: "" }));
    });

    const header = card.querySelector("h2, .profile-card-header, .admin-subsection");

    if (header && header.parentNode === card) {
      header.insertAdjacentElement("afterend", pane);
    } else {
      card.prepend(pane);
    }
  }

  //###################################################################################
  // (4) ACRESCENTAR TIPO LISTA NA CONFIGURAÇÃO DOS CAMPOS
  //###################################################################################

  function buildListSelect(selectedValue) {
    const select = document.createElement("select");
    select.name = "additional_field_list_key";

    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = getProcessLists().length ? "Selecione a lista" : "Crie uma lista na aba Lista";
    select.appendChild(emptyOption);

    getProcessLists().forEach(function (item) {
      const option = document.createElement("option");
      option.value = normalizeKey(item.key);
      option.textContent = item.label || item.key;

      if (normalizeKey(selectedValue) === normalizeKey(item.key)) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function enhanceAdditionalFieldsForm() {
    const forms = Array.from(
      document.querySelectorAll("form[action*='/settings/menu/process-additional-fields']")
    );

    if (!forms.length) {
      return;
    }

    const processFields = getProcessFieldOptions();

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

        if (!row || row.querySelector("[data-list-picker-v1]")) {
          return;
        }

        const currentMeta = processFields[index] || {};
        const picker = document.createElement("div");
        picker.className = "field additional-field-list-col-v1";
        picker.setAttribute("data-list-picker-v1", "1");

        const label = document.createElement("label");
        label.textContent = "Lista";
        picker.appendChild(label);
        picker.appendChild(buildListSelect(currentMeta.list_key || currentMeta.listKey || ""));

        row.appendChild(picker);

        function refreshPicker() {
          picker.style.display = typeSelect.value === "list" ? "" : "none";
        }

        typeSelect.addEventListener("change", refreshPicker);
        refreshPicker();
      });
    });
  }

  //###################################################################################
  // (5) TRANSFORMAR CAMPO LISTA EM SELECT NO PROCESSO
  //###################################################################################

  function enhanceDynamicProcessListFields() {
    const setting = getCurrentSetting();

    if (!setting) {
      return;
    }

    const menuKey = normalizeKey(setting.key || getUrlParam("menu"));

    if (!menuKey) {
      return;
    }

    const listFields = getProcessFieldOptions().filter(function (field) {
      return normalizeKey(field.field_type || field.fieldType) === "list";
    });

    listFields.forEach(function (field) {
      const fieldKey = normalizeKey(field.key);
      const listKey = normalizeKey(field.list_key || field.listKey);
      const processList = getListByKey(listKey);

      if (!fieldKey || !processList) {
        return;
      }

      const inputName = `process__${menuKey}__${fieldKey}`;
      const currentInput = document.querySelector(`[name="${inputName}"]`);

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
  // (6) INICIALIZAÇÃO
  //###################################################################################

  function run() {
    ensureListaTab();
    renderListaTab();
    enhanceAdditionalFieldsForm();
    enhanceDynamicProcessListFields();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }

  window.setTimeout(run, 100);
  window.setTimeout(run, 400);
  window.setTimeout(run, 1000);
  window.setTimeout(run, 1800);
})();
'''
    write_file(path, content)
    print("OK: process_lists_v1.js criado.")


####################################################################################
# (10) PATCH templates/new_user.html
####################################################################################

def patch_new_user_html_v1() -> None:
    path = FILES["new_user_html"]
    content = read_file(path)

    script_tag = '<script src="/static/js/modules/process_lists_v1.js?v=20260428a"></script>'

    if "process_lists_v1.js" in content:
        print("AVISO: process_lists_v1.js já está no template.")
        return

    match = re.search(r'(<script src="/static/js/new_user\.js[^"]*"></script>)', content)

    if match:
        content = content[:match.end()] + "\n  " + script_tag + content[match.end():]
    else:
        last_endblock = content.rfind("{% endblock %}")

        if last_endblock >= 0:
            content = content[:last_endblock] + "  " + script_tag + "\n" + content[last_endblock:]
        else:
            content = content + "\n" + script_tag + "\n"

    write_file(path, content)
    print("OK: new_user.html atualizado.")


####################################################################################
# (11) EXECUÇÃO PRINCIPAL
####################################################################################

def main() -> None:
    validate_project_v1()

    for path in FILES.values():
        backup_file(path)

    patch_menu_settings_v1()
    patch_admin_tabs_v1()
    patch_settings_handlers_v1()
    patch_settings_process_tabs_v1()
    patch_new_user_js_v1()
    create_process_lists_js_v1()
    patch_new_user_html_v1()

    run_command([sys.executable, "-m", "py_compile", "appverbo/menu_settings.py"])
    run_command([sys.executable, "-m", "py_compile", "appverbo/routes/profile/settings_handlers.py"])

    print("OK: patch Processo Lista V1 aplicado.")


if __name__ == "__main__":
    main()