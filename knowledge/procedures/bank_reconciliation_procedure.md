# PROC-RECON-BANK-001 — Bank Reconciliation Procedure

## 1. Metadata

| Field | Value |
| --- | --- |
| Procedure ID | PROC-RECON-BANK-001 |
| Version | 1.0 |
| Owner | Finance Manager (EMP-02), Tomas Weller |
| Governing policies | POL-RECON-001 (Reconciliation Policy v4.1), POL-PERIOD-001 (Accounting Period Policy v1.8) |
| Frequency | Monthly, Working Day 2 of close (see PROC-CLOSE-001) |
| Scope | BANK-USD-01 (GL 1000, Cash — Operating USD) and BANK-EUR-01 (GL 1010, Cash — Operating EUR), period 2026-08 |

## 2. Trigger

- Scheduled: month-end close, Working Day 2.
- Event-based: bank statement closing balance does not equal ledger cash balance at cut-off, or an unexplained bank line appears.

## 3. Inputs

| Input | Source system / file path | Format |
| --- | --- | --- |
| Bank statement, BANK-USD-01 | First Meridian Bank statement export | CSV: txn date, value date, dr/cr, amount, currency, description |
| Bank statement, BANK-EUR-01 | First Meridian Bank statement export | CSV, as above |
| GL cash account balances (1000, 1010) | Ledgerline | CSV: account, period, opening, debits, credits, closing |
| Cash receipts / payments journal | Ledgerline | CSV: payment ID, date, amount, allocation |
| Prior-period discrepancy register | `data/discrepancies.csv` | CSV |
| Canon bank transaction register | CANON.md §10 | Markdown table |

## 4. Steps

| # | Step | Actor | System | Input | Output | Control |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Pull bank statement lines for BANK-USD-01 and BANK-EUR-01 for 2026-08-01 to 2026-08-31 (transaction date) | `[AGENT]` | Bank portal export | Bank statement | Two transaction lists | Confirm opening balance matches prior period closing exactly |
| 2 | Pull GL cash ledger activity for accounts 1000 and 1010 for the same period | `[AGENT]` | Ledgerline | GL extract | GL cash activity list | Confirm no out-of-period postings included |
| 3 | Match each bank line to a ledger entry by amount, date (±3 days), and reference text (fuzzy match on customer alias, e.g. `BLUEPEAK LOGISTICS` vs `BLUEPEAK LOGISTICS GMBH`) | `[AGENT]` | Reconciliation tool | Bank lines, GL lines | Matched pairs, unmatched bank lines, unmatched GL lines | Match tolerance: exact amount, ±1.00 USD rounding |
| 4 | Classify unmatched bank lines: outstanding deposit/payment (in ledger, not yet cleared bank) vs. unrecorded item (in bank, not in ledger) vs. amount mismatch (matched by reference but different amount) | `[AGENT]` | Reconciliation tool | Unmatched lines | Classified exception list | Every unmatched line must get exactly one classification |
| 5 | Build reconciliation statement: bank statement closing balance, less outstanding deposits not yet ledger-recorded as cleared, plus/minus timing items, reconciled to GL cash balance | `[AGENT]` | Reconciliation tool | Steps 1-4 | Draft reconciliation statement | Must foot to GL closing balance within tolerance |
| 6 | For each unrecorded item, check whether a corresponding source document exists (refund request, expense invoice) that was never journaled | `[AGENT]` | Ledgerline, document store | Unrecorded item list | Root-cause hypothesis per item | Must cite supporting doc ID (e.g. REF-4001) |
| 7 | For each amount mismatch, compare underlying source document (expense invoice, vendor bill) to the bank amount | `[AGENT]` | AP subledger, vendor records | Mismatch line, vendor doc | Root-cause hypothesis (e.g. transposition) | Must show digit-level comparison |
| 8 | Open or link discrepancies in `data/discrepancies.csv` for each exception not already logged | `[AGENT]` | Discrepancy register | Exception list | Linked DISC-IDs | Per PROC-INV-DISC-001 intake |
| 9 | Review draft statement and exceptions | `[HUMAN]` Staff Accountant (EMP-01) | — | Draft statement | Reviewed statement | Reviewer initials and date required |
| 10 | Approve reconciliation and route remediation items | `[HUMAN]` Finance Manager (EMP-02) | — | Reviewed statement | Approved statement, routed items | Per POL-APPROVAL-001 |
| 11 | File statement, update close checklist | `[AGENT]` | Document store | Approved statement | Filed artifact | Retained per POL-RECON-001 |

## 5. Decision points

```text
For each unmatched bank line:
├── Does a ledger entry exist for this amount/customer but with a later value date (bank) than ledger date?
│   ├── YES -> Classify OUTSTANDING DEPOSIT (timing difference, cut-off) -> document as reconciling item, no adjustment
│   │          (e.g. BT-5006 vs PAY-2008/JE-8505 -> DISC-0003)
│   └── NO  -> continue
├── Does the bank line have no corresponding ledger entry at all?
│   ├── YES -> Classify UNRECORDED ITEM
│   │   ├── Is there a payment/refund/expense source doc for it? -> raise missing-ledger-entry discrepancy, route to PROC-ADJ-001
│   │   │      (e.g. BT-5002 duplicate receipt -> DISC-0002; BT-5007 refund -> DISC-0005)
│   │   └── No source doc found -> escalate as unexplained bank item (POL-ACCESS-001 exception) per PROC-ESC-001
│   └── NO  -> continue
└── Does the bank line match a ledger entry by reference/date but differ in amount?
    ├── YES -> Classify AMOUNT MISMATCH -> compare to vendor/customer source document -> raise adjustment
    │          (e.g. BT-5008 vs JE-8507/EXP-7002 -> DISC-0009, transposition 3,400.00 vs 3,040.00)
    └── NO  -> Line is fully matched; no action.
```

## 6. Required evidence

- Bank statement PDF/CSV export for BANK-USD-01 and BANK-EUR-01, 2026-08.
- GL cash ledger extract, accounts 1000 and 1010.
- Reconciliation statement bridge with every exception line itemized.
- Supporting source documents for each unrecorded item or mismatch (e.g. REF-4001 refund confirmation, EXP-7002 vendor invoice from VEND-2002).
- Discrepancy register entries linked (DISC-0002, DISC-0003, DISC-0005, DISC-0009).
- Reviewer/approver sign-off.

## 7. Approval requirements

Per CANON.md §17 / POL-APPROVAL-001:
- Routine reconciliation sign-off: Finance Manager (EMP-02).
- Any remediating journal entry follows Journal adjustment bands (Staff Accountant < 10,000; Finance Manager 10,000-50,000; Finance Director > 50,000).
- Any exception ≥ materiality (2,500 USD) unresolved at period close escalates to Controller (EMP-03) per PROC-ESC-001.
- Timing differences with no ledger impact (e.g. DISC-0003) require no approval beyond the Finance Manager's statement sign-off, per POL-RECON-001 and POL-PERIOD-001.

## 8. Expected output

**Artifact: Bank Reconciliation Statement — BANK-USD-01 — 2026-08**

| Line | Amount (USD) |
| --- | --- |
| Balance per bank statement, 2026-08-31 | 217,150.00 |
| Add: deposits in transit / outstanding deposits (BT-5006, 4,300.00, timing) | +4,300.00 |
| Less: unrecorded bank items not yet in ledger (BT-5002 duplicate receipt 8,750.00; BT-5007 unrecorded refund 1,250.00) | −10,000.00 |
| Adjust: amount mismatch correction (BT-5008 / EXP-7002, understated by 360.00) | −360.00 |
| **Adjusted balance per bank** | **211,090.00** |
| Balance per GL account 1000, 2026-08-31 (before adjustment) | to be confirmed against Ledgerline extract |
| Reconciling difference after adjustments | must equal 0.00 within tolerance |

Fields: bank account ID, GL account, period, opening balance, closing balance per bank, closing balance per GL, list of reconciling items (ID, type, amount, DISC-ID, disposition), preparer, reviewer, approver, date.

## 9. Escalation conditions

- Any unrecorded item without a traceable source document → escalate immediately (possible unauthorized cash movement, POL-ACCESS-001).
- Any single reconciling item ≥ 2,500 USD materiality threshold unresolved by close deadline → escalate to Controller (EMP-03).
- Reconciliation does not foot to GL balance after all known items applied → escalate to Finance Manager, then Controller if unresolved within 1 working day.

## 10. Verification

- [ ] Bank opening balance 184,300.00 (USD) ties to prior period closing.
- [ ] All bank lines BT-5001 through BT-5008 and BT-6001 are classified (matched, outstanding, unrecorded, or mismatch).
- [ ] Adjusted bank balance reconciles to GL cash account within POL-RECON-001 tolerance.
- [ ] Every exception has a linked DISC-ID and a disposition.
- [ ] Sign-off recorded by Finance Manager (EMP-02).

## 11. Worked example on canon data

**BANK-USD-01, period 2026-08. Opening balance 184,300.00 USD. Closing per statement 217,150.00 USD.**

Step 1-3 matching results:

| Bank txn | Amount | Dr/Cr | Ledger match | Classification |
| --- | --- | --- | --- | --- |
| BT-5001 | 8,750.00 | credit | PAY-2005 (matched) | Fully matched |
| BT-5002 | 8,750.00 | credit | none in ledger | **Unrecorded item** — duplicate receipt from Bluepeak, never booked (DISC-0002) |
| BT-5003 | 6,200.00 | credit | PAY-2011 (matched) | Fully matched |
| BT-5004 | 11,900.00 | credit | PAY-2001 (matched) | Fully matched (note: AR still shows a 500.00 residual, handled under DISC-0001 / PROC-RECON-INV-001, not a bank item) |
| BT-5005 | 2,200.00 | credit | PAY-2010 (matched, but misapplied to INV-1003 in AR — an AR issue, not a bank reconciling item) | Fully matched at bank level |
| BT-5006 | 4,300.00 | credit, value date 2026-09-01 | PAY-2008 / JE-8505 recorded 2026-08-31 | **Outstanding deposit** — timing difference (DISC-0003); documented reconciling item, no adjustment needed per CANON §13 |
| BT-5007 | 1,250.00 | debit | none in ledger | **Unrecorded item** — refund REF-4001 paid from bank portal, bypassing workflow, no journal entry exists (DISC-0005) |
| BT-5008 | 3,400.00 | debit | JE-8507 recorded 3,040.00 (EXP-7002 to VEND-2002 Northline Freight) | **Amount mismatch** — transposition, bank shows correct 3,400.00, ledger understated by 360.00 (DISC-0009) |

Step 5 reconciliation bridge:

```
Balance per bank statement, 2026-08-31:            217,150.00
Less: outstanding deposit BT-5006 (timing, already
      reflected in ledger period 2026-08):           -4,300.00   [documented, no GL change]
Less: unrecorded item BT-5002 (duplicate receipt,
      needs booking to 1950 Unapplied Cash):          -8,750.00
Less: unrecorded item BT-5007 (refund, needs
      booking Dr 1100 / Cr 1000):                     -1,250.00
Less: amount-mismatch correction BT-5008 (expense
      understated 360.00, needs correcting entry):      -360.00
                                                     ------------
Adjusted cash position after required postings:      202,490.00
```

Step 8: Open/confirm discrepancies DISC-0002, DISC-0003 (already `explained`), DISC-0005, DISC-0009 in `data/discrepancies.csv`. Route DISC-0002 to PROC-INV-PAY-001, DISC-0005 and DISC-0009 to PROC-ADJ-001 (ADJ-5006, ADJ-5007). DISC-0003 requires no adjustment — it is closed as a documented reconciling item per POL-RECON-001/POL-PERIOD-001.

Step 10: Finance Manager EMP-02 signs the statement noting three open remediation items and one documented timing item.

**BANK-EUR-01, period 2026-08.** Opening 42,000.00 EUR, closing per statement 51,000.00 EUR. Only BT-6001 (9,000.00 EUR credit, matched to PAY-2009/JE-8506) falls in this account; note PAY-2009 was booked using the correct 2026-08-27 FX rate of 1.0910 at settlement, while INV-1004 was originally booked at the erroneous stale rate 1.0500 instead of the correct 1.0850 (DISC-0004) — this is an AR/FX reconciling item, not a bank reconciling item, and is handled under PROC-ADJ-001 (ADJ-5005).

## 12. Related documents

- PROC-RECON-INV-001 (Invoice Reconciliation Procedure)
- PROC-INV-PAY-001 (Payment Investigation Procedure)
- PROC-INV-DISC-001 (Discrepancy Investigation Procedure)
- PROC-ADJ-001 (Adjustment Procedure)
- PROC-CLOSE-001 (Month-End Close Procedure)
- PROC-ESC-001 (Escalation Procedure)
- POL-RECON-001, POL-PERIOD-001, POL-ACCESS-001
