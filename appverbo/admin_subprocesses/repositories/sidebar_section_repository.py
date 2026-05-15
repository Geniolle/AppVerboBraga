from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.menu_settings import (
    MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY,
    MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
    SIDEBAR_SECTION_DEFAULTS,
    SIDEBAR_SECTION_DEFAULTS_BY_KEY,
    build_sidebar_global_refresh_version_v1,
    get_sidebar_section_visibility_scope_mode,
    normalize_menu_visibility_scopes,
    update_sidebar_sections_v2,
)


SESSION_STATUS_ACTIVE_V1 = "ativo"
SESSION_STATUS_INACTIVE_V1 = "inativo"
SESSION_STATUS_PENDING_V1 = "pending"
SESSION_STATUS_BLOCKED_V1 = "blocked"

SESSION_ALLOWED_STATUS_VALUES_V1 = frozenset(
    {
        SESSION_STATUS_ACTIVE_V1,
        SESSION_STATUS_INACTIVE_V1,
        SESSION_STATUS_PENDING_V1,
        SESSION_STATUS_BLOCKED_V1,
    }
)


# ###################################################################################
# (1) FILTROS DE LISTAGEM
# ###################################################################################

@dataclass(frozen=True)
class SidebarSectionListFilters:
    entity_id: int | None = None
    allowed_entity_ids: tuple[int, ...] = ()
    status_values: tuple[str, ...] = ()
    search_text: str = ""
    page: int = 1
    page_size: int = 5000


# ###################################################################################
# (2) REPOSITORY NATIVO DE SESSOES
# ###################################################################################

class SidebarSectionAdminRepository(BaseAdminSubprocessRepository):
    menu_key = "administrativo"

    def _normalize_text(self, value: object) -> str:
        return str(value or "").strip()

    def _normalize_key(self, value: object) -> str:
        return self._normalize_text(value).lower()

    def _slugify_session_key(self, value: object) -> str:
        raw_value = self._normalize_text(value).lower()
        raw_value = unicodedata.normalize("NFD", raw_value)
        raw_value = "".join(
            char
            for char in raw_value
            if unicodedata.category(char) != "Mn"
        )
        raw_value = re.sub(r"[^a-z0-9]+", "_", raw_value)
        raw_value = re.sub(r"_+", "_", raw_value).strip("_")

        if raw_value and raw_value[0].isdigit():
            raw_value = f"secao_{raw_value}"

        return raw_value

    def normalize_session_status(self, value: object) -> str:
        if isinstance(value, bool):
            return SESSION_STATUS_ACTIVE_V1 if value else SESSION_STATUS_INACTIVE_V1

        clean_value = self._normalize_key(value)

        if clean_value in {
            "inativo",
            "inactive",
            "0",
            "false",
            "no",
            "nao",
            "não",
            "off",
        }:
            return SESSION_STATUS_INACTIVE_V1

        if clean_value in {"pendente", "pending"}:
            return SESSION_STATUS_PENDING_V1

        if clean_value in {"bloqueado", "blocked"}:
            return SESSION_STATUS_BLOCKED_V1

        return SESSION_STATUS_ACTIVE_V1

    def _session_status_label(self, status: str) -> str:
        if status == SESSION_STATUS_INACTIVE_V1:
            return "Inativo"

        if status == SESSION_STATUS_PENDING_V1:
            return "Pendente"

        if status == SESSION_STATUS_BLOCKED_V1:
            return "Bloqueado"

        return "Ativo"

    def normalize_session_scope(self, value: object) -> str:
        clean_value = self._normalize_key(value)

        if clean_value in {"owner", "legado"}:
            return clean_value

        return "all"

    def _scope_to_scopes(self, scope_mode: str) -> list[str]:
        if scope_mode in {"owner", "legado"}:
            return [scope_mode]

        return ["owner", "legado"]

    def _scope_label(self, scope_mode: str) -> str:
        if scope_mode == "owner":
            return "Owner"

        if scope_mode == "legado":
            return "Legado"

        return "Owner e Legado"

    def make_unique_session_key(self, base_key: str, used_keys: set[str]) -> str:
        clean_base_key = self._slugify_session_key(base_key) or "nova_sessao"

        if clean_base_key not in used_keys:
            return clean_base_key

        counter = 2
        candidate = f"{clean_base_key}_{counter}"

        while candidate in used_keys:
            counter += 1
            candidate = f"{clean_base_key}_{counter}"

        return candidate

    def _normalize_status_values(self, raw_values: tuple[str, ...]) -> tuple[str, ...]:
        normalized_values: list[str] = []
        seen_values: set[str] = set()

        for raw_value in raw_values:
            clean_status = self.normalize_session_status(raw_value)

            if clean_status not in SESSION_ALLOWED_STATUS_VALUES_V1:
                continue

            if clean_status in seen_values:
                continue

            seen_values.add(clean_status)
            normalized_values.append(clean_status)

        return tuple(normalized_values)

    def _normalize_filters_from_context(
        self,
        context: dict[str, Any] | None,
    ) -> SidebarSectionListFilters:
        raw_context = context or {}

        raw_entity_id = self._normalize_text(raw_context.get("entity_id"))
        parsed_entity_id = int(raw_entity_id) if raw_entity_id.isdigit() else None

        raw_page = self._normalize_text(raw_context.get("page"))
        raw_page_size = self._normalize_text(raw_context.get("page_size"))

        parsed_page = int(raw_page) if raw_page.isdigit() else 1
        parsed_page_size = int(raw_page_size) if raw_page_size.isdigit() else 5000

        if parsed_page < 1:
            parsed_page = 1

        if parsed_page_size < 1:
            parsed_page_size = 1

        if parsed_page_size > 5000:
            parsed_page_size = 5000

        raw_status = self._normalize_text(raw_context.get("status")).lower()
        raw_status_values = tuple(
            part.strip().lower()
            for part in raw_status.split(",")
            if part.strip()
        )

        normalized_status_values = self._normalize_status_values(raw_status_values)

        raw_allowed_entity_ids = raw_context.get("allowed_entity_ids")
        normalized_allowed_entity_ids: list[int] = []

        if isinstance(raw_allowed_entity_ids, (list, tuple, set)):
            for raw_entity in raw_allowed_entity_ids:
                clean_entity = self._normalize_text(raw_entity)

                if clean_entity.isdigit():
                    normalized_allowed_entity_ids.append(int(clean_entity))

        return SidebarSectionListFilters(
            entity_id=parsed_entity_id,
            allowed_entity_ids=tuple(sorted(set(normalized_allowed_entity_ids))),
            status_values=normalized_status_values,
            search_text=self._normalize_text(raw_context.get("q") or raw_context.get("search")),
            page=parsed_page,
            page_size=parsed_page_size,
        )

    def _parse_menu_config(self, raw_value: object) -> dict[str, Any]:
        if isinstance(raw_value, dict):
            return dict(raw_value)

        try:
            parsed_value = json.loads(raw_value or "{}")
        except (TypeError, ValueError):
            parsed_value = {}

        if isinstance(parsed_value, dict):
            return dict(parsed_value)

        return {}

    def _load_administrativo_menu_config(
        self,
        *,
        session: Any,
    ) -> tuple[dict[str, Any], bool]:
        row = session.execute(
            text(
                """
                SELECT menu_config
                FROM sidebar_menu_settings
                WHERE lower(trim(menu_key)) = :menu_key
                LIMIT 1
                """
            ),
            {"menu_key": self.menu_key},
        ).fetchone()

        if not row:
            return {}, False

        return self._parse_menu_config(row[0]), True

    def _persist_administrativo_menu_config(
        self,
        *,
        session: Any,
        menu_config: dict[str, Any],
    ) -> tuple[bool, str]:
        result = session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": self.menu_key,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            },
        )

        if int(result.rowcount or 0) <= 0:
            session.rollback()
            return False, "Não foi possível atualizar a configuração do menu Administrativo."

        session.commit()
        return True, ""

    def normalize_session_row(
        self,
        row: dict[str, Any] | str,
        fallback_status: str = SESSION_STATUS_ACTIVE_V1,
    ) -> dict[str, Any]:
        raw_row: dict[str, Any]

        if isinstance(row, dict):
            raw_row = dict(row)
        else:
            raw_row = {"label": row}

        clean_label = self._normalize_text(raw_row.get("label"))
        clean_key = self._slugify_session_key(raw_row.get("key"))

        if not clean_key and clean_label:
            clean_key = self._slugify_session_key(clean_label)

        if clean_key and not clean_label:
            clean_label = str(SIDEBAR_SECTION_DEFAULTS_BY_KEY.get(clean_key) or "").strip()

        if not clean_key or not clean_label:
            return {}

        raw_scope_mode = get_sidebar_section_visibility_scope_mode(raw_row)
        clean_scope_mode = self.normalize_session_scope(raw_scope_mode)

        visibility_scopes = normalize_menu_visibility_scopes(
            raw_row.get("visibility_scopes")
            if raw_row.get("visibility_scopes") is not None
            else self._scope_to_scopes(clean_scope_mode)
        )

        if not visibility_scopes:
            visibility_scopes = self._scope_to_scopes(clean_scope_mode)

        clean_scope_mode = self.normalize_session_scope(clean_scope_mode)

        raw_status = raw_row.get("status")

        if raw_status is None:
            raw_status = raw_row.get("section_status")

        if raw_status is None:
            raw_status = raw_row.get("is_active", fallback_status)

        clean_status = self.normalize_session_status(raw_status)

        return {
            "key": clean_key,
            "id": clean_key,
            "label": clean_label,
            "name": clean_label,
            "visibility_scopes": visibility_scopes,
            "visibility_scope_mode": clean_scope_mode,
            "visibility_scope_label": self._scope_label(clean_scope_mode),
            "status": clean_status,
            "section_status": clean_status,
            "status_label": self._session_status_label(clean_status),
            "is_active": clean_status == SESSION_STATUS_ACTIVE_V1,
            "can_delete": clean_key not in SIDEBAR_SECTION_DEFAULTS_BY_KEY,
        }

    def _append_missing_defaults(
        self,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized_rows = list(rows)
        seen_keys = {
            self._normalize_key(row.get("key"))
            for row in normalized_rows
            if self._normalize_key(row.get("key"))
        }

        for default_row in SIDEBAR_SECTION_DEFAULTS:
            default_key = self._slugify_session_key(default_row.get("key"))

            if not default_key or default_key in seen_keys:
                continue

            seen_keys.add(default_key)
            normalized_default = self.normalize_session_row(
                {
                    "key": default_key,
                    "label": default_row.get("label"),
                    "visibility_scopes": default_row.get("visibility_scopes"),
                    "status": SESSION_STATUS_ACTIVE_V1,
                }
            )

            if normalized_default:
                normalized_rows.append(normalized_default)

        return normalized_rows

    def read_sidebar_sections(self, *, session: Any) -> list[dict[str, Any]]:
        menu_config, _ = self._load_administrativo_menu_config(session=session)
        raw_sections = menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)

        if not isinstance(raw_sections, list):
            raw_sections = []

        normalized_rows: list[dict[str, Any]] = []
        seen_keys: set[str] = set()

        for raw_section in raw_sections:
            normalized_row = self.normalize_session_row(raw_section)

            if not normalized_row:
                continue

            clean_key = self._normalize_key(normalized_row.get("key"))

            if not clean_key or clean_key in seen_keys:
                continue

            seen_keys.add(clean_key)
            normalized_rows.append(normalized_row)

        return self._append_missing_defaults(normalized_rows)

    def update_global_refresh_version(self, *, session: Any) -> tuple[bool, str]:
        menu_config, found_row = self._load_administrativo_menu_config(session=session)

        if not found_row:
            return False, "Configuração do menu Administrativo não encontrada."

        menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = (
            build_sidebar_global_refresh_version_v1()
        )

        return self._persist_administrativo_menu_config(
            session=session,
            menu_config=menu_config,
        )

    def persist_sidebar_sections(
        self,
        *,
        session: Any,
        sections: list[dict[str, Any]],
    ) -> tuple[bool, str, list[dict[str, Any]]]:
        normalized_payload_rows: list[dict[str, Any]] = []
        seen_keys: set[str] = set()

        for raw_section in sections:
            normalized_row = self.normalize_session_row(raw_section)

            if not normalized_row:
                continue

            clean_key = self._normalize_key(normalized_row.get("key"))

            if clean_key in seen_keys:
                continue

            seen_keys.add(clean_key)
            normalized_payload_rows.append(normalized_row)

        normalized_payload_rows = self._append_missing_defaults(normalized_payload_rows)

        if not normalized_payload_rows:
            return False, "Informe pelo menos uma sessão válida.", []

        payload_for_legacy_update = [
            {
                "key": row.get("key"),
                "label": row.get("label"),
                "visibility_scope_mode": row.get("visibility_scope_mode"),
                "status": row.get("status"),
            }
            for row in normalized_payload_rows
        ]

        ok, error_message = update_sidebar_sections_v2(
            session,
            payload_for_legacy_update,
        )

        if not ok:
            return False, error_message or "Não foi possível gravar as sessões.", []

        status_by_key = {
            self._normalize_key(row.get("key")): self.normalize_session_status(row.get("status"))
            for row in normalized_payload_rows
            if self._normalize_key(row.get("key"))
        }

        menu_config, found_row = self._load_administrativo_menu_config(session=session)

        if not found_row:
            return False, "Configuração do menu Administrativo não encontrada.", []

        raw_sections_after_legacy = menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)

        if not isinstance(raw_sections_after_legacy, list):
            raw_sections_after_legacy = []

        patched_rows: list[dict[str, Any]] = []
        seen_patched_keys: set[str] = set()

        for raw_section in raw_sections_after_legacy:
            normalized_row = self.normalize_session_row(raw_section)

            if not normalized_row:
                continue

            clean_key = self._normalize_key(normalized_row.get("key"))

            if not clean_key or clean_key in seen_patched_keys:
                continue

            seen_patched_keys.add(clean_key)
            normalized_row["status"] = self.normalize_session_status(
                status_by_key.get(clean_key, normalized_row.get("status"))
            )
            normalized_row["section_status"] = normalized_row["status"]
            normalized_row["status_label"] = self._session_status_label(normalized_row["status"])
            normalized_row["is_active"] = normalized_row["status"] == SESSION_STATUS_ACTIVE_V1
            normalized_row["can_delete"] = clean_key not in SIDEBAR_SECTION_DEFAULTS_BY_KEY
            patched_rows.append(normalized_row)

        patched_rows = self._append_missing_defaults(patched_rows)

        menu_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = patched_rows
        menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = (
            build_sidebar_global_refresh_version_v1()
        )

        persisted, persist_error = self._persist_administrativo_menu_config(
            session=session,
            menu_config=menu_config,
        )

        if not persisted:
            return False, persist_error or "Não foi possível finalizar a gravação das sessões.", []

        return True, "", patched_rows

    def _apply_filters(
        self,
        *,
        rows: list[dict[str, Any]],
        filters: SidebarSectionListFilters,
    ) -> list[dict[str, Any]]:
        filtered_rows = list(rows)

        if filters.entity_id is not None and filters.allowed_entity_ids:
            allowed_entity_ids = set(filters.allowed_entity_ids)

            if int(filters.entity_id) not in allowed_entity_ids:
                return []

        normalized_status_values = set(self._normalize_status_values(filters.status_values))

        if normalized_status_values:
            filtered_rows = [
                row
                for row in filtered_rows
                if self.normalize_session_status(row.get("status")) in normalized_status_values
            ]

        clean_search = self._normalize_text(filters.search_text)

        if clean_search:
            search_value = clean_search.lower()
            filtered_rows = [
                row
                for row in filtered_rows
                if search_value in self._normalize_text(row.get("label")).lower()
                or search_value in self._normalize_text(row.get("key")).lower()
                or search_value in self._normalize_text(row.get("visibility_scope_label")).lower()
                or search_value in self._normalize_text(row.get("status_label")).lower()
            ]

        return filtered_rows

    def _apply_row_actions_metadata(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result_rows = [dict(row) for row in rows]

        status_groups: dict[str, list[int]] = {}

        for row_index, row in enumerate(result_rows):
            status = self.normalize_session_status(row.get("status"))
            status_groups.setdefault(status, []).append(row_index)

        for status, indexes in status_groups.items():
            for group_index, row_index in enumerate(indexes):
                row = result_rows[row_index]
                can_move = status == SESSION_STATUS_ACTIVE_V1
                row["can_move_up"] = can_move and group_index > 0
                row["can_move_down"] = can_move and group_index < (len(indexes) - 1)
                row["can_delete"] = (
                    self._normalize_key(row.get("key")) not in SIDEBAR_SECTION_DEFAULTS_BY_KEY
                    and status != SESSION_STATUS_ACTIVE_V1
                )

        return result_rows

    def list_sessions(
        self,
        *,
        session: Any,
        filters: SidebarSectionListFilters | None = None,
    ) -> dict[str, Any]:
        resolved_filters = filters or SidebarSectionListFilters()

        rows = self.read_sidebar_sections(session=session)
        rows = self._apply_filters(rows=rows, filters=resolved_filters)
        rows = self._apply_row_actions_metadata(rows)

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
        filters: SidebarSectionListFilters | None = None,
    ) -> list[dict[str, Any]]:
        resolved_filters = filters or SidebarSectionListFilters()
        active_filters = SidebarSectionListFilters(
            entity_id=resolved_filters.entity_id,
            allowed_entity_ids=resolved_filters.allowed_entity_ids,
            status_values=(SESSION_STATUS_ACTIVE_V1,),
            search_text=resolved_filters.search_text,
            page=resolved_filters.page,
            page_size=resolved_filters.page_size,
        )

        return list(
            self.list_sessions(
                session=session,
                filters=active_filters,
            ).get("rows", [])
        )

    def list_inactive(
        self,
        *,
        session: Any,
        filters: SidebarSectionListFilters | None = None,
    ) -> list[dict[str, Any]]:
        resolved_filters = filters or SidebarSectionListFilters()
        inactive_filters = SidebarSectionListFilters(
            entity_id=resolved_filters.entity_id,
            allowed_entity_ids=resolved_filters.allowed_entity_ids,
            status_values=(SESSION_STATUS_INACTIVE_V1,),
            search_text=resolved_filters.search_text,
            page=resolved_filters.page,
            page_size=resolved_filters.page_size,
        )

        return list(
            self.list_sessions(
                session=session,
                filters=inactive_filters,
            ).get("rows", [])
        )

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = self._normalize_filters_from_context(context)
        result = self.list_sessions(
            session=session,
            filters=filters,
        )

        return list(result.get("rows", []))

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_edit_key = self._slugify_session_key(edit_key)

        if not clean_edit_key:
            return None

        for row in self.read_sidebar_sections(session=session):
            current_key = self._normalize_key(row.get("key"))

            if current_key == clean_edit_key:
                return dict(row)

        return None

    def save_session(
        self,
        *,
        session: Any,
        mode: str,
        original_section_key: str,
        section_label: str,
        section_visibility_scope_mode: str,
        section_status: str,
    ) -> tuple[bool, str, str]:
        clean_mode = self._normalize_key(mode)
        clean_original_key = self._slugify_session_key(original_section_key)
        clean_label = self._normalize_text(section_label)
        clean_scope_mode = self.normalize_session_scope(section_visibility_scope_mode)
        clean_status = self.normalize_session_status(section_status)

        if not clean_label:
            return False, "Informe o nome da sessão.", ""

        current_rows = self.read_sidebar_sections(session=session)
        payload_rows: list[dict[str, Any]] = []
        target_key = ""

        if clean_mode == "edit":
            found = False

            for row in current_rows:
                row_key = self._normalize_key(row.get("key"))

                if row_key == clean_original_key:
                    found = True
                    target_key = row_key
                    payload_rows.append(
                        {
                            "key": row_key,
                            "label": clean_label,
                            "visibility_scope_mode": clean_scope_mode,
                            "status": clean_status,
                        }
                    )
                else:
                    payload_rows.append(
                        {
                            "key": row_key,
                            "label": row.get("label"),
                            "visibility_scope_mode": row.get("visibility_scope_mode"),
                            "status": row.get("status"),
                        }
                    )

            if not found:
                return False, "Sessão não encontrada para edição.", ""
        else:
            used_keys = {
                self._normalize_key(row.get("key"))
                for row in current_rows
                if self._normalize_key(row.get("key"))
            }
            target_key = self.make_unique_session_key(clean_label, used_keys)

            for row in current_rows:
                payload_rows.append(
                    {
                        "key": self._normalize_key(row.get("key")),
                        "label": row.get("label"),
                        "visibility_scope_mode": row.get("visibility_scope_mode"),
                        "status": row.get("status"),
                    }
                )

            payload_rows.append(
                {
                    "key": target_key,
                    "label": clean_label,
                    "visibility_scope_mode": clean_scope_mode,
                    "status": clean_status,
                }
            )

        ok, error_message, _ = self.persist_sidebar_sections(
            session=session,
            sections=payload_rows,
        )

        if not ok:
            return False, error_message or "Não foi possível gravar a sessão.", ""

        return True, "", target_key

    def move_session(
        self,
        *,
        session: Any,
        section_key: str,
        direction: str,
    ) -> tuple[bool, str, bool]:
        clean_section_key = self._slugify_session_key(section_key)
        clean_direction = self._normalize_key(direction)

        if clean_direction not in {"up", "down"}:
            return False, "Direção inválida para mover a sessão.", False

        current_rows = self.read_sidebar_sections(session=session)
        payload_rows = [
            {
                "key": self._normalize_key(row.get("key")),
                "label": row.get("label"),
                "visibility_scope_mode": row.get("visibility_scope_mode"),
                "status": row.get("status"),
            }
            for row in current_rows
        ]

        current_index = next(
            (
                index
                for index, row in enumerate(payload_rows)
                if self._normalize_key(row.get("key")) == clean_section_key
            ),
            -1,
        )

        if current_index < 0:
            return False, "Sessão não encontrada para mover.", False

        current_status = self.normalize_session_status(payload_rows[current_index].get("status"))

        if clean_direction == "up":
            target_index = next(
                (
                    index
                    for index in range(current_index - 1, -1, -1)
                    if self.normalize_session_status(payload_rows[index].get("status"))
                    == current_status
                ),
                -1,
            )
        else:
            target_index = next(
                (
                    index
                    for index in range(current_index + 1, len(payload_rows))
                    if self.normalize_session_status(payload_rows[index].get("status"))
                    == current_status
                ),
                -1,
            )

        if target_index < 0:
            return True, "Sessão já está no limite da hierarquia.", False

        payload_rows[current_index], payload_rows[target_index] = (
            payload_rows[target_index],
            payload_rows[current_index],
        )

        ok, error_message, _ = self.persist_sidebar_sections(
            session=session,
            sections=payload_rows,
        )

        if not ok:
            return False, error_message or "Não foi possível mover a sessão.", False

        return True, "", True

    def delete_session(
        self,
        *,
        session: Any,
        section_key: str,
    ) -> tuple[bool, str]:
        clean_section_key = self._slugify_session_key(section_key)

        if not clean_section_key:
            return False, "Sessão inválida para eliminar."

        current_rows = self.read_sidebar_sections(session=session)
        payload_rows: list[dict[str, Any]] = []
        found_row: dict[str, Any] | None = None

        for row in current_rows:
            row_key = self._normalize_key(row.get("key"))

            if row_key == clean_section_key:
                found_row = row
                continue

            payload_rows.append(
                {
                    "key": row_key,
                    "label": row.get("label"),
                    "visibility_scope_mode": row.get("visibility_scope_mode"),
                    "status": row.get("status"),
                }
            )

        if found_row is None:
            return False, "Sessão não encontrada para eliminar."

        if clean_section_key in SIDEBAR_SECTION_DEFAULTS_BY_KEY:
            return False, "Não é permitido eliminar sessões padrão do sistema."

        if self.normalize_session_status(found_row.get("status")) == SESSION_STATUS_ACTIVE_V1:
            return False, "Só é permitido eliminar sessões inativas."

        ok, error_message, _ = self.persist_sidebar_sections(
            session=session,
            sections=payload_rows,
        )

        if not ok:
            return False, error_message or "Não foi possível eliminar a sessão."

        return True, ""

    def create(
        self,
        session: Any,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _, _ = self.save_session(
            session=session,
            mode="create",
            original_section_key="",
            section_label=self._normalize_text(payload.get("label")),
            section_visibility_scope_mode=self._normalize_text(payload.get("visibility_scope_mode")),
            section_status=self._normalize_text(payload.get("status")),
        )

        return ok

    def update(
        self,
        session: Any,
        edit_key: str,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _, _ = self.save_session(
            session=session,
            mode="edit",
            original_section_key=edit_key,
            section_label=self._normalize_text(payload.get("label")),
            section_visibility_scope_mode=self._normalize_text(payload.get("visibility_scope_mode")),
            section_status=self._normalize_text(payload.get("status")),
        )

        return ok

    def move(
        self,
        session: Any,
        edit_key: str,
        direction: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _, _ = self.move_session(
            session=session,
            section_key=edit_key,
            direction=direction,
        )

        return ok

    def delete(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        ok, _ = self.delete_session(
            session=session,
            section_key=edit_key,
        )

        return ok
