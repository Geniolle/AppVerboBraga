from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_PRINCIPAL = ROOT / "templates" / "new_user.html"
PARTIAL_UTILIZADOR = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
PARTIAL_TABELA_BASE = ROOT / "templates" / "partials" / "admin_user_table_base_v1.html"
MODULO_TABELA = ROOT / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js"
MODULO_NAVEGACAO = ROOT / "static" / "js" / "modules" / "admin_user_action_navigation_v1.js"

NOME_MODULO = "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1"
ARQUIVO_MODULO = "admin_user_action_navigation_v1.js"
ARQUIVO_TABELA = "admin_user_shadow_table_v1.js"
MARCADOR_BRIDGE_ANTIGO = "APPVERBO_UTILIZADOR_ACTION_CLICK_BRIDGE"


def read_text_v4(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"Ficheiro obrigatorio nao encontrado: {path}")
    return path.read_text(encoding="utf-8")


def assert_true_v4(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def contar_script_tags_v4(texto: str, arquivo: str) -> int:
    pattern = re.compile(
        rf"<script\b(?=[^>]*\bsrc\s*=\s*[\"'][^\"']*{re.escape(arquivo)}[^\"']*[\"'])[^>]*>\s*</script>",
        re.IGNORECASE | re.DOTALL,
    )
    return len(pattern.findall(texto))


def validar_modulo_navegacao_v4() -> None:
    texto = read_text_v4(MODULO_NAVEGACAO)

    assert_true_v4(
        NOME_MODULO in texto,
        "Modulo de navegacao do Utilizador deve identificar APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1.",
    )
    assert_true_v4(
        "window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1" in texto,
        "Modulo de navegacao deve exportar window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1.",
    )
    possui_listener_click = (
        'document.addEventListener("click"' in texto
        or "document.addEventListener('click'" in texto
        or 'window.addEventListener("click"' in texto
        or "window.addEventListener('click'" in texto
    )
    assert_true_v4(
        possui_listener_click,
        "Modulo de navegacao deve registar listener de click (document ou window).",
    )
    assert_true_v4(
        "window.location.assign" in texto,
        "Modulo de navegacao deve navegar usando window.location.assign.",
    )
    assert_true_v4(
        "preventDefault" in texto,
        "Modulo de navegacao deve impedir handlers concorrentes antes de navegar.",
    )
    assert_true_v4(
        "stopPropagation" in texto,
        "Modulo de navegacao deve interromper propagacao de click concorrente.",
    )
    assert_true_v4(
        "user_edit_id" in texto and "user_view" in texto,
        "Modulo de navegacao deve validar parametros de acao do Utilizador.",
    )
    assert_true_v4(
        "data-admin-user-action-link='1'" in texto or 'data-admin-user-action-link="1"' in texto,
        "Modulo de navegacao deve filtrar click por data-admin-user-action-link='1'.",
    )


def validar_modulo_tabela_v4() -> None:
    texto = read_text_v4(MODULO_TABELA)

    assert_true_v4(
        ARQUIVO_MODULO not in texto,
        "Modulo de tabela nao deve carregar nem depender do modulo de navegacao.",
    )
    assert_true_v4(
        "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1" not in texto,
        "Modulo de tabela nao deve conter logica de navegacao das acoes.",
    )
    assert_true_v4(
        "window.location.assign" not in texto and "window.location.href" not in texto,
        "Modulo de tabela nao deve navegar para Exibir/Editar/Fechar.",
    )
    assert_true_v4(
        "data-admin-user-shadow-real-link" not in texto,
        "Modulo de tabela nao deve interceptar link de acao do subprocesso Utilizador.",
    )


def validar_template_principal_v4() -> None:
    texto = read_text_v4(TEMPLATE_PRINCIPAL)

    assert_true_v4(
        contar_script_tags_v4(texto, ARQUIVO_MODULO) == 0,
        "Template principal nao deve carregar diretamente o modulo isolado de navegacao do Utilizador.",
    )
    assert_true_v4(
        MARCADOR_BRIDGE_ANTIGO not in texto,
        "Template principal nao deve conter bridge inline antigo de click do Utilizador.",
    )


def validar_partial_utilizador_v4() -> None:
    texto = read_text_v4(PARTIAL_UTILIZADOR)
    texto_tabela_base = read_text_v4(PARTIAL_TABELA_BASE)

    qtd_nav = contar_script_tags_v4(texto, ARQUIVO_MODULO)
    qtd_tabela = contar_script_tags_v4(texto, ARQUIVO_TABELA)

    assert_true_v4(
        qtd_nav == 1,
        f"Partial deve carregar modulo de navegacao do Utilizador exatamente uma vez como script. Encontradas: {qtd_nav}",
    )
    assert_true_v4(
        qtd_tabela >= 1,
        "Partial deve carregar modulo de tabela do Utilizador.",
    )
    assert_true_v4(
        texto.find(ARQUIVO_TABELA) < texto.find(ARQUIVO_MODULO),
        "Modulo de navegacao deve ser carregado depois do modulo de tabela.",
    )
    assert_true_v4(
        "view_url" in texto_tabela_base and "edit_url" in texto_tabela_base,
        "Partial de tabela base deve expor view_url e edit_url.",
    )
    assert_true_v4(
        'href="{{ view_url }}"' in texto_tabela_base,
        "Partial de tabela base deve usar href direto para Exibir.",
    )
    assert_true_v4(
        'href="{{ edit_url }}"' in texto_tabela_base,
        "Partial de tabela base deve usar href direto para Editar.",
    )
    assert_true_v4(
        'data-admin-user-action-link="1"' in texto_tabela_base
        or "data-admin-user-action-link='1'" in texto_tabela_base,
        "Partial de tabela base deve marcar links de Exibir/Editar com data-admin-user-action-link='1'.",
    )


def validar_referencias_runtime_v4() -> None:
    caminhos = [
        ROOT / "templates",
        ROOT / "appverbo",
        ROOT / "static",
    ]

    referencias_script_inesperadas: list[Path] = []

    for base in caminhos:
        if not base.exists():
            continue

        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".html", ".py", ".js"}:
                continue

            texto = path.read_text(encoding="utf-8", errors="ignore")
            qtd_scripts = contar_script_tags_v4(texto, ARQUIVO_MODULO)

            if qtd_scripts <= 0:
                continue

            relativo = path.relative_to(ROOT)

            if relativo != Path("templates/partials/admin_user_shadow_readonly_v1.html"):
                referencias_script_inesperadas.append(relativo)

    assert_true_v4(
        not referencias_script_inesperadas,
        "Carregamento inesperado do modulo de navegacao fora do partial: "
        + ", ".join(str(path) for path in referencias_script_inesperadas),
    )


def main_v4() -> None:
    validar_modulo_navegacao_v4()
    validar_modulo_tabela_v4()
    validar_template_principal_v4()
    validar_partial_utilizador_v4()
    validar_referencias_runtime_v4()

    print("OK: contrato JS do subprocesso Utilizador validado com sucesso.")


if __name__ == "__main__":
    main_v4()
