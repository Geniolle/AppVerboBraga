# NOTA (Issue #28, 2026-07-06): este pacote continha um hub de wildcard imports,
# mantido desde a Fase 2 como compatibilidade "por seguranca". Reconfirmado nesta
# issue (segunda validacao independente, apos a de 2026-07-05): nenhum ficheiro do
# repositorio, incluindo testes e scripts, importa de "appgenesis.services" ao
# nivel do pacote (nem wildcard nem nomeado) — todos os consumidores usam imports
# explicitos dos submodulos individuais (ex.: appgenesis.services.auth). Com prova
# de zero uso, os wildcard imports foram removidos. Detalhe em
# docs/refactoring/issue-28-legacy-hubs-report.md.
