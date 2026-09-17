# Adjustment Procedure

**Procedure ID:** PROC-006
**Version:** 1.0
**Effective Date:** 2025-06-01
**Owner:** Finance Operations

## Trigger
An approved recommendation to create a financial adjustment (journal entry, ledger correction, or balance modification).

## Steps

### Step 1: Validate Approval
Confirm the adjustment has been approved by a user with sufficient authority per FIN-010 Approval Matrix.

### Step 2: Validate Accounting Period
Confirm the target period is OPEN. If closed, the period must be reopened before proceeding.

### Step 3: Generate Idempotency Key
Create a unique key based on transaction ID, action type, approval ID, and version to prevent duplicate entries.

### Step 4: Create Journal Entry
Using the controlled accounting tool (never direct SQL):
- Debit the appropriate expense/asset account
- Credit the appropriate liability/receivable account
- Record the amount, description, and reference

### Step 5: Verify Entry
Call the accounting provider's verification method to confirm the journal entry was posted successfully.

### Step 6: Update Transaction
- Set difference to $0 (if fully resolved)
- Update transaction status to ADJUSTED → RESOLVED
- Update investigation status to RESOLVED

### Step 7: Re-Run Reconciliation
Execute deterministic reconciliation on the transaction to verify the difference is now zero.

### Step 8: Record Audit Events
Log: JOURNAL_ENTRY_POSTED, RECONCILIATION_VERIFIED, ADJUSTMENT_COMPLETED.

### Step 9: Save Investigation
Store the resolved investigation summary to Pinecone for future precedent reference.

### Step 10: Notify
- Send confirmation notification to the approver
- Send Slack message if configured
- Send email confirmation if required
