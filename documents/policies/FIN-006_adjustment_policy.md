# FIN-006: Adjustment Policy

**Policy ID:** FIN-006
**Version:** 1.3
**Effective Date:** 2025-01-15
**Owner:** Finance Department — Controller

## Scope
Governs all financial adjustments including ledger corrections, account reclassifications, and balance adjustments.

## Rules
1. All adjustments must have supporting documentation.
2. Adjustments must be idempotent — executing the same adjustment twice must not create duplicate entries.
3. Adjustments exceeding $500 require Finance Manager approval.
4. Adjustments exceeding $5,000 require Controller approval.
5. Adjustments to revenue accounts require Controller approval regardless of amount.
6. Post-close adjustments require period reopening and Controller approval.

## Thresholds
| Amount | Approver |
|--------|----------|
| $0 – $500 | Finance Analyst |
| $501 – $5,000 | Finance Manager |
| > $5,000 | Controller |
| Revenue accounts | Controller (any amount) |

## Audit Requirements
- Complete before/after state for every adjustment.
- Idempotency key recorded for each adjustment.
- Monthly adjustment summary in close report.
