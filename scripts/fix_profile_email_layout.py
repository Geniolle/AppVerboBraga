from __future__ import annotations

from pathlib import Path
import re

# ###################################################################################
# (1) CONFIGURACAO
# ###################################################################################

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
PROFILE_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"
CSS_PATH = ROOT / "static" / "css" / "new_user.css"

required_files = [
    TEMPLATE_PATH,
    PROFILE_HANDLERS_PATH,
    CSS_PATH,
]

for file_path in required_files:
    if not file_path.exists():
        raise SystemExit(f"ERRO: ficheiro nao encontrado: {file_path}")

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
# (3) AJUSTAR TEMPLATE: EMAIL EDITAVEL E TEXTO DO BOTAO
# ###################################################################################

template = read_file(TEMPLATE_PATH)

template = template.replace(
    'Email (não editÃ¡vel aqui)',
    'Email *',
)

template = template.replace(
    'Email (não editável aqui)',
    'Email *',
)

template = template.replace(
    'Gravar alterações',
    'Gravar',
)

email_block_pattern = re.compile(
    r'''(?P<block>\s*\{% if "email" in profile_personal_visible_fields %\}
\s*<div class="field full" data-profile-section-pane="\{\{ profile_personal_field_section_map\.get\('email', 'geral'\) \}\}">
\s*<label for="edit_login_email">Email \*</label>
\s*<input
\s*id="edit_login_email"
\s*value="\{\{ '' if user_personal_data\.login_email == '-' else user_personal_data\.login_email \}\}"
\s*readonly
\s*>
\s*</div>
\s*\{% endif %\})''',
    flags=re.DOTALL,
)

new_email_block = '''              {% if "email" in profile_personal_visible_fields %}
              <div class="field" data-profile-section-pane="{{ profile_personal_field_section_map.get('email', 'geral') }}">
                <label for="edit_login_email">Email *</label>
                <input
                  id="edit_login_email"
                  name="login_email"
                  type="email"
                  required
                  value="{{ '' if user_personal_data.login_email == '-' else user_personal_data.login_email }}"
                >
              </div>
              {% else %}
              <input
                type="hidden"
                name="login_email"
                value="{{ '' if user_personal_data.login_email == '-' else user_personal_data.login_email }}"
              >
              {% endif %}'''

template, replaced_count = email_block_pattern.subn(new_email_block, template, count=1)

if replaced_count == 0:
    template = template.replace(
        '<div class="field full" data-profile-section-pane="{{ profile_personal_field_section_map.get(\'email\', \'geral\') }}">',
        '<div class="field" data-profile-section-pane="{{ profile_personal_field_section_map.get(\'email\', \'geral\') }}">',
        1,
    )
    template = template.replace(
        '<label for="edit_login_email">Email *</label>',
        '<label for="edit_login_email">Email *</label>',
        1,
    )
    template = template.replace(
        'id="edit_login_email"\n                  value=',
        'id="edit_login_email"\n                  name="login_email"\n                  type="email"\n                  required\n                  value=',
        1,
    )
    template = template.replace(
        '\n                  readonly\n                >',
        '\n                >',
        1,
    )

write_file(TEMPLATE_PATH, template)
print("OK: templates/new_user.html atualizado.")


# ###################################################################################
# (4) AJUSTAR BACKEND: SALVAR EMAIL EDITADO
# ###################################################################################

profile_handlers = read_file(PROFILE_HANDLERS_PATH)

if 'clean_login_email = str(submitted_form.get("login_email") or submitted_form.get("email") or "").strip().lower()' not in profile_handlers:
    profile_handlers = profile_handlers.replace(
        '    clean_primary_phone = str(submitted_form.get("primary_phone") or "").strip()\n',
        '    clean_primary_phone = str(submitted_form.get("primary_phone") or "").strip()\n'
        '    clean_login_email = str(submitted_form.get("login_email") or submitted_form.get("email") or "").strip().lower()\n',
        1,
    )

if 'if not clean_login_email:' not in profile_handlers:
    profile_handlers = profile_handlers.replace(
        '''    if not clean_primary_phone:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Telefone principal é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

''',
        '''    if not clean_primary_phone:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Telefone principal é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not clean_login_email:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Email é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if "@" not in clean_login_email:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Email inválido.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

''',
        1,
    )

if 'user_account = session.get(User, current_user["id"])' not in profile_handlers:
    profile_handlers = profile_handlers.replace(
        '''        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

''',
        '''        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        user_account = session.get(User, current_user["id"])
        if user_account is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Conta de utilizador não encontrada.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        email_already_exists = session.execute(
            select(User.id)
            .join(Member, Member.id == User.member_id)
            .where(
                func.lower(User.login_email) == clean_login_email,
                User.id != current_user["id"],
            )
            .limit(1)
        ).scalar_one_or_none()

        member_email_already_exists = session.execute(
            select(Member.id)
            .where(
                func.lower(Member.email) == clean_login_email,
                Member.id != member.id,
            )
            .limit(1)
        ).scalar_one_or_none()

        if email_already_exists is not None or member_email_already_exists is not None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Este email já está associado a outro utilizador.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

''',
        1,
    )

if "        member.email = clean_login_email\n" not in profile_handlers:
    profile_handlers = profile_handlers.replace(
        '''        member.full_name = clean_full_name
        member.primary_phone = clean_primary_phone
''',
        '''        member.full_name = clean_full_name
        member.primary_phone = clean_primary_phone
        member.email = clean_login_email
        user_account.login_email = clean_login_email
''',
        1,
    )

if 'request.session["login_email"] = clean_login_email' not in profile_handlers:
    profile_handlers = profile_handlers.replace(
        '    request.session["user_name"] = clean_full_name\n',
        '    request.session["user_name"] = clean_full_name\n'
        '    request.session["login_email"] = clean_login_email\n'
        '    request.session["user_email"] = clean_login_email\n',
        1,
    )

write_file(PROFILE_HANDLERS_PATH, profile_handlers)
print("OK: profile_handlers.py atualizado para salvar email.")


# ###################################################################################
# (5) AJUSTAR CSS: PRIMEIRA LINHA COM NOME, TELEFONE E EMAIL
# ###################################################################################

css = read_file(CSS_PATH)

css_block = '''
/* ###################################################################################
   (PERFIL) Dados pessoais: Nome, Telefone e Email na primeira linha
################################################################################### */

#perfil-pessoal-card .profile-edit-form .personal-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

#perfil-pessoal-card .profile-edit-form .field.full {
  grid-column: 1 / -1;
}

#perfil-pessoal-card .profile-edit-form #edit_login_email {
  background: #ffffff;
}

@media (max-width: 1100px) {
  #perfil-pessoal-card .profile-edit-form .personal-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  #perfil-pessoal-card .profile-edit-form .personal-grid {
    grid-template-columns: 1fr;
  }
}
'''

if "(PERFIL) Dados pessoais: Nome, Telefone e Email na primeira linha" not in css:
    css = css.rstrip() + "\n" + css_block + "\n"
else:
    css = re.sub(
        r"/\* ###################################################################################\n   \(PERFIL\) Dados pessoais: Nome, Telefone e Email na primeira linha[\s\S]*?\n\}",
        css_block.strip(),
        css,
        count=1,
    )

write_file(CSS_PATH, css)
print("OK: static/css/new_user.css atualizado.")


# ###################################################################################
# (6) RESULTADO
# ###################################################################################

print("")
print("==== FICHEIROS ALTERADOS ====")

for file_name in sorted(changed_files):
    print(f"- {file_name}")

print("")
print("OK: ajuste concluido.")
