# FIN-012: Accounting Period Policy

**Policy ID:** FIN-012
**Version:** 1.2
**Effective Date:** 2025-01-15
**Owner:** Finance Department — Controller

## Scope
Governs the lifecycle of accounting periods including creation, opening, closing, and reopening.

## Rules
1. Each accounting period covers one calendar month.
2. Only one period may be actively closing at a time.
3. Periods progress through statuses: OPEN → CLOSING → CLOSED → REOPENED (if needed).
4. Duplicate periods are prevented by unique constraint on year-month code.
5. Transactions cannot be posted to closed periods.
6. Financial decisions are blocked for closed periods.
7. Reopening requires Controller approval and documented reason.

## Period Statuses
- **OPEN**: Active period accepting transactions and decisions
- **CLOSING**: Final reconciliation and report generation in progress
- **CLOSED**: Period is finalized, immutable unless reopened
- **REOPENED**: Previously closed period opened for corrections
