from __future__ import annotations

from pathlib import Path
import re

# ###################################################################################
# (1) CONFIGURACAO
# ###################################################################################

ROOT = Path.cwd()

MEMBER_MODEL_PATH = ROOT / "appverbo" / "models" / "member.py"
PROFILE_SERVICE_PATH = ROOT / "appverbo" / "services" / "profile.py"
PAGE_SERVICE_PATH = ROOT / "appverbo" / "services" / "page.py"
PROFILE_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"
NEW_USER_TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
SCRIPTS_DIR = ROOT / "scripts"

required_files = [
    MEMBER_MODEL_PATH,
    PROFILE_SERVICE_PATH,
    PAGE_SERVICE_PATH,
    PROFILE_HANDLERS_PATH,
    NEW_USER_TEMPLATE_PATH,
]

for file_path in required_files:
    if not file_path.exists():
        raise SystemExit(f"ERRO: ficheiro nao encontrado: {file_path}")

SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

changed_files: set[str] = set()


# ###################################################################################
# (2) FUNCOES AUXILIARES
# ###################################################################################

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")
    changed_files.add(str(path.relative_to(ROOT)))


# ###################################################################################
# (3) GARANTIR CAMPO country NO MODEL Member
# ###################################################################################

member_model = read_file(MEMBER_MODEL_PATH)

if "country: Mapped[Optional[str]]" not in member_model:
    member_model = member_model.replace(
        "    primary_phone: Mapped[str] = mapped_column(String(30), nullable=False)\n",
        "    primary_phone: Mapped[str] = mapped_column(String(30), nullable=False)\n"
        "    country: Mapped[Optional[str]] = mapped_column(String(120))\n",
        1,
    )
    write_file(MEMBER_MODEL_PATH, member_model)
    print("OK: country adicionado ao model Member.")
else:
    print("INFO: country ja existe no model Member.")


# ###################################################################################
# (4) GARANTIR country EM get_user_personal_data
# ###################################################################################

profile_service = read_file(PROFILE_SERVICE_PATH)

if "Member.country," not in profile_service:
    profile_service = profile_service.replace(
        "            Member.primary_phone,\n            Member.birth_date,",
        "            Member.primary_phone,\n            Member.country,\n            Member.birth_date,",
        1,
    )

if '"country": "-",' not in profile_service:
    profile_service = profile_service.replace(
        '            "primary_phone": "-",\n            "birth_date": "-",',
        '            "primary_phone": "-",\n            "country": "-",\n            "birth_date": "-",',
        1,
    )

if '"country": row.country or "-",' not in profile_service:
    profile_service = profile_service.replace(
        '        "primary_phone": row.primary_phone or "-",\n        "birth_date": format_optional_date_pt(row.birth_date),',
        '        "primary_phone": row.primary_phone or "-",\n        "country": row.country or "-",\n        "birth_date": format_optional_date_pt(row.birth_date),',
        1,
    )

write_file(PROFILE_SERVICE_PATH, profile_service)
print("OK: profile.py atualizado para devolver country.")


# ###################################################################################
# (5) FORCAR Nome, Telefone, Email e Pais COMO CAMPOS VISIVEIS DO PERFIL
# ###################################################################################

page_service = read_file(PAGE_SERVICE_PATH)

force_code = r'''
    required_profile_fields = ["nome", "telefone", "email", "pais"]

    for required_field in required_profile_fields:
        if required_field not in profile_personal_field_labels:
            profile_personal_field_labels[required_field] = {
                "nome": "Nome",
                "telefone": "Telefone",
                "email": "Email",
                "pais": "País",
            }[required_field]

        if required_field not in profile_personal_visible_fields:
            if required_field == "pais" and "telefone" in profile_personal_visible_fields:
                profile_personal_visible_fields.insert(
                    profile_personal_visible_fields.index("telefone") + 1,
                    required_field,
                )
            elif required_field == "email" and "telefone" in profile_personal_visible_fields:
                profile_personal_visible_fields.insert(
                    profile_personal_visible_fields.index("telefone") + 1,
                    required_field,
                )
            elif required_field == "telefone" and "nome" in profile_personal_visible_fields:
                profile_personal_visible_fields.insert(
                    profile_personal_visible_fields.index("nome") + 1,
                    required_field,
                )
            else:
                profile_personal_visible_fields.append(required_field)

    if "pais" not in profile_personal_field_section_map:
        profile_personal_field_section_map["pais"] = profile_personal_field_section_map.get("telefone", "geral")

    if "nome" not in profile_personal_field_section_map:
        profile_personal_field_section_map["nome"] = "geral"

    if "telefone" not in profile_personal_field_section_map:
        profile_personal_field_section_map["telefone"] = profile_personal_field_section_map.get("nome", "geral")

    if "email" not in profile_personal_field_section_map:
        profile_personal_field_section_map["email"] = profile_personal_field_section_map.get("telefone", "geral")

'''

if "required_profile_fields = [\"nome\", \"telefone\", \"email\", \"pais\"]" not in page_service:
    marker = "    scoped_entity_ids = sorted(allowed_entity_ids) if allowed_entity_ids is not None else []"
    if marker not in page_service:
        raise SystemExit("ERRO: ponto de insercao nao encontrado em appverbo/services/page.py")

    page_service = page_service.replace(marker, force_code + "\n" + marker, 1)
    write_file(PAGE_SERVICE_PATH, page_service)
    print("OK: page.py atualizado para forcar campos basicos no perfil.")
else:
    print("INFO: regra de campos basicos ja existe em page.py.")


# ###################################################################################
# (6) GARANTIR QUE O FORMULARIO SALVA country
# ###################################################################################

profile_handlers = read_file(PROFILE_HANDLERS_PATH)

if 'clean_country = str(submitted_form.get("country") or "").strip()' not in profile_handlers:
    profile_handlers = profile_handlers.replace(
        '    clean_primary_phone = str(submitted_form.get("primary_phone") or "").strip()\n',
        '    clean_primary_phone = str(submitted_form.get("primary_phone") or "").strip()\n'
        '    clean_country = str(submitted_form.get("country") or "").strip()\n',
        1,
    )

if "        member.country = clean_country or None\n" not in profile_handlers:
    profile_handlers = profile_handlers.replace(
        "        member.primary_phone = clean_primary_phone\n",
        "        member.primary_phone = clean_primary_phone\n"
        "        member.country = clean_country or None\n",
        1,
    )

write_file(PROFILE_HANDLERS_PATH, profile_handlers)
print("OK: profile_handlers.py atualizado para salvar country.")


# ###################################################################################
# (7) GARANTIR CAMPO PAIS NO TEMPLATE new_user.html
# ###################################################################################

template = read_file(NEW_USER_TEMPLATE_PATH)

readonly_country_block = '''              {% if "pais" in profile_personal_visible_fields %}
              <div class="personal-item" data-profile-section-pane="{{ profile_personal_field_section_map.get('pais', 'geral') }}">
                <span class="personal-label">País</span>
                <strong class="personal-value">{{ user_personal_data.country }}</strong>
              </div>
              {% endif %}
'''

edit_country_block = '''              {% if "pais" in profile_personal_visible_fields %}
              <div class="field" data-profile-section-pane="{{ profile_personal_field_section_map.get('pais', 'geral') }}">
                <label for="edit_country">País</label>
                <input
                  id="edit_country"
                  name="country"
                  value="{{ '' if user_personal_data.country == '-' else user_personal_data.country }}"
                >
              </div>
              {% else %}
              <input
                type="hidden"
                name="country"
                value="{{ '' if user_personal_data.country == '-' else user_personal_data.country }}"
              >
              {% endif %}
'''

if "{{ user_personal_data.country }}" not in template:
    first_marker = '              {% if "data_nascimento" in profile_personal_visible_fields %}'
    marker_index = template.find(first_marker)

    if marker_index == -1:
        raise SystemExit("ERRO: nao encontrei o ponto para inserir o Pais em modo leitura.")

    template = template[:marker_index] + readonly_country_block + template[marker_index:]
    print("OK: bloco readonly do Pais inserido no template.")
else:
    print("INFO: bloco readonly do Pais ja existe no template.")

if 'id="edit_country"' not in template:
    markers = [
        match.start()
        for match in re.finditer(
            re.escape('              {% if "data_nascimento" in profile_personal_visible_fields %}'),
            template,
        )
    ]

    if len(markers) < 2:
        raise SystemExit("ERRO: nao encontrei o ponto para inserir o Pais em modo edicao.")

    marker_index = markers[1]
    template = template[:marker_index] + edit_country_block + template[marker_index:]
    print("OK: campo editavel do Pais inserido no template.")
else:
    print("INFO: campo editavel do Pais ja existe no template.")

write_file(NEW_USER_TEMPLATE_PATH, template)


# ###################################################################################
# (8) CRIAR SCRIPT DB PARA GARANTIR COLUNA country NO BANCO
# ###################################################################################

db_script_path = SCRIPTS_DIR / "ensure_members_country_column.py"

db_script = '''from __future__ import annotations

from sqlalchemy import inspect, text

from appverbo.db.session import engine


# ###################################################################################
# (1) VALIDAR / CRIAR COLUNA members.country
# ###################################################################################

with engine.begin() as connection:
    inspector = inspect(connection)
    columns = {
        column["name"]
        for column in inspector.get_columns("members")
    }

    if "country" not in columns:
        connection.execute(text("ALTER TABLE members ADD COLUMN country VARCHAR(120)"))
        print("OK: coluna members.country criada.")
    else:
        print("INFO: coluna members.country ja existe.")
'''

write_file(db_script_path, db_script)
print("OK: script DB criado.")


# ###################################################################################
# (9) RESULTADO
# ###################################################################################

print("")
print("==== FICHEIROS ALTERADOS ====")

for file_name in sorted(changed_files):
    print(f"- {file_name}")

print("")
print("OK: correcao concluida.")
