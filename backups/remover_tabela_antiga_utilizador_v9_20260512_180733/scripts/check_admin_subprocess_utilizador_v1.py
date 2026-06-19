from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from appverbo.admin_subprocesses.registry import require_admin_subprocess_config
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository
from appverbo.core import SessionLocal


####################################################################################
# (1) VALIDAR STATE NATIVO DO SUBPROCESSO UTILIZADOR
####################################################################################

def main() -> None:
    config = require_admin_subprocess_config("utilizador")

    if not config.enabled:
        raise RuntimeError("Subprocesso Utilizador não está ativo no registry.")

    if not config.repository_class:
        raise RuntimeError("Subprocesso Utilizador sem repository_class.")

    expected_columns = {
        "id",
        "full_name",
        "login_email",
        "primary_phone",
        "entity_name",
        "profile_name",
        "status_label",
        "created_at_label",
    }

    configured_sources = {
        str(column.source or "").strip()
        for column in config.columns
    }

    missing_config_sources = expected_columns - configured_sources

    if missing_config_sources:
        raise RuntimeError(
            "Colunas esperadas ausentes no registry do Utilizador: "
            + ", ".join(sorted(missing_config_sources))
        )

    with SessionLocal() as session:
        state = build_admin_subprocess_state_from_repository(
            config=config,
            session=session,
            edit_key="",
            success="",
            error="",
            return_url="/users/new?menu=administrativo&admin_tab=utilizador",
            context={},
        )

    if state is None:
        raise RuntimeError("Não foi possível construir o state do Utilizador.")

    all_rows = list(state.active_rows or []) + list(state.inactive_rows or [])

    if all_rows:
        missing_row_fields = expected_columns - set(all_rows[0].keys())

        if missing_row_fields:
            raise RuntimeError(
                "Campos esperados ausentes na primeira linha do Utilizador: "
                + ", ".join(sorted(missing_row_fields))
            )

    print("OK: state do subprocesso Utilizador criado.")
    print(f"Config: {state.config.key} - {state.config.label}")
    print(f"Colunas: {', '.join(column.label for column in state.config.columns)}")
    print(f"Ativos: {len(state.active_rows)}")
    print(f"Inativos/Pendentes/Bloqueados: {len(state.inactive_rows)}")


if __name__ == "__main__":
    main()
