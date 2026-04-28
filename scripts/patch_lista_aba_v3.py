from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import shutil
import subprocess
import sys


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

ROOT = Path.cwd()
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"
CSS_PATH = ROOT / "static" / "css" / "new_user.css"
RUNTIME_JS_PATH = ROOT / "static" / "js" / "modules" / "process_lists_runtime_v3.js"


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
        backup_path = path.with_name(f"{path.name}.bak_lista_aba_v3_{TIMESTAMP}")
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

def validar_projeto_v3() -> None:
    required = [
        ROOT / "appverbo",
        TEMPLATE_PATH,
        SETTINGS_HANDLERS_PATH,
        MENU_SETTINGS_PATH,
        CSS_PATH,
    ]

    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"Não encontrado: {path}")

    print("OK: projeto validado.")


####################################################################################
# (4) CORRIGIR settings_handlers.py
####################################################################################

def corrigir_settings_handlers_v3() -> None:
    content = read_file(SETTINGS_HANDLERS_PATH)

    ####################################################################################
    # (4.1) CORRIGIR ERRO DE SINTAXE GERADO PELO PATCH ANTERIOR
    ####################################################################################

    content = re.sub(
        r'("adicionais"\s*:\s*"campos-adicionais")\s*,\s*,\s*"lista"\s*\}',
        r'\1, "lista": "lista"}',
        content,
    )

    content = content.replace(
        '"adicionais": "campos-adicionais",, "lista"}',
        '"adicionais": "campos-adicionais", "lista": "lista"}',
    )

    content = content.replace(
        '"adicionais": "campos-adicionais", "lista"}',
        '"adicionais": "campos-adicionais", "lista": "lista"}',
    )

    ####################################################################################
    # (4.2) GARANTIR QUE settings_tab=lista É ACEITE
    ####################################################################################

    content = content.replace(
        '{"geral", "campos-config", "campos-adicionais"}',
        '{"geral", "campos-config", "campos-adicionais", "lista"}',
    )

    content = content.replace(
        '{"geral", "configuracao_campos", "campos_adicionais"}',
        '{"geral", "configuracao_campos", "campos_adicionais", "lista"}',
    )

    content = content.replace(
        '["geral", "campos-config", "campos-adicionais"]',
        '["geral", "campos-config", "campos-adicionais", "lista"]',
    )

    content = content.replace(
        '["geral", "configuracao_campos", "campos_adicionais"]',
        '["geral", "configuracao_campos", "campos_adicionais", "lista"]',
    )

    ####################################################################################
    # (4.3) GARANTIR list_key NOS CAMPOS ADICIONAIS
    ####################################################################################

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
            "rows_count additional_field_list_key",
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

    ####################################################################################
    # (4.4) CRIAR ROTA PARA GRAVAR LISTAS
    ####################################################################################

    if "def edit_sidebar_menu_process_lists_v3" not in content:
        route_block = r'''


@router.post("/settings/menu/process-lists", response_class=HTMLResponse)
def edit_sidebar_menu_process_lists_v3(
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

        def normalize_list_key_v3(raw_key: str, label: str) -> str:
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

        def normalize_items_v3(raw_csv: str) -> list[str]:
            values: list[str] = []
            seen: set[str] = set()

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

        process_lists: list[dict[str, object]] = []
        seen_keys: set[str] = set()

        for row_index in range(rows_count):
            label = process_list_label[row_index] if row_index < len(process_list_label) else ""
            label = " ".join(str(label or "").strip().split())

            raw_items_csv = (
                process_list_items_csv[row_index]
                if row_index < len(process_list_items_csv)
                else ""
            )
            items = normalize_items_v3(raw_items_csv)

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
            list_key = normalize_list_key_v3(raw_key, label)
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
        content = content.rstrip() + route_block + "\n"

    write_file(SETTINGS_HANDLERS_PATH, content)
    print("OK: settings_handlers.py corrigido.")


####################################################################################
# (5) CORRIGIR menu_settings.py
####################################################################################

def corrigir_menu_settings_v3() -> None:
    content = read_file(MENU_SETTINGS_PATH)

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

    if "def normalize_menu_process_lists_v3" not in content:
        block = r'''

####################################################################################
# LISTA V3 - LISTAS REUTILIZÁVEIS DO PROCESSO
####################################################################################

def _normalize_process_list_key_v3(raw_key: Any) -> str:
    clean_key = str(raw_key or "").strip().lower()
    clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
    clean_key = re.sub(r"_+", "_", clean_key).strip("_")

    if not clean_key:
        return ""

    if not clean_key.startswith("list_"):
        clean_key = f"list_{clean_key}"

    return clean_key


def normalize_menu_process_lists_v3(raw_lists: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_lists, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for raw_item in raw_lists:
        if not isinstance(raw_item, dict):
            continue

        label = _normalize_sentence_case_text(raw_item.get("label", raw_item.get("name")))

        if not label:
            continue

        list_key = _normalize_process_list_key_v3(raw_item.get("key"))

        if not list_key:
            list_key = _normalize_process_list_key_v3(_build_menu_key_from_label(label))

        if not list_key:
            list_key = "list_lista"

        base_key = list_key
        suffix = 2

        while list_key in seen_keys:
            list_key = f"{base_key}_{suffix}"
            suffix += 1

        seen_keys.add(list_key)

        raw_items = raw_item.get("items_csv", raw_item.get("items"))
        if isinstance(raw_items, str):
            raw_values = raw_items.split(",")
        elif isinstance(raw_items, (list, tuple, set)):
            raw_values = raw_items
        else:
            raw_values = []

        items: list[str] = []
        seen_items: set[str] = set()

        for raw_value in raw_values:
            clean_value = " ".join(str(raw_value or "").strip().split())

            if not clean_value:
                continue

            lookup = clean_value.lower()

            if lookup in seen_items:
                continue

            seen_items.add(lookup)
            items.append(clean_value)

        normalized.append(
            {
                "key": list_key,
                "label": label,
                "items": items,
                "items_csv": ", ".join(items),
            }
        )

    return normalized


if "_original_normalize_menu_process_additional_fields_for_list_v3" not in globals():
    _original_normalize_menu_process_additional_fields_for_list_v3 = normalize_menu_process_additional_fields


def normalize_menu_process_additional_fields_v4(raw_fields: Any) -> list[dict[str, Any]]:
    normalized = _original_normalize_menu_process_additional_fields_for_list_v3(raw_fields)

    if not isinstance(raw_fields, (list, tuple, set)):
        return normalized

    raw_by_index: dict[int, dict[str, Any]] = {}

    for index, raw_item in enumerate(raw_fields):
        if isinstance(raw_item, dict):
            raw_by_index[index] = raw_item

    for index, item in enumerate(normalized):
        if str(item.get("field_type") or "").strip().lower() != "list":
            item.pop("list_key", None)
            continue

        raw_item = raw_by_index.get(index, {})
        item["list_key"] = _normalize_process_list_key_v3(
            raw_item.get("list_key", raw_item.get("process_list_key", raw_item.get("lista")))
        )

    return normalized


normalize_menu_process_additional_fields = normalize_menu_process_additional_fields_v4


if "_original_get_sidebar_menu_settings_for_lists_v3" not in globals():
    _original_get_sidebar_menu_settings_for_lists_v3 = get_sidebar_menu_settings


def get_sidebar_menu_settings_v4(session: Session) -> list[dict[str, Any]]:
    settings = _original_get_sidebar_menu_settings_for_lists_v3(session)

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
        process_lists = normalize_menu_process_lists_v3(menu_config.get("process_lists"))
        item["process_lists"] = process_lists
        item["process_list_options"] = [
            {"key": process_list["key"], "label": process_list["label"]}
            for process_list in process_lists
        ]

    return settings


get_sidebar_menu_settings = get_sidebar_menu_settings_v4
'''
        content = content.rstrip() + block + "\n"

    write_file(MENU_SETTINGS_PATH, content)
    print("OK: menu_settings.py corrigido.")


####################################################################################
# (6) CORRIGIR TEMPLATE NO LOCAL CERTO
####################################################################################

def encontrar_tag_aba_campos_adicionais_v3(content: str) -> tuple[int, int, str]:
    needle = "Campos adicionais"
    positions = [match.start() for match in re.finditer(re.escape(needle), content, flags=re.IGNORECASE)]

    for position in positions:
        tag_candidates = []

        for tag_name in ("a", "button"):
            start = content.rfind(f"<{tag_name}", 0, position)
            end = content.find(f"</{tag_name}>", position)

            if start >= 0 and end >= 0:
                end += len(f"</{tag_name}>")
                tag = content[start:end]

                if len(tag) <= 2000 and (
                    "settings_tab" in tag
                    or "settings-tab" in tag
                    or "campos-adicionais" in tag
                    or "Campos adicionais" in tag
                ):
                    tag_candidates.append((start, end, tag))

        if tag_candidates:
            tag_candidates.sort(key=lambda item: item[1] - item[0])
            return tag_candidates[0]

    raise RuntimeError(
        "Não encontrei a tag da aba 'Campos adicionais'. "
        "Abra templates/new_user.html e procure o texto 'Campos adicionais'."
    )


def corrigir_template_v3() -> None:
    content = read_file(TEMPLATE_PATH)

    ####################################################################################
    # (6.1) REMOVER TENTATIVA ANTIGA DE JS FORÇADO
    ####################################################################################

    content = re.sub(
        r'\s*<script[^>]+force_lista_tab_v1\.js[^>]*></script>\s*',
        "\n",
        content,
        flags=re.IGNORECASE,
    )

    ####################################################################################
    # (6.2) ADICIONAR ABA LISTA AO LADO DAS OUTRAS
    ####################################################################################

    if "settings_tab=lista" not in content and 'data-settings-tab="lista"' not in content:
        start, end, campos_tag = encontrar_tag_aba_campos_adicionais_v3(content)

        lista_tag = campos_tag
        lista_tag = lista_tag.replace("campos-adicionais", "lista")
        lista_tag = lista_tag.replace("campos_adicionais", "lista")
        lista_tag = lista_tag.replace("Campos adicionais", "Lista")
        lista_tag = lista_tag.replace("campos adicionais", "Lista")

        content = content[:end] + "\n              " + lista_tag + content[end:]
        print("OK: aba Lista inserida depois de Campos adicionais.")
    else:
        print("AVISO: aba Lista já existe no template.")

    ####################################################################################
    # (6.3) INSERIR PAINEL DA ABA LISTA ANTES DO BLOCO CAMPOS ADICIONAIS
    ####################################################################################

    if "APPVERBO_LISTA_PANEL_V3" not in content:
        panel = r'''
              <!-- APPVERBO_LISTA_PANEL_V3 -->
              {% if settings_tab == "lista" %}
              {% set process_lists = settings_edit_data.process_lists|default([]) %}
              <div class="admin-subsection process-lists-panel-v3" id="settings-process-lists-card">
                <h3>Lista</h3>
                <p class="muted">
                  Crie listas reutilizáveis para usar no tipo de campo Lista.
                  Separe os itens por vírgula. Ex.: Ativo, Inativo, Pendente, Em acompanhamento.
                </p>

                <form method="post" action="/settings/menu/process-lists">
                  <input type="hidden" name="menu_key" value="{{ settings_edit_data.key }}">
                  <input type="hidden" name="redirect_menu" value="administrativo">
                  <input type="hidden" name="redirect_target" value="#settings-menu-edit-card">

                  <div class="process-lists-rows-v3">
                    {% for process_list in process_lists %}
                    <div class="process-list-row-v3">
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
                      <div class="field process-list-actions-v3">
                        <button type="button" class="action-btn-cancel" onclick="this.closest('.process-list-row-v3').remove()">Remover</button>
                      </div>
                    </div>
                    {% endfor %}

                    <div class="process-list-row-v3">
                      <input type="hidden" name="process_list_key" value="">
                      <div class="field">
                        <label>Nome da lista</label>
                        <input name="process_list_label" placeholder="Ex.: Estado">
                      </div>
                      <div class="field full">
                        <label>Itens da lista separados por vírgula</label>
                        <input name="process_list_items_csv" placeholder="Ativo, Inativo, Pendente, Em acompanhamento">
                      </div>
                      <div class="field process-list-actions-v3">
                        <button type="button" class="action-btn-cancel" onclick="this.closest('.process-list-row-v3').remove()">Remover</button>
                      </div>
                    </div>
                  </div>

                  <div class="form-action-row">
                    <button type="button" class="action-btn-secondary" id="add-process-list-row-v3">Adicionar lista</button>
                    <button type="submit" class="action-btn">Guardar listas</button>
                  </div>
                </form>
              </div>
              {% endif %}
              <!-- /APPVERBO_LISTA_PANEL_V3 -->
'''

        campos_heading_index = content.find("<h3>Campos Adicionais")
        if campos_heading_index < 0:
            campos_heading_index = content.find("<h3>Campos adicionais")

        if campos_heading_index < 0:
            raise RuntimeError("Não encontrei o bloco <h3>Campos adicionais no template.")

        content = content[:campos_heading_index] + panel + "\n" + content[campos_heading_index:]
        print("OK: painel Lista inserido antes de Campos adicionais.")
    else:
        print("AVISO: painel Lista já existe.")

    ####################################################################################
    # (6.4) INJETAR RUNTIME JS
    ####################################################################################

    script_tag = '<script src="/static/js/modules/process_lists_runtime_v3.js?v=20260428c"></script>'

    if "process_lists_runtime_v3.js" not in content:
        marker = '<script src="/static/js/new_user.js'
        marker_index = content.find(marker)

        if marker_index >= 0:
            insert_at = content.find("</script>", marker_index)
            insert_at += len("</script>")
            content = content[:insert_at] + "\n  " + script_tag + content[insert_at:]
        else:
            endblock_index = content.rfind("{% endblock %}")
            content = content[:endblock_index] + "  " + script_tag + "\n" + content[endblock_index:]

        print("OK: runtime JS inserido.")
    else:
        print("AVISO: runtime JS já existe.")

    write_file(TEMPLATE_PATH, content)
    print("OK: new_user.html corrigido.")


####################################################################################
# (7) CRIAR RUNTIME JS
####################################################################################

def criar_runtime_js_v3() -> None:
    content = r'''//###################################################################################
// APPVERBOBRAGA - LISTA V3
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) AUXILIARES
  //###################################################################################

  function normalizarChave_v3(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function obterBootstrap_v3() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function obterUrlParam_v3(nome) {
    try {
      return new URL(window.location.href).searchParams.get(nome) || "";
    } catch (erro) {
      return "";
    }
  }

  function obterProcessoAtual_v3() {
    const chave = normalizarChave_v3(obterUrlParam_v3("settings_edit_key") || obterBootstrap_v3().settingsEditKey);
    const settings = Array.isArray(obterBootstrap_v3().sidebarMenuSettings)
      ? obterBootstrap_v3().sidebarMenuSettings
      : [];

    return settings.find(function (setting) {
      return normalizarChave_v3(setting.key) === chave;
    }) || null;
  }

  function obterListasProcesso_v3() {
    const processo = obterProcessoAtual_v3();

    return processo && Array.isArray(processo.process_lists)
      ? processo.process_lists
      : [];
  }

  function obterCamposProcesso_v3() {
    const processo = obterProcessoAtual_v3();

    return processo && Array.isArray(processo.process_field_options)
      ? processo.process_field_options
      : [];
  }

  //###################################################################################
  // (2) ADICIONAR LINHA NA ABA LISTA
  //###################################################################################

  function ligarBotaoAdicionarLista_v3() {
    const botao = document.getElementById("add-process-list-row-v3");
    const container = document.querySelector(".process-lists-rows-v3");

    if (!botao || !container || botao.dataset.listaBoundV3 === "1") {
      return;
    }

    botao.dataset.listaBoundV3 = "1";

    botao.addEventListener("click", function () {
      const linha = document.createElement("div");
      linha.className = "process-list-row-v3";
      linha.innerHTML = [
        '<input type="hidden" name="process_list_key" value="">',
        '<div class="field">',
        '  <label>Nome da lista</label>',
        '  <input name="process_list_label" placeholder="Ex.: Estado">',
        '</div>',
        '<div class="field full">',
        '  <label>Itens da lista separados por vírgula</label>',
        '  <input name="process_list_items_csv" placeholder="Ativo, Inativo, Pendente, Em acompanhamento">',
        '</div>',
        '<div class="field process-list-actions-v3">',
        '  <button type="button" class="action-btn-cancel" data-remover-lista-v3>Remover</button>',
        '</div>'
      ].join("");

      linha.querySelector("[data-remover-lista-v3]").addEventListener("click", function () {
        linha.remove();
      });

      container.appendChild(linha);
    });
  }

  //###################################################################################
  // (3) MOSTRAR SELECT "LISTA" NA CONFIGURAÇÃO DO CAMPO
  //###################################################################################

  function criarSelectLista_v3(valorSelecionado) {
    const select = document.createElement("select");
    select.name = "additional_field_list_key";

    const opcaoVazia = document.createElement("option");
    opcaoVazia.value = "";
    opcaoVazia.textContent = obterListasProcesso_v3().length
      ? "Selecione a lista"
      : "Crie uma lista na aba Lista";
    select.appendChild(opcaoVazia);

    obterListasProcesso_v3().forEach(function (lista) {
      const option = document.createElement("option");
      option.value = normalizarChave_v3(lista.key);
      option.textContent = lista.label || lista.key;

      if (normalizarChave_v3(valorSelecionado) === normalizarChave_v3(lista.key)) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function melhorarFormularioCamposAdicionais_v3() {
    const formularios = Array.from(
      document.querySelectorAll("form[action*='/settings/menu/process-additional-fields']")
    );

    if (!formularios.length) {
      return;
    }

    const campos = obterCamposProcesso_v3();

    formularios.forEach(function (formulario) {
      const selectsTipo = Array.from(formulario.querySelectorAll("select[name='additional_field_type']"));

      selectsTipo.forEach(function (selectTipo, indice) {
        if (!selectTipo.querySelector("option[value='list']")) {
          const option = document.createElement("option");
          option.value = "list";
          option.textContent = "Lista";
          selectTipo.appendChild(option);
        }

        const linha = selectTipo.closest(".additional-field-row-equalized")
          || (selectTipo.closest(".field") ? selectTipo.closest(".field").parentElement : null)
          || selectTipo.parentElement;

        if (!linha || linha.querySelector("[data-lista-picker-v3]")) {
          return;
        }

        const meta = campos[indice] || {};

        const colunaLista = document.createElement("div");
        colunaLista.className = "field additional-field-list-col-v3";
        colunaLista.setAttribute("data-lista-picker-v3", "1");

        const label = document.createElement("label");
        label.textContent = "Lista";
        colunaLista.appendChild(label);
        colunaLista.appendChild(criarSelectLista_v3(meta.list_key || meta.listKey || ""));

        linha.appendChild(colunaLista);

        function atualizarVisibilidade() {
          colunaLista.style.display = selectTipo.value === "list" ? "" : "none";
        }

        selectTipo.addEventListener("change", atualizarVisibilidade);
        atualizarVisibilidade();
      });
    });
  }

  //###################################################################################
  // (4) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v3() {
    ligarBotaoAdicionarLista_v3();
    melhorarFormularioCamposAdicionais_v3();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v3);
  } else {
    inicializar_v3();
  }

  window.setTimeout(inicializar_v3, 100);
  window.setTimeout(inicializar_v3, 400);
  window.setTimeout(inicializar_v3, 1000);
  window.setTimeout(inicializar_v3, 1800);
})();
'''
    write_file(RUNTIME_JS_PATH, content)
    print("OK: process_lists_runtime_v3.js criado.")


####################################################################################
# (8) CSS
####################################################################################

def corrigir_css_v3() -> None:
    content = read_file(CSS_PATH)

    if "Processo Lista V3" in content:
        print("AVISO: CSS V3 já existe.")
        return

    css = r'''

/* ###################################################################################
   Processo Lista V3
################################################################################### */

.process-lists-panel-v3 {
  margin-top: 16px;
}

.process-lists-rows-v3 {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.process-list-row-v3 {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(320px, 2fr) auto;
  gap: 12px;
  align-items: end;
  width: 100%;
}

.process-list-actions-v3 {
  display: flex;
  align-items: end;
  justify-content: flex-start;
}

.additional-field-list-col-v3 {
  min-width: 180px;
}

@media (max-width: 900px) {
  .process-list-row-v3 {
    grid-template-columns: 1fr;
  }
}
'''
    content = content.rstrip() + css + "\n"
    write_file(CSS_PATH, content)
    print("OK: CSS corrigido.")


####################################################################################
# (9) EXECUÇÃO
####################################################################################

def main() -> None:
    validar_projeto_v3()

    for path in [
        TEMPLATE_PATH,
        SETTINGS_HANDLERS_PATH,
        MENU_SETTINGS_PATH,
        CSS_PATH,
        RUNTIME_JS_PATH,
    ]:
        backup_file(path)

    corrigir_settings_handlers_v3()
    corrigir_menu_settings_v3()
    corrigir_template_v3()
    criar_runtime_js_v3()
    corrigir_css_v3()

    run_command([sys.executable, "-m", "py_compile", "appverbo/routes/profile/settings_handlers.py"])
    run_command([sys.executable, "-m", "py_compile", "appverbo/menu_settings.py"])

    print("OK: patch Lista Aba V3 aplicado.")


if __name__ == "__main__":
    main()