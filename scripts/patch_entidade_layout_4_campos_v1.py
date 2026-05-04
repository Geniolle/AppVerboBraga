from __future__ import annotations

import re
from pathlib import Path


def read_text_v1(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def replace_once_v1(content: str, old: str, new: str, label: str) -> str:
    if old not in content:
        raise RuntimeError(f"Bloco não encontrado para substituir: {label}")
    return content.replace(old, new, 1)


def regex_replace_once_v1(content: str, pattern: str, replacement: str, label: str) -> str:
    new_content, count = re.subn(pattern, replacement, content, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Bloco regex não encontrado para substituir: {label}")
    return new_content


def patch_entity_model_v1() -> None:
    path = "appverbo/models/entity.py"
    content = read_text_v1(path)

    if "city: Mapped[Optional[str]]" not in content:
        content = replace_once_v1(
            content,
            '    address: Mapped[Optional[str]] = mapped_column(String(255))\n'
            '    freguesia: Mapped[Optional[str]] = mapped_column(String(120))',
            '    address: Mapped[Optional[str]] = mapped_column(String(255))\n'
            '    city: Mapped[Optional[str]] = mapped_column(String(120))\n'
            '    freguesia: Mapped[Optional[str]] = mapped_column(String(120))',
            "Entity.city",
        )

    write_text_v1(path, content)


def patch_bootstrap_v1() -> None:
    path = "appverbo/db/bootstrap.py"
    content = read_text_v1(path)

    if '"city" not in existing_columns' not in content:
        content = replace_once_v1(
            content,
            '        if "address" not in existing_columns:\n'
            '            connection.execute(text("ALTER TABLE entities ADD COLUMN address VARCHAR(255)"))\n'
            '        if "freguesia" not in existing_columns:',
            '        if "address" not in existing_columns:\n'
            '            connection.execute(text("ALTER TABLE entities ADD COLUMN address VARCHAR(255)"))\n'
            '        if "city" not in existing_columns:\n'
            '            connection.execute(text("ALTER TABLE entities ADD COLUMN city VARCHAR(120)"))\n'
            '        if "freguesia" not in existing_columns:',
            "ensure_entities_optional_columns city",
        )

    write_text_v1(path, content)


def patch_create_handler_v1() -> None:
    path = "appverbo/routes/entities/create_handler.py"
    content = read_text_v1(path)

    if "city: str = Form" not in content:
        content = replace_once_v1(
            content,
            '    address: str = Form(...),\n'
            '    freguesia: str = Form(...),',
            '    address: str = Form(...),\n'
            '    city: str = Form(""),\n'
            '    freguesia: str = Form(...),',
            "create_entity city param",
        )

    if "clean_city = city.strip()" not in content:
        content = replace_once_v1(
            content,
            '    clean_address = address.strip()\n'
            '    clean_freguesia = freguesia.strip()',
            '    clean_address = address.strip()\n'
            '    clean_city = city.strip()\n'
            '    clean_freguesia = freguesia.strip()',
            "create_entity clean_city",
        )

    if '"city": clean_city,' not in content:
        content = replace_once_v1(
            content,
            '        "address": clean_address,\n'
            '        "freguesia": clean_freguesia,',
            '        "address": clean_address,\n'
            '        "city": clean_city,\n'
            '        "freguesia": clean_freguesia,',
            "create_entity form_data city",
        )

    if "city=clean_city or None," not in content:
        content = replace_once_v1(
            content,
            '            address=clean_address or None,\n'
            '            freguesia=clean_freguesia or None,',
            '            address=clean_address or None,\n'
            '            city=clean_city or None,\n'
            '            freguesia=clean_freguesia or None,',
            "create_entity object city",
        )

    write_text_v1(path, content)


def patch_update_handler_v1() -> None:
    path = "appverbo/routes/entities/update_handler.py"
    content = read_text_v1(path)

    if "city: str = Form" not in content:
        content = replace_once_v1(
            content,
            '    address: str = Form(...),\n'
            '    freguesia: str = Form(...),',
            '    address: str = Form(...),\n'
            '    city: str = Form(""),\n'
            '    freguesia: str = Form(...),',
            "update_entity city param",
        )

    if "clean_city = city.strip()" not in content:
        content = replace_once_v1(
            content,
            '    clean_address = address.strip()\n'
            '    clean_freguesia = freguesia.strip()',
            '    clean_address = address.strip()\n'
            '    clean_city = city.strip()\n'
            '    clean_freguesia = freguesia.strip()',
            "update_entity clean_city",
        )

    if "entity.city = clean_city or None" not in content:
        content = replace_once_v1(
            content,
            '        entity.address = clean_address or None\n'
            '        entity.freguesia = clean_freguesia or None',
            '        entity.address = clean_address or None\n'
            '        entity.city = clean_city or None\n'
            '        entity.freguesia = clean_freguesia or None',
            "update_entity save city",
        )

    write_text_v1(path, content)


def patch_page_service_v1() -> None:
    path = "appverbo/services/page.py"
    content = read_text_v1(path)

    if "Entity.city," not in content:
        content = replace_once_v1(
            content,
            '            Entity.phone,\n'
            '            Entity.address,\n'
            '            Entity.freguesia,',
            '            Entity.phone,\n'
            '            Entity.address,\n'
            '            Entity.city,\n'
            '            Entity.freguesia,',
            "entity_rows_stmt Entity.city",
        )

    if '"city": row.city or "",' not in content:
        content = replace_once_v1(
            content,
            '            "address": row.address or "",\n'
            '            "freguesia": row.freguesia or "",',
            '            "address": row.address or "",\n'
            '            "city": row.city or "",\n'
            '            "freguesia": row.freguesia or "",',
            "serialize_entity_row city",
        )

    if '"city": "",' not in content:
        content = replace_once_v1(
            content,
            '        "address": "",\n'
            '        "freguesia": "",',
            '        "address": "",\n'
            '        "city": "",\n'
            '        "freguesia": "",',
            "entity form defaults city first occurrence",
        )
        content = replace_once_v1(
            content,
            '        "address": "",\n'
            '        "freguesia": "",',
            '        "address": "",\n'
            '        "city": "",\n'
            '        "freguesia": "",',
            "entity edit defaults city second occurrence",
        )

    if '"city": entity.city or "",' not in content:
        content = replace_once_v1(
            content,
            '        "address": entity.address or "",\n'
            '        "freguesia": entity.freguesia or "",',
            '        "address": entity.address or "",\n'
            '        "city": entity.city or "",\n'
            '        "freguesia": entity.freguesia or "",',
            "get_entity_edit_data city",
        )

    write_text_v1(path, content)


CREATE_ENTITY_ROWS_V1 = '''                <div class="entity-first-row">
                  <div class="field entity-first-row-client">
                    <label for="entity_internal_number">Número do cliente</label>
                    <input id="entity_internal_number" class="readonly-field" value="{{ next_entity_internal_number }}" readonly disabled>
                  </div>
                  <div class="field entity-first-row-name">
                    <label for="entity_name">Nome da entidade *</label>
                    <input id="entity_name" name="name" required value="{{ entity_form_data.name }}">
                  </div>
                  <div class="field entity-first-row-acronym">
                    <label for="entity_acronym">Acrónimo (opcional)</label>
                    <input id="entity_acronym" name="acronym" maxlength="5" value="{{ entity_form_data.acronym }}">
                  </div>
                  <div class="field entity-first-row-tax">
                    <label for="entity_tax_id">Nº Identificação Fiscal *</label>
                    <input id="entity_tax_id" name="tax_id" maxlength="20" required value="{{ entity_form_data.tax_id }}">
                  </div>
                </div>
                <div class="entity-second-row">
                  <div class="field entity-second-row-profile">
                    <label for="entity_profile_scope">Perfil da entidade *</label>
                    <select id="entity_profile_scope" name="entity_profile_scope" required>
                      <option value="owner" {% if entity_form_data.profile_scope == "owner" %}selected{% endif %}>Owner</option>
                      <option value="legado" {% if entity_form_data.profile_scope != "owner" %}selected{% endif %}>Legado</option>
                    </select>
                  </div>
                  <div class="field entity-second-row-email">
                    <label for="entity_email">Email *</label>
                    <input id="entity_email" name="email" type="email" required value="{{ entity_form_data.email }}">
                  </div>
                  <div class="field entity-second-row-phone">
                    <label for="entity_phone">Telefone *</label>
                    <input id="entity_phone" name="phone" maxlength="15" required value="{{ entity_form_data.phone }}">
                  </div>
                  <div class="field entity-second-row-responsible">
                    <label for="entity_responsible_name">Nome do responsável *</label>
                    <input id="entity_responsible_name" name="responsible_name" required value="{{ entity_form_data.responsible_name }}">
                  </div>
                </div>
                <div class="entity-third-row">
                  <div class="field entity-third-row-address">
                    <label for="entity_address">Morada *</label>
                    <input id="entity_address" name="address" required value="{{ entity_form_data.address }}">
                  </div>
                  <div class="field entity-third-row-door">
                    <label for="entity_door_number">Nº da porta *</label>
                    <input id="entity_door_number" name="door_number" maxlength="15" required value="{{ entity_form_data.door_number }}">
                  </div>
                  <div class="field entity-third-row-freguesia">
                    <label for="entity_freguesia">Freguesia *</label>
                    <input id="entity_freguesia" name="freguesia" required value="{{ entity_form_data.freguesia }}">
                  </div>
                  <div class="field entity-third-row-postal">
                    <label for="entity_postal_code">Código postal *</label>
                    <input id="entity_postal_code" name="postal_code" maxlength="30" required value="{{ entity_form_data.postal_code }}">
                  </div>
                </div>
                <div class="entity-fourth-row">
                  <div class="field entity-fourth-row-city">
                    <label for="entity_city">Cidade</label>
                    <input id="entity_city" name="city" maxlength="120" value="{{ entity_form_data.city }}">
                  </div>
                  <div class="field entity-fourth-row-country">
                    <label for="entity_country">País *</label>
                    <input id="entity_country" name="country" maxlength="50" required value="{{ entity_form_data.country }}">
                  </div>
                  <div class="field entity-fourth-row-status">
                    <label for="entity_status_readonly">Estado da entidade</label>
                    <input id="entity_status_readonly" class="readonly-field" value="Ativa" readonly disabled>
                  </div>
                  <div class="field entity-fourth-row-created-at">
                    <label for="entity_created_at">Data da criação</label>
                    <input id="entity_created_at" class="readonly-field" value="{{ entity_form_data.created_at }}" readonly disabled>
                  </div>
                </div>
                <div class="entity-fifth-row">
                  <div class="field entity-fifth-row-logo">
                    <label for="entity_logo_file">Imagem/ícone da entidade (ficheiro opcional)</label>
                    <input id="entity_logo_file" name="entity_logo_file" type="file" accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml">
                  </div>
                </div>
'''


EDIT_ENTITY_ROWS_V1 = '''            <div class="entity-first-row">
              <div class="field entity-first-row-client">
                <label for="edit_entity_internal_number">Número do cliente</label>
                <input id="edit_entity_internal_number" class="readonly-field" value="{{ entity_edit_data.internal_number }}" readonly disabled>
              </div>
              <div class="field entity-first-row-name">
                <label for="edit_entity_name">Nome da entidade *</label>
                <input id="edit_entity_name" name="name" required value="{{ entity_edit_data.name }}">
              </div>
              <div class="field entity-first-row-acronym">
                <label for="edit_entity_acronym">Acrónimo (opcional)</label>
                <input id="edit_entity_acronym" name="acronym" maxlength="5" value="{{ entity_edit_data.acronym }}">
              </div>
              <div class="field entity-first-row-tax">
                <label for="edit_entity_tax_id">Nº Identificação Fiscal *</label>
                <input id="edit_entity_tax_id" name="tax_id" maxlength="20" required value="{{ entity_edit_data.tax_id }}">
              </div>
            </div>
            <div class="entity-second-row">
              {% if current_user_can_manage_all_entities %}
              <div class="field entity-second-row-profile">
                <label for="edit_entity_profile_scope">Perfil da entidade *</label>
                <select id="edit_entity_profile_scope" name="entity_profile_scope" required>
                  <option value="owner" {% if entity_edit_data.profile_scope == "owner" %}selected{% endif %}>Owner</option>
                  <option value="legado" {% if entity_edit_data.profile_scope != "owner" %}selected{% endif %}>Legado</option>
                </select>
              </div>
              {% else %}
              <input type="hidden" name="entity_profile_scope" value="{{ entity_edit_data.profile_scope }}">
              <div class="field entity-second-row-profile">
                <label for="edit_entity_profile_scope_readonly">Perfil da entidade *</label>
                <input
                  id="edit_entity_profile_scope_readonly"
                  class="readonly-field"
                  value="{% if entity_edit_data.profile_scope == 'owner' %}Owner{% else %}Legado{% endif %}"
                  readonly
                  disabled
                >
              </div>
              {% endif %}
              <div class="field entity-second-row-email">
                <label for="edit_entity_email">Email *</label>
                <input id="edit_entity_email" name="email" type="email" required value="{{ entity_edit_data.email }}">
              </div>
              <div class="field entity-second-row-phone">
                <label for="edit_entity_phone">Telefone *</label>
                <input id="edit_entity_phone" name="phone" maxlength="15" required value="{{ entity_edit_data.phone }}">
              </div>
              <div class="field entity-second-row-responsible">
                <label for="edit_entity_responsible_name">Nome do responsável *</label>
                <input id="edit_entity_responsible_name" name="responsible_name" required value="{{ entity_edit_data.responsible_name }}">
              </div>
            </div>
            <div class="entity-third-row">
              <div class="field entity-third-row-address">
                <label for="edit_entity_address">Morada *</label>
                <input id="edit_entity_address" name="address" required value="{{ entity_edit_data.address }}">
              </div>
              <div class="field entity-third-row-door">
                <label for="edit_entity_door_number">Nº da porta *</label>
                <input id="edit_entity_door_number" name="door_number" maxlength="15" required value="{{ entity_edit_data.door_number }}">
              </div>
              <div class="field entity-third-row-freguesia">
                <label for="edit_entity_freguesia">Freguesia *</label>
                <input id="edit_entity_freguesia" name="freguesia" required value="{{ entity_edit_data.freguesia }}">
              </div>
              <div class="field entity-third-row-postal">
                <label for="edit_entity_postal_code">Código postal *</label>
                <input id="edit_entity_postal_code" name="postal_code" maxlength="30" required value="{{ entity_edit_data.postal_code }}">
              </div>
            </div>
            <div class="entity-fourth-row">
              <div class="field entity-fourth-row-city">
                <label for="edit_entity_city">Cidade</label>
                <input id="edit_entity_city" name="city" maxlength="120" value="{{ entity_edit_data.city }}">
              </div>
              <div class="field entity-fourth-row-country">
                <label for="edit_entity_country">País *</label>
                <input id="edit_entity_country" name="country" maxlength="50" required value="{{ entity_edit_data.country }}">
              </div>
              <div class="field entity-fourth-row-status">
                <label for="edit_entity_status">Estado da entidade *</label>
                {% if current_user_can_manage_all_entities %}
                <select id="edit_entity_status" name="entity_status" required>
                  <option value="active" {% if entity_edit_data.status == "active" %}selected{% endif %}>Ativa</option>
                  <option value="inactive" {% if entity_edit_data.status == "inactive" %}selected{% endif %}>Inativa</option>
                </select>
                {% else %}
                <input
                  id="edit_entity_status"
                  class="readonly-field"
                  value="{% if entity_edit_data.status == 'active' %}Ativa{% else %}Inativa{% endif %}"
                  readonly
                  disabled
                >
                <input type="hidden" name="entity_status" value="{{ entity_edit_data.status }}">
                {% endif %}
              </div>
              <div class="field entity-fourth-row-created-at">
                <label for="edit_entity_created_at">Data da criação</label>
                <input id="edit_entity_created_at" class="readonly-field" value="{{ entity_edit_data.created_at }}" readonly disabled>
              </div>
            </div>
            <div class="entity-fifth-row entity-fifth-row-edit">
              <div class="field entity-fifth-row-logo">
                <label for="edit_entity_logo_file">Imagem/ícone da entidade (ficheiro opcional)</label>
                <input id="edit_entity_logo_file" name="entity_logo_file" type="file" accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml">
              </div>
            </div>
'''


def patch_template_v1() -> None:
    path = "templates/new_user.html"
    content = read_text_v1(path)

    content = regex_replace_once_v1(
        content,
        r'(<form method="post" action="/entities/new" enctype="multipart/form-data">\s*)(.*?)(\s*<div class="form-action-row">)',
        r'\1' + CREATE_ENTITY_ROWS_V1 + r'\3',
        "create entity form rows",
    )

    content = regex_replace_once_v1(
        content,
        r'(<form method="post" action="/entities/update" enctype="multipart/form-data">\s*<input type="hidden" name="entity_id" value="{{ entity_edit_data.id }}">\s*)(.*?)(\s*{% if entity_edit_data.logo_url %})',
        r'\1' + EDIT_ENTITY_ROWS_V1 + r'\3',
        "edit entity form rows",
    )

    content = re.sub(
        r'new_user\.css\?v=[^"]+',
        'new_user.css?v=20260504-entity-layout-4-fields-v1',
        content,
        count=1,
    )

    write_text_v1(path, content)


def patch_css_v1() -> None:
    path = "static/css/new_user.css"
    content = read_text_v1(path)

    block = '''
/* APPVERBO_ENTITY_LAYOUT_4_FIELDS_V1_START */
.entity-panel-card .entity-first-row,
.entity-panel-card .entity-second-row,
.entity-panel-card .entity-third-row,
.entity-panel-card .entity-fourth-row,
.entity-panel-card .entity-fifth-row,
.entity-panel-card .entity-scope-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.entity-panel-card .entity-fifth-row-edit {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.entity-panel-card .entity-first-row .field,
.entity-panel-card .entity-second-row .field,
.entity-panel-card .entity-third-row .field,
.entity-panel-card .entity-fourth-row .field,
.entity-panel-card .entity-fifth-row .field {
  min-width: 0;
  width: 100%;
  max-width: none;
}

.entity-panel-card .entity-first-row input,
.entity-panel-card .entity-first-row select,
.entity-panel-card .entity-second-row input,
.entity-panel-card .entity-second-row select,
.entity-panel-card .entity-third-row input,
.entity-panel-card .entity-third-row select,
.entity-panel-card .entity-fourth-row input,
.entity-panel-card .entity-fourth-row select,
.entity-panel-card .entity-fifth-row input,
.entity-panel-card .entity-fifth-row select {
  width: 100%;
  min-width: 0;
  max-width: 100%;
}

.entity-panel-card .entity-first-row label,
.entity-panel-card .entity-second-row label,
.entity-panel-card .entity-third-row label,
.entity-panel-card .entity-fourth-row label,
.entity-panel-card .entity-fifth-row label {
  white-space: nowrap;
  line-height: 1.2;
}

.entity-panel-card .entity-fifth-row-logo {
  grid-column: span 2;
}

.entity-panel-card .entity-edit-logo-row {
  margin-bottom: 12px;
}

.entity-panel-card .entity-edit-current-logo {
  max-width: 420px;
}

@media (max-width: 1500px) {
  .entity-panel-card .entity-first-row,
  .entity-panel-card .entity-second-row,
  .entity-panel-card .entity-third-row,
  .entity-panel-card .entity-fourth-row,
  .entity-panel-card .entity-fifth-row,
  .entity-panel-card .entity-scope-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .entity-panel-card .entity-fifth-row-logo {
    grid-column: 1 / -1;
  }
}

@media (max-width: 780px) {
  .entity-panel-card .entity-first-row,
  .entity-panel-card .entity-second-row,
  .entity-panel-card .entity-third-row,
  .entity-panel-card .entity-fourth-row,
  .entity-panel-card .entity-fifth-row,
  .entity-panel-card .entity-scope-row {
    grid-template-columns: 1fr;
  }

  .entity-panel-card .entity-fifth-row-logo {
    grid-column: auto;
  }
}
/* APPVERBO_ENTITY_LAYOUT_4_FIELDS_V1_END */
'''

    content = re.sub(
        r'/\* APPVERBO_ENTITY_LAYOUT_4_FIELDS_V1_START \*/.*?/\* APPVERBO_ENTITY_LAYOUT_4_FIELDS_V1_END \*/',
        '',
        content,
        flags=re.S,
    )

    content = content.rstrip() + "\n\n" + block.strip() + "\n"
    write_text_v1(path, content)


def validate_v1() -> None:
    template = read_text_v1("templates/new_user.html")
    page = read_text_v1("appverbo/services/page.py")
    model = read_text_v1("appverbo/models/entity.py")
    css = read_text_v1("static/css/new_user.css")
    create_handler = read_text_v1("appverbo/routes/entities/create_handler.py")
    update_handler = read_text_v1("appverbo/routes/entities/update_handler.py")

    checks = {
        "modelo Entity.city": "city: Mapped[Optional[str]]" in model,
        "bootstrap cidade": '"city" not in existing_columns' in read_text_v1("appverbo/db/bootstrap.py"),
        "create handler city": "city: str = Form" in create_handler and "city=clean_city or None" in create_handler,
        "update handler city": "city: str = Form" in update_handler and "entity.city = clean_city or None" in update_handler,
        "page defaults city": '"city": ""' in page and '"city": entity.city or ""' in page,
        "template create city": 'id="entity_city" name="city"' in template,
        "template edit city": 'id="edit_entity_city" name="city"' in template,
        "row1 ordem create": template.index('id="entity_internal_number"') < template.index('id="entity_name"') < template.index('id="entity_acronym"') < template.index('id="entity_tax_id"'),
        "row2 perfil email telefone responsavel": template.index('id="entity_profile_scope"') < template.index('id="entity_email"') < template.index('id="entity_phone"') < template.index('id="entity_responsible_name"'),
        "row3 morada porta freguesia postal": template.index('id="entity_address"') < template.index('id="entity_door_number"') < template.index('id="entity_freguesia"') < template.index('id="entity_postal_code"'),
        "row4 cidade pais estado data": template.index('id="entity_city"') < template.index('id="entity_country"') < template.index('id="entity_status_readonly"') < template.index('id="entity_created_at"'),
        "css 4 campos": "APPVERBO_ENTITY_LAYOUT_4_FIELDS_V1_START" in css and "repeat(4, minmax(0, 1fr))" in css,
        "cache css": "new_user.css?v=20260504-entity-layout-4-fields-v1" in template,
    }

    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("Falha na validação: " + ", ".join(failed))


def main_v1() -> None:
    patch_entity_model_v1()
    patch_bootstrap_v1()
    patch_create_handler_v1()
    patch_update_handler_v1()
    patch_page_service_v1()
    patch_template_v1()
    patch_css_v1()
    validate_v1()


if __name__ == "__main__":
    main_v1()
