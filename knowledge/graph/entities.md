# Entities — Node Label Reference

All 22 canonical node labels, each with purpose, primary ID, properties, source table, relationships, and a worked Cypher `CREATE` using a real canon record. Property types and full column lists are defined in `graph_schema.md`; this file focuses on meaning and usage.

---

## Company

**Purpose:** Root anchor node for the single fictional entity, Meridian Instruments Ltd, so every other node can (optionally) be traced back to one company in a multi-tenant graph.
**Primary ID:** `company_id`
**Properties**
| Name | Type | Required | Example |
| --- | --- | --- | --- |
| company_id | string | yes | `MERIDIAN-01` |
| legal_name | string | yes | `Meridian Instruments Ltd` |
| reporting_currency | string | yes | `USD` |
**Source table:** CANON.md §1 (no CSV)
**Relationships:** out: none required; conceptually owns all other nodes (not modelled as edges to keep the graph lean).
**Example**
```cypher
CREATE (c:Company {company_id: 'MERIDIAN-01', legal_name: 'Meridian Instruments Ltd', trading_name: 'Meridian Instruments', reporting_currency: 'USD', fiscal_year: 'Calendar', materiality_threshold: 2500.00});
```

---

## Customer

**Purpose:** The billed party for an invoice; the anchor for AR history and entity-resolution work (aliases seen in bank/remittance text).
**Primary ID:** `customer_id`
**Properties:** see `graph_schema.md` §2 Customer table. Example: `CUST-1001`, `Acme Incorporated`, `USA`, `NET30`, `50000.00`.
**Source table:** `data/customers.csv`
**Relationships:**
- out: `CUSTOMER_HAS_INVOICE` → Invoice; `CUSTOMER_MADE_PAYMENT` → Payment
- in: `ALIAS_OF` (alias string node → Customer); `PAYMENT_FOR_CUSTOMER` (Payment → Customer)
**Example**
```cypher
CREATE (c:Customer {customer_id: 'CUST-1001', name: 'Acme Incorporated', legal_name: 'Acme Incorporated', country: 'USA', currency: 'USD', payment_terms: 'NET30', credit_limit: 50000.00, contact_name: 'Dana Whitfield', contact_email: 'ap@acme-inc.example', created_at: date('2023-02-14')});
```

---

## Vendor

**Purpose:** Supplier paid via Accounts Payable; anchors Expense records.
**Primary ID:** `vendor_id`
**Properties:** see schema. Example: `VEND-2002`, `Northline Freight`, `Freight`, `NET30`.
**Source table:** `data/vendors.csv`
**Relationships:** out: none defined beyond being referenced; in: `Expense` → Vendor is implicit via `vendor_id` property, modelled with a direct edge for query convenience: `(Expense)-[:EXPENSE_FOR_VENDOR]->(Vendor)` — not in canonical list, so instead expose via `LedgerEntry.vendor_id` and `Expense.vendor_id` properties queried directly (no dedicated relationship type is defined for Vendor in the canonical relationship list; joins are done on property equality in Cypher, see `graph_queries.md`).
**Example**
```cypher
CREATE (v:Vendor {vendor_id: 'VEND-2002', name: 'Northline Freight', category: 'Freight', country: 'USA', currency: 'USD', payment_terms: 'NET30'});
```

---

## Employee

**Purpose:** Individual staff member; holds approval authority and posts/approves journal entries.
**Primary ID:** `employee_id`
**Properties:** see schema. Example: `EMP-02`, `Tomas Weller`, `Finance Manager`, authority `50000.00`.
**Source table:** `data/employees.csv`
**Relationships:**
- out: `EMPLOYEE_IN_DEPARTMENT` → Department; `EMPLOYEE_HOLDS_AUTHORITY` → Policy (or an authority band, expressed as a property on the edge)
- in: `APPROVAL_APPROVES_ACTION` originates from Approval, which references `approver_employee_id`; `ACTION_REQUIRES_APPROVAL` connects an action to Approval, not directly to Employee
**Example**
```cypher
CREATE (e:Employee {employee_id: 'EMP-02', name: 'Tomas Weller', role: 'Finance Manager', department_id: 'DEPT-FIN', approval_authority_usd: 50000.00, can_post_journals: true, can_lock_period: false});
```

---

## Department

**Purpose:** Groups employees for organisational and segregation-of-duties queries.
**Primary ID:** `department_id`
**Properties:** `department_id`, `name`.
**Source table:** derived from `data/employees.csv` (`department_id`, `department` columns), deduplicated.
**Relationships:** in: `EMPLOYEE_IN_DEPARTMENT` (Employee → Department).
**Example**
```cypher
CREATE (d:Department {department_id: 'DEPT-FIN', name: 'Finance'});
```

---

## BankAccount

**Purpose:** Real-world bank account that receives/pays cash; anchor for reconciliation.
**Primary ID:** `bank_account_id`
**Properties:** see schema. Example: `BANK-USD-01`, First Meridian Bank, GL account `1000`.
**Source table:** `data/bank_accounts.csv`
**Relationships:** in: `BankTransaction` posts to it (`(BankTransaction)-[:POSTED_TO_BANK_ACCOUNT]->(BankAccount)` — implemented via property `bank_account_id`; canonical relationship list does not define a dedicated type, so this join is done through `LEDGER_ENTRY_POSTED_TO_ACCOUNT` against the account's `gl_account`, and directly in queries via `bank_account_id` equality).
**Example**
```cypher
CREATE (b:BankAccount {bank_account_id: 'BANK-USD-01', bank_name: 'First Meridian Bank', account_masked: '****4471', identifier: 'ABA 011500120 / 30084471', currency: 'USD', gl_account: '1000', opening_balance_2026_08_01: 184300.00, closing_balance_2026_08_31: 217150.00});
```

---

## Invoice

**Purpose:** Bill issued to a customer; central node for AR investigations.
**Primary ID:** `invoice_id`
**Properties:** see schema. Example: `INV-1001`, total `12400.00`, status `partially_paid`.
**Source table:** `data/invoices.csv`
**Relationships:**
- in: `CUSTOMER_HAS_INVOICE` (Customer → Invoice)
- out: `INVOICE_HAS_LINE` → InvoiceLine; `INVOICE_PAID_BY` → Payment; `INVOICE_RECORDED_AS_LEDGER_ENTRY` → LedgerEntry; `INVOICE_HAS_CREDIT_NOTE` → CreditNote; `INVOICE_HAS_REFUND` → Refund; `INVOICE_REFERENCES_PURCHASE_ORDER` → PurchaseOrder
- in: `DISCREPANCY_INVOLVES_INVOICE` (Discrepancy → Invoice)
**Example**
```cypher
CREATE (i:Invoice {invoice_id: 'INV-1001', customer_id: 'CUST-1001', invoice_date: date('2026-08-03'), due_date: date('2026-09-02'), po_number: 'PO-ACM-8842', currency: 'USD', subtotal: 12000.00, discount: 0.00, tax: 400.00, total: 12400.00, amount_paid: 11900.00, balance: 500.00, status: 'partially_paid', accounting_period: '2026-08', journal_id: 'JE-8001', notes: 'Subject of DISC-0001'});
```

---

## InvoiceLine

**Purpose:** Individual product/service line on an invoice, ties revenue to a GL account.
**Primary ID:** `line_id`
**Properties:** see schema. Example: `IL-1001-1`, quantity `40`, unit price `250.00`.
**Source table:** `data/invoice_lines.csv`
**Relationships:** in: `INVOICE_HAS_LINE` (Invoice → InvoiceLine).
**Example**
```cypher
CREATE (l:InvoiceLine {line_id: 'IL-1001-1', invoice_id: 'INV-1001', line_no: 1, description: 'MI-400 Precision Caliper Set', quantity: 40, unit_price: 250.00, line_total: 10000.00, revenue_account: '4000'});
```

---

## Payment

**Purpose:** Customer cash receipt; central node for matching, duplicate detection and misallocation investigation.
**Primary ID:** `payment_id`
**Properties:** see schema. Example: `PAY-2010`, `2200.00`, reference `ACME INCORP 8859`.
**Source table:** `data/payments.csv` (allocation detail in `data/payment_allocations.csv`)
**Relationships:**
- in: `CUSTOMER_MADE_PAYMENT` (Customer → Payment); `INVOICE_PAID_BY` (Invoice → Payment)
- out: `PAYMENT_FOR_CUSTOMER` → Customer; `PAYMENT_MATCHED_TO_BANK_TRANSACTION` → BankTransaction
- in: `DISCREPANCY_INVOLVES_PAYMENT` (Discrepancy → Payment)
**Example**
```cypher
CREATE (p:Payment {payment_id: 'PAY-2010', customer_id: 'CUST-1001', payment_date: date('2026-08-29'), amount: 2200.00, currency: 'USD', method: 'bank_transfer', payment_reference: 'ACME INCORP 8859', bank_transaction_id: 'BT-5005', status: 'applied', unapplied_amount: 0.00, accounting_period: '2026-08', journal_id: 'JE-8504'});
```

---

## BankTransaction

**Purpose:** Line item on a bank statement; ground truth for cash movement, used for reconciliation and to detect timing differences / unmatched items.
**Primary ID:** `bank_transaction_id`
**Properties:** see schema. Example: `BT-5007`, debit `1250.00`, `reconciliation_status: unmatched`.
**Source table:** `data/bank_transactions.csv`
**Relationships:**
- in: `PAYMENT_MATCHED_TO_BANK_TRANSACTION` (Payment → BankTransaction)
- in: `DISCREPANCY_INVOLVES_BANK_TRANSACTION`
**Example**
```cypher
CREATE (bt:BankTransaction {bank_transaction_id: 'BT-5007', bank_account_id: 'BANK-USD-01', transaction_date: date('2026-08-30'), value_date: date('2026-08-30'), direction: 'debit', amount: 1250.00, currency: 'USD', description: 'REFUND EASTPORT MARINE', counterparty_raw: 'EASTPORT MARINE SVCS', statement_id: 'STMT-USD-2026-08', matched_payment_id: null, matched_ledger_entry_id: null, reconciliation_status: 'unmatched'});
```

---

## Account

**Purpose:** Chart-of-accounts node; every ledger posting resolves to one.
**Primary ID:** `account`
**Properties:** see schema. Example: `1900`, `Suspense`, `is_clearing: true`.
**Source table:** `data/chart_of_accounts.csv`
**Relationships:** in: `LEDGER_ENTRY_POSTED_TO_ACCOUNT` (LedgerEntry → Account); `JOURNAL_ENTRY_AFFECTS_ACCOUNT` (JournalEntry → Account).
**Example**
```cypher
CREATE (a:Account {account: '1900', name: 'Suspense', type: 'asset', normal_balance: 'debit', is_clearing: true, requires_monthly_reconciliation: true});
```

---

## LedgerEntry

**Purpose:** Single debit/credit line posted to the general ledger; the atomic unit of financial truth.
**Primary ID:** `ledger_entry_id`
**Properties:** see schema. Example: `LE-9035`, account `1900`, debit `14000.00`.
**Source table:** `data/ledger_entries.csv`
**Relationships:**
- in: `INVOICE_RECORDED_AS_LEDGER_ENTRY` (Invoice → LedgerEntry); `JOURNAL_ENTRY_HAS_LINE` (JournalEntry → LedgerEntry)
- out: `LEDGER_ENTRY_POSTED_TO_ACCOUNT` → Account
- in: `DISCREPANCY_INVOLVES_LEDGER_ENTRY`
**Example**
```cypher
CREATE (le:LedgerEntry {ledger_entry_id: 'LE-9035', journal_id: 'JE-9007', entry_date: date('2026-08-31'), accounting_period: '2026-08', account: '1900', debit: 14000.00, credit: 0.00, currency: 'USD', description: 'Unauthorized AR to Suspense adjustment'});
```

---

## JournalEntry

**Purpose:** A balanced set of ledger lines posted in one transaction; the unit of approval and authority control.
**Primary ID:** `journal_id`
**Properties:** see schema. Example: `JE-9007`, `is_adjustment: true`, `approved_by: null` (unauthorized).
**Source table:** `data/journal_entries.csv`
**Relationships:**
- out: `JOURNAL_ENTRY_HAS_LINE` → LedgerEntry; `JOURNAL_ENTRY_AFFECTS_ACCOUNT` → Account
- in: `ACTION_REQUIRES_APPROVAL` (JournalEntry → Approval, as the action)
**Example**
```cypher
CREATE (j:JournalEntry {journal_id: 'JE-9007', entry_date: date('2026-08-31'), accounting_period: '2026-08', description: 'Manual AR to Suspense adjustment', source: 'manual', prepared_by: 'EMP-01', approved_by: null, approval_id: null, status: 'posted', is_adjustment: true, total_debit: 14000.00, total_credit: 14000.00});
```

---

## Expense

**Purpose:** Vendor bill/expense record; anchors AP-side transposition and mismatch investigations.
**Primary ID:** `expense_id`
**Properties:** see schema. Example: `EXP-7002`, invoiced `3400.00`, recorded `3040.00`.
**Source table:** `data/expenses.csv`
**Relationships:** out: relates to Vendor (`vendor_id` property join), BankTransaction (`bank_transaction_id`), JournalEntry (`journal_id`) — no dedicated canonical relationship type; queried by property equality (see `graph_queries.md`).
**Example**
```cypher
CREATE (x:Expense {expense_id: 'EXP-7002', vendor_id: 'VEND-2002', expense_date: date('2026-08-12'), amount_invoiced: 3400.00, amount_recorded: 3040.00, currency: 'USD', category: 'Freight', gl_account: '6100', bank_transaction_id: 'BT-5008', journal_id: 'JE-8507', status: 'mismatch'});
```

---

## PurchaseOrder

**Purpose:** Customer purchase order that authorizes an invoice; used to detect duplicate billing runs.
**Primary ID:** `po_number`
**Properties:** see schema. Example: `PO-BLU-2210`, amount `8750.00`, `fulfilled (once)`.
**Source table:** `data/purchase_orders.csv`
**Relationships:** in: `INVOICE_REFERENCES_PURCHASE_ORDER` (Invoice → PurchaseOrder).
**Example**
```cypher
CREATE (po:PurchaseOrder {po_number: 'PO-BLU-2210', customer_id: 'CUST-1002', po_date: date('2026-08-01'), currency: 'USD', amount: 8750.00, status: 'fulfilled'});
```

---

## CreditNote

**Purpose:** Reduces an invoice balance; may be draft/proposed and thus a root cause when not posted.
**Primary ID:** `credit_note_id`
**Properties:** see schema. Example: `CN-3001`, `500.00`, `status: draft`.
**Source table:** `data/credit_notes.csv`
**Relationships:**
- in: `INVOICE_HAS_CREDIT_NOTE` (Invoice → CreditNote)
- out: `ACTION_REQUIRES_APPROVAL` → Approval
**Example**
```cypher
CREATE (cn:CreditNote {credit_note_id: 'CN-3001', invoice_id: 'INV-1001', customer_id: 'CUST-1001', issue_date: date('2026-08-27'), amount: 500.00, currency: 'USD', reason: 'Early-payment discount agreed verbally by Sales', status: 'draft', approval_id: 'APR-6001'});
```

---

## Refund

**Purpose:** Cash returned to a customer; may bypass ledger and workflow.
**Primary ID:** `refund_id`
**Properties:** see schema. Example: `REF-4001`, `1250.00`, `paid_not_recorded`.
**Source table:** `data/refunds.csv`
**Relationships:** in: `INVOICE_HAS_REFUND` (Invoice → Refund).
**Example**
```cypher
CREATE (r:Refund {refund_id: 'REF-4001', customer_id: 'CUST-1005', invoice_id: 'INV-1005', refund_date: date('2026-08-30'), amount: 1250.00, currency: 'USD', method: 'bank_transfer', reason: 'Damaged depth gauge returned', bank_transaction_id: 'BT-5007', status: 'paid_not_recorded'});
```

---

## Policy

**Purpose:** Governing document/version that a transaction type must comply with.
**Primary ID:** `policy_id`
**Properties:** see schema. Example: `POL-DISCOUNT-001`, version `4.0`.
**Source table:** `data/policies.csv`
**Relationships:**
- in: `TRANSACTION_REQUIRES_POLICY` (action/discrepancy → Policy)
- out: `EMPLOYEE_HOLDS_AUTHORITY` originates from Employee, references Policy indirectly through Approval's `required_approver_role`
**Example**
```cypher
CREATE (pol:Policy {policy_id: 'POL-DISCOUNT-001', title: 'Customer Discount Policy', version: '4.0', effective_date: date('2026-04-01'), owner_employee_id: 'EMP-04', document_path: 'knowledge/policies/discount_policy.md'});
```

---

## Approval

**Purpose:** Records a required or granted sign-off for a financial action; may be `missing`/`absent` (negative evidence).
**Primary ID:** `approval_id`
**Properties:** see schema. Example: `APR-6001`, `status: missing`.
**Source table:** `data/approvals.csv`
**Relationships:**
- out: `APPROVAL_APPROVES_ACTION` → the action node (Adjustment/CreditNote/Refund/JournalEntry)
- in: `ACTION_REQUIRES_APPROVAL` (action → Approval)
**Example**
```cypher
CREATE (apr:Approval {approval_id: 'APR-6001', action_type: 'discount', subject_id: 'INV-1001', amount: 500.00, currency: 'USD', requested_by: 'EMP-06', required_approver_role: 'Finance Manager', approver_employee_id: null, status: 'missing', policy_id: 'POL-DISCOUNT-001', note: 'Never requested - root cause of DISC-0001'});
```

---

## Discrepancy

**Purpose:** A detected financial anomaly; the entry point for every investigation.
**Primary ID:** `discrepancy_id`
**Properties:** see schema. Example: `DISC-0006`, `payment_applied_to_wrong_invoice`, `2200.00`.
**Source table:** `data/discrepancies.csv`
**Relationships:**
- out: `DISCREPANCY_INVOLVES_INVOICE`, `DISCREPANCY_INVOLVES_PAYMENT`, `DISCREPANCY_INVOLVES_BANK_TRANSACTION`, `DISCREPANCY_INVOLVES_LEDGER_ENTRY`, `TRANSACTION_REQUIRES_POLICY`
- in: `INVESTIGATION_INVESTIGATES_DISCREPANCY` (Investigation → Discrepancy); `ADJUSTMENT_RESOLVES_DISCREPANCY` (Adjustment → Discrepancy); `RECOMMENDATION_FOR_DISCREPANCY`
**Example**
```cypher
CREATE (d:Discrepancy {discrepancy_id: 'DISC-0006', type: 'payment_applied_to_wrong_invoice', detected_on: date('2026-09-02'), detected_by: 'ar_aging_review', amount: 2200.00, currency: 'USD', accounting_period: '2026-08', severity: 'medium', status: 'under_investigation', root_cause_summary: 'Entity-resolution failure on ACME INCORP 8859'});
```

---

## Investigation

**Purpose:** The record of an inquiry into one discrepancy, including AI/human investigator, confidence and recommendation.
**Primary ID:** `investigation_id`
**Properties:** see schema. Example: `INVG-7003`, confidence `0.81`.
**Source table:** `data/investigations.csv`
**Relationships:**
- out: `INVESTIGATION_INVESTIGATES_DISCREPANCY` → Discrepancy; `INVESTIGATION_USED_EVIDENCE` → evidence nodes (Invoice/Payment/BankTransaction/LedgerEntry/CreditNote etc.); `RECOMMENDATION_FOR_DISCREPANCY` → Discrepancy
**Example**
```cypher
CREATE (inv:Investigation {investigation_id: 'INVG-7003', discrepancy_id: 'DISC-0006', opened_on: date('2026-09-02'), investigator: 'ai_agent+EMP-01', status: 'complete', confidence: 0.81, root_cause_code: 'RC-ENTITY-RESOLUTION-FAILURE', recommendation: 'Re-allocate PAY-2010 from INV-1003 to INV-1006', adjustment_id: 'ADJ-5003'});
```

---

## Adjustment

**Purpose:** The proposed or posted correcting journal that resolves a discrepancy.
**Primary ID:** `adjustment_id`
**Properties:** see schema. Example: `ADJ-5001`, debit `4200`, credit `1100`, `500.00`.
**Source table:** `data/adjustments.csv`
**Relationships:**
- out: `ADJUSTMENT_RESOLVES_DISCREPANCY` → Discrepancy; `ACTION_REQUIRES_APPROVAL` → Approval
**Example**
```cypher
CREATE (adj:Adjustment {adjustment_id: 'ADJ-5001', discrepancy_id: 'DISC-0001', investigation_id: 'INVG-7001', proposed_on: date('2026-09-03'), accounting_period: '2026-08', debit_account: '4200', credit_account: '1100', amount: 500.00, currency: 'USD', status: 'awaiting_approval', requires_approval_role: 'Finance Manager', approval_id: 'APR-6001', verification_check: 'INV-1001 balance equals 0.00'});
```
