# Architecture Guidelines

## Goal

Keep refactoring incremental and avoid reintroducing monolithic handlers.

## Layering

- `routes/*`: HTTP only (request parsing, response rendering, redirects).
- `use_cases/*`: flow orchestration and business decisions.
- `repositories/*`: SQLAlchemy data access.
- `services/*`: shared technical/domain utilities used by use cases.

## Rules

- Route handlers should not execute direct SQL queries.
- New features should be added under `use_cases` first, then wired into routes.
- Keep business logic out of templates and browser-only scripts.
- Prefer explicit imports over wildcard imports in new and edited files.
- Use small focused modules; split files when responsibilities diverge.

## Testing

- Add or update tests for each refactor slice.
- Prioritize regression coverage for auth, users, entities, and profile flows.
- Keep unit tests for normalization/validation logic close to use cases.

