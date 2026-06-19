"""rename entity internal number to entity number

Revision ID: entitynum01
Revises: memberuser03
Create Date: 2026-06-19 18:55:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "entitynum01"
down_revision: Union[str, Sequence[str], None] = "memberuser03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ###################################################################################
# (1) HELPERS
# ###################################################################################


def _get_inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    inspector = _get_inspector()
    return table_name in set(inspector.get_table_names())


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = _get_inspector()
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = _get_inspector()
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _has_unique_constraint(table_name: str, constraint_name: str) -> bool:
    inspector = _get_inspector()
    return constraint_name in {
        constraint.get("name")
        for constraint in inspector.get_unique_constraints(table_name)
        if constraint.get("name")
    }


def _drop_index_if_exists(table_name: str, index_name: str) -> None:
    if _has_index(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def _drop_unique_constraints_for_columns(
    table_name: str,
    *,
    allowed_names: set[str],
    target_columns: set[tuple[str, ...]],
) -> None:
    bind = op.get_bind()
    inspector = _get_inspector()
    constraint_names = [
        constraint_name
        for constraint in inspector.get_unique_constraints(table_name)
        for constraint_name in [constraint.get("name")]
        if constraint_name
        and tuple(constraint.get("column_names") or []) in target_columns
        and constraint_name not in allowed_names
    ]

    if not constraint_names:
        return

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table_name, recreate="always") as batch_op:
            for constraint_name in constraint_names:
                batch_op.drop_constraint(constraint_name, type_="unique")
        return

    for constraint_name in constraint_names:
        op.drop_constraint(constraint_name, table_name, type_="unique")


def _rename_column(table_name: str, *, old_name: str, new_name: str) -> None:
    bind = op.get_bind()

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table_name, recreate="always") as batch_op:
            batch_op.alter_column(
                old_name,
                new_column_name=new_name,
                existing_type=sa.Integer(),
                existing_nullable=True,
            )
        return

    op.alter_column(
        table_name,
        old_name,
        new_column_name=new_name,
        existing_type=sa.Integer(),
        existing_nullable=True,
    )


def _drop_column(table_name: str, *, column_name: str) -> None:
    bind = op.get_bind()

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table_name, recreate="always") as batch_op:
            batch_op.drop_column(column_name)
        return

    op.drop_column(table_name, column_name)


def _create_unique_constraint(table_name: str, *, constraint_name: str, column_name: str) -> None:
    bind = op.get_bind()

    if _has_unique_constraint(table_name, constraint_name):
        return

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table_name, recreate="always") as batch_op:
            batch_op.create_unique_constraint(constraint_name, [column_name])
        return

    op.create_unique_constraint(constraint_name, table_name, [column_name])


# ###################################################################################
# (2) UPGRADE
# ###################################################################################


def upgrade() -> None:
    if not _has_table("entities"):
        return

    bind = op.get_bind()

    has_internal_number = _has_column("entities", "internal_number")
    has_entity_number = _has_column("entities", "entity_number")

    if not has_entity_number and has_internal_number:
        _rename_column("entities", old_name="internal_number", new_name="entity_number")
        has_internal_number = _has_column("entities", "internal_number")
        has_entity_number = _has_column("entities", "entity_number")
    elif not has_entity_number and not has_internal_number:
        op.add_column("entities", sa.Column("entity_number", sa.Integer(), nullable=True))
        has_entity_number = True

    if has_entity_number and has_internal_number:
        bind.execute(
            text(
                """
                UPDATE entities
                SET entity_number = internal_number
                WHERE entity_number IS NULL
                  AND internal_number IS NOT NULL
                """
            )
        )

    _drop_index_if_exists("entities", "uq_entities_internal_number")
    _drop_index_if_exists("entities", "uq_entities_entity_number")
    _drop_unique_constraints_for_columns(
        "entities",
        allowed_names={"uq_entities_entity_number"},
        target_columns={("internal_number",), ("entity_number",)},
    )

    has_internal_number = _has_column("entities", "internal_number")
    has_entity_number = _has_column("entities", "entity_number")
    if has_internal_number and has_entity_number:
        _drop_column("entities", column_name="internal_number")

    _create_unique_constraint(
        "entities",
        constraint_name="uq_entities_entity_number",
        column_name="entity_number",
    )


# ###################################################################################
# (3) DOWNGRADE
# ###################################################################################


def downgrade() -> None:
    if not _has_table("entities"):
        return

    bind = op.get_bind()

    has_internal_number = _has_column("entities", "internal_number")
    has_entity_number = _has_column("entities", "entity_number")

    if not has_internal_number and has_entity_number:
        _rename_column("entities", old_name="entity_number", new_name="internal_number")
        has_internal_number = _has_column("entities", "internal_number")
        has_entity_number = _has_column("entities", "entity_number")
    elif not has_internal_number and not has_entity_number:
        op.add_column("entities", sa.Column("internal_number", sa.Integer(), nullable=True))
        has_internal_number = True

    if has_internal_number and has_entity_number:
        bind.execute(
            text(
                """
                UPDATE entities
                SET internal_number = entity_number
                WHERE internal_number IS NULL
                  AND entity_number IS NOT NULL
                """
            )
        )

    _drop_index_if_exists("entities", "uq_entities_entity_number")
    _drop_index_if_exists("entities", "uq_entities_internal_number")
    _drop_unique_constraints_for_columns(
        "entities",
        allowed_names={"uq_entities_internal_number"},
        target_columns={("internal_number",), ("entity_number",)},
    )

    has_internal_number = _has_column("entities", "internal_number")
    has_entity_number = _has_column("entities", "entity_number")
    if has_internal_number and has_entity_number:
        _drop_column("entities", column_name="entity_number")

    _create_unique_constraint(
        "entities",
        constraint_name="uq_entities_internal_number",
        column_name="internal_number",
    )
