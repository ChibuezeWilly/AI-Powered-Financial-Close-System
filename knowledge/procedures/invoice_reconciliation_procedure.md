# PROC-RECON-INV-001 — Invoice Reconciliation Procedure

## 1. Metadata

| Field | Value |
| --- | --- |
| Procedure ID | PROC-RECON-INV-001 |
| Version | 1.0 |
| Owner | Finance Manager (EMP-02), Tomas Weller |
| Governing policies | POL-RECON-001 (Reconciliation Policy v4.1), POL-PAYMENT-001 (v3.2), POL-PERIOD-001 (v1.8) |
| Frequency | Monthly, as part of month-end close (see PROC-CLOSE-001), and ad hoc on discrepancy detection |
| Scope | Accounts Receivable subledger (Meridian Billing) vs. GL account 1100, and invoice-to-PO-to-payment three-way tie-out |
| Applies to | Meridian Instruments Ltd, all customers (CUST-1001 … CUST-1005), period 2026-08 |

## 2. Trigger

- Scheduled: Working Day 2 of month-end close (see PROC-CLOSE-001, task WD2-03).
- Event-based: an invoice status looks inconsistent with cash applied (e.g. `open (wrongly shows unpaid)` on INV-1006), or the bank reconciliation (PROC-RECON-BANK-001) surfaces an unmatched receipt.
- Any auto-generated discrepancy in `data/discrepancies.csv` with `type` in `{duplicate_invoice, payment_applied_to_wrong_invoice, undocumented_discount_partial_payment}`.

## 3. Inputs

| Input | Source system / file path | Format |
| --- | --- | --- |
| AR subledger (open invoice list) | Meridian Billing export | CSV: invoice, customer, date, due, PO, currency, subtotal, discount, tax, total, status |
| GL trial balance, account 1100 | Ledgerline | CSV: account, period, opening balance, debits, credits, closing balance |
| Purchase orders | Meridian Billing / PO register | CSV: PO ID, customer, date, amount, status |
| Payments received | Ledgerline cash receipts journal | CSV: payment, customer, date, amount, currency, method, bank reference text, allocation |
| Bank transactions (for cross-check) | `data/discrepancies.csv`, BANK-USD-01 / BANK-EUR-01 statements | CSV |
| Prior period discrepancy register | `data/discrepancies.csv` | CSV |
| Canon invoice register | CANON.md §8 | Markdown table |

## 4. Steps

| # | Step | Actor | System | Input | Output | Control |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Export AR subledger open-item list and GL account 1100 balance for period 2026-08 | `[AGENT]` | Meridian Billing, Ledgerline | AR subledger, GL 1100 | Two extracts, timestamped | Extract must be as-of last day of period (2026-08-31), four-eyes not required |
| 2 | Sum AR subledger total (all invoice totals net of applied cash) and compare to GL 1100 closing balance | `[AGENT]` | Reconciliation tool | AR subledger, GL 1100 | Variance figure | Tolerance per POL-RECON-001: USD 1.00 or 0.1% of lower amount, whichever is greater |
| 3 | If variance > tolerance, list constituent invoices in descending variance order | `[AGENT]` | Reconciliation tool | AR subledger | Ranked variance list | Must cite each invoice ID |
| 4 | For each invoice, three-way match: invoice total vs. PO amount vs. payments applied | `[AGENT]` | Ledgerline, Meridian Billing, PO register | INV-xxxx, PO-xxx, PAY-xxxx | Match/mismatch flag per invoice | Match if invoice total = PO amount (currency-adjusted) and sum of applied payments = invoice total within tolerance |
| 5 | Check invoice status field consistency (e.g. `open`, `paid`, `partially_paid`, `disputed`) against actual applied-cash calculation | `[AGENT]` | Meridian Billing | Invoice status, payment allocations | Status-exception list | Any invoice where system status conflicts with computed status is an exception |
| 6 | Check for duplicate invoices against the same PO (same customer + PO + amount issued twice) | `[AGENT]` | Meridian Billing | Invoice register | Duplicate-invoice flags | Duplicate defined as two invoice IDs referencing the same PO ID and same amount within the period |
| 7 | Cross-reference each exception against `data/discrepancies.csv` to see if already logged | `[AGENT]` | Discrepancy register | discrepancies.csv | Linked or new DISC-ID | If unlinked, open new discrepancy per PROC-INV-DISC-001 §Intake |
| 8 | Draft reconciliation summary with variance bridge (AR subledger → adjustments → GL 1100) | `[AGENT]` | Reconciliation tool | Steps 1-7 outputs | Draft reconciliation statement | Must reconcile to zero after listed adjustments |
| 9 | Review draft reconciliation and supporting exception list | `[HUMAN]` Staff Accountant (EMP-01) | Ledgerline | Draft reconciliation statement | Reviewed reconciliation | Reviewer signs off or returns for rework |
| 10 | Route unresolved exceptions to PROC-INV-DISC-001 for investigation; route confirmed root causes to PROC-ADJ-001 for posting | `[HUMAN]` Staff Accountant (EMP-01) | Discrepancy register, adjustment queue | Exception list | Investigation/adjustment references | Every exception must have a disposition: investigate, adjust, or accept as documented reconciling item |
| 11 | Obtain sign-off per approval matrix band for the reconciliation as a whole | `[HUMAN]` Finance Manager (EMP-02) | Ledgerline | Reconciled statement | Approved reconciliation | Per POL-APPROVAL-001; Finance Manager approves routine reconciliations, Controller for material (>2,500) unresolved items |
| 12 | File reconciliation pack and update close checklist | `[AGENT]` | Document store | Approved reconciliation | Filed pack, checklist update | Evidence retained per POL-RECON-001 retention rule |

## 5. Decision points

```text
Is |AR subledger total - GL 1100 balance| > tolerance (max(1.00, 0.1% lower))?
├── NO  -> Reconciliation clean. File and close.
└── YES -> For each contributing invoice:
    ├── Is invoice total ≠ PO amount?
    │   ├── YES -> Flag PO mismatch -> route to PROC-INV-DISC-001 (root-cause: pricing/PO error)
    │   └── NO  -> continue
    ├── Is sum(applied payments) ≠ invoice total, and no dispute/discount on file?
    │   ├── YES -> Is there an unapplied or duplicate payment for the same customer/amount?
    │   │   ├── YES -> Classify as duplicate_payment or payment_applied_to_wrong_invoice -> PROC-INV-PAY-001
    │   │   └── NO  -> Classify as undocumented_discount_partial_payment -> PROC-INV-DISC-001
    │   └── NO  -> continue
    ├── Does the same PO ID appear on two invoice IDs of equal amount in-period?
    │   ├── YES -> Classify as duplicate_invoice -> PROC-INV-DISC-001, then PROC-ADJ-001 (credit note)
    │   └── NO  -> continue
    └── Is invoice status inconsistent with computed cash-applied state (e.g. "open" but fully paid, or vice versa)?
        ├── YES -> Flag status-data exception -> correct in Meridian Billing, log discrepancy
        └── NO  -> Accept as timing/documented reconciling item, cite policy (e.g. POL-PERIOD-001)
```

## 6. Required evidence

- AR subledger export and GL 1100 trial balance extract (both timestamped 2026-08-31).
- Invoice PDFs / Meridian Billing invoice detail for each exception (e.g. INV-1001, INV-1008).
- PO register entries (PO-ACM-8842, PO-BLU-2210, etc.).
- Payment allocation detail from Ledgerline cash receipts journal.
- Any credit notes referenced (CN-3001, CN-3002) including status (draft/issued/posted).
- Screenshot or export of `data/discrepancies.csv` row(s) linked.
- Reviewer and approver sign-off records (names, EMP IDs, dates).

## 7. Approval requirements

Per canon approval matrix (CANON.md §17 / POL-APPROVAL-001):

| Reconciliation outcome | Approver band |
| --- | --- |
| Clean reconciliation, no exceptions | Staff Accountant (EMP-01) self-review sufficient |
| Exceptions requiring credit note ≤ 5,000 | Finance Manager (EMP-02) |
| Exceptions requiring credit note > 5,000 | Finance Director (EMP-04) |
| Unresolved exception ≥ materiality (2,500 USD) | Escalate to Controller (EMP-03) per PROC-ESC-001 |

The reconciliation itself (as a control activity) is signed off by the Finance Manager (EMP-02) each period; individual remediations follow their own approval band (discount, credit note, refund, adjustment) as routed in Step 10.

## 8. Expected output

**Artifact: AR Reconciliation Statement — 2026-08** containing:
- Header: period, prepared by, reviewed by, approved by, date.
- Bridge table: AR subledger total → + / − reconciling items → GL 1100 balance.
- Exception register: invoice ID, issue type, amount, linked DISC-ID, disposition, status.
- Sign-off block with EMP IDs and dates.

**Artifact: Three-way match report** with fields: invoice ID, PO ID, invoice total, PO amount, sum applied payments, match flag (Y/N), notes.

## 9. Escalation conditions

- Any single exception ≥ USD 2,500 (materiality threshold) → escalate to Controller (EMP-03) per PROC-ESC-001.
- Any exception involving a journal entry posted without a recorded approver (e.g. pattern seen in JE-9007 / DISC-0007) → immediate escalation regardless of amount.
- Reconciliation cannot be closed within 2 working days of month-end close deadline → escalate to Finance Manager, then Controller if unresolved by WD5.
- Suspected duplicate invoicing pattern recurring across periods → escalate to Finance Director (EMP-04).

## 10. Verification

- [ ] AR subledger total ties to GL 1100 within tolerance after adjustments.
- [ ] Every invoice in the exception list has a disposition (investigate / adjust / accept) and, where applicable, a linked DISC-ID.
- [ ] Every posted adjustment referenced has a corresponding ADJ-ID in `data/adjustments.csv` with `posted_journal_id` populated.
- [ ] Sign-off recorded by required approver band.
- [ ] Reconciliation pack filed and close checklist item marked complete (PROC-CLOSE-001).

## 11. Worked example on canon data

**Case A — INV-1001 (partial payment / undocumented discount, DISC-0001)**

1. Step 1-2: AR subledger shows INV-1001 total 12,400.00 USD outstanding (net of cash) still showing a balance, but GL 1100 posting via JE-8001 (12,400.00) and JE-8503 (cash receipt PAY-2001, 11,900.00) leaves a residual of 500.00.
2. Step 4: Three-way match — PO-ACM-8842 = 12,400.00 = invoice total (match). Payment applied: PAY-2001 = 11,900.00 (mismatch: 500.00 short).
3. Step 5: Invoice status is `partially_paid` — consistent with the shortfall, no status-data exception.
4. Step 6: Investigate cause — bank transaction BT-5004 confirms only 11,900.00 was received on 2026-08-28. A draft credit note CN-3001 for 500.00 exists but was never issued or posted.
5. Step 7: Cross-reference `data/discrepancies.csv` row DISC-0001 — already logged, `under_investigation`, linked to INVG-7001.
6. Step 8-10: Root cause per CANON §13 and §18: Sales Manager EMP-06 verbally granted a 500.00 early-payment discount (POL-DISCOUNT-001, 500-5,000 band requires Finance Manager EMP-02 approval, APR-6001). Approval was never requested (missing). Route to PROC-INV-DISC-001 for formal investigation closure, then to PROC-ADJ-001 to post ADJ-5001 (Dr 4200 Sales Discounts 500.00 / Cr 1100 AR 500.00) once APR-6001 is obtained from EMP-02.
7. Step 11-12: Once ADJ-5001 posts, INV-1001 balance = 0.00, reconciliation clean; file pack.

**Case B — INV-1008 (duplicate invoice, DISC-0008)**

1. Step 6: Duplicate-invoice check finds INV-1008 (issued 2026-08-25, 8,750.00 USD) references the same PO-BLU-2210 and same amount as INV-1002 (issued 2026-08-05, 8,750.00 USD, already paid via PAY-2005/BT-5001).
2. Step 4: Three-way match fails — PO-BLU-2210 was fulfilled once, but two invoices reference it.
3. Step 7: Matches `data/discrepancies.csv` DISC-0008, status `pending_credit_note`, root cause: billing batch for PO-BLU-2210 executed twice after a failed run.
4. Step 10: Route to PROC-ADJ-001 — proposed credit note CN-3002 for 8,750.00 to cancel INV-1008. Because the amount exceeds the Finance Manager credit-note band (≤5,000), per CANON §13 approval escalates to Finance Director EMP-04; approval record is APR-6005, currently `pending`.
5. Step 12: Reconciliation statement lists INV-1008 as an open exception with disposition "adjust — pending CN-3002 / APR-6005", not yet closed.

## 12. Related documents

- PROC-RECON-BANK-001 (Bank Reconciliation Procedure)
- PROC-INV-PAY-001 (Payment Investigation Procedure)
- PROC-INV-DISC-001 (Discrepancy Investigation Procedure — master runbook)
- PROC-ADJ-001 (Adjustment Procedure)
- PROC-CLOSE-001 (Month-End Close Procedure)
- PROC-ESC-001 (Escalation Procedure)
- POL-RECON-001, POL-PAYMENT-001, POL-PERIOD-001, POL-CREDITNOTE-001, POL-DISCOUNT-001
