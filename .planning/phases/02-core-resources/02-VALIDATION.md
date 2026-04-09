---
phase: 2
slug: core-resources
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-09
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `setup.cfg` / `pytest.ini` (existing) |
| **Quick run command** | `pytest tests/commands/test_v4_*.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/commands/test_v4_*.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | tests-ls | — | N/A | unit | `pytest tests/commands/test_v4_tests.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | tests-create | — | N/A | unit | `pytest tests/commands/test_v4_tests.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 2 | results-ls | — | N/A | unit | `pytest tests/commands/test_v4_results.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 2 | test-executions | — | N/A | unit | `pytest tests/commands/test_v4_test_executions.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 3 | workspaces | — | N/A | unit | `pytest tests/commands/test_v4_workspaces.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 3 | zones | — | N/A | unit | `pytest tests/commands/test_v4_zones.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/commands/test_v4_tests.py` — stubs for v4-tests subcommands
- [ ] `tests/commands/test_v4_results.py` — stubs for v4-results subcommands
- [ ] `tests/commands/test_v4_test_executions.py` — stubs for v4-test-executions subcommands
- [ ] `tests/commands/test_v4_workspaces.py` — stubs for v4-workspaces subcommands
- [ ] `tests/commands/test_v4_zones.py` — stubs for v4-zones subcommands

*Note: Existing pytest infrastructure covers framework requirement. Only test stub files need creating in Wave 0.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `--wait` blocks until test completion | test-executions create | Requires live NeoLoad Web instance | Run `neoload v4-test-executions create --test-id <id> --wait`; verify it blocks until terminal status |
| Live log streaming | test-executions logs | Requires active test execution | Run during an active test; verify lines appear incrementally |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
