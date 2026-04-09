---
phase: 01
slug: v4-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-09
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pytest.ini` (project root) |
| **Quick run command** | `python3 -m pytest tests/neoload_cli_lib/v4/ -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds (new tests only) |

---

## Sampling Rate

- **After every task commit:** `python3 -m pytest tests/neoload_cli_lib/v4/ -x -q`
- **After each wave:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

---

## Phase Requirements → Test Map

| Decision | Behavior | Test File | Automated Command |
|----------|----------|-----------|-------------------|
| D-06 | `v4_endpoint(*segments)` builds correct paths | `test_v4_endpoints.py` | `pytest tests/neoload_cli_lib/v4/test_v4_endpoints.py -x` |
| D-07 | `v4_base()` returns `'v4'` | `test_v4_endpoints.py` | same |
| D-04 | `v4_workspace_params()` raises CliException when no workspace | `test_v4_endpoints.py` | same |
| D-04 | `v4_inject_workspace(data)` raises CliException when no workspace | `test_v4_endpoints.py` | same |
| D-10 | `v4_workspace_params()` returns `{'workspaceId': id}` when workspace set | `test_v4_endpoints.py` | same |
| D-09/D-08 | `v4_list` paginates with pageNumber/pageSize, returns flat list | `test_v4_client.py` | `pytest tests/neoload_cli_lib/v4/test_v4_client.py -x` |
| D-09 | `v4_list` unwraps `items` from envelope | `test_v4_client.py` | same |
| D-10 | `v4_list` auto-injects `workspaceId` as query param | `test_v4_client.py` | same |
| D-11 | `v4_create` injects workspaceId into request body | `test_v4_client.py` | same |
| D-12 | `v4_get` delegates to `rest_crud.get` | `test_v4_client.py` | same |
| D-13 | `v4_update` delegates to `rest_crud.patch` | `test_v4_client.py` | same |
| D-14 | `v4_replace` delegates to `rest_crud.put` | `test_v4_client.py` | same |
| D-15 | `v4_delete` handles empty 202 body (returns None) | `test_v4_client.py` | same |
| D-01 | No existing files modified | git check | `git diff --name-only HEAD` contains only new files |

---

## Wave 0 Gaps (files that must be created by Wave 0 task)

- [ ] `neoload/neoload_cli_lib/v4/__init__.py`
- [ ] `neoload/neoload_cli_lib/v4/v4_endpoints.py`
- [ ] `neoload/neoload_cli_lib/v4/v4_client.py`
- [ ] `tests/neoload_cli_lib/v4/test_v4_endpoints.py`
- [ ] `tests/neoload_cli_lib/v4/test_v4_client.py`
