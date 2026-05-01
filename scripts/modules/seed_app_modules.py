from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from appverbo.db.session import SessionLocal
from appverbo.models import Entity
from appverbo.models.modules import (
    AppModule,
    EntityModuleEntitlement,
    SidebarMenuItem,
)


# ###################################################################################
# (1) DEFINICAO DOS MODULOS DO SISTEMA
# ###################################################################################

MODULES: list[dict[str, Any]] = [
    {
        "module_key": "home",
        "module_name": "Home",
        "description": "Resumo geral do sistema.",
        "menu_group": "geral",
        "icon": "[H]",
        "display_order": 10,
        "is_core": True,
        "is_active": True,
    },
    {
        "module_key": "administrativo",
        "module_name": "Administrativo",
        "description": "Gestao administrativa do sistema.",
        "menu_group": "geral",
        "icon": "[*]",
        "display_order": 20,
        "is_core": True,
        "is_active": True,
    },
    {
        "module_key": "meu_perfil",
        "module_name": "Meu perfil",
        "description": "Area de perfil e dados pessoais do utilizador.",
        "menu_group": "igreja",
        "icon": "[D]",
        "display_order": 100,
        "is_core": True,
        "is_active": True,
    },
    {
        "module_key": "funcionarios",
        "module_name": "Funcionarios",
        "description": "Gestao de funcionarios, colaboradores e acessos.",
        "menu_group": "igreja",
        "icon": "[F]",
        "display_order": 110,
        "is_core": True,
        "is_active": True,
    },
    {
        "module_key": "financeiro",
        "module_name": "Financeiro",
        "description": "Area financeira base existente no sistema.",
        "menu_group": "igreja",
        "icon": "[$]",
        "display_order": 120,
        "is_core": True,
        "is_active": True,
    },
    {
        "module_key": "relatorios",
        "module_name": "Relatorios",
        "description": "Relatorios gerais do sistema.",
        "menu_group": "igreja",
        "icon": "[R]",
        "display_order": 130,
        "is_core": True,
        "is_active": True,
    },
    {
        "module_key": "links",
        "module_name": "Links",
        "description": "Links e atalhos internos.",
        "menu_group": "igreja",
        "icon": "[L]",
        "display_order": 140,
        "is_core": True,
        "is_active": True,
    },
    {
        "module_key": "contato",
        "module_name": "Contacto",
        "description": "Informacoes de contacto.",
        "menu_group": "igreja",
        "icon": "[C]",
        "display_order": 150,
        "is_core": True,
        "is_active": True,
    },
    {
        "module_key": "tutorial",
        "module_name": "Tutorial",
        "description": "Guia rapido de utilizacao.",
        "menu_group": "igreja",
        "icon": "[T]",
        "display_order": 160,
        "is_core": True,
        "is_active": True,
    },
    {
        "module_key": "tesouraria",
        "module_name": "Tesouraria",
        "description": "Modulo pago para importacao de extrato bancario, movimentos, conciliacao e relatorios financeiros.",
        "menu_group": "tesouraria",
        "icon": "[T]",
        "display_order": 300,
        "is_core": False,
        "is_active": True,
    },
]


# ###################################################################################
# (2) DEFINICAO DOS ITENS DO MENU LATERAL
# ###################################################################################

SIDEBAR_ITEMS: list[dict[str, Any]] = [
    {
        "module_key": "home",
        "group_key": "geral",
        "item_key": "home",
        "label": "Home",
        "route_path": "/users/new?menu=home",
        "icon": "[H]",
        "display_order": 10,
        "requires_admin": False,
        "is_active": True,
    },
    {
        "module_key": "administrativo",
        "group_key": "geral",
        "item_key": "administrativo",
        "label": "Administrativo",
        "route_path": "/users/new?menu=administrativo",
        "icon": "[*]",
        "display_order": 20,
        "requires_admin": True,
        "is_active": True,
    },
    {
        "module_key": "meu_perfil",
        "group_key": "igreja",
        "item_key": "meu_perfil",
        "label": "Meu perfil",
        "route_path": "/users/new?menu=meu_perfil",
        "icon": "[D]",
        "display_order": 100,
        "requires_admin": False,
        "is_active": True,
    },
    {
        "module_key": "funcionarios",
        "group_key": "igreja",
        "item_key": "funcionarios",
        "label": "Funcionarios",
        "route_path": "/users/new?menu=funcionarios",
        "icon": "[F]",
        "display_order": 110,
        "requires_admin": True,
        "is_active": True,
    },
    {
        "module_key": "financeiro",
        "group_key": "igreja",
        "item_key": "financeiro",
        "label": "Financeiro",
        "route_path": "/users/new?menu=financeiro",
        "icon": "[$]",
        "display_order": 120,
        "requires_admin": True,
        "is_active": True,
    },
    {
        "module_key": "relatorios",
        "group_key": "igreja",
        "item_key": "relatorios",
        "label": "Relatorios",
        "route_path": "/users/new?menu=relatorios",
        "icon": "[R]",
        "display_order": 130,
        "requires_admin": True,
        "is_active": True,
    },
    {
        "module_key": "links",
        "group_key": "igreja",
        "item_key": "links",
        "label": "Links",
        "route_path": "/users/new?menu=links",
        "icon": "[L]",
        "display_order": 140,
        "requires_admin": False,
        "is_active": True,
    },
    {
        "module_key": "contato",
        "group_key": "igreja",
        "item_key": "contato",
        "label": "Contacto",
        "route_path": "/users/new?menu=contato",
        "icon": "[C]",
        "display_order": 150,
        "requires_admin": False,
        "is_active": True,
    },
    {
        "module_key": "tutorial",
        "group_key": "igreja",
        "item_key": "tutorial",
        "label": "Tutorial",
        "route_path": "/users/new?menu=tutorial",
        "icon": "[T]",
        "display_order": 160,
        "requires_admin": False,
        "is_active": True,
    },
    {
        "module_key": "tesouraria",
        "group_key": "tesouraria",
        "item_key": "tesouraria_dashboard",
        "label": "Dashboard",
        "route_path": "/tesouraria",
        "icon": "[T]",
        "display_order": 300,
        "requires_admin": True,
        "is_active": True,
    },
    {
        "module_key": "tesouraria",
        "group_key": "tesouraria",
        "item_key": "tesouraria_importar_extrato",
        "label": "Importar extrato",
        "route_path": "/tesouraria/extratos/importar",
        "icon": "[I]",
        "display_order": 310,
        "requires_admin": True,
        "is_active": True,
    },
    {
        "module_key": "tesouraria",
        "group_key": "tesouraria",
        "item_key": "tesouraria_movimentos",
        "label": "Movimentos",
        "route_path": "/tesouraria/movimentos",
        "icon": "[M]",
        "display_order": 320,
        "requires_admin": True,
        "is_active": True,
    },
    {
        "module_key": "tesouraria",
        "group_key": "tesouraria",
        "item_key": "tesouraria_relatorios",
        "label": "Relatorios",
        "route_path": "/tesouraria/relatorios",
        "icon": "[R]",
        "display_order": 330,
        "requires_admin": True,
        "is_active": True,
    },
]


# ###################################################################################
# (3) UPSERT DOS MODULOS
# ###################################################################################

def upsert_modules(session) -> dict[str, int]:
    inserted = 0
    updated = 0

    for item in MODULES:
        module = session.execute(
            select(AppModule).where(AppModule.module_key == item["module_key"])
        ).scalar_one_or_none()

        if module is None:
            module = AppModule(**item)
            session.add(module)
            inserted += 1
            continue

        module.module_name = item["module_name"]
        module.description = item["description"]
        module.menu_group = item["menu_group"]
        module.icon = item["icon"]
        module.display_order = item["display_order"]
        module.is_core = item["is_core"]
        module.is_active = item["is_active"]
        updated += 1

    return {"inserted": inserted, "updated": updated}


# ###################################################################################
# (4) UPSERT DOS ITENS DO MENU
# ###################################################################################

def upsert_sidebar_items(session) -> dict[str, int]:
    inserted = 0
    updated = 0

    for item in SIDEBAR_ITEMS:
        sidebar_item = session.execute(
            select(SidebarMenuItem).where(
                SidebarMenuItem.module_key == item["module_key"],
                SidebarMenuItem.item_key == item["item_key"],
            )
        ).scalar_one_or_none()

        if sidebar_item is None:
            sidebar_item = SidebarMenuItem(**item)
            session.add(sidebar_item)
            inserted += 1
            continue

        sidebar_item.group_key = item["group_key"]
        sidebar_item.label = item["label"]
        sidebar_item.route_path = item["route_path"]
        sidebar_item.icon = item["icon"]
        sidebar_item.display_order = item["display_order"]
        sidebar_item.requires_admin = item["requires_admin"]
        sidebar_item.is_active = item["is_active"]
        updated += 1

    return {"inserted": inserted, "updated": updated}


# ###################################################################################
# (5) CRIAR ENTITLEMENTS POR ENTIDADE
# ###################################################################################

def seed_entity_entitlements(session) -> dict[str, int]:
    inserted = 0
    updated = 0

    entity_ids = [
        int(entity_id)
        for entity_id in session.execute(select(Entity.id)).scalars().all()
    ]

    if not entity_ids:
        return {"inserted": inserted, "updated": updated}

    for entity_id in entity_ids:
        for module_item in MODULES:
            module_key = module_item["module_key"]
            is_core = bool(module_item["is_core"])

            entitlement = session.execute(
                select(EntityModuleEntitlement).where(
                    EntityModuleEntitlement.entity_id == entity_id,
                    EntityModuleEntitlement.module_key == module_key,
                )
            ).scalar_one_or_none()

            desired_status = "active" if is_core else "inactive"

            if entitlement is None:
                entitlement = EntityModuleEntitlement(
                    entity_id=entity_id,
                    module_key=module_key,
                    status=desired_status,
                    starts_at=datetime.now(timezone.utc) if is_core else None,
                    expires_at=None,
                    enabled_by_user_id=None,
                )
                session.add(entitlement)
                inserted += 1
                continue

            if module_key != "tesouraria":
                entitlement.status = desired_status
                if is_core and entitlement.starts_at is None:
                    entitlement.starts_at = datetime.now(timezone.utc)
                updated += 1

    return {"inserted": inserted, "updated": updated}


# ###################################################################################
# (6) EXECUCAO PRINCIPAL
# ###################################################################################

def main() -> int:
    with SessionLocal() as session:
        module_result = upsert_modules(session)
        session.flush()

        sidebar_result = upsert_sidebar_items(session)
        session.flush()

        entitlement_result = seed_entity_entitlements(session)

        session.commit()

        total_modules = session.execute(select(AppModule)).scalars().all()
        total_sidebar_items = session.execute(select(SidebarMenuItem)).scalars().all()
        total_entitlements = session.execute(select(EntityModuleEntitlement)).scalars().all()

    print("")
    print("==== SEED APP MODULES ====")
    print(f"Modulos inseridos: {module_result['inserted']}")
    print(f"Modulos atualizados: {module_result['updated']}")
    print("")
    print("==== SEED SIDEBAR MENU ITEMS ====")
    print(f"Itens inseridos: {sidebar_result['inserted']}")
    print(f"Itens atualizados: {sidebar_result['updated']}")
    print("")
    print("==== SEED ENTITY MODULE ENTITLEMENTS ====")
    print(f"Entitlements inseridos: {entitlement_result['inserted']}")
    print(f"Entitlements atualizados: {entitlement_result['updated']}")
    print("")
    print("==== TOTAIS ====")
    print(f"Total app_modules: {len(total_modules)}")
    print(f"Total sidebar_menu_items: {len(total_sidebar_items)}")
    print(f"Total entity_module_entitlements: {len(total_entitlements)}")
    print("")
    print("SEED CONCLUIDO COM SUCESSO.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

