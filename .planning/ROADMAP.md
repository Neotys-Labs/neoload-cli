# Roadmap — NeoLoad CLI v4 API Expansion

## Milestone 1: Full v4 API Coverage

### Phase 1: v4 API Foundation
**Goal:** Create the shared v4 helper package that all v4 commands depend on
**Status:** Not Started
**Depends on:** —

- v4_endpoints.py: path builders, workspace query/body injection helpers
- v4_client.py: thin wrappers over rest_crud using v4 paths
- Unit tests for the helper layer

### Phase 2: Core Resources
**Goal:** v4 commands for tests, results, test-executions, workspaces, zones
**Status:** Not Started
**Depends on:** Phase 1

- v4-tests: ls, create, get, patch, delete, scenario-get, scenario-update
- v4-results: ls, get, patch, delete, contexts, elements, monitors, statistics, timeseries, search-criteria
- v4-test-executions: create, get, cancel, force-cancel, logs
- v4-workspaces: ls, create, get, patch, delete, members-ls, members-add, members-remove, subscription
- v4-zones: ls, create, get, patch, delete

### Phase 3: Analytics and Trends
**Goal:** v4 commands for result analytics and test trends
**Status:** Not Started
**Depends on:** Phase 2

- v4-analytics: element-values, element-timeseries, element-percentiles, monitor-values, monitor-timeseries, intervals CRUD, interval-generation, report
- v4-trends: get, patch, config-get, config-put, config-patch, elements

### Phase 4: Events and SLAs
**Goal:** v4 commands for result events and SLA data
**Status:** Not Started
**Depends on:** Phase 2

- v4-events: ls, create, get, patch, delete, errors, statistics, content
- v4-slas: ls

### Phase 5: Operations
**Goal:** v4 commands for webhooks, SCM, reservations, deletion policies
**Status:** Not Started
**Depends on:** Phase 1

- v4-webhooks: ls, create, get, patch, delete, validate
- v4-scm-repositories: ls, create, get, patch, delete, refs, checkout, checkout-status
- v4-reservations: ls, create, get, patch, delete
- v4-deletion-policies: ls, create, get, patch, delete, dry-run

### Phase 6: Infrastructure
**Goal:** v4 commands for proxies, infrastructure providers, guaranteed resources
**Status:** Not Started
**Depends on:** Phase 1

- v4-proxies: ls, create, patch, delete
- v4-infrastructure-providers: ls, create, patch, delete
- v4-guaranteed-resources: ls, create, patch, delete (per-workspace)

### Phase 7: License Management
**Goal:** v4 commands for license and lease operations
**Status:** Not Started
**Depends on:** Phase 1

- v4-license: get, install, leases-ls, leases-create, leases-get, activation-request, deactivation-request, forced-release, release

### Phase 8: Users and Identity
**Goal:** v4 commands for user management, profile, sessions, settings, SSO, LDAP
**Status:** Not Started
**Depends on:** Phase 1

- v4-users: ls, create, get, patch, delete, workspaces-ls, workspaces-add, workspaces-remove
- v4-me: get, patch, password, tokens-ls, tokens-create, tokens-delete, features
- v4-sessions: create, delete
- v4-settings: get, patch, information, subscription
- v4-sso: config-get, config-create, config-put, config-patch, config-delete, config-status, saml-idp-get, saml-idp-put, saml-idp-delete, saml-sp-metadata
- v4-ldap: config-get, config-patch, entities-ls, entities-create, entities-patch, entities-delete, search-users, search-groups, search-user-groups

### Phase 9: Test Coverage
**Goal:** Unit tests for all v4 commands and helpers
**Status:** Not Started
**Depends on:** Phases 1-8

- Tests for v4_endpoints and v4_client helpers
- Tests for each v4 command module using existing mock pattern
