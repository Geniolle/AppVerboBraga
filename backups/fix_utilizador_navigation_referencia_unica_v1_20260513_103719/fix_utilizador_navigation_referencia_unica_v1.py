from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(".")
TEMPLATE_PRINCIPAL = ROOT / "templates" / "new_user.html"
PARTIAL_UTILIZADOR = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
MODULO_NAVEGACAO = ROOT / "static" / "js" / "modules" / "admin_user_action_navigation_v1.js"
MODULO_TABELA = ROOT / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js"

SCRIPT_NAV_CANONICO = '<script src="/static/js/modules/admin_user_action_navigation_v1.js?v=20260513-utilizador-action-navigation-v2" defer></script>'
SCRIPT_TABLE_REGEX = re.compile(
    r'<script\s+[^>]*src=["\']/static/js/modules/admin_user_shadow_table_v1\.js\?v=[^"\']+["\'][^>]*>\s*</script>',
    re.IGNORECASE,
)
SCRIPT_NAV_REGEX = re.compile(
    r'^[ \t]*<script\s+[^>]*src=["\']/static/js/modules/admin_user_action_navigation_v1\.js\?v=[^"\']+["\'][^>]*>\s*</script>[ \t]*\r?\n?',
    re.IGNORECASE | re.MULTILINE,
)
SCRIPT_NAV_ANYWHERE_REGEX = re.compile(
    r'<script\s+[^>]*src=["\']/static/js/modules/admin_user_action_navigation_v1\.js\?v=[^"\']+["\'][^>]*>\s*</script>',
    re.IGNORECASE,
)
SCRIPT_NAV_MARKED_BLOCK_REGEX = re.compile(
    r'[ \t]*<!--\s*APPVERBO_UTILIZADOR_ACTION_NAVIGATION_[A-Z0-9_]*_START\s*-->.*?<!--\s*APPVERBO_UTILIZADOR_ACTION_NAVIGATION_[A-Z0-9_]*_END\s*-->\s*\r?\n?',
    re.IGNORECASE | re.DOTALL,
)


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_v1(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_eof_v1(text: str) -> str:
    return text.rstrip() + "\n"


def remove_navigation_scripts_v1(text: str) -> str:
    text = SCRIPT_NAV_MARKED_BLOCK_REGEX.sub("", text)
    text = SCRIPT_NAV_REGEX.sub("", text)
    return text


def limpar_template_principal_v1() -> None:
    text = read_text_v1(TEMPLATE_PRINCIPAL)
    original = text

    text = remove_navigation_scripts_v1(text)
    text = normalize_eof_v1(text)

    if text != original:
        write_text_v1(TEMPLATE_PRINCIPAL, text)
        print(f"Template principal limpo: {TEMPLATE_PRINCIPAL}")
    else:
        write_text_v1(TEMPLATE_PRINCIPAL, text)
        print(f"Template principal sem referência duplicada: {TEMPLATE_PRINCIPAL}")


def garantir_script_unico_no_partial_v1() -> None:
    text = read_text_v1(PARTIAL_UTILIZADOR)
    original = text

    text = remove_navigation_scripts_v1(text)

    table_match = SCRIPT_TABLE_REGEX.search(text)
    if not table_match:
        raise RuntimeError(
            "ERRO: partial do Utilizador não contém o carregamento do módulo admin_user_shadow_table_v1.js."
        )

    insert_pos = table_match.end()
    after_table = text[insert_pos:]
    prefix = text[:insert_pos]

    if not after_table.startswith("\n"):
        prefix += "\n"

    text = prefix + SCRIPT_NAV_CANONICO + "\n" + after_table.lstrip("\n")
    text = normalize_eof_v1(text)

    if text != original:
        write_text_v1(PARTIAL_UTILIZADOR, text)
        print(f"Partial atualizado com script único: {PARTIAL_UTILIZADOR}")
    else:
        print(f"Partial já estava correto: {PARTIAL_UTILIZADOR}")


def validar_modulo_navegacao_v1() -> None:
    text = read_text_v1(MODULO_NAVEGACAO)

    required_tokens = [
        "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1",
        "normalizarUrlAcaoUtilizador_v1",
        "isUrlAcaoUtilizador_v1",
        "localizarLinkAcaoUtilizador_v1",
        "navegarParaAcaoUtilizador_v1",
        "document.addEventListener",
        "window.location.assign",
    ]

    missing = [token for token in required_tokens if token not in text]
    if missing:
        raise RuntimeError(
            "ERRO: módulo de navegação do Utilizador incompleto. Tokens ausentes: "
            + ", ".join(missing)
        )

    if "utilizador-action-navigation-head-v2" in text:
        raise RuntimeError(
            "ERRO: módulo de navegação ainda contém referência antiga head-v2."
        )

    print(f"Módulo de navegação validado: {MODULO_NAVEGACAO}")


def localizar_referencias_runtime_v1() -> list[Path]:
    allowed_suffixes = {
        ".html",
        ".js",
        ".py",
        ".css",
        ".txt",
        ".md",
    }

    ignored_dirs = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "backups",
        "node_modules",
    }

    files: list[Path] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        parts = set(path.parts)
        if parts & ignored_dirs:
            continue

        if path.suffix.lower() not in allowed_suffixes:
            continue

        try:
            text = read_text_v1(path)
        except UnicodeDecodeError:
            continue

        if "admin_user_action_navigation_v1.js" in text or "utilizador-action-navigation-head-v2" in text:
            files.append(path)

    return sorted(files)


def validar_referencias_finais_v1() -> None:
    template_text = read_text_v1(TEMPLATE_PRINCIPAL)
    partial_text = read_text_v1(PARTIAL_UTILIZADOR)

    if "utilizador-action-navigation-head-v2" in template_text:
        raise RuntimeError("ERRO: template principal ainda contém cache bust antigo head-v2.")

    if "admin_user_action_navigation_v1.js" in template_text:
        raise RuntimeError("ERRO: template principal ainda carrega módulo de navegação do Utilizador. Deve ficar só no partial.")

    nav_refs_partial = len(SCRIPT_NAV_ANYWHERE_REGEX.findall(partial_text))
    if nav_refs_partial != 1:
        raise RuntimeError(
            f"ERRO: partial deve conter exatamente 1 carregamento de admin_user_action_navigation_v1.js. Encontrado: {nav_refs_partial}"
        )

    if SCRIPT_NAV_CANONICO not in partial_text:
        raise RuntimeError("ERRO: partial não contém a referência canónica do módulo de navegação.")

    if "utilizador-action-navigation-head-v2" in partial_text:
        raise RuntimeError("ERRO: partial ainda contém cache bust antigo head-v2.")

    refs = localizar_referencias_runtime_v1()
    print("Referências runtime encontradas:")
    for ref in refs:
        print(f" - {ref}")

    unexpected: list[Path] = []
    for ref in refs:
        if ref == PARTIAL_UTILIZADOR:
            continue
        if ref == MODULO_NAVEGACAO:
            continue
        unexpected.append(ref)

    if unexpected:
        raise RuntimeError(
            "ERRO: referência inesperada ao módulo de navegação fora do partial/módulo: "
            + ", ".join(str(path) for path in unexpected)
        )

    print("OK: referência do módulo de navegação está única e isolada no partial.")


def main() -> None:
    limpar_template_principal_v1()
    garantir_script_unico_no_partial_v1()
    validar_modulo_navegacao_v1()
    validar_referencias_finais_v1()


if __name__ == "__main__":
    main()
