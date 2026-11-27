"""Sessoes criadas por entidade legado: dono por entity_number (regras puras)."""

from appgenesis.services.sidebar_section_ownership import (
    can_manage_section,
    filter_sections_for_entity,
    get_section_owner_map,
    is_section_visible_to_entity,
)

OWNER_MAP = {"departamentos": 2002, "pastoral": 2003}
SISTEMA = {"key": "geral", "label": "Geral"}


def test_owner_map_reads_entity_number_as_int_and_skips_invalid():
    menu_config = {
        "sidebar_section_owners": {"Departamentos": "2002", "x": "nao_numero", "": 9}
    }
    owners = get_section_owner_map(menu_config)
    assert owners == {"departamentos": 2002}


def test_owner_map_empty_when_missing():
    assert get_section_owner_map({}) == {}
    assert get_section_owner_map(None) == {}


def test_system_section_visible_to_everyone():
    assert is_section_visible_to_entity(OWNER_MAP, "geral", 2002)
    assert is_section_visible_to_entity(OWNER_MAP, "geral", 1000)


def test_legacy_section_visible_only_to_creator():
    assert is_section_visible_to_entity(OWNER_MAP, "departamentos", 2002)
    assert not is_section_visible_to_entity(OWNER_MAP, "departamentos", 2003)
    assert not is_section_visible_to_entity(OWNER_MAP, "departamentos", 1000)


def test_filter_keeps_system_and_own_sections_only():
    sections = [
        SISTEMA,
        {"key": "departamentos", "label": "Departamentos"},
        {"key": "pastoral", "label": "Pastoral"},
    ]
    kept = filter_sections_for_entity(sections, OWNER_MAP, 2002)
    assert [s["key"] for s in kept] == ["geral", "departamentos"]


def test_owner_tenant_does_not_see_legacy_sections():
    sections = [SISTEMA, {"key": "departamentos", "label": "Departamentos"}]
    kept = filter_sections_for_entity(sections, OWNER_MAP, 1000)
    assert [s["key"] for s in kept] == ["geral"]


def test_manage_system_section_only_for_tenant_owner():
    assert can_manage_section(OWNER_MAP, "geral", 1000, is_tenant_owner=True)
    assert not can_manage_section(OWNER_MAP, "geral", 2002, is_tenant_owner=False)


def test_manage_legacy_section_only_for_creator():
    assert can_manage_section(OWNER_MAP, "departamentos", 2002, is_tenant_owner=False)
    assert not can_manage_section(OWNER_MAP, "departamentos", 2003, is_tenant_owner=False)
    # Owner nao gere sessoes criadas por legado.
    assert not can_manage_section(OWNER_MAP, "departamentos", 1000, is_tenant_owner=True)


def test_manage_denied_without_entity_number():
    assert not can_manage_section(OWNER_MAP, "departamentos", None, is_tenant_owner=False)
