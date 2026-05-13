from __future__ import annotations

from typing import Any


# APPVERBO_PAGINA_DEFAULT_PROTECTED_AREA_V1_START
# Regra central e protegida do estado padrão da página.
#
# Objetivo:
# - refresh normal do browser deve voltar para HOME / Sessão Geral;
# - retorno após salvar/criar deve preservar o contexto;
# - ações explícitas, como Exibir/Editar, devem preservar o contexto da ação.
#
# Não alterar esta área durante correções de subprocessos sem validar o contrato em:
# scripts/check_pagina_default_contract_v1.py
# APPVERBO_PAGINA_DEFAULT_PROTECTED_AREA_V1_END


def _normalizar_texto_v1(value: Any) -> str:
    return str(value or "").strip()


def _normalizar_lower_v1(value: Any) -> str:
    return _normalizar_texto_v1(value).lower()


def _normalizar_menu_v1(value: Any) -> str:
    menu = _normalizar_lower_v1(value)

    aliases = {
        "": "home",
        "inicio": "home",
        "início": "home",
        "sessao_geral": "home",
        "sessão_geral": "home",
        "geral": "home",
    }

    return aliases.get(menu, menu or "home")


def _valor_booleano_explicito_v1(value: Any) -> bool:
    texto = _normalizar_lower_v1(value)

    return texto in {
        "0",
        "1",
        "true",
        "false",
        "sim",
        "nao",
        "não",
        "yes",
        "no",
        "on",
        "off",
    }


def resolver_pagina_default_v1(
    *,
    resolved_menu: str,
    resolved_admin_tab: str,
    resolved_profile_tab: str,
    parsed_user_edit_id: int | None,
    user_view: str,
    parsed_entity_edit_id: int | None,
    entity_view: str,
    clean_settings_edit_key: str,
    clean_settings_action: str,
    clean_target_from_query: str,
    clean_profile_section_from_query: str,
    clean_dynamic_section_from_query: str,
    sidebar_section_edit_key: str,
    is_post_save_return: bool,
) -> dict[str, Any]:
    menu_atual = _normalizar_menu_v1(resolved_menu)
    admin_tab_atual = _normalizar_lower_v1(resolved_admin_tab)
    profile_tab_atual = _normalizar_lower_v1(resolved_profile_tab)
    target_atual = _normalizar_texto_v1(clean_target_from_query)
    profile_section_atual = _normalizar_lower_v1(clean_profile_section_from_query)
    dynamic_section_atual = _normalizar_texto_v1(clean_dynamic_section_from_query)
    settings_edit_key_atual = _normalizar_texto_v1(clean_settings_edit_key)
    settings_action_atual = _normalizar_lower_v1(clean_settings_action)
    sidebar_section_edit_key_atual = _normalizar_lower_v1(sidebar_section_edit_key)

    acao_explicita_utilizador = (
        menu_atual == "administrativo"
        and admin_tab_atual == "utilizador"
        and parsed_user_edit_id is not None
        and _valor_booleano_explicito_v1(user_view)
    )

    acao_explicita_entidade = (
        menu_atual == "administrativo"
        and admin_tab_atual == "entidade"
        and parsed_entity_edit_id is not None
        and _valor_booleano_explicito_v1(entity_view)
    )

    acao_explicita_settings = bool(
        settings_edit_key_atual
        or settings_action_atual in {"toggle", "edit", "delete", "create"}
    )

    acao_explicita_sidebar = bool(sidebar_section_edit_key_atual)
    acao_explicita_secao = bool(profile_section_atual or dynamic_section_atual)

    preservar_contexto_no_refresh = bool(
        is_post_save_return
        or acao_explicita_utilizador
        or acao_explicita_entidade
        or acao_explicita_settings
        or acao_explicita_sidebar
        or acao_explicita_secao
    )

    return {
        "version": "APPVERBO_PAGINA_DEFAULT_V1",
        "refresh_home_url": "/users/new?menu=home",
        "refresh_home_menu": "home",
        "refresh_home_target": "#home-summary-card",
        "current_menu": menu_atual,
        "current_admin_tab": admin_tab_atual,
        "current_profile_tab": profile_tab_atual,
        "current_target": target_atual,
        "is_post_save_return": bool(is_post_save_return),
        "explicit_user_action": acao_explicita_utilizador,
        "explicit_entity_action": acao_explicita_entidade,
        "explicit_settings_action": acao_explicita_settings,
        "explicit_sidebar_action": acao_explicita_sidebar,
        "explicit_section_action": acao_explicita_secao,
        "preserve_on_browser_refresh": preservar_contexto_no_refresh,
    }
