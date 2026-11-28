"""O card de Dados da empresa serve a aba Administrativo > Dados da empresa e o menu Empresa.

Depois do #347 o card ficou so com scope "administrativo" e o menu Empresa (ainda no sidebar)
abria vazio: a aba "Dados da empresa" apontava para um card escondido.
"""

import re
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "new_user.html"


def test_empresa_card_is_scoped_to_administrativo_and_empresa() -> None:
    tag = re.search(r'<section id="empresa-card"[^>]*>', TEMPLATE.read_text(encoding="utf-8")).group(0)
    scopes = set(re.search(r'data-menu-scope="([^"]*)"', tag).group(1).split(","))
    assert {"administrativo", "empresa"} <= scopes
    # Com initial_menu=empresa o card nao pode nascer escondido.
    assert "initial_menu != 'empresa' and" in tag
