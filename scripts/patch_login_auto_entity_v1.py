from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

SESSION_PATH = ROOT / "appverbo" / "routes" / "auth" / "session_handlers.py"
LOGIN_TEMPLATE_PATH = ROOT / "templates" / "login.html"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


if not SESSION_PATH.exists():
    fail(f"ficheiro nao encontrado: {SESSION_PATH}")

if not LOGIN_TEMPLATE_PATH.exists():
    fail(f"ficheiro nao encontrado: {LOGIN_TEMPLATE_PATH}")


####################################################################################
# (1) LER FICHEIROS
####################################################################################

session_text = SESSION_PATH.read_text(encoding="utf-8")
login_text = LOGIN_TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (2) REMOVER CAMPO ENTIDADE DO LOGIN COMUM
####################################################################################

login_entity_block = '''        <div class="field">
          <label for="entity_id">Entidade</label>
          <select id="entity_id" name="entity_id" required>
            <option value="" disabled {% if not login_data.entity_id %}selected{% endif %}>Selecione</option>
            {% for entity in entities %}
              <option value="{{ entity.id }}" data-entity-email="{{ entity.email }}" {% if login_data.entity_id == entity.id|string %}selected{% endif %}>
                {{ entity.name }}
              </option>
            {% endfor %}
          </select>
        </div>

'''

common_login_marker = '''    {% else %}
      <h1>Entrar na sua conta</h1>'''

password_marker = '''        <div class="field-row">
          <label for="password">Palavra-passe</label>'''

common_start = login_text.find(common_login_marker)
if common_start == -1:
    fail("nao encontrei o bloco do login comum em templates/login.html")

password_start = login_text.find(password_marker, common_start)
if password_start == -1:
    fail("nao encontrei o bloco da palavra-passe no login comum")

entity_block_start = login_text.find(login_entity_block, common_start)

if entity_block_start != -1 and entity_block_start < password_start:
    entity_block_end = entity_block_start + len(login_entity_block)
    login_text = (
        login_text[:entity_block_start]
        + "        {# Entidade definida automaticamente no backend pelo email do utilizador. #}\n\n"
        + login_text[entity_block_end:]
    )
    print("OK: campo Entidade removido do login comum.")
else:
    print("AVISO: campo Entidade do login comum nao encontrado ou ja removido.")


####################################################################################
# (3) SUBSTITUIR FUNCAO DE LOGIN POR login_v1
####################################################################################

new_login_function = '''@router.post("/login", response_class=HTMLResponse)
def login_v1(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    entity_id: str = Form(""),
    login_mode: str = Form("login"),
) -> HTMLResponse:
    clean_email = email.strip().lower()
    clean_password = password
    requested_mode = "admin" if login_mode.strip().lower() == "admin" else "login"
    clean_entity_id = entity_id.strip() if requested_mode == "admin" else ""
    login_data = {
        "entity_id": clean_entity_id,
    }

    if not clean_email or not clean_password:
        return render_login(
            request,
            error="Informe email e palavra-passe.",
            email=clean_email,
            mode=requested_mode,
            login_data=login_data,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    parsed_entity_id: int | None = None
    if requested_mode == "admin":
        if not clean_entity_id:
            return render_login(
                request,
                error="Selecione a entidade para entrar como administrador.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parsed_entity_id = int(clean_entity_id)
        except ValueError:
            return render_login(
                request,
                error="Entidade selecionada inválida.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    selected_entity_context: dict[str, Any] | None = None

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is not None:
            return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)

        row = session.execute(
            select(
                User.id,
                User.login_email,
                User.password_hash,
                User.account_status,
                User.member_id,
                Member.full_name,
            )
           .join(Member, Member.id == User.member_id)
           .where(func.lower(User.login_email) == clean_email)
        ).one_or_none()

        if row is None or not verify_password(clean_password, row.password_hash):
            return render_login(
                request,
                error="Credenciais inválidas.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if row.account_status != UserAccountStatus.ACTIVE.value:
            return render_login(
                request,
                error=f"Conta com estado '{row.account_status}'. Contacte o administrador.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        current_user_is_admin = is_admin_user(session, row.id, row.login_email)
        if requested_mode == "admin" and not current_user_is_admin:
            return render_login(
                request,
                error="Acesso administrativo disponível apenas para utilizadores administradores.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if requested_mode == "admin":
            linked_entity_ids_rows = session.scalars(
                select(MemberEntity.entity_id)
               .where(
                    MemberEntity.member_id == int(row.member_id),
                    MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                )
               .order_by(MemberEntity.id.asc())
            ).all()

            linked_entity_ids = [
                int(linked_entity_id)
                for linked_entity_id in linked_entity_ids_rows
                if isinstance(linked_entity_id, int)
            ]

            if not linked_entity_ids:
                return render_login(
                    request,
                    error="Utilizador sem entidade ativa associada.",
                    email=clean_email,
                    mode="admin",
                    login_data=login_data,
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            if parsed_entity_id not in linked_entity_ids:
                return render_login(
                    request,
                    error="Não é permitido entrar com uma entidade diferente da associada ao seu utilizador.",
                    email=clean_email,
                    mode="admin",
                    login_data=login_data,
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            selected_entity_context = get_entity_context_for_user(
                session,
                row.id,
                row.login_email,
                parsed_entity_id,
            )

            if selected_entity_context is None:
                return render_login(
                    request,
                    error="Não tem permissão para entrar na entidade selecionada.",
                    email=clean_email,
                    mode="admin",
                    login_data=login_data,
                    status_code=status.HTTP_403_FORBIDDEN,
                )
        else:
            selected_entity_context = get_entity_context_for_user(
                session,
                row.id,
                row.login_email,
                None,
            )

            if selected_entity_context is None:
                return render_login(
                    request,
                    error="Utilizador sem entidade ativa associada.",
                    email=clean_email,
                    mode="login",
                    login_data=login_data,
                    status_code=status.HTTP_403_FORBIDDEN,
                )

    request.session["user_id"] = row.id
    request.session["user_name"] = row.full_name
    request.session["user_email"] = row.login_email
    set_session_entity_context(request, selected_entity_context)

    return RedirectResponse(url="/users/new", status_code=status.HTTP_303_SEE_OTHER)

'''

login_route_pattern = re.compile(
    r'@router\.post\("/login", response_class=HTMLResponse\)\n'
    r'def login(?:_v\d+)?\(\n'
    r'.*?\n'
    r'(?=@router\.post\("/signup", response_class=HTMLResponse\))',
    re.S,
)

session_text_new, count = login_route_pattern.subn(new_login_function, session_text, count=1)

if count != 1:
    fail("nao consegui substituir a funcao de login em session_handlers.py")


####################################################################################
# (4) VALIDAR SINTAXE PYTHON
####################################################################################

try:
    ast.parse(session_text_new)
except SyntaxError as exc:
    fail(f"session_handlers.py ficaria com erro de sintaxe: {exc}")


####################################################################################
# (5) GRAVAR FICHEIROS
####################################################################################

SESSION_PATH.write_text(session_text_new, encoding="utf-8")
LOGIN_TEMPLATE_PATH.write_text(login_text, encoding="utf-8")

print("OK: session_handlers.py atualizado com login_v1.")
print("OK: login.html atualizado.")
print("OK: patch_login_auto_entity_v1 concluido.")
