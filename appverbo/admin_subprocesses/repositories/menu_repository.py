from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.menu_settings import (
    MENU_SECTION_OPTIONS,
    create_sidebar_menu_setting,
    delete_sidebar_menu_setting,
    get_sidebar_menu_settings,
    move_sidebar_menu_additional_field,
    move_sidebar_menu_setting,
    normalize_sidebar_sections,
    resolve_menu_key_alias,
    set_sidebar_menu_visibility,
    update_sidebar_menu_additional_fields_v1,
    update_sidebar_menu_label,
    update_sidebar_menu_process_fields,
    update_sidebar_menu_process_lists,
    update_sidebar_menu_process_quantity_fields_v1,
    update_sidebar_menu_subsequent_fields,
)


MENU_STATUS_ACTIVE_V1 = "active"
MENU_STATUS_INACTIVE_V1 = "inactive"
MENU_ALLOWED_STATUS_VALUES_V1 = frozenset(
    {
        MENU_STATUS_ACTIVE_V1,
        MENU_STATUS_INACTIVE_V1,
    }
)


# ###################################################################################
# (1) FILTROS DE LISTAGEM
# ###################################################################################


@dataclass(frozen=True)
class MenuListFilters:
    entity_id: int | None = None
    allowed_entity_ids: tuple[int, ...] = ()
    status_values: tuple[str, ...] = ()
    search_text: str = ""
    page: int = 1
    page_size: int = 5000


# ###################################################################################
# (2) REPOSITÓRIO NATIVO DE MENU
# ###################################################################################


class MenuAdminRepository(BaseAdminSubprocessRepository):
    def _normalize_text(self, value: object) -> str:
        return str(value or "").strip()

    def _coerce_int(self, value: object) -> int | None:
        clean_value = self._normalize_text(value)

        if not clean_value.isdigit():
            return None

        return int(clean_value)

    def normalize_menu_key(self, raw_value: object) -> str:
        return str(resolve_menu_key_alias(raw_value) or "").strip().lower()

    def normalize_menu_label(self, raw_value: object) -> str:
        return " ".join(self._normalize_text(raw_value).split())

    def normalize_menu_status(self, raw_value: object) -> str:
        clean_status = self._normalize_text(raw_value).lower()

        if clean_status in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
            return MENU_STATUS_INACTIVE_V1

        return MENU_STATUS_ACTIVE_V1

    def _normalize_status_values_v1(
        self,
        raw_status_values: tuple[str, ...],
    ) -> tuple[str, ...]:
        normalized_values: list[str] = []
        seen_values: set[str] = set()

        for raw_status in raw_status_values:
            clean_status = self.normalize_menu_status(raw_status)

            if clean_status not in MENU_ALLOWED_STATUS_VALUES_V1:
                continue

            if clean_status in seen_values:
                continue

            seen_values.add(clean_status)
            normalized_values.append(clean_status)

        return tuple(normalized_values)

    def _normalize_filters_from_context(
        self,
        context: dict[str, Any] | None,
    ) -> MenuListFilters:
        raw_context = context or {}

        raw_page = self._normalize_text(raw_context.get("page"))
        raw_page_size = self._normalize_text(raw_context.get("page_size"))
        raw_status = self._normalize_text(raw_context.get("status")).lower()
        clean_search = self._normalize_text(raw_context.get("q") or raw_context.get("search"))

        page = int(raw_page) if raw_page.isdigit() else 1
        page_size = int(raw_page_size) if raw_page_size.isdigit() else 5000

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 1

        if page_size > 5000:
            page_size = 5000

        raw_entity_id = self._coerce_int(raw_context.get("entity_id"))
        normalized_allowed_entity_ids: list[int] = []

        raw_allowed_entity_ids = raw_context.get("allowed_entity_ids")
        if isinstance(raw_allowed_entity_ids, (list, tuple, set)):
            for raw_entity_id in raw_allowed_entity_ids:
                parsed_entity_id = self._coerce_int(raw_entity_id)

                if parsed_entity_id is not None:
                    normalized_allowed_entity_ids.append(parsed_entity_id)

        status_values = self._normalize_status_values_v1(
            tuple(
                part.strip()
                for part in raw_status.split(",")
                if part.strip()
            )
        )

        return MenuListFilters(
            entity_id=raw_entity_id,
            allowed_entity_ids=tuple(sorted(set(normalized_allowed_entity_ids))),
            status_values=status_values,
            search_text=clean_search,
            page=page,
            page_size=page_size,
        )

    def _to_row_v1(self, raw_row: dict[str, Any]) -> dict[str, Any]:
        row = dict(raw_row)
        menu_key = self.normalize_menu_key(row.get("key"))
        menu_label = self._normalize_text(row.get("label"))
        is_active = bool(row.get("is_active")) and not bool(row.get("is_deleted"))
        status = MENU_STATUS_ACTIVE_V1 if is_active else MENU_STATUS_INACTIVE_V1
        visibility_scope_mode = self._normalize_text(
            row.get("visibility_scope_mode") or "all"
        ).lower()
        section_key = self._normalize_text(
            row.get("sidebar_section_key") or row.get("menu_section")
        ).lower()
        section_label = self._normalize_text(
            row.get("sidebar_section_label") or row.get("menu_section_label")
        )

        return {
            **row,
            "id": menu_key,
            "key": menu_key,
            "menu_key": menu_key,
            "label": menu_label,
            "name": menu_label,
            "status": status,
            "status_label": "Ativo" if status == MENU_STATUS_ACTIVE_V1 else "Inativo",
            "is_active": bool(is_active),
            "visibility_scope_mode": visibility_scope_mode or "all",
            "visibility_scope_label": self._normalize_text(
                row.get("visibility_scope_label") or "Owner e Legado"
            ),
            "display_order": row.get("display_order", row.get("order_index", 0)),
            "order": row.get("display_order", row.get("order_index", 0)),
            "menu_section": section_key,
            "menu_section_label": section_label,
            "group": section_label,
            "section": section_label,
            "can_delete": bool(row.get("can_delete")),
            "can_move_up": bool(row.get("can_move_up", True)),
            "can_move_down": bool(row.get("can_move_down", True)),
        }

    def _apply_filters_v1(
        self,
        *,
        rows: list[dict[str, Any]],
        filters: MenuListFilters,
    ) -> list[dict[str, Any]]:
        filtered_rows = list(rows)

        if filters.entity_id is not None and filters.allowed_entity_ids:
            allowed_entity_ids = set(filters.allowed_entity_ids)

            if int(filters.entity_id) not in allowed_entity_ids:
                return []

        status_values = set(filters.status_values or ())
        if status_values:
            filtered_rows = [
                row
                for row in filtered_rows
                if self.normalize_menu_status(row.get("status")) in status_values
            ]

        clean_search = self._normalize_text(filters.search_text).lower()
        if clean_search:
            filtered_rows = [
                row
                for row in filtered_rows
                if clean_search in self._normalize_text(row.get("label")).lower()
                or clean_search in self._normalize_text(row.get("key")).lower()
                or clean_search in self._normalize_text(row.get("menu_section_label")).lower()
            ]

        return filtered_rows

    def list_menus(
        self,
        *,
        session: Any,
        filters: MenuListFilters | None = None,
    ) -> dict[str, Any]:
        resolved_filters = filters or MenuListFilters()
        rows = [self._to_row_v1(raw_row) for raw_row in get_sidebar_menu_settings(session)]
        rows = self._apply_filters_v1(rows=rows, filters=resolved_filters)

        total_rows = len(rows)
        start_index = (resolved_filters.page - 1) * resolved_filters.page_size
        end_index = start_index + resolved_filters.page_size
        paginated_rows = rows[start_index:end_index]

        return {
            "rows": paginated_rows,
            "total": total_rows,
            "page": resolved_filters.page,
            "page_size": resolved_filters.page_size,
            "has_next": end_index < total_rows,
        }

    def list_active(
        self,
        *,
        session: Any,
        filters: MenuListFilters | None = None,
    ) -> list[dict[str, Any]]:
        resolved_filters = filters or MenuListFilters()
        active_filters = MenuListFilters(
            entity_id=resolved_filters.entity_id,
            allowed_entity_ids=resolved_filters.allowed_entity_ids,
            status_values=(MENU_STATUS_ACTIVE_V1,),
            search_text=resolved_filters.search_text,
            page=resolved_filters.page,
            page_size=resolved_filters.page_size,
        )

        return list(
            self.list_menus(
                session=session,
                filters=active_filters,
            ).get("rows", [])
        )

    def list_inactive(
        self,
        *,
        session: Any,
        filters: MenuListFilters | None = None,
    ) -> list[dict[str, Any]]:
        resolved_filters = filters or MenuListFilters()
        inactive_filters = MenuListFilters(
            entity_id=resolved_filters.entity_id,
            allowed_entity_ids=resolved_filters.allowed_entity_ids,
            status_values=(MENU_STATUS_INACTIVE_V1,),
            search_text=resolved_filters.search_text,
            page=resolved_filters.page,
            page_size=resolved_filters.page_size,
        )

        return list(
            self.list_menus(
                session=session,
                filters=inactive_filters,
            ).get("rows", [])
        )

    def get_by_key(
        self,
        *,
        session: Any,
        menu_key: str,
    ) -> dict[str, Any] | None:
        clean_menu_key = self.normalize_menu_key(menu_key)

        if not clean_menu_key:
            return None

        for row in get_sidebar_menu_settings(session):
            current_key = self.normalize_menu_key(row.get("key"))

            if current_key == clean_menu_key:
                return self._to_row_v1(row)

        return None

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return self.get_by_key(
            session=session,
            menu_key=edit_key,
        )

    def get_next_display_order(self, *, session: Any) -> int:
        rows = get_sidebar_menu_settings(session)
        return len(rows)

    def create_menu(
        self,
        *,
        session: Any,
        menu_label: str,
        visibility_scope_mode: str,
        menu_section: str = "",
    ) -> tuple[bool, str, str]:
        ok, error_message, new_menu_key = create_sidebar_menu_setting(
            session,
            menu_label,
            visibility_scope_mode,
        )

        if not ok:
            return False, error_message or "Não foi possível criar o menu.", ""

        clean_menu_section = self._normalize_text(menu_section)
        if clean_menu_section:
            ok, error_message = update_sidebar_menu_label(
                session,
                new_menu_key,
                menu_label,
                visibility_scope_mode,
                clean_menu_section,
            )
            if not ok:
                return False, error_message or "Não foi possível configurar a sessão do menu.", ""

        return True, "", self.normalize_menu_key(new_menu_key)

    def update_menu_label(
        self,
        *,
        session: Any,
        menu_key: str,
        menu_label: str,
        visibility_scope_mode: str,
        menu_sidebar_section: str = "",
    ) -> tuple[bool, str]:
        return update_sidebar_menu_label(
            session,
            menu_key,
            menu_label,
            visibility_scope_mode,
            menu_sidebar_section,
        )

    def update_menu_visibility(
        self,
        *,
        session: Any,
        menu_key: str,
        make_visible: bool,
    ) -> tuple[bool, str]:
        return set_sidebar_menu_visibility(session, menu_key, make_visible)

    def move_menu(
        self,
        *,
        session: Any,
        menu_key: str,
        direction: str,
    ) -> tuple[bool, str]:
        return move_sidebar_menu_setting(session, menu_key, direction)

    def delete_menu(
        self,
        *,
        session: Any,
        menu_key: str,
    ) -> tuple[bool, str]:
        return delete_sidebar_menu_setting(session, menu_key)

    def update_process_fields(
        self,
        *,
        session: Any,
        menu_key: str,
        visible_fields: list[str],
        visible_headers: list[str],
    ) -> tuple[bool, str]:
        return update_sidebar_menu_process_fields(
            session=session,
            menu_key=menu_key,
            visible_fields=visible_fields,
            visible_headers=visible_headers,
        )

    def _read_sidebar_menu_config_v1(
        self,
        *,
        session: Any,
        menu_key: str,
    ) -> dict[str, Any]:
        clean_menu_key = self.normalize_menu_key(menu_key)

        if not clean_menu_key:
            return {}

        raw_config = session.execute(
            text(
                """
                SELECT menu_config
                FROM sidebar_menu_settings
                WHERE lower(trim(menu_key)) = :menu_key
                LIMIT 1
                """
            ),
            {"menu_key": clean_menu_key},
        ).scalar_one_or_none()

        if not raw_config:
            return {}

        try:
            parsed_config = json.loads(raw_config)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}

        if isinstance(parsed_config, dict):
            return parsed_config

        return {}

    def _write_sidebar_menu_config_v1(
        self,
        *,
        session: Any,
        menu_key: str,
        menu_config: dict[str, Any],
    ) -> None:
        clean_menu_key = self.normalize_menu_key(menu_key)

        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": clean_menu_key,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            },
        )

    def _get_header_assignments_from_config_v1(self, menu_config: dict[str, Any]) -> dict[str, str]:
        assignments: dict[str, str] = {}

        raw_rows = menu_config.get("process_visible_field_rows")
        if isinstance(raw_rows, list):
            for raw_row in raw_rows:
                if not isinstance(raw_row, dict):
                    continue

                field_key = self._normalize_text(raw_row.get("field_key")).lower()
                header_key = self._normalize_text(raw_row.get("header_key")).lower()

                if not field_key or not header_key:
                    continue

                assignments[field_key] = header_key

        raw_header_map = menu_config.get("process_visible_field_header_map")
        if isinstance(raw_header_map, dict):
            for raw_field_key, raw_header_key in raw_header_map.items():
                field_key = self._normalize_text(raw_field_key).lower()
                header_key = self._normalize_text(raw_header_key).lower()

                if not field_key or not header_key:
                    continue

                assignments[field_key] = header_key

        return assignments

    def _get_header_keys_from_config_v1(self, menu_config: dict[str, Any]) -> set[str]:
        header_keys: set[str] = set()

        raw_fields = menu_config.get("additional_fields")
        if not isinstance(raw_fields, list):
            return header_keys

        for raw_field in raw_fields:
            if not isinstance(raw_field, dict):
                continue

            field_key = self._normalize_text(raw_field.get("key")).lower()
            field_type = self._normalize_text(
                raw_field.get("field_type") or raw_field.get("type")
            ).lower()

            if field_key and field_type == "header":
                header_keys.add(field_key)

        return header_keys

    def _get_visible_fields_from_config_v1(self, menu_config: dict[str, Any]) -> list[str]:
        visible_fields: list[str] = []
        seen_fields: set[str] = set()

        raw_visible_fields = menu_config.get("process_visible_fields")
        if isinstance(raw_visible_fields, list):
            for raw_field_key in raw_visible_fields:
                field_key = self._normalize_text(raw_field_key).lower()

                if not field_key or field_key in seen_fields:
                    continue

                seen_fields.add(field_key)
                visible_fields.append(field_key)

        raw_rows = menu_config.get("process_visible_field_rows")
        if isinstance(raw_rows, list):
            for raw_row in raw_rows:
                if not isinstance(raw_row, dict):
                    continue

                field_key = self._normalize_text(raw_row.get("field_key")).lower()

                if not field_key or field_key in seen_fields:
                    continue

                seen_fields.add(field_key)
                visible_fields.append(field_key)

        return visible_fields

    def _restore_menu_header_assignments_after_additional_fields_v1(
        self,
        *,
        session: Any,
        menu_key: str,
        old_menu_config: dict[str, Any],
    ) -> None:
        old_assignments = self._get_header_assignments_from_config_v1(old_menu_config)

        if not old_assignments:
            return

        current_config = self._read_sidebar_menu_config_v1(
            session=session,
            menu_key=menu_key,
        )
        if not current_config:
            return

        current_header_keys = self._get_header_keys_from_config_v1(current_config)
        current_visible_fields = self._get_visible_fields_from_config_v1(current_config)

        if not current_visible_fields:
            return

        restored_header_map: dict[str, str] = {}
        restored_rows: list[dict[str, str]] = []

        for field_key in current_visible_fields:
            if field_key in current_header_keys:
                continue

            header_key = old_assignments.get(field_key, "")
            if header_key not in current_header_keys:
                header_key = ""

            if header_key:
                restored_header_map[field_key] = header_key

            restored_rows.append(
                {
                    "field_key": field_key,
                    "header_key": header_key,
                }
            )

        current_config["process_visible_field_header_map"] = restored_header_map
        current_config["process_visible_field_rows"] = restored_rows

        self._write_sidebar_menu_config_v1(
            session=session,
            menu_key=menu_key,
            menu_config=current_config,
        )
        session.commit()

    def update_additional_fields(
        self,
        *,
        session: Any,
        menu_key: str,
        fields: list[dict[str, Any]],
    ) -> tuple[bool, str]:
        old_menu_config = self._read_sidebar_menu_config_v1(
            session=session,
            menu_key=menu_key,
        )

        ok, error_message = update_sidebar_menu_additional_fields_v1(
            session=session,
            menu_key=menu_key,
            fields=fields,
        )
        if not ok:
            return False, error_message

        self._restore_menu_header_assignments_after_additional_fields_v1(
            session=session,
            menu_key=menu_key,
            old_menu_config=old_menu_config,
        )

        return True, ""

    def update_process_lists(
        self,
        *,
        session: Any,
        menu_key: str,
        raw_lists: list[dict[str, str]],
    ) -> tuple[bool, str]:
        return update_sidebar_menu_process_lists(
            session=session,
            menu_key=menu_key,
            raw_lists=raw_lists,
        )

    def update_quantity_fields(
        self,
        *,
        session: Any,
        menu_key: str,
        raw_fields: list[dict[str, str]],
    ) -> tuple[bool, str]:
        return update_sidebar_menu_process_quantity_fields_v1(
            session=session,
            menu_key=menu_key,
            raw_fields=raw_fields,
        )

    def update_subsequent_fields(
        self,
        *,
        session: Any,
        menu_key: str,
        raw_fields: list[dict[str, str]],
    ) -> tuple[bool, str]:
        return update_sidebar_menu_subsequent_fields(
            session=session,
            menu_key=menu_key,
            raw_fields=raw_fields,
        )

    def move_additional_field(
        self,
        *,
        session: Any,
        menu_key: str,
        field_key: str,
        direction: str,
    ) -> tuple[bool, str]:
        return move_sidebar_menu_additional_field(
            session=session,
            menu_key=menu_key,
            field_key=field_key,
            direction=direction,
        )

    def load_menu_config(
        self,
        *,
        session: Any,
        menu_key: str,
    ) -> dict[str, Any]:
        return self._read_sidebar_menu_config_v1(
            session=session,
            menu_key=menu_key,
        )

    def persist_menu_config(
        self,
        *,
        session: Any,
        menu_key: str,
        menu_config: dict[str, Any],
    ) -> tuple[bool, str]:
        clean_menu_key = self.normalize_menu_key(menu_key)

        if not clean_menu_key:
            return False, "Menu inválido."

        self._write_sidebar_menu_config_v1(
            session=session,
            menu_key=clean_menu_key,
            menu_config=dict(menu_config or {}),
        )
        session.commit()
        return True, ""

    def get_section_options(
        self,
        *,
        session: Any,
    ) -> list[dict[str, str]]:
        administrativo_menu = self.get_by_key(session=session, menu_key="administrativo") or {}
        menu_config = dict(administrativo_menu.get("menu_config") or {})
        dynamic_sections = normalize_sidebar_sections(menu_config.get("sidebar_sections"))

        if dynamic_sections:
            return [
                {
                    "key": self._normalize_text(row.get("key")).lower(),
                    "label": self._normalize_text(row.get("label")),
                }
                for row in dynamic_sections
                if self._normalize_text(row.get("key")) and self._normalize_text(row.get("label"))
            ]

        return [
            {
                "key": self._normalize_text(row.get("key")).lower(),
                "label": self._normalize_text(row.get("label")),
            }
            for row in MENU_SECTION_OPTIONS
            if self._normalize_text(row.get("key")) and self._normalize_text(row.get("label"))
        ]

    def list_rows(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        filters = self._normalize_filters_from_context(context)
        result = self.list_menus(
            session=session,
            filters=filters,
        )
        return list(result.get("rows", []))

    def create(
        self,
        session: Any,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _, _ = self.create_menu(
            session=session,
            menu_label=self.normalize_menu_label(payload.get("menu_label") or payload.get("label")),
            visibility_scope_mode=self._normalize_text(
                payload.get("menu_visibility_scope") or payload.get("visibility_scope_mode") or "all"
            ),
            menu_section=self._normalize_text(
                payload.get("menu_section") or payload.get("menu_sidebar_section") or ""
            ),
        )
        return ok

    def update(
        self,
        session: Any,
        edit_key: str,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _ = self.update_menu_label(
            session=session,
            menu_key=edit_key,
            menu_label=self.normalize_menu_label(payload.get("menu_label") or payload.get("label")),
            visibility_scope_mode=self._normalize_text(
                payload.get("menu_visibility_scope") or payload.get("visibility_scope_mode") or "all"
            ),
            menu_sidebar_section=self._normalize_text(
                payload.get("menu_sidebar_section") or payload.get("menu_section") or ""
            ),
        )
        return ok

    def move(
        self,
        session: Any,
        edit_key: str,
        direction: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _ = self.move_menu(
            session=session,
            menu_key=edit_key,
            direction=direction,
        )
        return ok

    def delete(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _ = self.delete_menu(
            session=session,
            menu_key=edit_key,
        )
        return ok
