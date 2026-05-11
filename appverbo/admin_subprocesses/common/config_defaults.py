from __future__ import annotations

from appverbo.admin_subprocesses.models import AdminActionConfig


# ###################################################################################
# (1) ACOES ADMINISTRATIVAS PADRAO
# ###################################################################################

DEFAULT_ADMIN_ACTIONS = (
    AdminActionConfig(
        key="move_up",
        label="Subir",
        icon="\u2191",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="move_down",
        label="Descer",
        icon="\u2193",
        action_type="post",
        visible_when=("ativo",),
    ),
    AdminActionConfig(
        key="view",
        label="Visualizar",
        icon="\U0001f441",
        action_type="button",
        visible_when=("ativo", "inativo"),
    ),
    AdminActionConfig(
        key="edit",
        label="Editar",
        icon="\u270e",
        action_type="link",
        visible_when=("ativo", "inativo"),
    ),
)


DEFAULT_ACTIVE_ACTIONS = DEFAULT_ADMIN_ACTIONS