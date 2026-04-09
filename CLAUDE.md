# NeoLoad CLI — Project Guidelines

## Git Branch Convention

Each phase must execute on its own dedicated branch:

- **Format:** `GSD-[phase-slug]`
- **Examples:** `GSD-v4-foundation`, `GSD-core-resources`, `GSD-analytics-trends`

**Rules:**
- Create the branch from `master` (or the previous phase's branch if there's a hard dependency) at the start of phase execution
- All commits for a phase land on that branch
- Do not execute phase work on `master` or the `gsd` planning branch
- Phase branch is the PR source when the phase is complete

## Code Conventions

- All v4 features are additive — zero modifications to existing v2/v3 command or library files
- v4 command files use `v4_` file prefix (`v4_tests.py` → `neoload v4-tests`)
- Shared v4 helpers live in `neoload/neoload_cli_lib/v4/`
- workspaceId is mandatory for v4 workspace-scoped operations (auto-injected, not opt-in)
- No new dependencies — use only packages already in `setup.py install_requires`
