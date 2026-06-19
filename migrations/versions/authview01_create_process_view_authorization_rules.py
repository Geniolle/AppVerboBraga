from __future__ import annotations

import json
from datetime import datetime, timezone
import unicodedata

from alembic import op
import sqlalchemy as sa


revision = "authview01"
down_revision = "songs01"
branch_labels = None
depends_on = None


# ###################################################################################
# (1) HELPERS
# ###################################################################################


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _normalize_lookup_text(raw_value: object) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(raw_value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    return " ".join(normalized.split())


def _normalize_rule_status(raw_value: object) -> str:
    clean_value = _normalize_lookup_text(raw_value)
    if clean_value in {"inactive", "inativo"}:
        return "inactive"
    return "active"


def _parse_created_at(raw_value: object) -> datetime:
    clean_value = str(raw_value or "").strip()
    if not clean_value:
        return datetime.now(timezone.utc)

    for fmt in ("%Y-%m-%d %H:%M UTC", "%Y-%m-%d %H:%M:%S UTC"):
        try:
            return datetime.strptime(clean_value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return datetime.now(timezone.utc)


def _backfill_legacy_rules() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {
        column["name"]
        for column in inspector.get_columns("members")
    }
    if "profile_custom_fields" not in column_names:
        return

    total_rows = bind.execute(
        sa.text("SELECT count(*) FROM process_view_authorization_rules")
    ).scalar_one()
    if int(total_rows or 0) > 0:
        return

    users_by_member_id = {
        int(row.member_id): int(row.user_id)
        for row in bind.execute(
            sa.text(
                """
                SELECT id AS user_id, member_id
                FROM users
                WHERE member_id IS NOT NULL
                """
            )
        ).fetchall()
        if row.member_id is not None
    }

    legacy_rows = bind.execute(
        sa.text(
            """
            SELECT id, profile_custom_fields
            FROM members
            WHERE coalesce(profile_custom_fields, '') <> ''
            ORDER BY id
            """
        )
    ).fetchall()

    dedupe_keys: set[tuple[str, str, str, str, str]] = set()
    rows_to_insert: list[dict[str, object]] = []

    for legacy_row in legacy_rows:
        raw_payload = str(legacy_row.profile_custom_fields or "").strip()
        if not raw_payload:
            continue

        try:
            parsed_fields = json.loads(raw_payload)
        except json.JSONDecodeError:
            continue

        if not isinstance(parsed_fields, dict):
            continue

        raw_records_payload = parsed_fields.get("process_records__administrativo")
        if not isinstance(raw_records_payload, str) or not raw_records_payload.strip():
            continue

        try:
            parsed_records = json.loads(raw_records_payload)
        except json.JSONDecodeError:
            continue

        if not isinstance(parsed_records, list):
            continue

        created_by_user_id = users_by_member_id.get(int(legacy_row.id))

        for parsed_record in parsed_records:
            if not isinstance(parsed_record, dict):
                continue

            section_key = str(parsed_record.get("section_key") or "").strip().lower()
            if section_key != "custom_perfil_de_autorizacao":
                continue

            values = parsed_record.get("values")
            if not isinstance(values, dict):
                continue

            profile_name = str(values.get("custom_perfil") or "").strip()
            process_label = str(values.get("custom_processo") or "").strip()
            subprocess_label = str(values.get("custom_subprocesso") or "").strip()
            department_name = str(values.get("custom_departamento") or "").strip()
            status = _normalize_rule_status(values.get("__estado"))

            if not profile_name or not process_label:
                continue

            dedupe_key = (
                _normalize_lookup_text(profile_name),
                _normalize_lookup_text(process_label),
                _normalize_lookup_text(subprocess_label),
                _normalize_lookup_text(department_name),
                status,
            )
            if dedupe_key in dedupe_keys:
                continue

            dedupe_keys.add(dedupe_key)
            created_at = _parse_created_at(parsed_record.get("created_at"))
            rows_to_insert.append(
                {
                    "entity_id": None,
                    "profile_name": profile_name[:100],
                    "process_key": None,
                    "process_label": process_label[:120],
                    "subprocess_key": None,
                    "subprocess_label": subprocess_label[:120],
                    "department_name": department_name[:150],
                    "status": status,
                    "legacy_record_id": str(parsed_record.get("record_id") or "").strip()[:40] or None,
                    "created_by_user_id": created_by_user_id,
                    "updated_by_user_id": created_by_user_id,
                    "created_at": created_at,
                    "updated_at": created_at,
                }
            )

    if rows_to_insert:
        process_view_authorization_rules = sa.table(
            "process_view_authorization_rules",
            sa.column("entity_id", sa.Integer()),
            sa.column("profile_name", sa.String(length=100)),
            sa.column("process_key", sa.String(length=120)),
            sa.column("process_label", sa.String(length=120)),
            sa.column("subprocess_key", sa.String(length=120)),
            sa.column("subprocess_label", sa.String(length=120)),
            sa.column("department_name", sa.String(length=150)),
            sa.column("status", sa.String(length=20)),
            sa.column("legacy_record_id", sa.String(length=40)),
            sa.column("created_by_user_id", sa.Integer()),
            sa.column("updated_by_user_id", sa.Integer()),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("updated_at", sa.DateTime(timezone=True)),
        )
        op.bulk_insert(process_view_authorization_rules, rows_to_insert)


# ###################################################################################
# (2) UPGRADE / DOWNGRADE
# ###################################################################################


def upgrade() -> None:
    if not _has_table("process_view_authorization_rules"):
        op.create_table(
            "process_view_authorization_rules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("profile_name", sa.String(length=100), nullable=False),
            sa.Column("process_key", sa.String(length=120), nullable=True),
            sa.Column(
                "process_label",
                sa.String(length=120),
                nullable=False,
                server_default=sa.text("''"),
            ),
            sa.Column("subprocess_key", sa.String(length=120), nullable=True),
            sa.Column(
                "subprocess_label",
                sa.String(length=120),
                nullable=False,
                server_default=sa.text("''"),
            ),
            sa.Column(
                "department_name",
                sa.String(length=150),
                nullable=False,
                server_default=sa.text("''"),
            ),
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
                server_default=sa.text("'active'"),
            ),
            sa.Column("legacy_record_id", sa.String(length=40), nullable=True),
            sa.Column("created_by_user_id", sa.Integer(), nullable=True),
            sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint(
                "status IN ('active', 'inactive')",
                name="ck_process_view_authorization_rules_status",
            ),
            sa.ForeignKeyConstraint(["entity_id"], ["entities.id"]),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_index(
        "process_view_authorization_rules",
        "ix_process_view_authorization_rules_entity_status",
    ):
        op.create_index(
            "ix_process_view_authorization_rules_entity_status",
            "process_view_authorization_rules",
            ["entity_id", "status"],
            unique=False,
        )

    if not _has_index(
        "process_view_authorization_rules",
        "ix_process_view_authorization_rules_profile_status",
    ):
        op.create_index(
            "ix_process_view_authorization_rules_profile_status",
            "process_view_authorization_rules",
            ["profile_name", "status"],
            unique=False,
        )

    if not _has_index(
        "process_view_authorization_rules",
        "ix_process_view_authorization_rules_process_targets",
    ):
        op.create_index(
            "ix_process_view_authorization_rules_process_targets",
            "process_view_authorization_rules",
            ["process_key", "subprocess_key"],
            unique=False,
        )

    _backfill_legacy_rules()


def downgrade() -> None:
    if _has_table("process_view_authorization_rules"):
        if _has_index(
            "process_view_authorization_rules",
            "ix_process_view_authorization_rules_process_targets",
        ):
            op.drop_index(
                "ix_process_view_authorization_rules_process_targets",
                table_name="process_view_authorization_rules",
            )

        if _has_index(
            "process_view_authorization_rules",
            "ix_process_view_authorization_rules_profile_status",
        ):
            op.drop_index(
                "ix_process_view_authorization_rules_profile_status",
                table_name="process_view_authorization_rules",
            )

        if _has_index(
            "process_view_authorization_rules",
            "ix_process_view_authorization_rules_entity_status",
        ):
            op.drop_index(
                "ix_process_view_authorization_rules_entity_status",
                table_name="process_view_authorization_rules",
            )

        op.drop_table("process_view_authorization_rules")
