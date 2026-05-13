from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) HELPERS
####################################################################################

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


####################################################################################
# (2) CONTRATO DA REFATORAÇÃO DO SUBPROCESSO UTILIZADOR
####################################################################################

def main() -> None:
    registry = read("appverbo/admin_subprocesses/registry.py")
    configuracao = read("appverbo/admin_subprocesses/utilizador/configuracao.py")
    urls = read("appverbo/admin_subprocesses/utilizador/urls.py")
    pagina = read("appverbo/admin_subprocesses/utilizador/pagina.py")
    repository = read("appverbo/admin_subprocesses/repositories/user_repository.py")
    page_handler = read("appverbo/routes/profile/page_handler.py")

    assert_true(
        "from .utilizador.configuracao import UTILIZADOR_CONFIG" in registry
        or "from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG" in registry,
        "registry.py deve importar UTILIZADOR_CONFIG de utilizador/configuracao.py",
    )

    assert_true(
        "UTILIZADOR_CONFIG = AdminSubprocessConfig(" not in registry,
        "registry.py não deve manter definição inline de UTILIZADOR_CONFIG",
    )

    assert_true(
        'enabled=True' in configuracao and 'migration_status="native_shadow"' in configuracao,
        "configuracao.py deve manter Utilizador enabled=True e native_shadow",
    )

    assert_true(
        "montar_url_exibir_utilizador_v1" in urls
        and "montar_url_editar_utilizador_v1" in urls
        and "montar_url_fechar_utilizador_v1" in urls,
        "urls.py deve centralizar URLs de Exibir, Editar e Fechar",
    )

    assert_true(
        "montar_estado_pagina_utilizador_v1" in pagina,
        "pagina.py deve centralizar o state do subprocesso Utilizador",
    )

    assert_true(
        "view_url" in repository
        and "edit_url" in repository
        and "montar_url_exibir_utilizador_v1" in repository,
        "UserAdminRepository deve entregar URLs de ação por linha",
    )

    assert_true(
        "montar_estado_pagina_utilizador_v1" in page_handler,
        "page_handler.py deve chamar a montagem isolada do state do Utilizador",
    )

    partial_path = ROOT / "templates/partials/admin_user_shadow_readonly_v1.html"

    if partial_path.exists():
        partial = partial_path.read_text(encoding="utf-8")

        assert_true(
            'row.get("view_url")' in partial or "row.get('view_url')" in partial,
            "partial do Utilizador deve usar view_url vindo do repository",
        )

        assert_true(
            'row.get("edit_url")' in partial or "row.get('edit_url')" in partial,
            "partial do Utilizador deve usar edit_url vindo do repository",
        )

        assert_true(
            '{% set view_url = "/users/new?menu=administrativo' not in partial,
            "partial do Utilizador não deve montar URL de Exibir manualmente",
        )

        assert_true(
            '{% set edit_url = "/users/new?menu=administrativo' not in partial,
            "partial do Utilizador não deve montar URL de Editar manualmente",
        )

    print("OK: contrato do subprocesso Utilizador isolado validado com sucesso.")


if __name__ == "__main__":
    main()
