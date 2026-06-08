from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = ROOT / "backups" / f"refatorar_numero_entidade_default_{STAMP}"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def backup(path: Path):
    if path.exists():
        dest = BACKUP_DIR / str(path.relative_to(ROOT)).replace("\\", "__").replace("/", "__")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")

def fail(message: str):
    print(f"ERRO: {message}")
    sys.exit(1)

def replace_once(text: str, old: str, new: str, description: str) -> str:
    if old not in text:
        fail(f"não encontrei o marcador: {description}")
    return text.replace(old, new, 1)

# ---------------------------------------------------------------------
# 1) Serviço reutilizável: contexto default da entidade logada
# ---------------------------------------------------------------------

service_path = ROOT / "appverbo" / "services" / "entity_default_context.py"
backup(service_path)

service_path.write_text(
'''from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity


def empty_entity_default_context_v1() -> dict[str, str]:
    return {
        "entity_id": "",
        "numero_entidade": "",
        "entity_name": "",
    }


def get_entity_default_context_v1(
    session: Session,
    selected_entity_id: int | None,
) -> dict[str, str]:
    """
    Regra default de entidade.

    Toda criação de dado de processo deve receber o Nº Entidade da entidade
    atualmente selecionada/logada.

    O valor visualizado como "Nº Entidade" é o internal_number da tabela Entity,
    o mesmo número apresentado como "Nº Cliente" na gestão de entidades.
    """
    if selected_entity_id is None:
        return empty_entity_default_context_v1()

    row = session.execute(
        select(
            Entity.id,
            Entity.internal_number,
            Entity.name,
        )
        .where(Entity.id == selected_entity_id)
        .limit(1)
    ).one_or_none()

    if row is None:
        return empty_entity_default_context_v1()

    return {
        "entity_id": str(row.id or "").strip(),
        "numero_entidade": str(row.internal_number or "").strip(),
        "entity_name": str(row.name or "").strip(),
    }


__all__ = [
    "empty_entity_default_context_v1",
    "get_entity_default_context_v1",
]
''',
encoding="utf-8",
)

print("OK: serviço appverbo/services/entity_default_context.py criado.")

# ---------------------------------------------------------------------
# 2) page.py: expõe entity_default_context no contexto da página
# ---------------------------------------------------------------------

page_path = ROOT / "appverbo" / "services" / "page.py"
if not page_path.exists():
    fail("appverbo/services/page.py não encontrado.")

backup(page_path)
page_text = read(page_path)

if "from appverbo.services.entity_default_context import get_entity_default_context_v1" not in page_text:
    marker = "from appverbo.services.permissions import get_user_entity_permissions\n"
    page_text = replace_once(
        page_text,
        marker,
        marker + "from appverbo.services.entity_default_context import get_entity_default_context_v1\n",
        "import de entity_default_context em page.py",
    )

if "entity_default_context = get_entity_default_context_v1(session, selected_entity_id)" not in page_text:
    marker = "    sidebar_menu_settings = get_sidebar_menu_settings(session)\n"
    page_text = replace_once(
        page_text,
        marker,
        "    entity_default_context = get_entity_default_context_v1(session, selected_entity_id)\n\n" + marker,
        "criação de entity_default_context em page.py",
    )

if '"entity_default_context": entity_default_context,' not in page_text:
    marker = '        "entity_permissions": permissions,\n'
    page_text = replace_once(
        page_text,
        marker,
        marker + '        "entity_default_context": entity_default_context,\n',
        "entity_default_context no return de page.py",
    )

write(page_path, page_text)
print("OK: appverbo/services/page.py atualizado.")

# ---------------------------------------------------------------------
# 3) new_user.html: envia entityDefaultContext para o JavaScript
# ---------------------------------------------------------------------

template_path = ROOT / "templates" / "new_user.html"
if not template_path.exists():
    fail("templates/new_user.html não encontrado.")

backup(template_path)
template_text = read(template_path)

if "entityDefaultContext" not in template_text:
    marker = "      currentEntityId: {{ entity_permissions.selected_entity_id|tojson }},\n"
    template_text = replace_once(
        template_text,
        marker,
        marker + "      entityDefaultContext: {{ entity_default_context|tojson }},\n",
        "entityDefaultContext no bootstrap do new_user.html",
    )

write(template_path, template_text)
print("OK: templates/new_user.html atualizado.")

# ---------------------------------------------------------------------
# 4) new_user.js: regra nativa para inserir Nº Entidade nos processos
# ---------------------------------------------------------------------

js_path = ROOT / "static" / "js" / "new_user.js"
if not js_path.exists():
    fail("static/js/new_user.js não encontrado.")

backup(js_path)
js_text = read(js_path)

if "const entityDefaultContextV1" not in js_text:
    marker = 'const currentEntityId = Number.parseInt(String(bootstrap.currentEntityId || "").trim(), 10);\n'
    js_text = replace_once(
        js_text,
        marker,
        marker + '''const entityDefaultContextV1 = (
  bootstrap.entityDefaultContext &&
  typeof bootstrap.entityDefaultContext === "object" &&
  !Array.isArray(bootstrap.entityDefaultContext)
)
  ? bootstrap.entityDefaultContext
  : {};
''',
        "const entityDefaultContextV1 em new_user.js",
    )

helper = r'''
function getAppVerboDefaultEntityNumberV1() {
  const valueFromContext = String(entityDefaultContextV1.numero_entidade || "").trim();

  if (valueFromContext) {
    return valueFromContext;
  }

  const legacyValue = String(
    bootstrap.currentEntityInternalNumber ||
    bootstrap.numeroEntidade ||
    bootstrap.numero_entidade ||
    ""
  ).trim();

  return legacyValue;
}

function getAppVerboDefaultEntityNameV1() {
  return String(entityDefaultContextV1.entity_name || bootstrap.currentEntityName || "").trim();
}

function appendDynamicProcessDefaultEntityFieldV1(gridEl, menuKey) {
  if (!gridEl) {
    return;
  }

  const entityNumber = getAppVerboDefaultEntityNumberV1();

  if (!entityNumber) {
    return;
  }

  if (
    gridEl.querySelector("[data-appverbo-default-entity-v1='numero_entidade']") ||
    gridEl.querySelector("[name='numero_entidade']") ||
    gridEl.querySelector("[name='process_entity_internal_number']")
  ) {
    return;
  }

  const fieldContainerEl = document.createElement("div");
  fieldContainerEl.className = "field appverbo-default-entity-field";
  fieldContainerEl.setAttribute("data-appverbo-default-entity-v1", "numero_entidade");

  const inputId = `dynamic_process_${normalizeMenuKey(menuKey)}_numero_entidade`
    .replace(/[^a-z0-9_]+/gi, "_");

  const labelEl = document.createElement("label");
  labelEl.setAttribute("for", inputId);
  labelEl.textContent = "Nº Entidade";

  const inputEl = document.createElement("input");
  inputEl.id = inputId;
  inputEl.name = "numero_entidade";
  inputEl.type = "text";
  inputEl.value = entityNumber;
  inputEl.defaultValue = entityNumber;
  inputEl.readOnly = true;
  inputEl.setAttribute("readonly", "readonly");
  inputEl.setAttribute("aria-readonly", "true");
  inputEl.className = "readonly-field appverbo-default-entity-input";

  const entityName = getAppVerboDefaultEntityNameV1();

  if (entityName) {
    inputEl.title = `Nº Cliente da entidade logada: ${entityName}`;
  }

  const hiddenEntityNumberEl = document.createElement("input");
  hiddenEntityNumberEl.type = "hidden";
  hiddenEntityNumberEl.name = "process_entity_internal_number";
  hiddenEntityNumberEl.value = entityNumber;

  fieldContainerEl.appendChild(labelEl);
  fieldContainerEl.appendChild(inputEl);
  fieldContainerEl.appendChild(hiddenEntityNumberEl);

  const stateInputEl = gridEl.querySelector("[name='process_state'], [name='process_field__estado']");
  const stateFieldEl = stateInputEl ? stateInputEl.closest(".field") : null;

  if (stateFieldEl && stateFieldEl.parentElement === gridEl) {
    stateFieldEl.insertAdjacentElement("afterend", fieldContainerEl);
    return;
  }

  const estadoFieldEl = Array.from(gridEl.querySelectorAll(".field")).find((fieldEl) => {
    const labelEl = fieldEl.querySelector("label");
    return normalizeLookupText(labelEl ? labelEl.textContent : "") === "estado";
  });

  if (estadoFieldEl && estadoFieldEl.parentElement === gridEl) {
    estadoFieldEl.insertAdjacentElement("afterend", fieldContainerEl);
    return;
  }

  gridEl.appendChild(fieldContainerEl);
}
'''

if "function appendDynamicProcessDefaultEntityFieldV1" not in js_text:
    marker = "function renderDynamicProcessHistory(menuKey, sectionKey, sectionLabel, sectionFields, recordLabels) {\n"
    js_text = replace_once(
        js_text,
        marker,
        helper + "\n" + marker,
        "helper appendDynamicProcessDefaultEntityFieldV1",
    )

if "appendDynamicProcessDefaultEntityFieldV1(dynamicProcessEditGridEl, cleanMenuKey);" not in js_text:
    marker = "  renderDynamicProcessQuantityGroups(\n"
    js_text = replace_once(
        js_text,
        marker,
        "  appendDynamicProcessDefaultEntityFieldV1(dynamicProcessEditGridEl, cleanMenuKey);\n\n" + marker,
        "chamada da regra default antes dos campos quantidade",
    )

if "const showEntityNumberColumn = true;" not in js_text:
    js_text = replace_once(
        js_text,
        '  const showStateColumn = String(recordLabels.singular || "") === "departamento";\n',
        '  const showStateColumn = String(recordLabels.singular || "") === "departamento";\n  const showEntityNumberColumn = true;\n',
        "coluna Nº Entidade no histórico",
    )

if 'entityHeadEl.textContent = "Nº Entidade";' not in js_text:
    js_text = replace_once(
        js_text,
        '''  const createdHeadEl = document.createElement("th");
  createdHeadEl.textContent = "Criado em";
  headRowEl.appendChild(createdHeadEl);
''',
        '''  const createdHeadEl = document.createElement("th");
  createdHeadEl.textContent = "Criado em";
  headRowEl.appendChild(createdHeadEl);

  if (showEntityNumberColumn) {
    const entityHeadEl = document.createElement("th");
    entityHeadEl.textContent = "Nº Entidade";
    headRowEl.appendChild(entityHeadEl);
  }
''',
        "header Nº Entidade no histórico",
    )

if "values.__numero_entidade" not in js_text:
    js_text = replace_once(
        js_text,
        '''    const createdCellEl = document.createElement("td");
    createdCellEl.textContent = String(row.created_at || "-").trim() || "-";
    trEl.appendChild(createdCellEl);

    const values = row.values && typeof row.values === "object" ? row.values : {};
''',
        '''    const createdCellEl = document.createElement("td");
    createdCellEl.textContent = String(row.created_at || "-").trim() || "-";
    trEl.appendChild(createdCellEl);

    const values = row.values && typeof row.values === "object" ? row.values : {};

    if (showEntityNumberColumn) {
      const entityCellEl = document.createElement("td");
      entityCellEl.textContent = String(values.__numero_entidade || getAppVerboDefaultEntityNumberV1() || "-").trim() || "-";
      trEl.appendChild(entityCellEl);
    }
''',
        "célula Nº Entidade no histórico",
    )

write(js_path, js_text)
print("OK: static/js/new_user.js atualizado.")

# ---------------------------------------------------------------------
# 5) profile_handlers.py: backend grava Nº Entidade de forma autoritativa
# ---------------------------------------------------------------------

handler_path = ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"
if not handler_path.exists():
    fail("appverbo/routes/profile/profile_handlers.py não encontrado.")

backup(handler_path)
handler_text = read(handler_path)

if "from appverbo.services.entity_default_context import get_entity_default_context_v1" not in handler_text:
    marker = "from appverbo.routes.profile.router import router\n"
    handler_text = replace_once(
        handler_text,
        marker,
        marker + "from appverbo.services.entity_default_context import get_entity_default_context_v1\nfrom appverbo.services.session import get_session_entity_id\nfrom appverbo.services.permissions import get_user_entity_permissions\n",
        "imports de entity default em profile_handlers.py",
    )

if "build_menu_process_field_storage_key" not in handler_text:
    marker = "from appverbo.services.profile import (\n"
    handler_text = replace_once(
        handler_text,
        marker,
        marker + "    build_menu_process_field_storage_key,\n",
        "import build_menu_process_field_storage_key",
    )

if "clean_process_entity_number = str(entity_default_context.get" not in handler_text:
    marker = '@router.post("/users/profile/process-data")'
    idx = handler_text.find(marker)

    if idx < 0:
        fail("não encontrei endpoint /users/profile/process-data")

    target = "        member = session.execute(\n"
    pos = handler_text.find(target, idx)

    if pos < 0:
        fail("não encontrei ponto para inserir entity_default_context no endpoint process-data")

    block = '''        selected_entity_id_for_process = get_session_entity_id(request)
        process_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id_for_process,
        )
        entity_default_context = get_entity_default_context_v1(
            session,
            process_permissions.get("selected_entity_id"),
        )
        clean_process_entity_number = str(entity_default_context.get("numero_entidade") or "").strip()

'''

    handler_text = handler_text[:pos] + block + handler_text[pos:]

if 'submitted_section_values["__numero_entidade"]' not in handler_text:
    old = '''        if history_process_mode and not absence_process_mode:
            submitted_section_values["__estado"] = _normalize_process_state(
                submitted_form.get("process_state")
            )
'''

    new = '''        if history_process_mode and not absence_process_mode:
            submitted_section_values["__estado"] = _normalize_process_state(
                submitted_form.get("process_state")
            )

        if clean_process_entity_number:
            submitted_section_values["__numero_entidade"] = clean_process_entity_number

            if not history_process_mode and not absence_process_mode:
                entity_number_storage_key = build_menu_process_field_storage_key(
                    clean_menu_key,
                    "numero_entidade",
                )

                if entity_number_storage_key:
                    existing_profile_fields[entity_number_storage_key] = clean_process_entity_number
'''

    handler_text = replace_once(
        handler_text,
        old,
        new,
        "gravação de __numero_entidade no endpoint process-data",
    )

write(handler_path, handler_text)
print("OK: appverbo/routes/profile/profile_handlers.py atualizado.")

# ---------------------------------------------------------------------
# 6) CSS
# ---------------------------------------------------------------------

css_path = ROOT / "static" / "css" / "new_user.css"
if css_path.exists():
    backup(css_path)
    css_text = read(css_path)

    css_block = '''
/* APPVERBO_DEFAULT_ENTITY_CONTEXT_V1_START */
.appverbo-default-entity-field .appverbo-default-entity-input,
.appverbo-default-entity-input[readonly] {
  background: #f3f5f8 !important;
  color: #344054;
  cursor: not-allowed;
}
/* APPVERBO_DEFAULT_ENTITY_CONTEXT_V1_END */
'''

    if "APPVERBO_DEFAULT_ENTITY_CONTEXT_V1_START" not in css_text:
        css_text = css_text.rstrip() + "\n\n" + css_block + "\n"
        write(css_path, css_text)

    print("OK: static/css/new_user.css atualizado.")

# ---------------------------------------------------------------------
# 7) Validação rápida
# ---------------------------------------------------------------------

print("")
print("A validar Python...")
import py_compile

for rel in [
    "appverbo/services/entity_default_context.py",
    "appverbo/services/page.py",
    "appverbo/routes/profile/profile_handlers.py",
]:
    py_compile.compile(str(ROOT / rel), doraise=True)
    print(f"OK: {rel}")

print("")
print("Correção refatorada aplicada com sucesso.")
print(f"Backups criados em: {BACKUP_DIR}")
