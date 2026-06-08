from pathlib import Path
from datetime import datetime
import shutil
import re
import sys

ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = ROOT / "backups" / f"fix_numero_entidade_nativo_{STAMP}"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def backup(path: Path):
    if path.exists():
        dest = BACKUP_DIR / str(path.relative_to(ROOT)).replace("\\", "__").replace("/", "__")
        shutil.copy2(path, dest)

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")

def fail(message: str):
    print(f"ERRO: {message}")
    sys.exit(1)

def remove_entity_default_global_refs():
    for rel in ["templates/base.html", "templates/new_user.html"]:
        path = ROOT / rel
        if not path.exists():
            continue

        backup(path)
        text = read(path)
        lines = text.splitlines()
        next_lines = [
            line for line in lines
            if "entity_default_rule.js" not in line
            and "entity_default_rule.css" not in line
        ]

        if next_lines != lines:
            write(path, "\n".join(next_lines) + "\n")
            print(f"OK: removidas referências globais em {rel}")
        else:
            print(f"OK: sem referências globais em {rel}")

def patch_page_service():
    path = ROOT / "appverbo" / "services" / "page.py"

    if not path.exists():
        fail("appverbo/services/page.py não encontrado.")

    backup(path)
    text = read(path)

    if "current_entity_internal_number" not in text:
        pattern = (
            r'    current_entity_scope = ""\n'
            r'    if selected_entity_id is not None:\n'
            r'        raw_entity_scope = session\.execute\(\n'
            r'            select\(Entity\.profile_scope\)\n'
            r'\s*\.where\(Entity\.id == selected_entity_id\)\n'
            r'\s*\.limit\(1\)\n'
            r'        \)\.scalar_one_or_none\(\)\n'
            r'        current_entity_scope = str\(raw_entity_scope or ""\)\.strip\(\)\.lower\(\)\n'
        )

        replacement = '''    current_entity_scope = ""
    current_entity_internal_number = ""
    current_entity_name = ""

    if selected_entity_id is not None:
        current_entity_row = session.execute(
            select(
                Entity.profile_scope,
                Entity.internal_number,
                Entity.name,
            )
           .where(Entity.id == selected_entity_id)
           .limit(1)
        ).one_or_none()

        if current_entity_row is not None:
            current_entity_scope = str(current_entity_row.profile_scope or "").strip().lower()
            current_entity_internal_number = str(current_entity_row.internal_number or "").strip()
            current_entity_name = str(current_entity_row.name or "").strip()
'''

        text, count = re.subn(pattern, replacement, text)

        if count != 1:
            fail("não consegui substituir o bloco current_entity_scope em appverbo/services/page.py")

    if '"current_entity_internal_number": current_entity_internal_number,' not in text:
        anchor = '        "current_entity_scope": current_entity_scope,\n'
        insert = (
            '        "current_entity_scope": current_entity_scope,\n'
            '        "current_entity_internal_number": current_entity_internal_number,\n'
            '        "current_entity_name": current_entity_name,\n'
        )

        if anchor not in text:
            fail("não encontrei current_entity_scope no return de appverbo/services/page.py")

        text = text.replace(anchor, insert, 1)

    write(path, text)
    print("OK: appverbo/services/page.py atualizado.")

def patch_new_user_template():
    path = ROOT / "templates" / "new_user.html"

    if not path.exists():
        fail("templates/new_user.html não encontrado.")

    backup(path)
    text = read(path)

    if "currentEntityInternalNumber" not in text:
        anchor = '      currentEntityId: {{ entity_permissions.selected_entity_id|tojson }},\n'
        insert = (
            '      currentEntityId: {{ entity_permissions.selected_entity_id|tojson }},\n'
            '      currentEntityInternalNumber: {{ current_entity_internal_number|tojson }},\n'
            '      currentEntityName: {{ current_entity_name|tojson }},\n'
        )

        if anchor not in text:
            fail("não encontrei currentEntityId no bootstrap do templates/new_user.html")

        text = text.replace(anchor, insert, 1)

    write(path, text)
    print("OK: templates/new_user.html atualizado.")

def patch_new_user_js():
    path = ROOT / "static" / "js" / "new_user.js"

    if not path.exists():
        fail("static/js/new_user.js não encontrado.")

    backup(path)
    text = read(path)

    if "currentEntityInternalNumber" not in text:
        anchor = 'const currentEntityId = Number.parseInt(String(bootstrap.currentEntityId || "").trim(), 10);\n'
        insert = (
            'const currentEntityId = Number.parseInt(String(bootstrap.currentEntityId || "").trim(), 10);\n'
            'const currentEntityInternalNumber = String(bootstrap.currentEntityInternalNumber || "").trim();\n'
            'const currentEntityName = String(bootstrap.currentEntityName || "").trim();\n'
        )

        if anchor not in text:
            fail("não encontrei currentEntityId em static/js/new_user.js")

        text = text.replace(anchor, insert, 1)

    if "function appendDynamicProcessEntityDefaultField" not in text:
        helper = r'''

function getCurrentEntityInternalNumberValue() {
  return String(currentEntityInternalNumber || "").trim();
}

function appendDynamicProcessEntityDefaultField(gridEl, menuKey) {
  if (!gridEl) {
    return;
  }

  const entityNumber = getCurrentEntityInternalNumberValue();

  if (!entityNumber) {
    return;
  }

  if (gridEl.querySelector("[data-appverbo-entity-default-field='numero_entidade']")) {
    return;
  }

  const fieldContainerEl = document.createElement("div");
  fieldContainerEl.className = "field appverbo-default-entity-field";
  fieldContainerEl.setAttribute("data-appverbo-entity-default-field", "numero_entidade");

  const inputId = `dynamic_process_${normalizeMenuKey(menuKey)}_numero_entidade`
    .replace(/[^a-z0-9_]+/gi, "_");

  const labelEl = document.createElement("label");
  labelEl.setAttribute("for", inputId);
  labelEl.textContent = "Nº Entidade *";

  const inputEl = document.createElement("input");
  inputEl.id = inputId;
  inputEl.name = "numero_entidade";
  inputEl.type = "text";
  inputEl.value = entityNumber;
  inputEl.defaultValue = entityNumber;
  inputEl.readOnly = true;
  inputEl.setAttribute("readonly", "readonly");
  inputEl.setAttribute("aria-readonly", "true");
  inputEl.className = "readonly-field appverbo-entity-default-input";
  inputEl.title = currentEntityName
    ? `Nº Cliente da entidade logada: ${currentEntityName}`
    : "Nº Cliente da entidade logada";

  const hiddenClientNumberEl = document.createElement("input");
  hiddenClientNumberEl.type = "hidden";
  hiddenClientNumberEl.name = "process_entity_internal_number";
  hiddenClientNumberEl.value = entityNumber;

  fieldContainerEl.appendChild(labelEl);
  fieldContainerEl.appendChild(inputEl);
  fieldContainerEl.appendChild(hiddenClientNumberEl);

  if (Number.isFinite(currentEntityId)) {
    const hiddenEntityIdEl = document.createElement("input");
    hiddenEntityIdEl.type = "hidden";
    hiddenEntityIdEl.name = "process_entity_id";
    hiddenEntityIdEl.value = String(currentEntityId);
    fieldContainerEl.appendChild(hiddenEntityIdEl);
  }

  const stateInputEl = gridEl.querySelector("[name='process_state'], [name='process_field__estado']");
  const stateFieldEl = stateInputEl ? stateInputEl.closest(".field") : null;

  if (stateFieldEl && stateFieldEl.parentElement === gridEl) {
    stateFieldEl.insertAdjacentElement("afterend", fieldContainerEl);
    return;
  }

  const estadoLabelFieldEl = Array.from(gridEl.querySelectorAll(".field")).find((fieldEl) => {
    const labelEl = fieldEl.querySelector("label");
    return normalizeLookupText(labelEl ? labelEl.textContent : "") === "estado";
  });

  if (estadoLabelFieldEl && estadoLabelFieldEl.parentElement === gridEl) {
    estadoLabelFieldEl.insertAdjacentElement("afterend", fieldContainerEl);
    return;
  }

  gridEl.appendChild(fieldContainerEl);
}
'''

        anchor = 'function getDynamicProcessInputType(fieldType) {\n'

        if anchor not in text:
            fail("não encontrei getDynamicProcessInputType em static/js/new_user.js")

        text = text.replace(anchor, helper + "\n" + anchor, 1)

    if "appendDynamicProcessEntityDefaultField(dynamicProcessEditGridEl, cleanMenuKey);" not in text:
        anchor = '  if (absenceProcessMode) {\n'
        insert = (
            '  appendDynamicProcessEntityDefaultField(dynamicProcessEditGridEl, cleanMenuKey);\n\n'
            '  if (absenceProcessMode) {\n'
        )

        if anchor not in text:
            fail("não encontrei o ponto antes de absenceProcessMode em static/js/new_user.js")

        text = text.replace(anchor, insert, 1)

    write(path, text)
    print("OK: static/js/new_user.js atualizado.")

def patch_profile_handler():
    path = ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"

    if not path.exists():
        fail("appverbo/routes/profile/profile_handlers.py não encontrado.")

    backup(path)
    text = read(path)

    if '"__numero_entidade"' not in text:
        old = '''        if history_process_mode and not absence_process_mode:
            submitted_section_values["__estado"] = _normalize_process_state(
                submitted_form.get("process_state")
            )
'''

        new = '''        if history_process_mode and not absence_process_mode:
            submitted_section_values["__estado"] = _normalize_process_state(
                submitted_form.get("process_state")
            )

        if history_process_mode:
            clean_process_entity_number = str(
                submitted_form.get("numero_entidade")
                or submitted_form.get("process_entity_internal_number")
                or ""
            ).strip()

            if clean_process_entity_number:
                submitted_section_values["__numero_entidade"] = clean_process_entity_number
'''

        if old not in text:
            fail("não encontrei bloco de gravação __estado em profile_handlers.py")

        text = text.replace(old, new, 1)

    write(path, text)
    print("OK: appverbo/routes/profile/profile_handlers.py atualizado.")

def patch_css():
    path = ROOT / "static" / "css" / "new_user.css"

    if not path.exists():
        fail("static/css/new_user.css não encontrado.")

    backup(path)
    text = read(path)

    css = '''
/* APPVERBO_DEFAULT_ENTITY_NUMBER_V1_START */
.appverbo-default-entity-field .appverbo-entity-default-input,
.appverbo-entity-default-input[readonly] {
  background: #f3f5f8 !important;
  color: #344054;
  cursor: not-allowed;
}
/* APPVERBO_DEFAULT_ENTITY_NUMBER_V1_END */
'''

    if "APPVERBO_DEFAULT_ENTITY_NUMBER_V1_START" not in text:
        text = text.rstrip() + "\n\n" + css + "\n"

    write(path, text)
    print("OK: static/css/new_user.css atualizado.")

remove_entity_default_global_refs()
patch_page_service()
patch_new_user_template()
patch_new_user_js()
patch_profile_handler()
patch_css()

print("")
print("Correção aplicada com sucesso.")
print(f"Backups criados em: {BACKUP_DIR}")
