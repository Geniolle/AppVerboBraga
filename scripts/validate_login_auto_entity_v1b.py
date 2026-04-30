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
# (2) LER CONTEUDO
####################################################################################

session_text = SESSION_PATH.read_text(encoding="utf-8")
login_text = LOGIN_TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) VALIDAR LOGIN_V1
####################################################################################

if "def login_v1(" not in session_text:
    fail("funcao login_v1 nao encontrada em session_handlers.py.")

if 'requested_mode = "admin" if login_mode.strip().lower() == "admin" else "login"' not in session_text:
    fail("login_v1 nao contem separacao entre login comum e admin.")

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
    fail("login comum nao resolve entidade automaticamente com get_entity_context_for_user(..., None).")


####################################################################################
# (4) VALIDAR BLOCO DO LOGIN COMUM NO TEMPLATE
####################################################################################

common_login_pattern = re.compile(
    r'\{%\s*else\s*%\}\s*'
    r'<h1>\s*Entrar na sua conta\s*</h1>'
    r'(?P<body>[\s\S]*?)'
    r'<div class="providers">',
    re.S,
)

match = common_login_pattern.search(login_text)

if not match:
    fail("nao consegui localizar o bloco do login comum no template login.html.")

common_login_body = match.group("body")

if 'for="entity_id"' in common_login_body or 'name="entity_id"' in common_login_body:
    fail("campo Entidade ainda existe dentro do bloco do login comum.")

if '<input id="email"' not in common_login_body:
    fail("campo Email nao encontrado no login comum.")

if 'name="password"' not in common_login_body:
    fail("campo Palavra-passe nao encontrado no login comum.")

if 'login_mode" value="login"' not in common_login_body:
    fail("input hidden login_mode=login nao encontrado no login comum.")

print("OK: login comum esta sem campo Entidade.")
print("OK: login comum contem Email, Palavra-passe e login_mode=login.")


####################################################################################
# (5) VALIDAR QUE LOGIN ADMIN CONTINUA COM ENTIDADE
####################################################################################

admin_login_pattern = re.compile(
    r'\{%\s*if mode == "admin"\s*%\}'
    r'(?P<body>[\s\S]*?)'
    r'\{%\s*elif mode == "signup"\s*%\}',
    re.S,
)

admin_match = admin_login_pattern.search(login_text)

if not admin_match:
    fail("nao consegui localizar o bloco de login admin no template login.html.")

admin_login_body = admin_match.group("body")

if 'name="entity_id"' not in admin_login_body:
    fail("campo Entidade nao encontrado no login admin. O admin deve continuar a selecionar entidade.")

print("OK: login admin continua com campo Entidade.")


####################################################################################
# (6) VALIDAR SINTAXE PYTHON
####################################################################################

try:
    ast.parse(session_text)
except SyntaxError as exc:
    fail(f"session_handlers.py tem erro de sintaxe: {exc}")

print("OK: session_handlers.py sem erro de sintaxe.")
print("OK: VALIDACAO LOGIN AUTO ENTITY V1B CONCLUIDA.")
