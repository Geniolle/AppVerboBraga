from __future__ import annotations

import importlib
import py_compile
import re
import sys
from pathlib import Path


ROOT = Path.cwd()

INIT_FILE = ROOT / "appverbo" / "admin_subprocesses" / "utilizador" / "__init__.py"
PAGINA_FILE = ROOT / "appverbo" / "admin_subprocesses" / "utilizador" / "pagina.py"
CONFIGURACAO_FILE = ROOT / "appverbo" / "admin_subprocesses" / "utilizador" / "configuracao.py"
URLS_FILE = ROOT / "appverbo" / "admin_subprocesses" / "utilizador" / "urls.py"
PAGE_HANDLER_FILE = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
REGISTRY_FILE = ROOT / "appverbo" / "admin_subprocesses" / "registry.py"

DIRECT_PAGE_IMPORT = "from appverbo.admin_subprocesses.utilizador.pagina import montar_estado_pagina_utilizador_v1"
PACKAGE_PAGE_IMPORT = "from appverbo.admin_subprocesses.utilizador import montar_estado_pagina_utilizador_v1"
CONFIG_IMPORT_ABSOLUTE = "from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG"
CONFIG_IMPORT_RELATIVE = "from .configuracao import UTILIZADOR_CONFIG"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def ensure_files_exist() -> None:
    for path in (
        INIT_FILE,
        PAGINA_FILE,
        CONFIGURACAO_FILE,
        URLS_FILE,
        PAGE_HANDLER_FILE,
        REGISTRY_FILE,
    ):
        if not path.exists():
            raise FileNotFoundError(f"Ficheiro obrigatório não encontrado: {path}")


def rewrite_utilizador_init() -> None:
    text = '''from __future__ import annotations

from .configuracao import UTILIZADOR_CONFIG
from .urls import (
    montar_url_editar_utilizador_v1,
    montar_url_exibir_utilizador_v1,
    montar_url_fechar_utilizador_v1,
)

__all__ = (
    "UTILIZADOR_CONFIG",
    "montar_url_editar_utilizador_v1",
    "montar_url_exibir_utilizador_v1",
    "montar_url_fechar_utilizador_v1",
)
'''
    write_text(INIT_FILE, text)
    print("Atualizado sem import circular:", INIT_FILE.relative_to(ROOT))


def patch_pagina_sem_registry() -> None:
    text = read_text(PAGINA_FILE)

    text = re.sub(
        r"(?m)^\s*from\s+appverbo\.admin_subprocesses\.registry\s+import\s+get_admin_subprocess_config\s*\n",
        "",
        text,
    )
    text = re.sub(
        r"(?m)^\s*from\s+appverbo\.admin_subprocesses\s+import\s+get_admin_subprocess_config\s*\n",
        "",
        text,
    )
    text = re.sub(
        r"(?m)^\s*from\s+\.{1,2}registry\s+import\s+get_admin_subprocess_config\s*\n",
        "",
        text,
    )

    if CONFIG_IMPORT_ABSOLUTE not in text and CONFIG_IMPORT_RELATIVE not in text:
        future_line = "from __future__ import annotations\n"
        if future_line in text:
            text = text.replace(future_line, future_line + "\n" + CONFIG_IMPORT_ABSOLUTE + "\n", 1)
        else:
            text = CONFIG_IMPORT_ABSOLUTE + "\n" + text

    text = text.replace('get_admin_subprocess_config("utilizador")', "UTILIZADOR_CONFIG")
    text = text.replace("get_admin_subprocess_config('utilizador')", "UTILIZADOR_CONFIG")

    if "get_admin_subprocess_config" in text:
        raise RuntimeError(
            "ERRO: pagina.py ainda contém get_admin_subprocess_config. "
            "O módulo específico do Utilizador não pode importar o registry."
        )

    if "admin_subprocesses.registry" in text:
        raise RuntimeError(
            "ERRO: pagina.py ainda importa appverbo.admin_subprocesses.registry."
        )

    if "UTILIZADOR_CONFIG" not in text:
        raise RuntimeError("ERRO: pagina.py não contém UTILIZADOR_CONFIG após a correção.")

    write_text(PAGINA_FILE, text)
    print("Atualizado sem dependência do registry:", PAGINA_FILE.relative_to(ROOT))


def patch_page_handler_import_direto() -> None:
    text = read_text(PAGE_HANDLER_FILE)

    text = text.replace(PACKAGE_PAGE_IMPORT, DIRECT_PAGE_IMPORT)

    lines = text.splitlines()
    new_lines: list[str] = []
    found_direct_import = False

    for line in lines:
        if line.strip() == DIRECT_PAGE_IMPORT:
            if not found_direct_import:
                new_lines.append(DIRECT_PAGE_IMPORT)
                found_direct_import = True
            continue
        new_lines.append(line)

    if not found_direct_import:
        insert_index = 0

        for index, line in enumerate(new_lines):
            if line.startswith("from __future__ import"):
                insert_index = index + 1
                break

        while insert_index < len(new_lines) and new_lines[insert_index].strip() == "":
            insert_index += 1

        new_lines.insert(insert_index, DIRECT_PAGE_IMPORT)

    text = "\n".join(new_lines) + "\n"

    if PACKAGE_PAGE_IMPORT in text:
        raise RuntimeError(
            "ERRO: page_handler.py ainda importa montar_estado_pagina_utilizador_v1 pelo package __init__."
        )

    if DIRECT_PAGE_IMPORT not in text:
        raise RuntimeError(
            "ERRO: page_handler.py não contém import direto de utilizador.pagina."
        )

    write_text(PAGE_HANDLER_FILE, text)
    print("Import direto garantido:", PAGE_HANDLER_FILE.relative_to(ROOT))


def validate_text_contracts() -> None:
    init_text = read_text(INIT_FILE)
    pagina_text = read_text(PAGINA_FILE)
    handler_text = read_text(PAGE_HANDLER_FILE)

    if ".pagina import" in init_text or "montar_estado_pagina_utilizador_v1" in init_text:
        raise RuntimeError(
            "ERRO: utilizador/__init__.py continua importando pagina.py ou montar_estado_pagina_utilizador_v1."
        )

    if "admin_subprocesses.registry" in pagina_text or "get_admin_subprocess_config" in pagina_text:
        raise RuntimeError(
            "ERRO: utilizador/pagina.py continua acoplado ao registry."
        )

    if "UTILIZADOR_CONFIG" not in pagina_text:
        raise RuntimeError(
            "ERRO: utilizador/pagina.py não usa UTILIZADOR_CONFIG."
        )

    if PACKAGE_PAGE_IMPORT in handler_text:
        raise RuntimeError(
            "ERRO: page_handler.py ainda importa pelo package utilizador."
        )

    if DIRECT_PAGE_IMPORT not in handler_text:
        raise RuntimeError(
            "ERRO: page_handler.py não importa diretamente utilizador.pagina."
        )


def validate_py_compile() -> None:
    for path in (
        INIT_FILE,
        PAGINA_FILE,
        CONFIGURACAO_FILE,
        URLS_FILE,
        PAGE_HANDLER_FILE,
        REGISTRY_FILE,
    ):
        py_compile.compile(str(path), doraise=True)
        print("py_compile OK:", path.relative_to(ROOT))


def validate_import_boot() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    modules_to_clear = [
        name
        for name in list(sys.modules)
        if name == "web_app"
        or name == "appverbo"
        or name.startswith("appverbo.")
    ]

    for name in modules_to_clear:
        sys.modules.pop(name, None)

    importlib.import_module("appverbo.admin_subprocesses.registry")
    print("Import OK: appverbo.admin_subprocesses.registry")

    importlib.import_module("appverbo.admin_subprocesses.utilizador.pagina")
    print("Import OK: appverbo.admin_subprocesses.utilizador.pagina")

    importlib.import_module("appverbo.routes.profile.page_handler")
    print("Import OK: appverbo.routes.profile.page_handler")

    importlib.import_module("web_app")
    print("Import OK: web_app")


def main() -> None:
    ensure_files_exist()
    rewrite_utilizador_init()
    patch_pagina_sem_registry()
    patch_page_handler_import_direto()
    validate_text_contracts()
    validate_py_compile()
    validate_import_boot()
    print("OK: import circular do subprocesso Utilizador corrigido com sucesso.")


if __name__ == "__main__":
    main()
