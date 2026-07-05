# Fase 6 — Motor de regras dinâmicas do processo (Meu Perfil)

## Objetivo

O plano original previa a Fase 6 como a unificação do "motor de processo
dinâmico": suspeitava-se que o bloco `_apply_meu_perfil_subsequent_visibility_v2`
e as suas 13 funções auxiliares privadas em `appgenesis/services/page.py`
(lado de leitura, usado por `get_page_data` para decidir que campos do Meu
Perfil mostrar) fossem uma reimplementação paralela e redundante do motor
genérico já existente em `appgenesis/services/profile.py`
(`normalize_process_subsequent_rules`, `is_process_subsequent_rule_met`,
`get_hidden_process_targets_from_rules`, `filter_process_fields_by_hidden_targets`),
que já é usado pelo lado de escrita (`update_personal_profile` e
`update_dynamic_process_profile` em `routes/profile/profile_handlers.py`).

## Investigação

Comparação função a função confirmou que a hipótese estava **parcialmente
errada**:

- `_apply_meu_perfil_subsequent_visibility_v2` já chama o motor genérico
  `get_hidden_process_targets_from_rules` para o cálculo de campos ocultos
  por grupo (semântica "E": todas as regras de um alvo têm de ser
  satisfeitas para o campo continuar visível).
- As funções `_get_subsequent_rule_trigger_field_v2` /
  `_get_subsequent_rule_target_field_v2` / `_get_subsequent_rule_operator_v2` /
  `_get_subsequent_rule_trigger_value_v2` resolvem exatamente os mesmos
  aliases de chave que `normalize_process_subsequent_rules` já resolve —
  redundantes em teoria, mas operam sobre a lista de regras **não
  normalizada**, o que muda o comportamento em casos de regras malformadas
  (o motor genérico descarta silenciosamente regras sem `trigger_field`/
  `field_key`; a versão V2 não).
- `_is_subsequent_rule_met_v2` usa comparação simples (strip+lower), ao
  contrário de `is_process_subsequent_rule_met`, que aplica remoção de
  acentos (NFD) via `_normalize_process_rule_lookup_text`. Substituir uma
  pela outra mudaria que valores acentuados correspondem — uma mudança de
  comportamento real em produção, sem cobertura de testes que a valide.
- `_target_has_specific_rule_v2` / `_target_has_specific_rule_met_v2` /
  `_filter_meu_perfil_fields_by_subsequent_rules_v2` implementam uma
  semântica adicional **que não existe no motor genérico**: permitir que
  uma regra específica para um campo (semântica "OU": basta uma regra
  satisfeita) substitua a ocultação por grupo/secção calculada pelo motor
  genérico. Isto é lógica de negócio real do Meu Perfil, não duplicação.
- `_build_meu_perfil_visibility_values_v2` e
  `_collect_meu_perfil_subsequent_rules_v2` resolvem valores/roteiros
  específicos do Meu Perfil (consulta a `Member`/`User`, leitura de
  `sidebar_item` com 3 chaves de armazenamento possíveis) — não fazem
  sentido no motor genérico, que é agnóstico da origem dos valores.

**Conclusão:** o bloco V2 não é uma duplicação a eliminar; é uma camada de
orquestração específica do Meu Perfil que já reutiliza o motor genérico
onde é seguro fazê-lo, e acrescenta lógica adicional legítima por cima.
Forçar uma fusão total introduziria risco real de alterar em produção quais
campos do Meu Perfil aparecem/desaparecem (comparação com/sem acentos,
tratamento de regras malformadas), sem nenhum teste que comprove
equivalência — o que viola a regra de preservar comportamento atual.

## Decisão e trabalho realizado

Em vez de fundir a lógica, o bloco foi **movido tal como estava** (sem
nenhuma alteração de comportamento) para
`appgenesis/domains/meu_perfil/visibility.py`, que já é o pacote de domínio
usado para o resto da lógica de Meu Perfil (`use_cases.py`,
`repositories.py`, `schemas.py`). Isto:

- Separa claramente a orquestração específica do Meu Perfil (agora em
  `domains/meu_perfil/`) do motor de regras genérico e agnóstico de
  processo (que continua em `services/profile.py`, partilhado por leitura
  e escrita).
- Não altera nenhuma linha de lógica — apenas localização e a assinatura
  pública da função de entrada, renomeada de `_apply_meu_perfil_subsequent_visibility_v2`
  (privada) para `apply_meu_perfil_subsequent_visibility_v2` (pública, por
  cruzar fronteira de módulo).
- Confirmado por grep que todas as 14 funções do bloco eram usadas
  exclusivamente dentro de `page.py` (nenhum outro consumidor), pelo que a
  mudança tem impacto num único ponto de chamada.
- Removidos dois imports de `services/profile` em `page.py` que ficaram
  sem uso após a mudança: `get_hidden_process_targets_from_rules` (passou a
  ser usado apenas dentro do novo módulo) e `filter_process_fields_by_hidden_targets`
  (já estava sem uso antes desta fase — achado confirmado na Fase 4).

## Técnica de validação usada

- `python -m pyflakes appgenesis/services/page.py appgenesis/domains/meu_perfil/visibility.py`
  — zero erros.
- `python -c "import appgenesis.services.page; import appgenesis.domains.meu_perfil.visibility"`
  — import limpo.
- `pytest -q` completo — 196/196 aprovados (sem alteração face à Fase 5;
  nenhum teste novo foi necessário porque nenhuma lógica mudou).

## Ficheiros alterados/criados

- `appgenesis/domains/meu_perfil/visibility.py` (novo) — bloco V2 movido
  integralmente.
- `appgenesis/services/page.py` (alterado) — bloco V2 removido, import do
  novo módulo adicionado, ponto de chamada atualizado, dois imports mortos
  removidos.

## Riscos

Nenhum risco introduzido em comportamento existente — mudança de
localização apenas, sem alteração de lógica, com todos os 196 testes a
passar sem modificação. O risco residual (documentado, não resolvido nesta
fase, e considerado não compensador face ao risco de regressão) é que a
lógica de matching em `_is_subsequent_rule_met_v2` (sem remoção de acentos)
diverge do motor genérico (com remoção de acentos) e que regras malformadas
são tratadas de forma diferente nos dois motores. Uma futura unificação
completa só deve ser feita com testes de regressão específicos para estes
dois casos de borda antes de qualquer fusão de lógica.
