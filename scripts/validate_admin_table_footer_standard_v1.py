from __future__ import annotations

from pathlib import Path


ROOT = Path.cwd()


####################################################################################
# (1) CONFIGURAR FICHEIROS
####################################################################################

FILES_TO_VALIDATE = [
    "templates/partials/admin_table_footer_standard_v1.html",
    "templates/partials/admin_user_table_v1.html",
    "templates/macros/admin_subprocess.html",
    "templates/new_user.html",
    "static/css/modules/admin_table_footer_standard_v1.css",
    "static/js/modules/admin_table_footer_standard_v1.js",
]

CONTENT_CHECKS = [
    (
        "templates/partials/admin_table_footer_standard_v1.html",
        "render_admin_table_footer_standard_v1",
        "macro reutilizavel do rodape",
    ),
    (
        "templates/partials/admin_table_footer_standard_v1.html",
        "data-admin-table-footer-standard-v1",
        "data attribute do rodape reutilizavel",
    ),
    (
        "static/css/modules/admin_table_footer_standard_v1.css",
        "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START",
        "CSS modular do rodape",
    ),
    (
        "static/js/modules/admin_table_footer_standard_v1.js",
        "window.AppVerboAdminTableFooterStandard_v1",
        "API JS reutilizavel",
    ),
    (
        "templates/partials/admin_user_table_v1.html",
        "render_admin_table_footer_standard_v1(table_id=table_id",
        "partial de utilizadores usa macro do rodape",
    ),
    (
        "templates/macros/admin_subprocess.html",
        "render_admin_table_footer_standard_v1",
        "macro de subprocessos usa rodape padrao",
    ),
    (
        "templates/macros/admin_subprocess.html",
        "admin-subprocess-{{ state.config.key }}-{{ status_value }}-table",
        "tabela de subprocessos tem id padrao",
    ),
    (
        "templates/new_user.html",
        "admin_table_footer_standard_v1.css",
        "new_user carrega CSS do rodape",
    ),
    (
        "templates/new_user.html",
        "admin_table_footer_standard_v1.js",
        "new_user carrega JS do rodape",
    ),
]


####################################################################################
# (2) FUNCOES BASE
####################################################################################

def read_text_v1(relative_path: str) -> str:
    path = ROOT / relative_path

    if not path.exists():
        raise FileNotFoundError(f"Ficheiro esperado nao encontrado: {relative_path}")

    return path.read_text(encoding="utf-8")


def validate_no_real_mojibake_v1(relative_path: str, content: str) -> None:
    bad_tokens = ("Ã", "Â", "\ufffd")
    bad_lines = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        if any(token in line for token in bad_tokens):
            bad_lines.append((line_number, line))

    if bad_lines:
        print(f"ERRO: possivel mojibake real em {relative_path}")
        for line_number, line in bad_lines:
            print(f"Linha {line_number}: {line}")
        raise RuntimeError(f"Possivel mojibake real em {relative_path}")

    print(f"OK: sem mojibake real em {relative_path}")


def validate_content_checks_v1() -> None:
    for relative_path, pattern, label in CONTENT_CHECKS:
        content = read_text_v1(relative_path)

        if pattern not in content:
            raise RuntimeError(f"Validacao falhou: {label}")

        print(f"OK: {label}")


####################################################################################
# (3) EXECUTAR VALIDACAO
####################################################################################

def main_v1() -> None:
    print("===== VALIDAR FICHEIROS =====")

    for relative_path in FILES_TO_VALIDATE:
        content = read_text_v1(relative_path)
        validate_no_real_mojibake_v1(relative_path, content)

    print("")
    print("===== VALIDAR CONTEUDO =====")
    validate_content_checks_v1()

    print("")
    print("OK: validacao Python concluida sem falso positivo de acentos portugueses.")


if __name__ == "__main__":
    main_v1()
