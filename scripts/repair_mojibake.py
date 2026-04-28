from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import inspect, text

from appverbo.db.session import SessionLocal, engine


# ###################################################################################
# (1) CONFIGURACAO
# ###################################################################################

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FILE_ROOTS = [
    PROJECT_ROOT / "templates",
    PROJECT_ROOT / "appverbo",
    PROJECT_ROOT / "static",
]

FILE_EXTENSIONS = {
    ".py",
    ".html",
    ".js",
    ".css",
}

DB_TARGETS = {
    "sidebar_menu_settings": ["menu_label", "menu_config"],
    "app_modules": ["module_name", "description", "menu_group", "icon"],
    "sidebar_menu_items": ["group_key", "item_key", "label", "icon"],
}

MOJIBAKE_MARKERS = ("Ã", "Â", "�")

MOJIBAKE_CHUNK_RE = re.compile(
    r"(?:[\u00c2\u00c3][\u0080-\u00bf\u00a0-\u00ff\u0100-\u017f\u2010-\u202f])+"
)

DIRECT_REPLACEMENTS = {
    "\u00ef\u00bb\u00bf": "",
}


# ###################################################################################
# (2) FUNCOES DE CORRECAO
# ###################################################################################

def has_mojibake(value: str) -> bool:
    return any(marker in value for marker in MOJIBAKE_MARKERS)


def decode_chunk(chunk: str) -> str:
    for encoding in ("cp1252", "latin1"):
        try:
            return chunk.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return chunk


def repair_text(value: str | None) -> str | None:
    if value is None:
        return None

    original_value = str(value)
    repaired_value = original_value

    for bad_value, good_value in DIRECT_REPLACEMENTS.items():
        repaired_value = repaired_value.replace(bad_value, good_value)

    if has_mojibake(repaired_value):
        repaired_value = MOJIBAKE_CHUNK_RE.sub(
            lambda match: decode_chunk(match.group(0)),
            repaired_value,
        )

    return repaired_value


def read_text_safe(path: Path) -> str | None:
    raw_content = path.read_bytes()

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return raw_content.decode(encoding)
        except UnicodeDecodeError:
            continue

    return None


def write_text_utf8(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


# ###################################################################################
# (3) CORRIGIR FICHEIROS
# ###################################################################################

def repair_files() -> list[str]:
    changed_files: list[str] = []

    for root in FILE_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() not in FILE_EXTENSIONS:
                continue

            content = read_text_safe(path)

            if content is None:
                continue

            repaired_content = repair_text(content)

            if repaired_content != content:
                write_text_utf8(path, repaired_content)
                changed_files.append(str(path.relative_to(PROJECT_ROOT)))

    return changed_files


# ###################################################################################
# (4) CORRIGIR BANCO DE DADOS
# ###################################################################################

def repair_database() -> list[str]:
    changed_rows: list[str] = []
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with SessionLocal() as session:
        for table_name, columns in DB_TARGETS.items():
            if table_name not in existing_tables:
                continue

            select_columns = ", ".join(["id", *columns])
            rows = session.execute(
                text(f"SELECT {select_columns} FROM {table_name} ORDER BY id")
            ).mappings().all()

            for row in rows:
                updates: dict[str, str] = {}

                for column_name in columns:
                    old_value = row.get(column_name)

                    if old_value is None:
                        continue

                    new_value = repair_text(str(old_value))

                    if new_value != old_value:
                        updates[column_name] = new_value

                if not updates:
                    continue

                set_clause = ", ".join(
                    [f"{column_name} = :{column_name}" for column_name in updates]
                )

                params = dict(updates)
                params["id"] = row["id"]

                session.execute(
                    text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id"),
                    params,
                )

                changed_rows.append(f"{table_name}[id={row['id']}]")

        session.commit()

    return changed_rows


# ###################################################################################
# (5) PROCURAR OCORRENCIAS RESTANTES
# ###################################################################################

def find_remaining_mojibake() -> list[str]:
    hits: list[str] = []

    for root in FILE_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() not in FILE_EXTENSIONS:
                continue

            content = read_text_safe(path)

            if not content:
                continue

            if has_mojibake(content):
                hits.append(str(path.relative_to(PROJECT_ROOT)))

    return hits


# ###################################################################################
# (6) EXECUCAO PRINCIPAL
# ###################################################################################

def main() -> int:
    changed_files = repair_files()
    changed_rows = repair_database()
    remaining_hits = find_remaining_mojibake()

    print("")
    print("==== FICHEIROS CORRIGIDOS ====")

    if changed_files:
        for file_name in changed_files:
            print(f"- {file_name}")
    else:
        print("Nenhum ficheiro precisou de correcao.")

    print("")
    print("==== REGISTOS DO BANCO CORRIGIDOS ====")

    if changed_rows:
        for row_name in changed_rows:
            print(f"- {row_name}")
    else:
        print("Nenhum registo do banco precisou de correcao.")

    print("")
    print("==== OCORRENCIAS RESTANTES COM MARCADORES ====")

    if remaining_hits:
        print("Ainda existem marcadores em ficheiros. Verificar se sao exemplos intencionais ou codigo de tratamento:")
        for file_name in remaining_hits[:30]:
            print(f"- {file_name}")
    else:
        print("Nenhuma ocorrencia restante encontrada nos ficheiros analisados.")

    print("")
    print("CORRECAO DE MOJIBAKE CONCLUIDA.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
