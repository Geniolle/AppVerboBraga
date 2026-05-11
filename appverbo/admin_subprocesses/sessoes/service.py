from __future__ import annotations

####################################################################################
# (1) IMPORTS
####################################################################################

from typing import Any

from appverbo.admin_subprocesses.sessoes.common import (
    build_sessoes_context_v2,
    get_sessoes_column_keys_v2,
    get_sessoes_columns_v2,
    get_sessoes_config_v2,
    get_sessoes_field_keys_v2,
    get_sessoes_fields_v2,
    get_sessoes_key_v2,
    get_sessoes_title_v2,
    is_sessoes_config_v2,
)


####################################################################################
# (2) SERVIÇO DO SUBPROCESSO SESSÕES
####################################################################################

class SessoesServiceV2:
    def get_config_v2(self) -> Any:
        return get_sessoes_config_v2()

    def get_key_v2(self) -> str:
        return get_sessoes_key_v2()

    def get_title_v2(self) -> str:
        return get_sessoes_title_v2()

    def get_fields_v2(self) -> list[Any]:
        return get_sessoes_fields_v2()

    def get_columns_v2(self) -> list[Any]:
        return get_sessoes_columns_v2()

    def get_field_keys_v2(self) -> list[str]:
        return get_sessoes_field_keys_v2()

    def get_column_keys_v2(self) -> list[str]:
        return get_sessoes_column_keys_v2()

    def is_config_v2(self, config: Any) -> bool:
        return is_sessoes_config_v2(config)

    def build_context_v2(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return build_sessoes_context_v2(context)

    def build_diagnostic_summary_v2(self) -> dict[str, Any]:
        return {
            "subprocess_key": self.get_key_v2(),
            "subprocess_title": self.get_title_v2(),
            "field_keys": self.get_field_keys_v2(),
            "column_keys": self.get_column_keys_v2(),
            "uses_generic_v2_crud": True,
            "has_custom_create_service": False,
            "has_custom_delete_service": False,
            "has_custom_resend_service": False,
        }


####################################################################################
# (3) FACTORY DO SERVIÇO
####################################################################################

def get_sessoes_service_v2() -> SessoesServiceV2:
    return SessoesServiceV2()


####################################################################################
# (4) COMPATIBILIDADE COM NOMES V1
####################################################################################

class SessoesServiceV1(SessoesServiceV2):
    def get_config_v1(self) -> Any:
        return self.get_config_v2()

    def get_key_v1(self) -> str:
        return self.get_key_v2()

    def get_title_v1(self) -> str:
        return self.get_title_v2()

    def get_fields_v1(self) -> list[Any]:
        return self.get_fields_v2()

    def get_columns_v1(self) -> list[Any]:
        return self.get_columns_v2()

    def build_context_v1(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.build_context_v2(context)


def get_sessoes_service_v1() -> SessoesServiceV1:
    return SessoesServiceV1()
