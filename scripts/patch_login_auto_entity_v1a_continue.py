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


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not SESSION_PATH.exists():
    fail(f"ficheiro nao encontrado: {SESSION_PATH}")

if not LOGIN_TEMPLATE_PATH.exists():
    fail(f"ficheiro nao encontrado: {LOGIN_TEMPLATE_PATH}")


####################################################################################
# (2) LER FICHEIROS
####################################################################################

session_text = SESSION_PATH.read_text(encoding="utf-8")
login_text = LOGIN_TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) GARANTIR QUE O LOGIN COMUM NAO TEM CAMPO ENTIDADE
####################################################################################

common_start_marker = '''    {% else %}
      <h1>Entrar na sua conta</h1>'''

providers_marker = '''      <div class="providers">'''

common_start = login_text.find(common_start_marker)
if common_start == -1:
    fail("nao encontrei o inicio do bloco de login comum.")

providers_start = login_text.find(providers_marker, common_start)
if providers_start == -1:
    fail("nao encontrei o fim do formulario do login comum antes dos providers.")

common_block = login_text[common_start:providers_start]

entity_field_pattern = re.compile(
    r'\n\s*<div class="field">\s*'
    r'\n\s*<label for="entity_id">Entidade</label>'
    r'[\s\S]*?'
    r'\n\s*</div>\s*\n',
    re.S,
)

common_block_new, remove_count = entity_field_pattern.subn(
    '\n        {# Entidade definida automaticamente no backend pelo email do utilizador. #}\n\n',
    common_block,
    count=1,
)

if remove_count > 0:
    print("OK: campo Entidade removido do bloco de login comum.")
else:
    print("OK: bloco de login comum ja estava sem o campo Entidade.")

if 'for="entity_id"' in common_block_new or 'name="entity_id"' in common_block_new:
    fail("campo Entidade ainda existe dentro do bloco de login comum.")

login_text = login_text[:common_start] + common_block_new + login_text[providers_start:]


####################################################################################
# (4) VALIDAR LOGIN_V1 E RESOLUCAO AUTOMATICA DA ENTIDADE
####################################################################################

if "def login_v1(" not in session_text:
    fail("funcao login_v1 nao encontrada em session_handlers.py.")

if "requested_mode = \"admin\" if login_mode.strip().lower() == \"admin\" else \"login\"" not in session_text:
    fail("login_v1 nao contem a separacao entre login comum e admin.")

auto_entity_pattern = re.compile(
    r'selected_entity_context\s*=\s*get_entity_context_for_user\(\s*'
    r'session,\s*'
    r'row\.id,\s*'
    r'row\.login_email,\s*'
    r'None,\s*'
    r'\)',
    re.S,
)

if not auto_entity_pattern.search(session_text):
    fail("login comum nao esta a resolver a entidade automaticamente com get_entity_context_for_user(..., None).")


####################################################################################
# (5) VALIDAR SINTAXE PYTHON
####################################################################################

try:
    ast.parse(session_text)
except SyntaxError as exc:
    fail(f"session_handlers.py tem erro de sintaxe: {exc}")


####################################################################################
# (6) GRAVAR TEMPLATE VALIDADO
####################################################################################

LOGIN_TEMPLATE_PATH.write_text(login_text, encoding="utf-8")

print("OK: login.html validado.")
print("OK: session_handlers.py validado.")
print("OK: patch_login_auto_entity_v1a_continue concluido.")
