# Architecture plan

## Foundation delivered

`DATABASE_URL` configures the source-of-truth datastore. The backend now persists user accounts, password hashes, signed sessions, session revocations, roles, and audit events. Secrets are backend environment variables only.

Roles are `ADMIN`, `FINANCE_ADMIN`, `FINANCE_MANAGER`, `ANALYST`, and `VIEWER`. Registration creates an `ANALYST`; only an `ADMIN` can list, update, deactivate, change roles, or delete accounts. The first administrator can be bootstrapped through backend environment variables.

## Next domain increments

1. Add migrations and financial-period, transaction, evidence, approval, journal-entry, and audit models.
2. Build deterministic reconciliation and state-transition services plus controlled accounting-provider adapters.
3. Add LangGraph investigation workflows that recommend but never directly modify accounting records.
4. Connect protected UI pages through React Query and implement human approval workflows.
