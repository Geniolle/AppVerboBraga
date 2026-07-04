# Task 003: Login Multi-Language

Status: completed
Updated: 2026-07-03

## Objective

Add initial multi-language support to the current login experience for `pt`, `en`, `es`, and `fr` without changing the current authentication architecture.

## Scope

- Create the task record for login multi-language
- Add a small translation structure under `appverbo/i18n/`
- Add a reusable helper to resolve and persist the active language
- Use `pt` as the default fallback language
- Expose a simple translation function to the login template
- Add a visible language selector to the current login experience
- Translate the main login texts and login-related runtime messages
- Keep the current FastAPI + Jinja login flow intact
- Update `gsd/STATE.md`
- Update `gsd/DECISIONS.md` with any durable technical choice from this step

## Out Of Scope

- Rewriting the authentication flow
- Changing Docker
- Changing database structure
- Adding a user language column
- Replacing Jinja
- Introducing Next.js
- Changing Supabase direction
- Translating the whole application
- Refactoring unrelated templates or routes

## Checklist

- [x] `gsd/tasks/003-login-multi-language.md` exists
- [x] Translation files exist for `pt`, `en`, `es`, and `fr`
- [x] A reusable language helper resolves cookie/session language with `pt` fallback
- [x] The login template receives a simple translation function
- [x] The login page shows a visible language selector
- [x] The selected language persists across refresh through session/cookie
- [x] Main login labels and OAuth labels are translated
- [x] `gsd/STATE.md` reflects the status of this task
- [x] `gsd/DECISIONS.md` records the durable choice for language persistence

## Completion Criteria

This task is complete when:

- `GET /login` can render with `pt`, `en`, `es`, and `fr`
- the language selection persists after refresh
- local login behavior remains unchanged apart from translated text
- OAuth buttons remain visible in the current login UI
- the implementation stays localized and reusable for future templates
