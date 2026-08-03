# Relatório — Avaliação de Unificação da Visibilidade V2 do Meu Perfil (Issue #26)

Updated: 2026-07-05

## Contexto

A Issue #26 pede a avaliação de se o motor de visibilidade V2 do Meu Perfil (`apply_meu_perfil_subsequent_visibility_v2`) deve ser unificado com o motor genérico de `services/profile.py`.

## Estrutura Atual

### Motor Genérico — `services/profile.py`

`get_hidden_process_targets_from_rules(rules, values_by_field)` → devolve o conjunto de chaves de campos a ocultar, baseado nas regras de subsequência genéricas.

### Motor V2 do Meu Perfil — `domains/meu_perfil/visibility.py`

`apply_meu_perfil_subsequent_visibility_v2(session, actor_user_id, sidebar_item, actor_profile_fields, visible_fields, field_header_map)` → orquestra o motor genérico com lógica específica:

1. Recolhe regras de subsequência de múltiplas chaves de armazenamento (`process_subsequent_fields`, `subsequent_fields`, `process_subsequent_rules`).
2. Constrói o dicionário de valores do utilizador incluindo campos do `Member` (nome, telefone, email, país, data de nascimento).
3. Chama `get_hidden_process_targets_from_rules` do motor genérico.
4. Filtra os campos visíveis respeitando regras de header e subsequência.

## Diagnóstico

A Fase 6 da refatoração original investigou esta questão e confirmou explicitamente:
> "confirmado que não era duplicação mas orquestração legítima adicional. Bloco movido (sem alteração de lógica) para `domains/meu_perfil/visibility.py`." — `docs/refactoring/final-summary.md`, linha 50-54.

### Por que não é duplicação

| Aspeto | Motor Genérico | Motor V2 do Meu Perfil |
|---|---|---|
| Input | `rules`, `values_by_field` | `session`, `actor_user_id`, `sidebar_item`, `actor_profile_fields`, `visible_fields`, `field_header_map` |
| Responsabilidade | Calcular campos ocultos por regras | Orquestrar: coletar regras, construir valores do actor, filtrar campo por campo |
| Contexto | Agnóstico de domínio | Específico do Meu Perfil |
| Lida com headers de campo | ❌ | ✅ |
| Lê base de dados | ❌ | ✅ (Member, User) |
| Trata múltiplas chaves de armazenamento | ❌ | ✅ |

## Decisão

**Não unificar.** A separação está correta e intencional:
- O motor genérico resolve regras de subsequência (função pura, agnóstica de domínio).
- O motor V2 do Meu Perfil é a camada de orquestração específica ao domínio.
- Unificar forçaria o motor genérico a ter conhecimento de `Member`, `User` e da estrutura de dados específica do Meu Perfil — quebrando o encapsulamento.

## Caminho Documentado

A separação `services/profile.py → domains/meu_perfil/visibility.py` é o contrato correto. Futuras extensões ao motor de visibilidade do Meu Perfil devem:
1. Manter a lógica de orquestração específica em `domains/meu_perfil/visibility.py`.
2. Usar `get_hidden_process_targets_from_rules` do motor genérico como suporte.
3. Não adicionar lógica de domínio ao motor genérico.

## Validação

- Nenhuma alteração de código foi necessária.
- A separação já está implementada e testada.
- `pytest -q` (sem Selenium): 180 passed, 0 falhados.
