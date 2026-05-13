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
        'f"?menu={USER_ADMIN_MENU_V1}"' in urls
        and 'f"&admin_tab={USER_ADMIN_TAB_V1}"' in urls
        and 'f"&user_edit_id={clean_user_id}"' in urls
        and 'f"&target={USER_EDIT_TARGET_V1}"' in urls
        and 'f"#{USER_EDIT_TARGET_V1}"' in urls,
        "urls.py deve montar menu/admin_tab/user_edit_id/target/hash para o subprocesso Utilizador.",
    )
    assert_true(
        'f"&user_view=1"' in urls and 'f"&user_view=0"' in urls,
        "urls.py deve montar user_view=1 (Exibir) e user_view=0 (Editar).",
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
    table_base_path = ROOT / "templates/partials/admin_user_table_base_v1.html"

    if partial_path.exists():
        partial = partial_path.read_text(encoding="utf-8")
        table_base = table_base_path.read_text(encoding="utf-8") if table_base_path.exists() else ""

        assert_true(
            ('row.get("view_url")' in partial or "row.get('view_url')" in partial)
            or ('row.get("view_url")' in table_base or "row.get('view_url')" in table_base),
            "partial do Utilizador deve usar view_url vindo do repository (no partial principal ou no table base)",
        )

        assert_true(
            ('row.get("edit_url")' in partial or "row.get('edit_url')" in partial)
            or ('row.get("edit_url")' in table_base or "row.get('edit_url')" in table_base),
            "partial do Utilizador deve usar edit_url vindo do repository (no partial principal ou no table base)",
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
