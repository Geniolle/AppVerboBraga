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
MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"
NEW_USER_TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
MIGRATIONS_DIR = ROOT / "migrations" / "versions"
SCRIPTS_DIR = ROOT / "scripts"

required_files = [
    MEMBER_MODEL_PATH,
    PROFILE_SERVICE_PATH,
    PAGE_SERVICE_PATH,
    PROFILE_HANDLERS_PATH,
    MENU_SETTINGS_PATH,
    NEW_USER_TEMPLATE_PATH,
]

for file_path in required_files:
    if not file_path.exists():
        raise SystemExit(f"ERRO: ficheiro nao encontrado: {file_path}")

MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
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


def replace_once(content: str, old: str, new: str) -> tuple[str, bool]:
    if old not in content:
        return content, False
    return content.replace(old, new, 1), True


def insert_before_nth(content: str, marker: str, insertion: str, nth: int) -> tuple[str, bool]:
    positions = [match.start() for match in re.finditer(re.escape(marker), content)]
    if len(positions) < nth:
        return content, False

    position = positions[nth - 1]
    return content[:position] + insertion + content[position:], True


# ###################################################################################
# (3) ADICIONAR country NO MODEL Member
# ###################################################################################

member_model = read_file(MEMBER_MODEL_PATH)

if "country: Mapped[Optional[str]]" not in member_model:
    old = '    primary_phone: Mapped[str] = mapped_column(String(30), nullable=False)\n'
    new = (
        '    primary_phone: Mapped[str] = mapped_column(String(30), nullable=False)\n'
        '    country: Mapped[Optional[str]] = mapped_column(String(120))\n'
    )
    member_model, ok = replace_once(member_model, old, new)

    if not ok:
        raise SystemExit("ERRO: nao foi possivel inserir country em appverbo/models/member.py")

    write_file(MEMBER_MODEL_PATH, member_model)
    print("OK: Member.country adicionado ao model.")
else:
    print("INFO: Member.country ja existe no model.")


# ###################################################################################
# (4) CRIAR MIGRATION PARA members.country
# ###################################################################################

migration_exists = any(
    "add_country_to_members" in path.name or "membercountry01" in path.read_text(encoding="utf-8", errors="ignore")
    for path in MIGRATIONS_DIR.glob("*.py")
)

if not migration_exists:
    migration_path = MIGRATIONS_DIR / "membercountry01_add_country_to_members.py"
    migration_content = '''from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "membercountry01"
down_revision = "sidemenucompat01"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def upgrade() -> None:
    if not _has_column("members", "country"):
        op.add_column(
            "members",
            sa.Column("country", sa.String(length=120), nullable=True),
        )


def downgrade() -> None:
    if _has_column("members", "country"):
        op.drop_column("members", "country")
'''
    write_file(migration_path, migration_content)
    print(f"OK: migration criada -> {migration_path.relative_to(ROOT)}")
else:
    print("INFO: migration de members.country ja existe.")


# ###################################################################################
# (5) ATUALIZAR get_user_personal_data PARA DEVOLVER PAIS
# ###################################################################################

profile_service = read_file(PROFILE_SERVICE_PATH)

if "Member.country," not in profile_service:
    profile_service, ok = replace_once(
        profile_service,
        "            Member.primary_phone,\n            Member.birth_date,",
        "            Member.primary_phone,\n            Member.country,\n            Member.birth_date,",
    )

    if not ok:
        raise SystemExit("ERRO: nao foi possivel adicionar Member.country no SELECT de get_user_personal_data.")

if '"country": "-",' not in profile_service:
    profile_service, ok = replace_once(
        profile_service,
        '            "primary_phone": "-",\n            "birth_date": "-",',
        '            "primary_phone": "-",\n            "country": "-",\n            "birth_date": "-",',
    )

    if not ok:
        raise SystemExit("ERRO: nao foi possivel adicionar country no retorno vazio de get_user_personal_data.")

if '"country": row.country or "-",' not in profile_service:
    profile_service, ok = replace_once(
        profile_service,
        '        "primary_phone": row.primary_phone or "-",\n        "birth_date": format_optional_date_pt(row.birth_date),',
        '        "primary_phone": row.primary_phone or "-",\n        "country": row.country or "-",\n        "birth_date": format_optional_date_pt(row.birth_date),',
    )

    if not ok:
        raise SystemExit("ERRO: nao foi possivel adicionar country no retorno principal de get_user_personal_data.")

write_file(PROFILE_SERVICE_PATH, profile_service)
print("OK: appverbo/services/profile.py atualizado.")


# ###################################################################################
# (6) ATUALIZAR EDICAO DOS DADOS PESSOAIS PARA GRAVAR PAIS
# ###################################################################################

profile_handlers = read_file(PROFILE_HANDLERS_PATH)

if 'clean_country = str(submitted_form.get("country") or "").strip()' not in profile_handlers:
    profile_handlers, ok = replace_once(
        profile_handlers,
        '    clean_primary_phone = str(submitted_form.get("primary_phone") or "").strip()\n',
        '    clean_primary_phone = str(submitted_form.get("primary_phone") or "").strip()\n'
        '    clean_country = str(submitted_form.get("country") or "").strip()\n',
    )

    if not ok:
        raise SystemExit("ERRO: nao foi possivel adicionar clean_country em update_personal_profile.")

if "        member.country = clean_country or None\n" not in profile_handlers:
    profile_handlers, ok = replace_once(
        profile_handlers,
        "        member.primary_phone = clean_primary_phone\n",
        "        member.primary_phone = clean_primary_phone\n"
        "        member.country = clean_country or None\n",
    )

    if not ok:
        raise SystemExit("ERRO: nao foi possivel gravar member.country em update_personal_profile.")

write_file(PROFILE_HANDLERS_PATH, profile_handlers)
print("OK: appverbo/routes/profile/profile_handlers.py atualizado.")


# ###################################################################################
# (7) GARANTIR PAIS NAS CONFIGURACOES DO PROCESSO MEU PERFIL
# ###################################################################################

menu_settings = read_file(MENU_SETTINGS_PATH)

default_block_match = re.search(
    r"(MENU_MEU_PERFIL_FIELDS_DEFAULT\s*=\s*[\(\[])(.*?)([\)\]])",
    menu_settings,
    flags=re.DOTALL,
)

if default_block_match and '"pais"' not in default_block_match.group(2) and "'pais'" not in default_block_match.group(2):
    block = default_block_match.group(0)
    new_block = block.replace('"telefone",', '"telefone",\n    "pais",', 1)
    if new_block == block:
        new_block = block.replace("'telefone',", "'telefone',\n    'pais',", 1)
    if new_block != block:
        menu_settings = menu_settings.replace(block, new_block, 1)

labels_block_match = re.search(
    r"(MENU_MEU_PERFIL_FIELD_LABELS\s*=\s*\{)(.*?)(\})",
    menu_settings,
    flags=re.DOTALL,
)

if labels_block_match and '"pais"' not in labels_block_match.group(2) and "'pais'" not in labels_block_match.group(2):
    block = labels_block_match.group(0)
    new_block = re.sub(
        r'("telefone"\s*:\s*"[^"]+"\s*,)',
        r'\1\n    "pais": "País",',
        block,
        count=1,
    )
    if new_block == block:
        new_block = re.sub(
            r"('telefone'\s*:\s*'[^']+'\s*,)",
            r"\1\n    'pais': 'País',",
            block,
            count=1,
        )
    if new_block != block:
        menu_settings = menu_settings.replace(block, new_block, 1)

options_block_match = re.search(
    r"(MENU_MEU_PERFIL_FIELD_OPTIONS\s*=\s*[\(\[])(.*?)([\)\]])",
    menu_settings,
    flags=re.DOTALL,
)

if options_block_match and '"pais"' not in options_block_match.group(2) and "'pais'" not in options_block_match.group(2):
    block = options_block_match.group(0)
    option = '    {"key": "pais", "label": "País", "field_type": "text", "size": 120},\n'
    telefone_option_match = re.search(
        r'(\s*\{[^\{\}]*["\']key["\']\s*:\s*["\']telefone["\'][^\{\}]*\}\s*,?\n)',
        block,
        flags=re.DOTALL,
    )
    if telefone_option_match:
        insert_at = telefone_option_match.end()
        new_block = block[:insert_at] + option + block[insert_at:]
    else:
        new_block = block.replace(options_block_match.group(3), option + options_block_match.group(3), 1)

    if new_block != block:
        menu_settings = menu_settings.replace(block, new_block, 1)

write_file(MENU_SETTINGS_PATH, menu_settings)
print("OK: appverbo/menu_settings.py atualizado.")


# ###################################################################################
# (8) ATUALIZAR TEMPLATE DOS DADOS DO UTILIZADOR
# ###################################################################################

template = read_file(NEW_USER_TEMPLATE_PATH)

country_readonly_block = '''              {% if "pais" in profile_personal_visible_fields %}
              <div class="personal-item" data-profile-section-pane="{{ profile_personal_field_section_map.get('pais', 'geral') }}">
                <span class="personal-label">País</span>
                <strong class="personal-value">{{ user_personal_data.country }}</strong>
              </div>
              {% endif %}
'''

country_edit_block = '''              {% if "pais" in profile_personal_visible_fields %}
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

marker = '              {% if "data_nascimento" in profile_personal_visible_fields %}'

if "{{ user_personal_data.country }}" not in template:
    template, ok = insert_before_nth(template, marker, country_readonly_block, 1)

    if not ok:
        raise SystemExit("ERRO: nao foi possivel inserir bloco readonly do Pais no template.")

if 'id="edit_country"' not in template:
    template, ok = insert_before_nth(template, marker, country_edit_block, 2)

    if not ok:
        raise SystemExit("ERRO: nao foi possivel inserir campo editavel do Pais no template.")

write_file(NEW_USER_TEMPLATE_PATH, template)
print("OK: templates/new_user.html atualizado.")


# ###################################################################################
# (9) TENTAR ATUALIZAR O FLUXO DE CRIACAO DE CONTA PARA GRAVAR PAIS
# ###################################################################################

patched_account_files: list[str] = []

for path in (ROOT / "appverbo").rglob("*.py"):
    if path in {MEMBER_MODEL_PATH, PROFILE_SERVICE_PATH, PAGE_SERVICE_PATH, PROFILE_HANDLERS_PATH, MENU_SETTINGS_PATH}:
        continue

    content = read_file(path)
    lower_content = content.lower()

    is_candidate = (
        "member(" in lower_content
        and "password_hash" in lower_content
        and "primary_phone" in lower_content
        and "full_name" in lower_content
        and ("confirm_password" in lower_content or "password" in lower_content)
    )

    if not is_candidate:
        continue

    original = content

    if "country: str = Form" not in content:
        content = re.sub(
            r"(\n\s*primary_phone\s*:\s*str\s*=\s*Form\([^)]*\)\s*,)",
            r'\1\n    country: str = Form(""),',
            content,
            count=1,
        )

    if "clean_country = country.strip()" not in content:
        content = re.sub(
            r"(\n\s*clean_primary_phone\s*=\s*[^\n]+\n)",
            r"\1    clean_country = country.strip()\n",
            content,
            count=1,
        )

    if "country=clean_country or None" not in content:
        content = re.sub(
            r"(\n\s*primary_phone\s*=\s*clean_primary_phone\s*,)",
            r"\1\n            country=clean_country or None,",
            content,
            count=1,
        )

    if content != original:
        write_file(path, content)
        patched_account_files.append(str(path.relative_to(ROOT)))

if patched_account_files:
    print("OK: fluxo de criacao de conta atualizado nos ficheiros:")
    for file_name in patched_account_files:
        print(f"- {file_name}")
else:
    print("AVISO: nao encontrei automaticamente a rota de criacao de conta para gravar country.")
    print("AVISO: se o campo Pais nao gravar na criacao, sera necessario indicar o ficheiro da rota de cadastro.")


# ###################################################################################
# (10) CRIAR SCRIPT DE CORRECAO DO menu_config NO BANCO
# ###################################################################################

db_script_path = SCRIPTS_DIR / "sync_member_country_profile_config.py"

db_script_content = '''from __future__ import annotations

import json

from sqlalchemy import inspect, text

from appverbo.db.session import SessionLocal, engine


# ###################################################################################
# (1) FUNCOES AUXILIARES
# ###################################################################################

def normalize_key(value: object) -> str:
    return str(value or "").strip().lower()


def insert_after(values: list[str], after_key: str, new_key: str) -> list[str]:
    clean_values = [normalize_key(value) for value in values if normalize_key(value)]

    if new_key in clean_values:
        return clean_values

    if after_key in clean_values:
        index = clean_values.index(after_key)
        clean_values.insert(index + 1, new_key)
        return clean_values

    clean_values.append(new_key)
    return clean_values


# ###################################################################################
# (2) ATUALIZAR CONFIGURACAO DO MENU MEU PERFIL
# ###################################################################################

inspector = inspect(engine)
tables = set(inspector.get_table_names())

if "sidebar_menu_settings" not in tables:
    raise SystemExit("ERRO: tabela sidebar_menu_settings nao existe.")

with SessionLocal() as session:
    row = session.execute(
        text(
            """
            SELECT id, menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = 'meu_perfil'
            LIMIT 1
            """
        )
    ).mappings().one_or_none()

    if row is None:
        print("AVISO: menu_key=meu_perfil nao encontrado em sidebar_menu_settings.")
        raise SystemExit(0)

    try:
        config = json.loads(row["menu_config"] or "{}")
    except json.JSONDecodeError:
        config = {}

    if not isinstance(config, dict):
        config = {}

    options = config.get("process_field_options")
    if not isinstance(options, list):
        options = []

    has_pais_option = any(normalize_key(item.get("key")) == "pais" for item in options if isinstance(item, dict))

    if not has_pais_option:
        pais_option = {
            "key": "pais",
            "label": "País",
            "field_type": "text",
            "size": 120,
            "is_required": False,
        }

        telefone_index = next(
            (
                index
                for index, item in enumerate(options)
                if isinstance(item, dict) and normalize_key(item.get("key")) == "telefone"
            ),
            None,
        )

        if telefone_index is None:
            options.append(pais_option)
        else:
            options.insert(telefone_index + 1, pais_option)

    config["process_field_options"] = options

    visible_fields = config.get("process_visible_fields")
    if not isinstance(visible_fields, list):
        visible_fields = []

    config["process_visible_fields"] = insert_after(visible_fields, "telefone", "pais")

    visible_rows = config.get("process_visible_field_rows")
    if isinstance(visible_rows, list):
        has_pais_row = any(
            isinstance(item, dict) and normalize_key(item.get("field_key")) == "pais"
            for item in visible_rows
        )

        if not has_pais_row:
            telefone_row = next(
                (
                    item
                    for item in visible_rows
                    if isinstance(item, dict) and normalize_key(item.get("field_key")) == "telefone"
                ),
                {},
            )

            header_key = ""
            if isinstance(telefone_row, dict):
                header_key = normalize_key(telefone_row.get("header_key"))

            pais_row = {
                "field_key": "pais",
                "header_key": header_key,
            }

            telefone_index = next(
                (
                    index
                    for index, item in enumerate(visible_rows)
                    if isinstance(item, dict) and normalize_key(item.get("field_key")) == "telefone"
                ),
                None,
            )

            if telefone_index is None:
                visible_rows.append(pais_row)
            else:
                visible_rows.insert(telefone_index + 1, pais_row)

        config["process_visible_field_rows"] = visible_rows

    header_map = config.get("process_visible_field_header_map")
    if isinstance(header_map, dict) and "pais" not in header_map:
        telefone_header = normalize_key(header_map.get("telefone"))
        if telefone_header:
            header_map["pais"] = telefone_header
            config["process_visible_field_header_map"] = header_map

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE id = :id
            """
        ),
        {
            "id": row["id"],
            "menu_config": json.dumps(config, ensure_ascii=False),
        },
    )

    session.commit()

print("OK: configuracao do menu Meu perfil atualizada com o campo País.")
'''

write_file(db_script_path, db_script_content)
print(f"OK: script de banco criado -> {db_script_path.relative_to(ROOT)}")


# ###################################################################################
# (11) RESULTADO
# ###################################################################################

print("")
print("==== FICHEIROS ALTERADOS ====")

for file_name in sorted(changed_files):
    print(f"- {file_name}")

print("")
print("OK: ajuste local concluido.")
