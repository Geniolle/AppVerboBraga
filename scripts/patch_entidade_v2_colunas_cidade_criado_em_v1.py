from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

REGISTRY_PATH = PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_registry.py"
REPOSITORY_PATH = PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_entity_repository.py"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado para backup: {path}")

    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


####################################################################################
# (3) PATCH REPOSITORY: DISPONIBILIZAR CRIADO EM
####################################################################################

def patch_repository_v1() -> None:
    content = read_text_v1(REPOSITORY_PATH)

    if "def format_entity_created_at_v2" not in content:
        anchor = "def entity_status_label_v2(is_active: object) -> str:\n    return \"Ativo\" if bool(is_active) else \"Inativo\"\n"

        helper = '''def entity_status_label_v2(is_active: object) -> str:
    return "Ativo" if bool(is_active) else "Inativo"


def format_entity_created_at_v2(value: object) -> str:
    if value is None:
        return ""

    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")

    return str(value or "").strip()
'''

        if anchor not in content:
            raise RuntimeError("Nao encontrei entity_status_label_v2 para inserir format_entity_created_at_v2.")

        content = content.replace(anchor, helper, 1)

    if '"created_at_display": format_entity_created_at_v2(entity.created_at),' not in content:
        anchor = '''            "profile_scope_label": entity_scope_label_v2(entity.profile_scope),
            "is_active": bool(entity.is_active),'''

        replacement = '''            "profile_scope_label": entity_scope_label_v2(entity.profile_scope),
            "created_at": entity.created_at,
            "created_at_display": format_entity_created_at_v2(entity.created_at),
            "is_active": bool(entity.is_active),'''

        if anchor not in content:
            raise RuntimeError("Nao encontrei ponto para inserir created_at_display no row da Entidade V2.")

        content = content.replace(anchor, replacement, 1)

    required = [
        "format_entity_created_at_v2",
        '"city": entity.city or ""',
        '"created_at_display": format_entity_created_at_v2(entity.created_at)',
    ]

    missing = [marker for marker in required if marker not in content]

    if missing:
        raise RuntimeError("Marcadores ausentes em v2_entity_repository.py: " + ", ".join(missing))

    write_text_v1(REPOSITORY_PATH, content)


####################################################################################
# (4) PATCH REGISTRY: ADICIONAR COLUNAS AO LAYOUT
####################################################################################

def patch_registry_v1() -> None:
    content = read_text_v1(REGISTRY_PATH)

    old_columns = '''    columns=(
        AdminColumnConfigV2("internal_number", "Nº cliente"),
        AdminColumnConfigV2("name", "Nome"),
        AdminColumnConfigV2("profile_scope_label", "Perfil"),
        AdminColumnConfigV2("status_label", "Estado", column_type="badge"),
    ),'''

    new_columns = '''    columns=(
        AdminColumnConfigV2("internal_number", "Nº cliente"),
        AdminColumnConfigV2("name", "Nome"),
        AdminColumnConfigV2("profile_scope_label", "Perfil"),
        AdminColumnConfigV2("city", "Cidade"),
        AdminColumnConfigV2("created_at_display", "Criado em"),
        AdminColumnConfigV2("status_label", "Estado", column_type="badge"),
    ),'''

    if old_columns in content:
        content = content.replace(old_columns, new_columns, 1)
    elif 'AdminColumnConfigV2("city", "Cidade")' in content and 'AdminColumnConfigV2("created_at_display", "Criado em")' in content:
        pass
    else:
        raise RuntimeError("Nao encontrei bloco de columns da ENTIDADE_CONFIG_V2 para atualizar.")

    required = [
        'AdminColumnConfigV2("city", "Cidade")',
        'AdminColumnConfigV2("created_at_display", "Criado em")',
        'AdminColumnConfigV2("status_label", "Estado", column_type="badge")',
    ]

    missing = [marker for marker in required if marker not in content]

    if missing:
        raise RuntimeError("Marcadores ausentes em v2_registry.py: " + ", ".join(missing))

    write_text_v1(REGISTRY_PATH, content)


####################################################################################
# (5) VALIDAR
####################################################################################

def validate_v1() -> None:
    registry_content = read_text_v1(REGISTRY_PATH)
    repository_content = read_text_v1(REPOSITORY_PATH)

    required_registry = [
        'AdminColumnConfigV2("city", "Cidade")',
        'AdminColumnConfigV2("created_at_display", "Criado em")',
    ]

    missing_registry = [marker for marker in required_registry if marker not in registry_content]

    if missing_registry:
        raise RuntimeError("Marcadores ausentes em v2_registry.py: " + ", ".join(missing_registry))

    required_repository = [
        "def format_entity_created_at_v2",
        '"city": entity.city or ""',
        '"created_at_display": format_entity_created_at_v2(entity.created_at)',
    ]

    missing_repository = [marker for marker in required_repository if marker not in repository_content]

    if missing_repository:
        raise RuntimeError("Marcadores ausentes em v2_entity_repository.py: " + ", ".join(missing_repository))

    print("OK: coluna Cidade adicionada ao layout V2.")
    print("OK: coluna Criado em adicionada ao layout V2.")
    print("OK: repository fornece created_at_display.")


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(REGISTRY_PATH)
    require_file_v1(REPOSITORY_PATH)

    registry_backup = backup_file_v1(REGISTRY_PATH, "entidade_v2_colunas_cidade_criado_em_v1")
    repository_backup = backup_file_v1(REPOSITORY_PATH, "entidade_v2_colunas_cidade_criado_em_v1")

    print(f"OK: backup criado: {registry_backup}")
    print(f"OK: backup criado: {repository_backup}")

    patch_repository_v1()
    patch_registry_v1()
    validate_v1()

    print("OK: patch colunas Entidade V2 concluido.")


if __name__ == "__main__":
    main()
