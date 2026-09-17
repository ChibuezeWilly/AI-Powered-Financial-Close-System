# CANON — The Single Fictional Financial Universe

**This file is the source of truth for every other file in the project.**
All knowledge documents, policies, procedures, source documents, graph schemas,
RAG metadata examples, and ground-truth cases MUST use the entities, IDs, dates
and amounts defined here. Never invent a new company, customer, invoice number,
employee, policy ID or amount that is not listed below.

---

## 1. The Company

| Field | Value |
| --- | --- |
| Legal name | Meridian Instruments Ltd |
| Trading name | Meridian Instruments |
| Registration | Company No. 08842217 (England & Wales) |
| VAT / Tax ID | GB 442 8871 09 |
| Registered address | 14 Calder Wharf, Unit 3, Bristol BS1 6QT, United Kingdom |
| Operating address (US) | 220 Harbor Point Rd, Suite 410, Portland, ME 04101, USA |
| Industry | Design and distribution of precision measurement instruments |
| Reporting currency | USD |
| Fiscal year | Calendar year (1 Jan – 31 Dec) |
| Accounting basis | Accrual |
| ERP / ledger system | "Ledgerline" (internal name for the accounting system) |
| Billing system | "Meridian Billing" (issues invoices) |
| Period under close in all examples | **August 2026** (2026-08-01 → 2026-08-31) |
| Close deadline | Working day 5 (2026-09-05) |
| Materiality threshold (period) | USD 2,500 |
| Reconciliation tolerance | USD 1.00 or 0.1% of the lower amount, whichever is greater |

## 2. Bank accounts

| Bank account ID | Bank | Account (masked) | IBAN / Routing | Currency | GL account |
| --- | --- | --- | --- | --- | --- |
| BANK-USD-01 | First Meridian Bank | ****4471 | ABA 011500120 / Acct 30084471 | USD | 1000 |
| BANK-EUR-01 | First Meridian Bank | ****8820 | GB29 FMBK 6016 1331 9268 20 | EUR | 1010 |

## 3. Chart of accounts

| Account | Name | Type | Normal balance |
| --- | --- | --- | --- |
| 1000 | Cash — Operating USD | Asset | Debit |
| 1010 | Cash — Operating EUR | Asset | Debit |
| 1100 | Accounts Receivable | Asset | Debit |
| 1190 | Allowance for Doubtful Accounts | Asset (contra) | Credit |
| 1900 | Suspense | Asset (clearing) | Debit |
| 1950 | Unapplied Cash | Liability (clearing) | Credit |
| 2000 | Accounts Payable | Liability | Credit |
| 2100 | Accrued Liabilities | Liability | Credit |
| 2200 | Sales Tax Payable | Liability | Credit |
| 3000 | Retained Earnings | Equity | Credit |
| 4000 | Product Revenue | Revenue | Credit |
| 4100 | Service Revenue | Revenue | Credit |
| 4200 | Sales Discounts | Revenue (contra) | Debit |
| 5000 | Cost of Goods Sold | Expense | Debit |
| 6100 | Freight Expense | Expense | Debit |
| 6200 | Office Supplies Expense | Expense | Debit |
| 6900 | FX Gain / Loss | Expense | Debit |
| 6950 | Bad Debt Expense | Expense | Debit |

## 4. Customers (with the messy aliases used in source documents)

| Customer ID | Canonical name | Aliases seen in documents | Country | Terms | Credit limit |
| --- | --- | --- | --- | --- | --- |
| CUST-1001 | Acme Incorporated | `ACME INC.`, `ACME INCORP`, `Acme Inc`, `ACME INCORPORATED` | USA | Net 30 | 50,000 USD |
| CUST-1002 | Bluepeak Logistics GmbH | `BLUEPEAK LOGISTICS`, `Bluepeak Log. GmbH`, `BLUEPEAK LOGISTIK GMBH` | Germany | Net 15 | 40,000 USD |
| CUST-1003 | Corvus Analytics LLC | `CORVUS ANALYTICS`, `Corvus Analytics L.L.C.`, `CORVUS ANALYTIC LLC` | USA | Net 30 | 25,000 USD |
| CUST-1004 | Dunmore Retail Group | `DUNMORE RETAIL GRP`, `Dunmore Retail`, `DUNMORE RETIAL GROUP` (OCR typo) | Ireland | Net 30 | 60,000 EUR |
| CUST-1005 | Eastport Marine Services | `EASTPORT MARINE SVCS`, `Eastport Marine`, `EASTP0RT MARINE` (OCR typo) | USA | Net 30 | 30,000 USD |

## 5. Vendors

| Vendor ID | Name | Category | Terms |
| --- | --- | --- | --- |
| VEND-2001 | Halcyon Print & Packaging | Packaging | Net 30 |
| VEND-2002 | Northline Freight | Freight | Net 30 |
| VEND-2003 | Sable Office Supplies | Office supplies | Net 14 |

## 6. Employees, departments and authority

| Employee ID | Name | Role | Department | Approval authority |
| --- | --- | --- | --- | --- |
| EMP-01 | Priya Raghunathan | Staff Accountant | Finance (DEPT-FIN) | Journal adjustments < 10,000 USD |
| EMP-02 | Tomas Weller | Finance Manager | Finance (DEPT-FIN) | Discounts 500–5,000; journal adjustments ≥ 10,000 to 50,000; credit notes ≤ 5,000 |
| EMP-03 | Nadia Okonkwo | Controller | Finance (DEPT-FIN) | Write-offs > 5,000; period lock/unlock |
| EMP-04 | Ines Bertrand | Finance Director | Finance (DEPT-FIN) | Discounts 5,000–10,000; refunds > 2,000 |
| EMP-05 | David Achebe | CFO | Executive (DEPT-EXE) | Discounts > 10,000; all policy exceptions |
| EMP-06 | Greg Molloy | Sales Manager | Sales (DEPT-SAL) | Discounts < 500; refunds < 2,000 |
| EMP-07 | Lena Fischer | Collections Analyst | Finance (DEPT-FIN) | None |

## 7. FX rates (USD per 1 EUR)

| Date | Rate | Note |
| --- | --- | --- |
| 2026-08-11 | 1.0850 | Correct rate on invoice date of INV-1004 |
| 2026-08-27 | 1.0910 | Rate on payment date of PAY-2009 |
| 2026-08-31 | 1.0875 | Month-end revaluation rate |
| (erroneous) | 1.0500 | Stale July rate wrongly applied to INV-1004 by the ledger interface |

## 8. Invoices (August 2026)

| Invoice | Customer | Date | Due | PO | Ccy | Subtotal | Discount | Tax | Total | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-1001 | CUST-1001 | 2026-08-03 | 2026-09-02 | PO-ACM-8842 | USD | 12,000.00 | 0.00 | 400.00 | **12,400.00** | partially_paid |
| INV-1002 | CUST-1002 | 2026-08-05 | 2026-08-20 | PO-BLU-2210 | USD | 8,500.00 | 0.00 | 250.00 | 8,750.00 | paid |
| INV-1003 | CUST-1003 | 2026-08-07 | 2026-09-06 | PO-COR-0091 | USD | 4,200.00 | 0.00 | 100.00 | 4,300.00 | paid (overpaid) |
| INV-1004 | CUST-1004 | 2026-08-11 | 2026-09-10 | PO-DUN-7731 | EUR | 8,700.00 | 0.00 | 300.00 | 9,000.00 | paid |
| INV-1005 | CUST-1005 | 2026-08-14 | 2026-09-13 | PO-EAS-5510 | USD | 6,000.00 | 0.00 | 200.00 | 6,200.00 | paid |
| INV-1006 | CUST-1001 | 2026-08-18 | 2026-09-17 | PO-ACM-8859 | USD | 2,100.00 | 0.00 | 100.00 | 2,200.00 | open (wrongly shows unpaid) |
| INV-1007 | CUST-1003 | 2026-08-21 | 2026-09-20 | PO-COR-0104 | USD | 5,000.00 | 0.00 | 150.00 | 5,150.00 | open |
| INV-1008 | CUST-1002 | 2026-08-25 | 2026-09-09 | PO-BLU-2210 | USD | 8,500.00 | 0.00 | 250.00 | 8,750.00 | disputed (duplicate of INV-1002) |

## 9. Payments

| Payment | Customer | Date | Amount | Ccy | Method | Bank reference text | Allocation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PAY-2001 | CUST-1001 | 2026-08-28 | 11,900.00 | USD | bank_transfer | `ACME INC INV1001 PMT` | 11,900.00 → INV-1001 |
| PAY-2005 | CUST-1002 | 2026-08-18 | 8,750.00 | USD | bank_transfer | `BLUEPEAK LOGISTICS GMBH INV1002` | 8,750.00 → INV-1002 |
| PAY-2006 | CUST-1002 | 2026-08-19 | 8,750.00 | USD | bank_transfer | `BLUEPEAK LOGISTICS INV1002` | unapplied |
| PAY-2008 | CUST-1003 | 2026-08-31 | 4,300.00 | USD | bank_transfer | `CORVUS ANALYTICS LLC INV1003` | 4,300.00 → INV-1003 |
| PAY-2009 | CUST-1004 | 2026-08-27 | 9,000.00 | EUR | bank_transfer | `DUNMORE RETAIL GRP INV1004` | 9,000.00 → INV-1004 |
| PAY-2010 | CUST-1001 | 2026-08-29 | 2,200.00 | USD | bank_transfer | `ACME INCORP 8859` | 2,200.00 → INV-1003 (**wrong**; belongs to INV-1006) |
| PAY-2011 | CUST-1005 | 2026-08-26 | 6,200.00 | USD | bank_transfer | `EASTPORT MARINE SVCS INV-1005` | 6,200.00 → INV-1005 |

## 10. Bank transactions

| Bank txn | Account | Txn date | Value date | Dr/Cr | Amount | Ccy | Description | Matched to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BT-5001 | BANK-USD-01 | 2026-08-18 | 2026-08-18 | credit | 8,750.00 | USD | `BLUEPEAK LOGISTICS GMBH INV1002` | PAY-2005 |
| BT-5002 | BANK-USD-01 | 2026-08-19 | 2026-08-19 | credit | 8,750.00 | USD | `BLUEPEAK LOGISTICS INV1002` | PAY-2006 |
| BT-5003 | BANK-USD-01 | 2026-08-26 | 2026-08-26 | credit | 6,200.00 | USD | `EASTPORT MARINE SVCS INV-1005` | PAY-2011 |
| BT-5004 | BANK-USD-01 | 2026-08-28 | 2026-08-28 | credit | 11,900.00 | USD | `ACME INC INV1001 PMT` | PAY-2001 |
| BT-5005 | BANK-USD-01 | 2026-08-29 | 2026-08-29 | credit | 2,200.00 | USD | `ACME INCORP 8859` | PAY-2010 |
| BT-5006 | BANK-USD-01 | 2026-08-31 | **2026-09-01** | credit | 4,300.00 | USD | `CORVUS ANALYTICS LLC INV1003` | PAY-2008 (timing difference) |
| BT-5007 | BANK-USD-01 | 2026-08-30 | 2026-08-30 | debit | 1,250.00 | USD | `REFUND EASTPORT MARINE` | REF-4001 (no ledger entry) |
| BT-5008 | BANK-USD-01 | 2026-08-12 | 2026-08-12 | debit | 3,400.00 | USD | `NORTHLINE FREIGHT AUG` | EXP-7002 |
| BT-6001 | BANK-EUR-01 | 2026-08-27 | 2026-08-27 | credit | 9,000.00 | EUR | `DUNMORE RETAIL GRP INV1004` | PAY-2009 |

Opening balance BANK-USD-01 on 2026-08-01: 184,300.00 USD. Closing per statement 2026-08-31: 217,150.00 USD.
Opening balance BANK-EUR-01 on 2026-08-01: 42,000.00 EUR. Closing per statement 2026-08-31: 51,000.00 EUR.

## 11. Credit notes, refunds, purchase orders, expenses

| ID | Type | Related | Date | Amount | Status |
| --- | --- | --- | --- | --- | --- |
| CN-3001 | Credit note | INV-1001 | 2026-08-27 | 500.00 USD | **draft — never issued or posted** (root cause of DISC-0001) |
| CN-3002 | Credit note | INV-1008 | 2026-09-02 | 8,750.00 USD | proposed (to cancel duplicate invoice) |
| REF-4001 | Refund | CUST-1005 / INV-1005 | 2026-08-30 | 1,250.00 USD | paid from bank, **not in ledger** |
| PO-ACM-8842 | Purchase order | CUST-1001 | 2026-07-29 | 12,400.00 USD | fulfilled |
| PO-ACM-8859 | Purchase order | CUST-1001 | 2026-08-14 | 2,200.00 USD | fulfilled |
| PO-BLU-2210 | Purchase order | CUST-1002 | 2026-08-01 | 8,750.00 USD | fulfilled (once) |
| PO-COR-0091 | Purchase order | CUST-1003 | 2026-08-04 | 4,300.00 USD | fulfilled |
| PO-COR-0104 | Purchase order | CUST-1003 | 2026-08-19 | 5,150.00 USD | fulfilled |
| PO-DUN-7731 | Purchase order | CUST-1004 | 2026-08-06 | 9,000.00 EUR | fulfilled |
| PO-EAS-5510 | Purchase order | CUST-1005 | 2026-08-10 | 6,200.00 USD | fulfilled |
| EXP-7002 | Expense | VEND-2002 | 2026-08-12 | 3,400.00 USD | paid; ledger shows 3,040.00 (transposition) |

## 12. Journal entries

| Journal | Date | Period | Description | Preparer | Approver |
| --- | --- | --- | --- | --- | --- |
| JE-8001 | 2026-08-03 | 2026-08 | Invoice INV-1001 issued | system | n/a |
| JE-8002 | 2026-08-05 | 2026-08 | Invoice INV-1002 issued | system | n/a |
| JE-8003 | 2026-08-07 | 2026-08 | Invoice INV-1003 issued | system | n/a |
| JE-8004 | 2026-08-11 | 2026-08 | Invoice INV-1004 issued (EUR @ 1.0500 — wrong rate) | system | n/a |
| JE-8005 | 2026-08-14 | 2026-08 | Invoice INV-1005 issued | system | n/a |
| JE-8006 | 2026-08-18 | 2026-08 | Invoice INV-1006 issued | system | n/a |
| JE-8007 | 2026-08-21 | 2026-08 | Invoice INV-1007 issued | system | n/a |
| JE-8008 | 2026-08-25 | 2026-08 | Invoice INV-1008 issued (duplicate) | system | n/a |
| JE-8501 | 2026-08-18 | 2026-08 | Cash receipt PAY-2005 | system | n/a |
| JE-8502 | 2026-08-26 | 2026-08 | Cash receipt PAY-2011 | system | n/a |
| JE-8503 | 2026-08-28 | 2026-08 | Cash receipt PAY-2001 (11,900) | system | n/a |
| JE-8504 | 2026-08-29 | 2026-08 | Cash receipt PAY-2010 applied to INV-1003 | system | n/a |
| JE-8505 | 2026-08-31 | 2026-08 | Cash receipt PAY-2008 | system | n/a |
| JE-8506 | 2026-08-27 | 2026-08 | Cash receipt PAY-2009 (EUR) | system | n/a |
| JE-8507 | 2026-08-12 | 2026-08 | Freight expense EXP-7002 recorded at 3,040.00 (should be 3,400.00) | EMP-01 | EMP-02 |
| JE-9007 | 2026-08-31 | 2026-08 | Manual AR adjustment 14,000.00 to Suspense | EMP-01 | **none (unauthorized)** |

**Missing ledger entries:** PAY-2006 (duplicate cash receipt, in bank only) and REF-4001 (refund, in bank only).

## 13. Injected discrepancies (the investigation universe)

| ID | Type | Amount | Records involved | Root cause | Governing policy | Required approval | Expected resolution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DISC-0001 | Undocumented early-payment discount / partial payment | 500.00 USD | INV-1001, PAY-2001, BT-5004, LE for JE-8001/JE-8503, CN-3001 (draft) | Sales Manager EMP-06 granted a 500 discount verbally; credit note CN-3001 was drafted but never issued, so AR still carries 12,400 while cash received is 11,900 | POL-DISCOUNT-001 | Finance Manager EMP-02 (500–5,000 band) | Approve and post CN-3001 for 500.00 (Dr 4200 / Cr 1100), closing INV-1001 |
| DISC-0002 | Duplicate customer payment | 8,750.00 USD | INV-1002, PAY-2005, PAY-2006, BT-5001, BT-5002 | Bluepeak's AP system re-released the same payment run on 2026-08-19; the second receipt was never booked | POL-PAYMENT-001, POL-REFUND-001 | Finance Director EMP-04 (refund > 2,000) | Book PAY-2006 to 1950 Unapplied Cash, then refund 8,750 to CUST-1002 |
| DISC-0003 | Timing difference (cut-off) | 4,300.00 USD | PAY-2008, BT-5006, JE-8505 | Bank value-dated the 2026-08-31 transfer to 2026-09-01; ledger recorded it in August | POL-RECON-001, POL-PERIOD-001 | None — documented reconciling item | Record as an outstanding deposit in the August bank reconciliation; no adjustment |
| DISC-0004 | Incorrect exchange rate | 315.00 USD | INV-1004, JE-8004, PAY-2009, BT-6001 | The ledger interface used the stale July rate 1.0500 instead of 1.0850 on 2026-08-11 | POL-ADJUST-001 | Staff Accountant EMP-01 (< 10,000) | Post FX correction of 315.00 (Dr 1100 / Cr 6900) |
| DISC-0005 | Missing ledger entry for refund | 1,250.00 USD | REF-4001, BT-5007, CUST-1005, INV-1005 | Refund was paid manually from the bank portal, bypassing the refund workflow, so no journal entry was created | POL-REFUND-001, POL-ACCESS-001 | Sales Manager EMP-06 approved verbally; retrospective Finance Manager EMP-02 approval required | Post refund entry (Dr 1100 / Cr 1000) and raise an access-control exception |
| DISC-0006 | Payment applied to wrong invoice / entity-resolution failure | 2,200.00 USD | PAY-2010, BT-5005, INV-1006, INV-1003 | Auto-matcher read `ACME INCORP 8859` and matched on amount to an open Corvus invoice; INV-1006 shows unpaid and INV-1003 shows overpaid | POL-PAYMENT-001, POL-RECON-001 | Staff Accountant EMP-01 | Re-allocate PAY-2010 from INV-1003 to INV-1006 |
| DISC-0007 | Unauthorized journal adjustment | 14,000.00 USD | JE-9007, accounts 1100 and 1900 | EMP-01 posted a 14,000 AR-to-Suspense adjustment above their 10,000 authority with no approver recorded | POL-JE-001, POL-ADJUST-001, POL-APPROVAL-001 | Finance Manager EMP-02, escalate to Controller EMP-03 | Reverse JE-9007, re-post with approval, log a control exception |
| DISC-0008 | Duplicate invoice | 8,750.00 USD | INV-1008, INV-1002, PO-BLU-2210 | Billing run for PO-BLU-2210 executed twice after a failed batch; INV-1008 duplicates INV-1002 | POL-CREDITNOTE-001 | Finance Manager EMP-02 (credit note ≤ 5,000 → exceeds, escalate to EMP-04) | Cancel INV-1008 via credit note CN-3002 with Finance Director approval |
| DISC-0009 | Expense amount mismatch (transposition) | 360.00 USD | EXP-7002, BT-5008, JE-8507, VEND-2002 | 3,400.00 keyed as 3,040.00 | POL-ADJUST-001 | Staff Accountant EMP-01 | Post correcting entry of 360.00 (Dr 6100 / Cr 2000) |

## 14. Approvals on record

| Approval | Action | Amount | Requested by | Approver | Status | Date |
| --- | --- | --- | --- | --- | --- | --- |
| APR-6001 | Discount on INV-1001 | 500.00 | EMP-06 | EMP-02 | **missing — never requested** | — |
| APR-6002 | Refund of duplicate payment PAY-2006 | 8,750.00 | EMP-07 | EMP-04 | pending | 2026-09-02 |
| APR-6003 | FX correction for DISC-0004 | 315.00 | EMP-01 | EMP-01 (self, within authority) | approved | 2026-09-03 |
| APR-6004 | Journal JE-9007 | 14,000.00 | EMP-01 | — | **absent (control breach)** | — |
| APR-6005 | Cancel INV-1008 via CN-3002 | 8,750.00 | EMP-01 | EMP-04 | pending | 2026-09-03 |

## 15. Investigations

| ID | Discrepancy | Investigator | Status | Confidence | Root cause |
| --- | --- | --- | --- | --- | --- |
| INVG-7001 | DISC-0001 | AI agent + EMP-01 | complete | 0.92 | Unapproved 500 discount, credit note never issued |
| INVG-7002 | DISC-0002 | AI agent + EMP-07 | complete | 0.88 | Customer double-released payment run |
| INVG-7003 | DISC-0006 | AI agent + EMP-01 | complete | 0.81 | Entity-resolution failure in auto-matcher |
| INVG-7004 | DISC-0007 | EMP-03 | escalated | 0.95 | Authority limit breach |

## 16. Policy register

| Policy ID | Document | Version | Effective |
| --- | --- | --- | --- |
| POL-PAYMENT-001 | policies/payment_policy.md | 3.2 | 2026-01-01 |
| POL-DISCOUNT-001 | policies/discount_policy.md | 4.0 | 2026-04-01 |
| POL-REFUND-001 | policies/refund_policy.md | 2.1 | 2026-01-01 |
| POL-CREDITNOTE-001 | policies/credit_note_policy.md | 2.0 | 2025-10-01 |
| POL-JE-001 | policies/journal_entry_policy.md | 5.1 | 2026-01-01 |
| POL-ADJUST-001 | policies/adjustment_policy.md | 3.0 | 2026-01-01 |
| POL-WRITEOFF-001 | policies/writeoff_policy.md | 2.2 | 2025-07-01 |
| POL-RECON-001 | policies/reconciliation_policy.md | 4.1 | 2026-02-01 |
| POL-CLOSE-001 | policies/month_end_close_policy.md | 3.3 | 2026-01-01 |
| POL-APPROVAL-001 | policies/approval_matrix.md | 6.0 | 2026-04-01 |
| POL-ACCESS-001 | policies/access_control_policy.md | 2.4 | 2026-01-01 |
| POL-PERIOD-001 | policies/accounting_period_policy.md | 1.8 | 2025-04-01 |
| POL-EXCEPTION-001 | policies/exception_management_policy.md | 2.0 | 2026-01-01 |

## 17. Authority thresholds (canonical — approval_matrix.md must match exactly)

| Action | Band | Approver |
| --- | --- | --- |
| Discount | < 500 | Sales Manager (EMP-06) |
| Discount | 500 – 5,000 | Finance Manager (EMP-02) |
| Discount | 5,000 – 10,000 | Finance Director (EMP-04) |
| Discount | > 10,000 | CFO (EMP-05) |
| Refund | < 2,000 | Sales Manager (EMP-06) |
| Refund | ≥ 2,000 | Finance Director (EMP-04) |
| Journal adjustment | < 10,000 | Staff Accountant (EMP-01) |
| Journal adjustment | 10,000 – 50,000 | Finance Manager (EMP-02) |
| Journal adjustment | > 50,000 | Finance Director (EMP-04) |
| Credit note | ≤ 5,000 | Finance Manager (EMP-02) |
| Credit note | > 5,000 | Finance Director (EMP-04) |
| Write-off | ≤ 5,000 | Finance Manager (EMP-02) |
| Write-off | > 5,000 | Controller (EMP-03) |
| Write-off | > 25,000 | CFO (EMP-05) |
| Period unlock | any | Controller (EMP-03) |
| Policy exception | any | CFO (EMP-05) |

## 18. The flagship trace (must appear consistently across the project)

```
INV-1001  Acme Incorporated       12,400.00
PAY-2001  customer payment        11,900.00
BT-5004   bank credit             11,900.00
Ledger    AR balance on INV-1001  12,400.00
                                 -----------
DISC-0001 difference                 500.00
      -> INVG-7001 investigation
      -> evidence: INV-1001 PDF, remittance advice, BT-5004 statement line, CN-3001 draft, email from EMP-06
      -> policy: POL-DISCOUNT-001 v4.0 (500 band -> Finance Manager)
      -> approval: APR-6001 missing, must be obtained from EMP-02
      -> adjustment: issue CN-3001 (Dr 4200 Sales Discounts 500 / Cr 1100 AR 500)
      -> verification: INV-1001 balance = 0, AR subledger ties to GL, bank reconciliation clears
```

## 19. Writing rules for all generated files

1. Only use IDs, names, dates and amounts from this file.
2. Amounts always two decimals; dates always ISO `YYYY-MM-DD` **except** in messy
   source documents, where varied formats are deliberate.
3. Cross-reference by ID (`DISC-0001`, `POL-DISCOUNT-001`, `INV-1001`) so the
   corpus is navigable as a graph.
4. Audience: an engineer new to accounting. Define terms before using them.
5. No real companies, people, banks or bank details.
