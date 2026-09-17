# FIN-008: Reconciliation Policy

**Policy ID:** FIN-008
**Version:** 2.1
**Effective Date:** 2025-06-01
**Owner:** Finance Department — Controller

## Scope
Governs all financial reconciliation activities including invoice, bank, payment, and ledger reconciliation.

## Rules
1. All transactions must be reconciled before the accounting period is closed.
2. Reconciliation must be performed deterministically using exact amounts, dates, and reference IDs.
3. Tolerance for automatic matching is $0.50 for rounding differences.
4. Unmatched items must be investigated within 5 business days.
5. Bank reconciliation must be completed within 3 business days of statement receipt.
6. Discrepancies exceeding $100 must have an investigation record.
7. The reconciliation engine must never use AI/LLM for arithmetic or amount calculations.
8. All reconciliation results must be persisted to the database as the source of truth.

## Reconciliation Types
- **Invoice Reconciliation**: Match payments to invoices
- **Bank Reconciliation**: Match bank transactions to internal payment records
- **Ledger Reconciliation**: Verify ledger entries match source transactions
- **Inter-company Reconciliation**: Match transactions between departments

## Discrepancy Categories
- Exact match (no discrepancy)
- Partial payment
- Overpayment
- Duplicate payment
- Missing payment
- Timing difference
- Currency mismatch
- Unauthorized discount
- Bank processing fee
- Incorrect ledger posting

## Audit Requirements
- Reconciliation results stored with full transaction detail.
- Monthly reconciliation summary in close report.
- Quarterly external audit of reconciliation accuracy.
