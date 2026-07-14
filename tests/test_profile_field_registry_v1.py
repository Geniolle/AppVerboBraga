from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O REGISTRY DO MEU PERFIL DEVE EXPOR AS FUNCOES CANONICAS
####################################################################################

def test_profile_field_registry_v1_exposes_expected_api() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "modules" / "profile_field_registry_v1.js").read_text(
        encoding="utf-8"
    )

    assert "window.AppGenesisProfileFieldRegistryV1 = {" in script_text
    assert "normalizeFieldKey" in script_text
    assert "resolveControlName" in script_text
    assert "resolveFieldKeyFromControlName" in script_text
    assert "findProfileControl" in script_text
    assert "collectProfileValues" in script_text
    assert "getProfileForm" in script_text
    assert "getCurrentProfileSection" in script_text


####################################################################################
# (2) NEW_USER DEVE USAR O REGISTRY PARA MENOS MAPAS DUPLICADOS
####################################################################################

def test_new_user_runtime_delegates_profile_field_mapping_to_registry() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "window.AppGenesisProfileFieldRegistryV1" in script_text
    assert "collectProfileValues(formEl)" in script_text
    assert "resolveControlName(fieldKey)" in script_text


####################################################################################
# (3) O ORDENADOR DE CAMPOS DO MEU PERFIL DEVE REUTILIZAR O REGISTRY
####################################################################################

def test_profile_field_order_reuses_registry_helpers() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "modules" / "profile_field_order.js").read_text(
        encoding="utf-8"
    )

    assert "window.AppGenesisProfileFieldRegistryV1" in script_text
    assert "profileFieldRegistryV1.getProfileForm(document)" in script_text
    assert "profileFieldRegistryV1.findProfileControl(form, fieldKey)" in script_text


####################################################################################
# (4) TEMPLATE: O REGISTRY NOVO TEM DE CARREGAR ANTES DO RUNTIME E DO ORDER MODULE
####################################################################################

def test_new_user_template_loads_profile_registry_before_runtime_and_order_module() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    registry_index = template_text.index('src="/static/js/modules/profile_field_registry_v1.js?v=20260714-profile-field-registry-v1"')
    runtime_index = template_text.index('src="/static/js/new_user.js?v=20260714-new-user-runtime-v2"')
    order_index = template_text.index('src="/static/js/modules/profile_field_order.js?v=20260714-profile-field-registry-v1"')

    assert registry_index < runtime_index < order_index
