from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-remover-textos-v1"


def fail_v1(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail_v1(f"ficheiro não encontrado: {TEMPLATE_PATH}")

if not JS_PATH.exists():
    fail_v1(f"ficheiro não encontrado: {JS_PATH}")


####################################################################################
# (2) REMOVER TEXTO SUPERIOR DO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

text_patterns = [
    r'\n\s*<p>\s*Defina e organize apenas as sess[oõ]es do menu lateral\.\s*</p>',
    r'\n\s*<p>\s*Defina e organize apenas as sessoes do menu lateral\.\s*</p>',
]

template_before = template_content

for pattern in text_patterns:
    template_content = re.sub(pattern, "", template_content, flags=re.IGNORECASE)

if template_content == template_before:
    print("AVISO: texto 'Defina e organize apenas as sessoes do menu lateral.' não encontrado no template ou já removido.")
else:
    print("OK: texto superior removido do template.")


####################################################################################
# (3) REMOVER TITULO DEFINICOES DO JS DA TELA SESSOES
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_before = js_content

remove_title_patterns = [
    r'\n\s*const titulo = document\.createElement\("h2"\);\s*\n\s*titulo\.textContent = "Definições";\s*\n\s*',
    r'\n\s*const titulo = document\.createElement\("h2"\);\s*\n\s*titulo\.textContent = "Definicoes";\s*\n\s*',
]

for pattern in remove_title_patterns:
    js_content = re.sub(pattern, "\n", js_content, flags=re.IGNORECASE)

append_title_patterns = [
    r'\n\s*tituloBloco\.appendChild\(titulo\);\s*',
]

for pattern in append_title_patterns:
    js_content = re.sub(pattern, "\n", js_content)

if js_content == js_before:
    print("AVISO: título 'Definições' não encontrado no JS ou já removido.")
else:
    print("OK: título Definições removido do JS da tela Sessões.")


####################################################################################
# (4) ATUALIZAR CACHE BUSTER DO JS NO TEMPLATE
####################################################################################

if "sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    print("AVISO: sidebar_sections_layout_v1.js não encontrado no template para cache buster.")


####################################################################################
# (5) GRAVAR ALTERACOES
####################################################################################

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")
JS_PATH.write_text(js_content, encoding="utf-8")


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")

if re.search(r"Defina e organize apenas as sess[oõ]es do menu lateral\.", template_validado, flags=re.IGNORECASE):
    fail_v1("texto 'Defina e organize apenas as sessoes do menu lateral.' ainda existe no template.")

if 'titulo.textContent = "Definições";' in js_validado or 'titulo.textContent = "Definicoes";' in js_validado:
    fail_v1("texto 'Definições' ainda existe como título no JS.")

if "Ative os processos do menu lateral" not in js_validado:
    fail_v1("texto restante 'Ative os processos...' não foi preservado no JS.")

if "Sessoes do sidebar" not in template_validado and "Sessões do sidebar" not in template_validado:
    fail_v1("título principal 'Sessoes do sidebar' não foi preservado no template.")

print("OK: textos removidos e demais conteúdos preservados.")
