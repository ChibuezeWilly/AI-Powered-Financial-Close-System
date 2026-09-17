# Accounting Fundamentals

**Document ID:** KA-01
**Type:** accounting_knowledge
**Period covered:** 2026-08 (Meridian Instruments Ltd)
**Related canon IDs:** INV-1001, LE-9001, LE-9002, LE-9003, BT-5004, JE-8001
**Related policies:** POL-CLOSE-001, POL-PERIOD-001

---

## 1. Definition

Accounting is the discipline of identifying, recording, classifying, summarizing and reporting the financial events ("transactions") of a business so that management, owners, lenders, tax authorities and auditors can understand its financial position and performance. At Meridian Instruments Ltd, accounting is performed on an **accrual basis** — revenue and expenses are recorded when they are earned or incurred, not necessarily when cash moves. The company's fiscal year is the calendar year, and the period used throughout this knowledge base is **August 2026** (2026-08-01 to 2026-08-31).

A **transaction** is any economic event that changes the financial position of the company — issuing an invoice, receiving cash, paying a vendor, adjusting a balance. Every transaction is recorded as an **accounting record**, expressed in **debits and credits** (see document 10), and posted to an **account**.

An **account** is a named bucket that accumulates the value of one type of economic item (cash, receivables, revenue, etc.). The full list of accounts a company uses is its **chart of accounts (CoA)**.

### Meridian's chart of accounts (canon)

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

**Assets** are things the company owns or is owed (cash, AR). **Liabilities** are amounts the company owes others (AP, accrued liabilities). **Equity** is the residual claim of owners after liabilities are subtracted from assets. **Revenue** is value earned from customers (Product Revenue 4000, Service Revenue 4100). **Expenses** are costs incurred to earn that revenue (COGS 5000, Freight 6100). **Profit (or loss)** is Revenue minus Expenses for a period, and it flows into Retained Earnings (3000) at year end.

An **accounting period** is a defined span of time (a month, quarter or year) used to measure performance. Meridian closes its books monthly; the period in every canon example is **2026-08**. **Month-end** is the point at which a period's transactions are cut off so the period can be summarized. **Financial close** (or "the close") is the disciplined process of finalizing all transactions, reconciling all subledgers and bank accounts, resolving discrepancies, and locking the period so its numbers become final and reportable. Meridian's close deadline is working day 5 of the following month — 2026-09-05 for the August 2026 period.

## 2. Why it exists

Without a structured accounting system, a company cannot answer basic questions: How much cash do we have? Who owes us money? Are we profitable? Accounting exists to:

- Provide a faithful, auditable record of every economic event.
- Let management make decisions (pricing, staffing, investment) based on real numbers rather than guesses.
- Satisfy external requirements — tax authorities (Meridian's VAT ID GB 442 8871 09), lenders, and (if applicable) shareholders.
- Create a control environment: because every debit has an equal, offsetting credit, errors and fraud are structurally easier to detect (see document 10).
- Enable **reconciliation** — the comparison of independent records (invoices, payments, bank statements, ledger) to catch mistakes such as the nine discrepancies (DISC-0001 through DISC-0009) embedded in Meridian's August 2026 books.

## 3. Real-world example (canon)

On 2026-08-03, Meridian's Billing system issues **INV-1001** to Acme Incorporated (CUST-1001) for 12,000.00 USD of product plus 400.00 USD sales tax, totaling **12,400.00 USD**, against purchase order PO-ACM-8842. This single business event triggers a full accounting lifecycle:

```text
Business Event                Transaction            Accounting Record        General Ledger              Financial Statements     Financial Close
---------------                -----------            ------------------        --------------              ---------------------     ---------------
Meridian ships goods    -->    Invoice INV-1001  -->  Journal JE-8001      -->  LE-9001 Dr 1100 12,400  -->  Balance Sheet: AR up  --> Period 2026-08
to Acme Incorporated           issued 2026-08-03      recorded in Ledgerline    LE-9002 Cr 4000 12,000       Income Stmt: Revenue      locked 2026-09-05
                                                                                LE-9003 Cr 2200    400        up 12,000                 after all discrepancies
                                                                                                              (DISC-0001..0009)
                                                                                                              investigated
```

The invoice is later **partially paid**: on 2026-08-28 Acme sends PAY-2001 for 11,900.00 USD (a 500.00 discount was verbally promised but never formally credited — this is DISC-0001, covered in document 05). The bank confirms the cash arrival as BT-5004.

## 4. Important fields

| Field | Type | Example value from canon | Notes |
| --- | --- | --- | --- |
| account | string (4-digit code) | `1100` (Accounts Receivable) | Identifies the CoA bucket a debit/credit posts to |
| account_type | enum | Asset | Determines normal balance side |
| period | string `YYYY-MM` | `2026-08` | The accounting period a transaction is assigned to |
| transaction_date | date | `2026-08-03` (INV-1001) | Date the underlying business event occurred |
| posting_date | date | `2026-08-03` (JE-8001) | Date the journal is posted to the ledger |
| debit | decimal | 12,400.00 (LE-9001) | Increases asset/expense accounts |
| credit | decimal | 12,000.00 (LE-9002) | Increases liability/equity/revenue accounts |
| currency | ISO code | USD, EUR | Meridian reports in USD; EUR transactions (INV-1004) must be converted |

## 5. How it relates to other financial records

Accounting fundamentals underpin every other document in this knowledge base. The chart of accounts is the skeleton onto which invoices (05), payments (06), bank transactions (07), general ledger postings (08) and journal entries (09) all attach. Financial statements (02) are simply aggregations of ledger account balances at period end.

### Operational record vs accounting record vs bank record vs source document

A single business event produces **four different kinds of records**, and confusing them is the root of many discrepancies:

| Record type | What it is | Canon example | Who "owns" it |
| --- | --- | --- | --- |
| Source document | The original evidence of a transaction | The INV-1001 PDF sent to Acme, showing line items, tax, PO-ACM-8842 | Billing system output; often the exhibit an auditor asks for |
| Operational record | The subledger/business record derived from the source document | The invoices.csv row for INV-1001 (status `partially_paid`, balance 500.00) | AR subledger (Meridian Billing) |
| Accounting record | The double-entry journal representation | JE-8001 → LE-9001 (Dr 1100 12,400.00), LE-9002 (Cr 4000 12,000.00), LE-9003 (Cr 2200 400.00) | General ledger (Ledgerline) |
| Bank record | An independent statement from a third party (the bank) | BT-5004: credit of 11,900.00 USD on 2026-08-28, description `ACME INC INV1001 PMT` | First Meridian Bank, external to Meridian's own systems |

```text
                 +------------------+
                 | Source Document  |   INV-1001 PDF (12,400.00, PO-ACM-8842)
                 +------------------+
                          |
                          v
 +--------------------+       +---------------------+       +------------------+
 | Operational Record |  -->  | Accounting Record    |  -->  | Bank Record      |
 | invoices.csv row   |       | LE-9001/9002/9003     |       | BT-5004 (11,900) |
 | balance=500.00     |       | (JE-8001)             |       | independent      |
 +--------------------+       +---------------------+       +------------------+
```

Because the bank record (BT-5004, 11,900.00) never matches the accounting record's AR balance (12,400.00) without a credit note, the difference of 500.00 becomes **DISC-0001** — proof that reconciliation must compare all four layers, not just one.

## 6. Common mistakes

- Treating the operational record (invoice status) as automatically correct without checking the ledger — INV-1001 says "partially_paid" but does not by itself explain *why* 500.00 is missing.
- Assuming the bank record and the accounting record are the same thing; they are produced by independent systems and can diverge (see DISC-0002, DISC-0003, DISC-0005).
- Posting a transaction to the wrong account (e.g., mixing up 4000 Product Revenue and 4100 Service Revenue, as correctly kept separate for INV-1003's service revenue).
- Failing to close a period on time, allowing late edits that break comparability (POL-PERIOD-001 governs period locking).
- Forgetting that a **contra account** (1190 Allowance for Doubtful Accounts, 4200 Sales Discounts) moves in the opposite direction to its parent account type.

## 7. How reconciliation uses it

Reconciliation exists precisely because the operational, accounting and bank records are separate. Meridian's reconciliation tolerance is **USD 1.00 or 0.1% of the lower amount, whichever is greater** (per CANON.md). Any difference above tolerance — like the 500.00 gap on INV-1001 — is flagged as a discrepancy and routed to an investigation (INVG-7001).

## 8. How discrepancies can occur

Fundamentals-level failures that cascade into the nine canon discrepancies include: verbal approvals not translated into postings (DISC-0001), duplicate system runs (DISC-0002, DISC-0008), stale reference data such as FX rates (DISC-0004), manual/off-system actions bypassing the ledger (DISC-0005), entity-resolution errors matching the wrong customer/invoice (DISC-0006), and journal entries posted outside authority limits (DISC-0007).

## 9. Example database representation

```sql
CREATE TABLE chart_of_accounts (
    account_code    VARCHAR(4)   PRIMARY KEY,
    account_name    VARCHAR(100) NOT NULL,
    account_type    VARCHAR(20)  NOT NULL, -- Asset, Liability, Equity, Revenue, Expense
    normal_balance  VARCHAR(6)   NOT NULL  -- Debit or Credit
);

INSERT INTO chart_of_accounts VALUES
 ('1100','Accounts Receivable','Asset','Debit'),
 ('4000','Product Revenue','Revenue','Credit'),
 ('2200','Sales Tax Payable','Liability','Credit');

CREATE TABLE ledger_entries (
    ledger_entry_id VARCHAR(10) PRIMARY KEY,
    journal_id      VARCHAR(10) NOT NULL,
    entry_date      DATE NOT NULL,
    accounting_period VARCHAR(7) NOT NULL,
    account         VARCHAR(4) REFERENCES chart_of_accounts(account_code),
    debit           NUMERIC(12,2) DEFAULT 0,
    credit          NUMERIC(12,2) DEFAULT 0,
    currency        VARCHAR(3),
    description     VARCHAR(200),
    invoice_id      VARCHAR(10)
);

INSERT INTO ledger_entries VALUES
 ('LE-9001','JE-8001','2026-08-03','2026-08','1100',12400.00,0.00,'USD','AR - INV-1001','INV-1001'),
 ('LE-9002','JE-8001','2026-08-03','2026-08','4000',0.00,12000.00,'USD','Product revenue - INV-1001','INV-1001'),
 ('LE-9003','JE-8001','2026-08-03','2026-08','2200',0.00,400.00,'USD','Sales tax - INV-1001','INV-1001');
```

## 10. Example investigation scenario

**Scenario:** A new engineer joins Meridian's finance-tech team and is told "AR for Acme is wrong." Walking the four record layers: (1) the source document (INV-1001 PDF) says 12,400.00 is owed; (2) the operational record (invoices.csv) shows `balance=500.00`, status `partially_paid`; (3) the accounting record shows LE-9001 (Dr 1100 12,400.00) and LE-9026 (Cr 1100 11,900.00 from PAY-2001), leaving a ledger balance of exactly 500.00 — consistent with the operational record; (4) the bank record BT-5004 confirms only 11,900.00 was ever received. All records agree that 500.00 is outstanding — the real question is *why*. Checking CN-3001 (a draft credit note for exactly 500.00, never issued) and the approvals register (APR-6001, "missing — never requested") reveals the root cause: Sales Manager EMP-06 verbally promised a discount that was never formally approved or posted. This is DISC-0001, resolved by Finance Manager EMP-02 approving and posting CN-3001 (Dr 4200 Sales Discounts / Cr 1100 Accounts Receivable, 500.00).

## 11. Relevant terminology

| Term | Definition |
| --- | --- |
| Transaction | An economic event that changes financial position |
| Account | A named bucket accumulating one type of financial item |
| Chart of accounts | The complete list of accounts a company uses |
| Asset | Something owned or owed to the company |
| Liability | Something the company owes |
| Equity | Owners' residual claim on assets after liabilities |
| Revenue | Value earned from customers |
| Expense | Cost incurred to earn revenue |
| Accounting period | A defined span of time used for reporting |
| Fiscal year | A company's 12-month reporting year (calendar year for Meridian) |
| Month-end | The cutoff point closing a monthly period |
| Financial close | The process of finalizing and locking a period's books |

## 12. Relationship to financial close

Every concept in this document exists in service of a clean financial close. The close cannot happen until every transaction for the period (2026-08) is recorded in the correct account, every subledger (AR, AP, bank) ties to the general ledger, and every discrepancy above the materiality threshold (USD 2,500) is investigated and resolved or explained. Meridian's close deadline is 2026-09-05; open items like DISC-0007 (unauthorized 14,000.00 adjustment) are severity "critical" precisely because they threaten the integrity of the close.
