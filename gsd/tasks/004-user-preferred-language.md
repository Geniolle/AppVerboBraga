# Task 004: User Preferred Language

Status: completed
Updated: 2026-07-03

## Objective

Persist the authenticated user's language preference in the database while keeping Task 003 cookie/session behavior compatible.

## Scope

- Create the task record for user preferred language
- Add `preferred_language` to the correct user model
- Add a safe Alembic migration for existing data
- Keep `pt` as the canonical fallback
- Resolve language before login from query, session, cookie, then fallback
- Resolve language after login from user profile, session, cookie, then fallback
- Persist the chosen pre-login language into the user profile when missing
- Reuse the same logic for local login, signup auto-login, and OAuth login
- Keep session/cookie synchronized with the resolved language
- Update `gsd/STATE.md`
- Update `gsd/DECISIONS.md` with the durable persistence decision

## Out Of Scope

- Full application translation
- New authenticated language-management UI
- New generic settings API for language changes
- Docker changes
- Supabase changes
- Next.js migration
- Authentication redesign
- Entity-level language storage

## Checklist

- [x] `gsd/tasks/004-user-preferred-language.md` exists
- [x] `users.preferred_language` exists in the model
- [x] The allowed values are `pt`, `en`, `es`, and `fr`
- [x] The migration adds the column without dropping existing user data
- [x] Pre-login language resolution remains query -> session -> cookie -> `pt`
- [x] Post-login language resolution now uses profile -> session -> cookie -> `pt`
- [x] Successful local login syncs language with the user profile
- [x] Successful OAuth login syncs language with the user profile
- [x] `gsd/STATE.md` reflects the new persisted-language state
- [x] `gsd/DECISIONS.md` records the canonical user-level storage decision
- [x] No unsafe authenticated language-change route was introduced

## Completion Criteria

This task is complete when:

- the database can store a user's preferred language safely
- missing profile language values are initialized from the pre-login selection
- invalid stored values fall back to `pt`
- local login and OAuth continue to work with the current flow
- session and cookie remain compatible with Task 003
- the implementation stays localized and safe for future web/mobile evolution
