---
phase: "08-users-identity"
plan: "08-01"
subsystem: "users-identity"
tags: ["v4", "users", "identity", "sso", "ldap", "sessions", "settings"]
dependency_graph:
  requires: ["01-01"]
  provides: ["v4-users", "v4-me", "v4-sessions", "v4-settings", "v4-sso", "v4-ldap"]
  affects: []
tech_stack:
  added: []
  patterns: ["click-command", "rest_crud-passthrough", "plain-v4-endpoint"]
key_files:
  created:
    - neoload/commands/v4_users.py
    - neoload/commands/v4_me.py
    - neoload/commands/v4_sessions.py
    - neoload/commands/v4_settings.py
    - neoload/commands/v4_sso.py
    - neoload/commands/v4_ldap.py
  modified: []
decisions:
  - "No workspaceId injection on any endpoint — all 6 files use plain v4_endpoint() calls only"
  - "workspaces-add uses --workspace-id option or --file body (flexible input)"
  - "search-user-groups uses --login option to supply path segment (not positional id)"
metrics:
  duration: "~8 minutes"
  completed: "2026-04-10"
  tasks_completed: 6
  files_created: 6
  files_modified: 0
---

# Phase 8 Plan 1: Users and Identity Summary

Six v4 CLI command files covering user management, personal profile, sessions, account settings, SSO configuration, and LDAP integration — all using plain `v4_endpoint()` with no workspace injection.

## Tasks Completed

| Task | File | Commit | Subcommands |
|------|------|--------|-------------|
| 1 | v4_users.py | 61f9be6 | ls, create, get, patch, delete, workspaces-ls, workspaces-add, workspaces-remove |
| 2 | v4_me.py | c393582 | get, patch, password, tokens-ls, tokens-create, tokens-delete, features |
| 3 | v4_sessions.py | aa93c35 | create, delete |
| 4 | v4_settings.py | 2bd5108 | get, patch, information, subscription |
| 5 | v4_sso.py | fe6eada | config-get, config-create, config-put, config-patch, config-delete, config-status, saml-idp-get, saml-idp-put, saml-idp-delete, saml-sp-metadata |
| 6 | v4_ldap.py | 551565c | config-get, config-patch, entities-ls, entities-create, entities-patch, entities-delete, search-users, search-groups, search-user-groups |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all commands wire directly to live API endpoints via `rest_crud`.

## Threat Flags

None — no new auth paths, network endpoints beyond the API surface described in the plan, or schema changes at trust boundaries.

## Self-Check: PASSED

Files exist:
- FOUND: neoload/commands/v4_users.py
- FOUND: neoload/commands/v4_me.py
- FOUND: neoload/commands/v4_sessions.py
- FOUND: neoload/commands/v4_settings.py
- FOUND: neoload/commands/v4_sso.py
- FOUND: neoload/commands/v4_ldap.py

Commits exist (via git log):
- FOUND: 61f9be6 (v4_users.py)
- FOUND: c393582 (v4_me.py)
- FOUND: aa93c35 (v4_sessions.py)
- FOUND: 2bd5108 (v4_settings.py)
- FOUND: fe6eada (v4_sso.py)
- FOUND: 551565c (v4_ldap.py)
