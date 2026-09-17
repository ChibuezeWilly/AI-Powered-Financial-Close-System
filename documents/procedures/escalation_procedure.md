# Escalation Procedure

**Procedure ID:** PROC-008
**Version:** 1.0
**Effective Date:** 2025-06-01
**Owner:** Finance Operations

## Trigger
A financial decision is rejected at the analyst/manager level, or a discrepancy exceeds the current approver's authority.

## Steps

### Step 1: Record Rejection
Document the rejection decision with reason and timestamp.

### Step 2: Update Transaction Status
Transition: REJECTED → ESCALATED → AWAITING_MANAGER_APPROVAL

### Step 3: Send Slack Notification
Post a structured message to the configured Slack channel with:
- Transaction ID
- Invoice ID
- Customer name
- Amount in question
- Reason for escalation
- Link to the TallyFlow review page

### Step 4: Create Manager Approval Request
Store the escalation in the database with the pending status.

### Step 5: Await Manager Decision
The manager can approve or reject through:
- TallyFlow web interface
- Slack interactive buttons (if configured)

### Step 6: Process Manager Decision
**If Manager Approves:**
- Create the appropriate ledger adjustment
- Verify reconciliation
- Update transaction to RESOLVED

**If Manager Rejects:**
- Record the remaining receivable
- Send payment request to the customer via email
- Update transaction to PAYMENT_REQUESTED
- Monitor for incoming payment

### Step 7: Verify and Close
After resolution (either through adjustment or payment receipt):
- Confirm difference is $0
- Update all statuses
- Complete audit trail
