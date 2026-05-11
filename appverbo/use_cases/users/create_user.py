from __future__ import annotations

from appverbo.admin_subprocesses.utilizador.create_service import (
    CreateUserInput,
    CreateUserOutcome,
    execute_create_user,
    normalize_create_user_input,
    normalize_create_user_input_v1,
)


# ###################################################################################
# (1) COMPATIBILIDADE COM IMPORTS ANTIGOS
# ###################################################################################

__all__ = [
    "CreateUserInput",
    "CreateUserOutcome",
    "execute_create_user",
    "normalize_create_user_input",
    "normalize_create_user_input_v1",
]