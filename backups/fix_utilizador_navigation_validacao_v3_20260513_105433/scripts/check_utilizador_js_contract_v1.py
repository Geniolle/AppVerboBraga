from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_PRINCIPAL = ROOT / "templates" / "new_user.html"
PARTIAL_UTILIZADOR = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
MODULO_TABELA = ROOT / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js"
MODULO_NAVEGACAO = ROOT / "static" / "js" / "modules" / "admin_user_action_navigation_v1.js"

NOME_MODULO = "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1"
ARQUIVO_MODULO = "admin_user_action_navigation_v1.js"


def read_text(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"Ficheiro obrigatorio nao encontrado: {path}")
    return path.read_text(encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def contar_ocorrencias(texto: str, termo: str) -> int:
    return texto.count(termo)


def validar_modulo_navegacao() -> None:
    texto = read_text(MODULO_NAVEGACAO)

    assert_true(
        NOME_MODULO in texto,
        "Modulo de navegacao do Utilizador deve identificar APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1.",
    )
    assert_true(
        "window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1" in texto,
        "Modulo de navegacao deve exportar window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1.",
    )
    assert_true(
        "document.addEventListener" in texto and '"click"' in texto,
        "Modulo de navegacao deve registar listener de click.",
    )
    assert_true(
        "window.location.assign" in texto,
        "Modulo de navegacao deve navegar usando window.location.assign.",
    )
    assert_true(
        "preventDefault" in texto,
        "Modulo de navegacao deve impedir handlers concorrentes antes de navegar.",
    )
    assert_true(
        "user_edit_id" in texto and "user_view" in texto,
        "Modulo de navegacao deve validar parametros de acao do Utilizador.",
    )


def validar_modulo_tabela() -> None:
    texto = read_text(MODULO_TABELA)

    assert_true(
        ARQUIVO_MODULO not in texto,
        "Modulo de tabela nao deve carregar nem depender do modulo de navegacao.",
    )
    assert_true(
        "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1" not in texto,
        "Modulo de tabela nao deve conter logica de navegacao das acoes.",
    )


def validar_template_principal() -> None:
    texto = read_text(TEMPLATE_PRINCIPAL)

    assert_true(
        ARQUIVO_MODULO not in texto,
        "Template principal nao deve carregar diretamente o modulo isolado de navegacao do Utilizador.",
    )


def validar_partial_utilizador() -> None:
    texto = read_text(PARTIAL_UTILIZADOR)

    assert_true(
        ARQUIVO_MODULO in texto,
        "Partial deve carregar modulo isolado de navegacao do Utilizador.",
    )
    assert_true(
        contar_ocorrencias(texto, ARQUIVO_MODULO) == 1,
        "Partial deve carregar modulo de navegacao do Utilizador exatamente uma vez.",
    )
    assert_true(
        "admin_user_shadow_table_v1.js" in texto,
        "Partial deve carregar modulo de tabela do Utilizador.",
    )
    assert_true(
        texto.find("admin_user_shadow_table_v1.js") < texto.find(ARQUIVO_MODULO),
        "Modulo de navegacao deve ser carregado depois do modulo de tabela.",
    )
    assert_true(
        "view_url" in texto and "edit_url" in texto and "close_url" in texto,
        "Partial deve expor view_url, edit_url e close_url.",
    )
    assert_true(
        'href="{{ view_url }}"' in texto,
        "Partial deve usar href direto para Exibir.",
    )
    assert_true(
        'href="{{ edit_url }}"' in texto,
        "Partial deve usar href direto para Editar.",
    )


def validar_referencias_runtime() -> None:
    caminhos = [
        ROOT / "templates",
        ROOT / "appverbo",
        ROOT / "static",
    ]

    referencias: list[Path] = []

    for base in caminhos:
        if not base.exists():
            continue

        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".html", ".py", ".js"}:
                continue

            texto = path.read_text(encoding="utf-8", errors="ignore")
            if ARQUIVO_MODULO in texto:
                referencias.append(path.relative_to(ROOT))

    referencias_permitidas = {
        Path("templates/partials/admin_user_shadow_readonly_v1.html"),
    }

    inesperadas = [
        path
        for path in referencias
        if path not in referencias_permitidas
        and path != Path("static/js/modules/admin_user_action_navigation_v1.js")
    ]

    assert_true(
        not inesperadas,
        "Referencia inesperada ao modulo de navegacao fora do partial/modulo: "
        + ", ".join(str(path) for path in inesperadas),
    )


def main() -> None:
    validar_modulo_navegacao()
    validar_modulo_tabela()
    validar_template_principal()
    validar_partial_utilizador()
    validar_referencias_runtime()

    print("OK: contrato JS do subprocesso Utilizador validado com sucesso.")


if __name__ == "__main__":
    main()