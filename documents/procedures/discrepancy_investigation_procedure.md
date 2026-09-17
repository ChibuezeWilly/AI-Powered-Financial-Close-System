# Discrepancy Investigation Procedure

**Procedure ID:** PROC-004
**Version:** 1.2
**Effective Date:** 2025-06-01
**Owner:** Finance Operations

## Trigger
A discrepancy is detected during reconciliation (expected amount ≠ actual amount).

## Inputs
- Transaction record with discrepancy
- Invoice details
- Payment details
- Bank transaction (if available)
- Ledger entries
- Customer history

## Steps

### Step 1: Classify Discrepancy
Determine the type: partial payment, overpayment, duplicate, timing difference, unauthorized discount, bank fee, ledger error, currency mismatch, etc.

### Step 2: Retrieve Structured Evidence
Query PostgreSQL for all related records: invoice, payment, bank transaction, ledger entries, prior investigations for same customer.

### Step 3: Retrieve Documents
Use hybrid RAG to find relevant invoices, contracts, credit notes, or correspondence that may explain the discrepancy.

### Step 4: Retrieve Policies
Search for applicable policies using the discrepancy type. Example: discount discrepancy → FIN-042 discount policy.

### Step 5: Graph Traversal
Traverse the knowledge graph to discover related entities, prior similar discrepancies, and cross-references.

### Step 6: Evidence Fusion
Combine all evidence into a structured evidence record. Mark each evidence item with source, confidence, and retrieval method.

### Step 7: Hypothesis Generation
Based on evidence, generate possible root causes. Label each as "detected fact," "supporting evidence," or "AI hypothesis."

### Step 8: Root Cause Analysis
Select the most likely root cause based on evidence weight and confidence scores.

### Step 9: Recommendation
Generate a recommended action (approve, reject, escalate, request payment, create adjustment).

### Step 10: Human Approval
Present the recommendation to the appropriate approver based on the approval matrix.

## Decision Points
- If approved → Create accounting adjustment
- If rejected → Escalate to manager
- If more evidence needed → Return to Step 2

## Verification
After any accounting action:
1. Re-run reconciliation
2. Verify difference becomes $0
3. Update transaction status
4. Save investigation summary

## Escalation
- Unresolved after 5 business days → Finance Manager
- Unresolved after 10 business days → Controller
- Suspected fraud → Immediate compliance notification
