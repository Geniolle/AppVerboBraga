# Refatoracao - Abas globais do Administrativo -> Menu

Objetivo: centralizar a regra das abas internas Geral, Configuracao dos campos e Campos adicionais.

Regra: essas abas aparecem somente quando o utilizador edita um processo dentro de Administrativo -> Menu.

A regra nao depende do nome do processo. Exemplos: Meu perfil, Funcionarios, Empresa, Departamentos ou qualquer nova pasta criada dentro de Administrativo -> Menu.

Estrutura criada:
- appverbo/process_settings/
- static/js/process_settings/
- tests/process_settings/

Esta V1 cria a base isolada da refatoracao. A integracao no route/view e no template deve ser feita na etapa seguinte.
