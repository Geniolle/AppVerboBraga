from __future__ import annotations

from typing import Any


####################################################################################
# (1) CONSTANTES CANÓNICAS DE STATUS DE UTILIZADOR
####################################################################################

USER_ACCOUNT_STATUS_ACTIVE_V1 = "active"
USER_ACCOUNT_STATUS_PENDING_V1 = "pending"
USER_ACCOUNT_STATUS_INACTIVE_V1 = "inactive"
USER_ACCOUNT_STATUS_BLOCKED_V1 = "blocked"


####################################################################################
# (2) NORMALIZAÇÃO E LABELS DE STATUS
####################################################################################

def normalize_user_account_status_v1(raw_status: Any) -> str:
    value = str(raw_status or "").strip().lower()

    status_aliases = {
        "ativo": USER_ACCOUNT_STATUS_ACTIVE_V1,
        "activa": USER_ACCOUNT_STATUS_ACTIVE_V1,
        "ativa": USER_ACCOUNT_STATUS_ACTIVE_V1,
        "inativo": USER_ACCOUNT_STATUS_INACTIVE_V1,
        "inactiva": USER_ACCOUNT_STATUS_INACTIVE_V1,
        "inativa": USER_ACCOUNT_STATUS_INACTIVE_V1,
        "pendente": USER_ACCOUNT_STATUS_PENDING_V1,
        "bloqueado": USER_ACCOUNT_STATUS_BLOCKED_V1,
        "bloqueada": USER_ACCOUNT_STATUS_BLOCKED_V1,
    }

    return status_aliases.get(value, value)


def user_account_status_label_pt_v1(raw_status: Any) -> str:
    normalized_status = normalize_user_account_status_v1(raw_status)

    status_label_map = {
        USER_ACCOUNT_STATUS_ACTIVE_V1: "Ativo",
        USER_ACCOUNT_STATUS_PENDING_V1: "Pendente",
        USER_ACCOUNT_STATUS_INACTIVE_V1: "Inativo",
        USER_ACCOUNT_STATUS_BLOCKED_V1: "Bloqueado",
    }

    return status_label_map.get(normalized_status, normalized_status or "-")


####################################################################################
# (3) PREDICADOS REUTILIZÁVEIS
####################################################################################

def is_user_account_status_active_v1(raw_status: Any) -> bool:
    return normalize_user_account_status_v1(raw_status) == USER_ACCOUNT_STATUS_ACTIVE_V1


def is_user_account_status_pending_v1(raw_status: Any) -> bool:
    return normalize_user_account_status_v1(raw_status) == USER_ACCOUNT_STATUS_PENDING_V1


def is_user_account_status_inactive_v1(raw_status: Any) -> bool:
    return normalize_user_account_status_v1(raw_status) == USER_ACCOUNT_STATUS_INACTIVE_V1


def is_user_account_status_blocked_v1(raw_status: Any) -> bool:
    return normalize_user_account_status_v1(raw_status) == USER_ACCOUNT_STATUS_BLOCKED_V1


def is_user_account_status_non_active_v1(raw_status: Any) -> bool:
    normalized_status = normalize_user_account_status_v1(raw_status)

    return normalized_status in {
        USER_ACCOUNT_STATUS_INACTIVE_V1,
        USER_ACCOUNT_STATUS_PENDING_V1,
        USER_ACCOUNT_STATUS_BLOCKED_V1,
    }
