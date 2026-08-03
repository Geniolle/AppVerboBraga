# Handlers das 6 abas de configuração de processo (Fase 8 da refatoração de
# process-settings), separados por domínio. A importação dos submódulos abaixo
# é o que regista as rotas no `router` partilhado (mesmo padrão de efeito
# colateral usado por appgenesis/routes/profile/router.py para settings_handlers).
from appgenesis.routes.profile.process_settings import (
    common,
    general_handlers,
    additional_field_handlers,
    field_handlers,
    quantity_field_handlers,
    list_handlers,
    subsequent_field_handlers,
)

__all__ = [
    "common",
    "general_handlers",
    "additional_field_handlers",
    "field_handlers",
    "quantity_field_handlers",
    "list_handlers",
    "subsequent_field_handlers",
]
