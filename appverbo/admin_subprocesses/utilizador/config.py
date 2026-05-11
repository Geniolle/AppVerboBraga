from __future__ import annotations

from appverbo.admin_subprocesses.models import AdminSubprocessConfig


# ###################################################################################
# (1) CONFIGURACAO DO SUBPROCESSO UTILIZADOR
# ###################################################################################

UTILIZADOR_CONFIG = AdminSubprocessConfig(
    key="utilizador",
    label="Utilizador",
    singular_label="Utilizador",
    plural_label="Utilizadores",
    edit_param="user_edit_id",
    default_target="create-user-card",
    edit_target="edit-user-card",
    create_title="Criar utilizador",
    edit_title="Editar utilizador",
    active_title="Utilizadores ativos",
    inactive_title="Utilizadores inativos",
    create_endpoint="/users/new",
    update_endpoint="/users/update",
    save_endpoint="/users/update",
    repository_name="user",
    repository_class="",
    enabled=False,
    migration_status="legacy_pending",
)