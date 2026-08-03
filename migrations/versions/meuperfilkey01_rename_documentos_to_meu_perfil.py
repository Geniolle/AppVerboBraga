from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "meuperfilkey01"
down_revision = "membercountry01"
branch_labels = None
depends_on = None


CANONICAL_KEY = "meu_perfil"
LEGACY_KEY = "documentos"


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def _rename_sidebar_menu_settings(bind: sa.Connection, source_key: str, target_key: str) -> None:
    if not _has_table("sidebar_menu_settings"):
        return

    bind.execute(
        sa.text(
            """
            UPDATE sidebar_menu_settings
            SET menu_key = :target_key,
                menu_label = 'Meu perfil'
            WHERE lower(trim(menu_key)) = :source_key
              AND NOT EXISTS (
                  SELECT 1
                  FROM sidebar_menu_settings
                  WHERE lower(trim(menu_key)) = :target_key
              )
            """
        ),
        {"source_key": source_key, "target_key": target_key},
    )
    bind.execute(
        sa.text(
            """
            UPDATE sidebar_menu_settings AS target
            SET menu_label = 'Meu perfil',
                is_active = source.is_active,
                is_deleted = source.is_deleted,
                menu_config = COALESCE(NULLIF(source.menu_config, ''), target.menu_config)
            FROM sidebar_menu_settings AS source
            WHERE lower(trim(target.menu_key)) = :target_key
              AND lower(trim(source.menu_key)) = :source_key
            """
        ),
        {"source_key": source_key, "target_key": target_key},
    )
    bind.execute(
        sa.text(
            """
            DELETE FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :source_key
            """
        ),
        {"source_key": source_key},
    )


def _ensure_target_app_module(bind: sa.Connection, source_key: str, target_key: str) -> None:
    if not _has_table("app_modules"):
        return

    bind.execute(
        sa.text(
            """
            INSERT INTO app_modules (
                module_key,
                module_name,
                description,
                menu_group,
                icon,
                display_order,
                is_core,
                is_active,
                created_at,
                updated_at
            )
            SELECT
                :target_key,
                module_name,
                description,
                menu_group,
                icon,
                display_order,
                is_core,
                is_active,
                created_at,
                updated_at
            FROM app_modules
            WHERE lower(trim(module_key)) = :source_key
            ON CONFLICT (module_key) DO NOTHING
            """
        ),
        {"source_key": source_key, "target_key": target_key},
    )
    bind.execute(
        sa.text(
            """
            UPDATE app_modules
            SET module_name = 'Meu perfil',
                menu_group = 'igreja',
                icon = '[D]'
            WHERE lower(trim(module_key)) = :target_key
            """
        ),
        {"target_key": target_key},
    )


def _rename_sidebar_menu_items(bind: sa.Connection, source_key: str, target_key: str) -> None:
    if not _has_table("sidebar_menu_items"):
        return

    bind.execute(
        sa.text(
            """
            DELETE FROM sidebar_menu_items AS source
            USING sidebar_menu_items AS target
            WHERE lower(trim(source.module_key)) = :source_key
              AND lower(trim(target.module_key)) = :target_key
              AND source.item_key = target.item_key
            """
        ),
        {"source_key": source_key, "target_key": target_key},
    )
    bind.execute(
        sa.text(
            """
            UPDATE sidebar_menu_items
            SET module_key = :target_key
            WHERE lower(trim(module_key)) = :source_key
            """
        ),
        {"source_key": source_key, "target_key": target_key},
    )
    bind.execute(
        sa.text(
            """
            UPDATE sidebar_menu_items
            SET route_path = replace(route_path, :source_query, :target_query)
            WHERE route_path LIKE :source_like
            """
        ),
        {
            "source_query": f"menu={source_key}",
            "target_query": f"menu={target_key}",
            "source_like": f"%menu={source_key}%",
        },
    )
    bind.execute(
        sa.text(
            """
            UPDATE sidebar_menu_items
            SET item_key = 'meu_perfil',
                label = 'Meu perfil',
                route_path = :route_path,
                icon = '[D]'
            WHERE lower(trim(module_key)) = :target_key
              AND item_key = 'meu_perfil'
            """
        ),
        {"target_key": target_key, "route_path": f"/users/new?menu={target_key}"},
    )


def _rename_entity_module_entitlements(bind: sa.Connection, source_key: str, target_key: str) -> None:
    if not _has_table("entity_module_entitlements"):
        return

    bind.execute(
        sa.text(
            """
            DELETE FROM entity_module_entitlements AS source
            USING entity_module_entitlements AS target
            WHERE lower(trim(source.module_key)) = :source_key
              AND lower(trim(target.module_key)) = :target_key
              AND source.entity_id = target.entity_id
            """
        ),
        {"source_key": source_key, "target_key": target_key},
    )
    bind.execute(
        sa.text(
            """
            UPDATE entity_module_entitlements
            SET module_key = :target_key
            WHERE lower(trim(module_key)) = :source_key
            """
        ),
        {"source_key": source_key, "target_key": target_key},
    )


def _delete_source_app_module(bind: sa.Connection, source_key: str) -> None:
    if not _has_table("app_modules"):
        return

    bind.execute(
        sa.text(
            """
            DELETE FROM app_modules
            WHERE lower(trim(module_key)) = :source_key
            """
        ),
        {"source_key": source_key},
    )


def upgrade() -> None:
    bind = op.get_bind()
    _rename_sidebar_menu_settings(bind, LEGACY_KEY, CANONICAL_KEY)
    _ensure_target_app_module(bind, LEGACY_KEY, CANONICAL_KEY)
    _rename_sidebar_menu_items(bind, LEGACY_KEY, CANONICAL_KEY)
    _rename_entity_module_entitlements(bind, LEGACY_KEY, CANONICAL_KEY)
    _delete_source_app_module(bind, LEGACY_KEY)


def downgrade() -> None:
    bind = op.get_bind()
    _rename_sidebar_menu_settings(bind, CANONICAL_KEY, LEGACY_KEY)
    _ensure_target_app_module(bind, CANONICAL_KEY, LEGACY_KEY)
    _rename_sidebar_menu_items(bind, CANONICAL_KEY, LEGACY_KEY)
    _rename_entity_module_entitlements(bind, CANONICAL_KEY, LEGACY_KEY)
    _delete_source_app_module(bind, CANONICAL_KEY)
