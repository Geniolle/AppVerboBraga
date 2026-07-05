# NOTA (Fase 2 - refactor/appgenesis-process-architecture): hub de wildcard imports.
# Validado em 2026-07-05: nenhum ficheiro do repositorio (incluindo testes) importa
# de "appgenesis.services" ao nivel do pacote (nem wildcard nem nomeado); todos os
# consumidores usam agora imports explicitos dos submodulos individuais.
# Mantido temporariamente por compatibilidade; candidato a remocao numa fase futura
# apos nova validacao de uso.
from appgenesis.services.user_system import *  # noqa: F403,F401
from appgenesis.services.auth import *  # noqa: F403,F401
from appgenesis.services.phone_country import *  # noqa: F403,F401
from appgenesis.services.entities import *  # noqa: F403,F401
from appgenesis.services.navigation_context import *  # noqa: F403,F401
from appgenesis.services.page import *  # noqa: F403,F401
from appgenesis.services.permissions import *  # noqa: F403,F401
from appgenesis.services.profile import *  # noqa: F403,F401
from appgenesis.services.session import *  # noqa: F403,F401
from appgenesis.services.i18n import *  # noqa: F403,F401
from appgenesis.services.whatsapp import *  # noqa: F403,F401
