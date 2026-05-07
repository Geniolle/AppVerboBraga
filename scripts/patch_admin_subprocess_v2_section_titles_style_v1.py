from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()
MACRO_PATH = PROJECT_ROOT / "templates" / "macros" / "admin_subprocess_v2.html"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path:
    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


####################################################################################
# (3) PATCH CSS REUTILIZAVEL DOS TITULOS
####################################################################################

STYLE_START = "{# APPVERBO_ADMIN_SUBPROCESS_V2_SECTION_TITLE_STYLE_V1_START #}"
STYLE_END = "{# APPVERBO_ADMIN_SUBPROCESS_V2_SECTION_TITLE_STYLE_V1_END #}"

STYLE_BLOCK = """{# APPVERBO_ADMIN_SUBPROCESS_V2_SECTION_TITLE_STYLE_V1_START #}
<style>
  .admin-subprocess-v2-section-title {
    margin: 0;
    font-size: 1.5rem;
    line-height: 1.25;
    font-weight: 700;
    color: #0f2940;
    letter-spacing: -0.01em;
  }
</style>
{# APPVERBO_ADMIN_SUBPROCESS_V2_SECTION_TITLE_STYLE_V1_END #}
"""


def patch_style_block_v1(content: str) -> str:
    if STYLE_START in content and STYLE_END in content:
        pattern = re.compile(
            re.escape(STYLE_START) + r".*?" + re.escape(STYLE_END),
            flags=re.DOTALL,
        )
        return pattern.sub(lambda _m: STYLE_BLOCK.strip(), content, count=1)

    macro_anchor = "{% macro"
    position = content.find(macro_anchor)

    if position < 0:
        raise RuntimeError("Nao encontrei o ponto para inserir o bloco de estilo no macro admin_subprocess_v2.html.")

    return content[:position] + STYLE_BLOCK + "\n\n" + content[position:]


####################################################################################
# (4) PATCH DOS HEADERS DE SECAO
####################################################################################

def append_css_class_v1(attrs: str, class_name: str) -> str:
    attrs = attrs or ""

    class_match = re.search(r'class=(["\'])(.*?)\1', attrs, flags=re.IGNORECASE | re.DOTALL)
    if class_match:
        existing_classes = class_match.group(2).split()
        if class_name not in existing_classes:
            existing_classes.append(class_name)
        new_class_attr = f'class="{ " ".join(existing_classes) }"'
        start, end = class_match.span()
        return attrs[:start] + new_class_attr + attrs[end:]

    return attrs + f' class="{class_name}"'


def replace_heading_v1(content: str, variable_expression: str) -> tuple[str, int]:
    pattern = re.compile(
        rf"<(?P<tag>h[1-6])(?P<attrs>[^>]*)>\s*\{{\{{\s*{variable_expression}\s*\}}\}}\s*</(?P=tag)>",
        flags=re.IGNORECASE,
    )

    replacement_count = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal replacement_count
        replacement_count += 1

        tag = match.group("tag")
        attrs = append_css_class_v1(match.group("attrs"), "admin-subprocess-v2-section-title")

        return f"<{tag}{attrs}>{{{{ {variable_expression} }}}}</{tag}>"

    updated = pattern.sub(_repl, content)
    return updated, replacement_count


def patch_section_titles_v1(content: str) -> str:
    variables = [
        r"section\.title",
        r"group\.title",
        r"card\.title",
        r"block\.title",
    ]

    total_replacements = 0
    updated = content

    for variable in variables:
        updated, count = replace_heading_v1(updated, variable)
        total_replacements += count

    if total_replacements == 0:
        raise RuntimeError("Nao encontrei headings dinamicos de secao para aplicar a classe admin-subprocess-v2-section-title.")

    return updated


####################################################################################
# (5) VALIDACAO
####################################################################################

def validate_v1(content: str) -> None:
    required_markers = [
        STYLE_START,
        STYLE_END,
        ".admin-subprocess-v2-section-title",
    ]

    missing = [marker for marker in required_markers if marker not in content]
    if missing:
        raise RuntimeError("Marcadores ausentes no macro admin_subprocess_v2.html: " + ", ".join(missing))

    if 'class="admin-subprocess-v2-section-title"' not in content and 'class="admin-subprocess-v2-section-title ' not in content and ' admin-subprocess-v2-section-title"' not in content:
        raise RuntimeError("Nao encontrei a classe admin-subprocess-v2-section-title aplicada em headings dinamicos.")

    print("OK: estilo reutilizavel dos titulos V2 foi aplicado.")
    print("OK: headings dinamicos agora usam admin-subprocess-v2-section-title.")


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(MACRO_PATH)

    backup_path = backup_file_v1(MACRO_PATH, "admin_subprocess_v2_section_titles_style_v1")
    print(f"OK: backup criado: {backup_path}")

    content = read_text_v1(MACRO_PATH)
    content = patch_style_block_v1(content)
    content = patch_section_titles_v1(content)

    write_text_v1(MACRO_PATH, content)
    validate_v1(content)

    print("OK: patch de estilo dos titulos dos cards V2 concluido.")


if __name__ == "__main__":
    main()
