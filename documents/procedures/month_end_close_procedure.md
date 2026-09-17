# Month-End Close Procedure

**Procedure ID:** PROC-005
**Version:** 1.3
**Effective Date:** 2025-06-01
**Owner:** Finance Operations

## Trigger
Last business day of the month or scheduled close date.

## Steps

### Step 1: Pre-Close Review
- Verify all transactions for the period are posted.
- Review pending invoices and payments.
- Confirm all bank statements have been received and reconciled.

### Step 2: Final Reconciliation
Run the deterministic reconciliation engine across all transactions for the period.

### Step 3: Discrepancy Resolution
- Review all open discrepancies.
- Ensure CRITICAL and HIGH severity items are resolved or escalated.
- Document any items carried forward with justification.

### Step 4: Adjustments
- Process all approved adjustments.
- Verify journal entries are balanced and posted.
- Confirm idempotency keys prevent duplicate entries.

### Step 5: Report Generation
Generate the monthly close report including:
- Transaction summary
- Reconciliation statistics
- Discrepancy analysis
- Root cause summary
- Adjustment log
- Outstanding balances
- Policy compliance notes

### Step 6: Controller Review
Controller reviews the report and approves the close.

### Step 7: Close Period
- Mark period as CLOSED
- Record closing user and timestamp
- Prevent new transactions from being posted

### Step 8: Post-Close
- Archive supporting documentation
- Notify stakeholders
- Begin next period preparation

## Reopen Procedure
If errors are discovered after close:
1. Controller approves reopening with documented reason
2. Period status changes to REOPENED
3. Corrections are made with full audit trail
4. Period is re-closed
