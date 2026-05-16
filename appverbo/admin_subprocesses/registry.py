from __future__ import annotations

from .entidade.configuracao import ENTIDADE_CONFIG
from .menu.configuracao import MENU_CONFIG
from .models import AdminSubprocessConfig
from .sessoes.configuracao import SESSOES_CONFIG
from .utilizador.configuracao import UTILIZADOR_CONFIG


####################################################################################
# (1) CONFIGURACAO - UTILIZADOR
####################################################################################

# UTILIZADOR_CONFIG e definido em appverbo/admin_subprocesses/utilizador/configuracao.py


####################################################################################
# (2) CONFIGURACAO - MENU
####################################################################################

# MENU_CONFIG e definido em appverbo/admin_subprocesses/menu/configuracao.py


####################################################################################
# (3) CONFIGURACAO - CONTAS
####################################################################################

CONTAS_CONFIG = AdminSubprocessConfig(
    key="contas",
    label="Contas",
    singular_label="Conta",
    plural_label="Contas",
    edit_param="account_edit_id",
    default_target="admin-account-status-card",
    edit_target="admin-account-status-card",
    create_title="Criar conta",
    edit_title="Editar conta",
    active_title="Contas ativas",
    inactive_title="Contas inativas",
    save_endpoint="",
    repository_name="account",
    repository_class="",
    enabled=False,
    migration_status="legacy_pending",
)


####################################################################################
# (4) REGISTRY UNICO
####################################################################################

ADMIN_SUBPROCESS_REGISTRY = {
    ENTIDADE_CONFIG.key: ENTIDADE_CONFIG,
    SESSOES_CONFIG.key: SESSOES_CONFIG,
    UTILIZADOR_CONFIG.key: UTILIZADOR_CONFIG,
    MENU_CONFIG.key: MENU_CONFIG,
    CONTAS_CONFIG.key: CONTAS_CONFIG,
}


def get_admin_subprocess_config(key: str) -> AdminSubprocessConfig | None:
    return ADMIN_SUBPROCESS_REGISTRY.get(str(key or "").strip().lower())


def require_admin_subprocess_config(key: str) -> AdminSubprocessConfig:
    config = get_admin_subprocess_config(key)

    if config is None:
        raise KeyError(f"Subprocesso administrativo não configurado: {key}")

    return config


def list_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(ADMIN_SUBPROCESS_REGISTRY.values())


def list_enabled_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(
        config
        for config in ADMIN_SUBPROCESS_REGISTRY.values()
        if config.enabled
    )
