from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ###################################################################################
# (1) ESTADO DEDICADO DO SUBPROCESSO MENU
# ###################################################################################


@dataclass
class AdminMenuState:
    active_rows: list[dict[str, Any]] = field(default_factory=list)
    inactive_rows: list[dict[str, Any]] = field(default_factory=list)
    section_options: tuple[tuple[str, str], ...] = ()
    can_manage_all_entities: bool = False
    success: str = ""
    error: str = ""
    return_url: str = "/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card"
    create_target: str = "admin-menu-card-create"
    active_target: str = "admin-menu-card"
    inactive_target: str = "admin-menu-card-inactive"
    edit_target: str = "settings-menu-edit-card"
    create_title: str = "Criar menu"
    active_title: str = "Menus ativos"
    inactive_title: str = "Menus inativos"
