from __future__ import annotations

from appverbo.admin_subprocesses.contas.config import CONTAS_CONFIG
from appverbo.admin_subprocesses.entidade.config import ENTIDADE_CONFIG
from appverbo.admin_subprocesses.menu.config import MENU_CONFIG
from appverbo.admin_subprocesses.models import AdminSubprocessConfig
from appverbo.admin_subprocesses.sessoes import SESSOES_CONFIG
from appverbo.admin_subprocesses.utilizador.config import UTILIZADOR_CONFIG


# ###################################################################################
# (1) REGISTO CENTRAL DOS SUBPROCESSOS ADMINISTRATIVOS
# ###################################################################################

ADMIN_SUBPROCESS_REGISTRY: dict[str, AdminSubprocessConfig] = {
    ENTIDADE_CONFIG.key: ENTIDADE_CONFIG,
    SESSOES_CONFIG.key: SESSOES_CONFIG,
    UTILIZADOR_CONFIG.key: UTILIZADOR_CONFIG,
    MENU_CONFIG.key: MENU_CONFIG,
    CONTAS_CONFIG.key: CONTAS_CONFIG,
}


# ###################################################################################
# (2) CONSULTA DE CONFIGURACOES
# ###################################################################################

def get_admin_subprocess_config(key: str) -> AdminSubprocessConfig | None:
    return ADMIN_SUBPROCESS_REGISTRY.get(str(key or "").strip().lower())


def require_admin_subprocess_config(key: str) -> AdminSubprocessConfig:
    config = get_admin_subprocess_config(key)

    if config is None:
        raise KeyError(f"Subprocesso administrativo n\u00e3o configurado: {key}")

    return config


def list_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(ADMIN_SUBPROCESS_REGISTRY.values())


def list_enabled_admin_subprocess_configs() -> tuple[AdminSubprocessConfig, ...]:
    return tuple(
        config
        for config in ADMIN_SUBPROCESS_REGISTRY.values()
        if config.enabled
    )
