from __future__ import annotations

from dataclasses import dataclass

MEU_PERFIL_MENU_KEY_V1 = "meu_perfil"
MEU_PERFIL_MENU_ALIASES_V1 = ("perfil", "documentos")

MEU_PERFIL_TAB_PESSOAL_V1 = "pessoal"
MEU_PERFIL_TAB_MORADA_V1 = "morada"
MEU_PERFIL_TAB_TREINAMENTO_V1 = "treinamento"

MEU_PERFIL_TABS_ORDER_V1 = (
    MEU_PERFIL_TAB_PESSOAL_V1,
    MEU_PERFIL_TAB_MORADA_V1,
    MEU_PERFIL_TAB_TREINAMENTO_V1,
)

MEU_PERFIL_TAB_TARGETS_V1 = {
    MEU_PERFIL_TAB_PESSOAL_V1: "#perfil-pessoal-card",
    MEU_PERFIL_TAB_MORADA_V1: "#perfil-morada-card",
    MEU_PERFIL_TAB_TREINAMENTO_V1: "#dados-treinamento-card",
}


@dataclass(frozen=True)
class MeuPerfilTabV1:
    key: str
    label: str
    target: str

    def to_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "label": self.label,
            "target": self.target,
        }


MEU_PERFIL_TABS_V1 = (
    MeuPerfilTabV1(MEU_PERFIL_TAB_PESSOAL_V1, "Pessoal", MEU_PERFIL_TAB_TARGETS_V1[MEU_PERFIL_TAB_PESSOAL_V1]),
    MeuPerfilTabV1(MEU_PERFIL_TAB_MORADA_V1, "Morada", MEU_PERFIL_TAB_TARGETS_V1[MEU_PERFIL_TAB_MORADA_V1]),
    MeuPerfilTabV1(
        MEU_PERFIL_TAB_TREINAMENTO_V1,
        "Treinamento",
        MEU_PERFIL_TAB_TARGETS_V1[MEU_PERFIL_TAB_TREINAMENTO_V1],
    ),
)

