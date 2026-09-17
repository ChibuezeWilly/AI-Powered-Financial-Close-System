# Graph Schema — Meridian Instruments Ltd Financial Knowledge Graph

Scope: August 2026 close period. All IDs below are canon IDs from `knowledge/CANON.md` and `data/*.csv`. This document is the schema of record; `entities.md` and `relationships.md` must stay consistent with it.

## 1. Label list

| # | Label | Source table (data/) |
| --- | --- | --- |
| 1 | Company | CANON.md §1 (no CSV; single row) |
| 2 | Customer | customers.csv |
| 3 | Vendor | vendors.csv |
| 4 | Employee | employees.csv |
| 5 | Department | employees.csv (department_id, department) |
| 6 | BankAccount | bank_accounts.csv |
| 7 | Invoice | invoices.csv |
| 8 | InvoiceLine | invoice_lines.csv |
| 9 | Payment | payments.csv |
| 10 | BankTransaction | bank_transactions.csv |
| 11 | Account | chart_of_accounts.csv |
| 12 | LedgerEntry | ledger_entries.csv |
| 13 | JournalEntry | journal_entries.csv |
| 14 | Expense | expenses.csv |
| 15 | PurchaseOrder | purchase_orders.csv |
| 16 | CreditNote | credit_notes.csv |
| 17 | Refund | refunds.csv |
| 18 | Policy | policies.csv |
| 19 | Approval | approvals.csv |
| 20 | Discrepancy | discrepancies.csv |
| 21 | Investigation | investigations.csv |
| 22 | Adjustment | adjustments.csv |

Additional supporting data files feed relationship properties rather than new labels: `entity_aliases.csv` → `ALIAS_OF` edges, `payment_allocations.csv` → properties on `INVOICE_HAS_LINE`/allocation edges (modelled as properties on `INVOICE_PAID_BY`), `fx_rates.csv` → properties on `JournalEntry`/`LedgerEntry` nodes.

## 2. Property tables

### Company
| Property | Type | Notes |
| --- | --- | --- |
| company_id | string (PK) | `MERIDIAN-01` (synthetic, single instance) |
| legal_name | string | Meridian Instruments Ltd |
| trading_name | string | Meridian Instruments |
| registration_no | string | 08842217 |
| vat_id | string | GB 442 8871 09 |
| reporting_currency | string | USD |
| fiscal_year | string | Calendar |
| materiality_threshold | float | 2500.00 |
| reconciliation_tolerance_note | string | "USD 1.00 or 0.1%, whichever greater" |

### Customer (customers.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| customer_id | string (PK) | yes | `CUST-1001` |
| name | string | yes | `Acme Incorporated` |
| legal_name | string | yes | `Acme Incorporated` |
| country | string | yes | `USA` |
| currency | string | yes | `USD` |
| payment_terms | string | yes | `NET30` |
| credit_limit | float | yes | `50000.00` |
| contact_name | string | no | `Dana Whitfield` |
| contact_email | string | no | `ap@acme-inc.example` |
| created_at | date | yes | `2023-02-14` |

### Vendor (vendors.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| vendor_id | string (PK) | yes | `VEND-2002` |
| name | string | yes | `Northline Freight` |
| category | string | yes | `Freight` |
| country | string | yes | `USA` |
| currency | string | yes | `USD` |
| payment_terms | string | yes | `NET30` |

### Employee (employees.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| employee_id | string (PK) | yes | `EMP-02` |
| name | string | yes | `Tomas Weller` |
| role | string | yes | `Finance Manager` |
| department_id | string | yes | `DEPT-FIN` |
| approval_authority_usd | float | no | `50000.00` |
| can_post_journals | boolean | yes | `true` |
| can_lock_period | boolean | yes | `false` |

### Department (derived from employees.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| department_id | string (PK) | yes | `DEPT-FIN` |
| name | string | yes | `Finance` |

### BankAccount (bank_accounts.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| bank_account_id | string (PK) | yes | `BANK-USD-01` |
| bank_name | string | yes | `First Meridian Bank` |
| account_masked | string | yes | `****4471` |
| identifier | string | yes | `ABA 011500120 / 30084471` |
| currency | string | yes | `USD` |
| gl_account | string | yes | `1000` |
| opening_balance_2026_08_01 | float | yes | `184300.00` |
| closing_balance_2026_08_31 | float | yes | `217150.00` |

### Invoice (invoices.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| invoice_id | string (PK) | yes | `INV-1001` |
| customer_id | string (FK) | yes | `CUST-1001` |
| invoice_date | date | yes | `2026-08-03` |
| due_date | date | yes | `2026-09-02` |
| po_number | string (FK) | no | `PO-ACM-8842` |
| currency | string | yes | `USD` |
| subtotal | float | yes | `12000.00` |
| discount | float | yes | `0.00` |
| tax | float | yes | `400.00` |
| total | float | yes | `12400.00` |
| amount_paid | float | yes | `11900.00` |
| balance | float | yes | `500.00` |
| status | string | yes | `partially_paid` |
| accounting_period | string | yes | `2026-08` |
| journal_id | string (FK) | yes | `JE-8001` |
| notes | string | no | `Subject of DISC-0001` |

### InvoiceLine (invoice_lines.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| line_id | string (PK) | yes | `IL-1001-1` |
| invoice_id | string (FK) | yes | `INV-1001` |
| line_no | int | yes | `1` |
| description | string | yes | `MI-400 Precision Caliper Set` |
| quantity | int | yes | `40` |
| unit_price | float | yes | `250.00` |
| line_total | float | yes | `10000.00` |
| revenue_account | string (FK) | yes | `4000` |

### Payment (payments.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| payment_id | string (PK) | yes | `PAY-2001` |
| customer_id | string (FK) | yes | `CUST-1001` |
| payment_date | date | yes | `2026-08-28` |
| amount | float | yes | `11900.00` |
| currency | string | yes | `USD` |
| method | string | yes | `bank_transfer` |
| payment_reference | string | yes | `ACME INC INV1001 PMT` |
| bank_transaction_id | string (FK) | yes | `BT-5004` |
| status | string | yes | `applied` |
| unapplied_amount | float | yes | `0.00` |
| accounting_period | string | yes | `2026-08` |
| journal_id | string (FK) | no | `JE-8503` |

### BankTransaction (bank_transactions.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| bank_transaction_id | string (PK) | yes | `BT-5004` |
| bank_account_id | string (FK) | yes | `BANK-USD-01` |
| transaction_date | date | yes | `2026-08-28` |
| value_date | date | yes | `2026-08-28` |
| direction | string | yes | `credit` |
| amount | float | yes | `11900.00` |
| currency | string | yes | `USD` |
| description | string | yes | `ACME INC INV1001 PMT` |
| counterparty_raw | string | yes | `ACME INC` |
| statement_id | string | yes | `STMT-USD-2026-08` |
| matched_payment_id | string (FK) | no | `PAY-2001` |
| matched_ledger_entry_id | string (FK) | no | `LE-9025` |
| reconciliation_status | string | yes | `matched` |

### Account (chart_of_accounts.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| account | string (PK) | yes | `1100` |
| name | string | yes | `Accounts Receivable` |
| type | string | yes | `asset` |
| normal_balance | string | yes | `debit` |
| is_clearing | boolean | yes | `false` |
| requires_monthly_reconciliation | boolean | yes | `true` |

### LedgerEntry (ledger_entries.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| ledger_entry_id | string (PK) | yes | `LE-9001` |
| journal_id | string (FK) | yes | `JE-8001` |
| entry_date | date | yes | `2026-08-03` |
| accounting_period | string | yes | `2026-08` |
| account | string (FK) | yes | `1100` |
| debit | float | yes | `12400.00` |
| credit | float | yes | `0.00` |
| currency | string | yes | `USD` |
| description | string | yes | `AR - INV-1001` |
| invoice_id | string (FK) | no | `INV-1001` |
| payment_id | string (FK) | no | `PAY-2001` |
| bank_transaction_id | string (FK) | no | `BT-5004` |
| customer_id | string (FK) | no | `CUST-1001` |
| vendor_id | string (FK) | no | `VEND-2002` |

### JournalEntry (journal_entries.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| journal_id | string (PK) | yes | `JE-9007` |
| entry_date | date | yes | `2026-08-31` |
| accounting_period | string | yes | `2026-08` |
| description | string | yes | `Manual AR to Suspense adjustment` |
| source | string | yes | `manual` |
| prepared_by | string (FK) | yes | `EMP-01` |
| approved_by | string (FK) | no | `` (empty = unauthorized) |
| approval_id | string (FK) | no | `` |
| status | string | yes | `posted` |
| is_adjustment | boolean | yes | `true` |
| total_debit | float | yes | `14000.00` |
| total_credit | float | yes | `14000.00` |

### Expense (expenses.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| expense_id | string (PK) | yes | `EXP-7002` |
| vendor_id | string (FK) | yes | `VEND-2002` |
| expense_date | date | yes | `2026-08-12` |
| amount_invoiced | float | yes | `3400.00` |
| amount_recorded | float | yes | `3040.00` |
| currency | string | yes | `USD` |
| category | string | yes | `Freight` |
| gl_account | string (FK) | yes | `6100` |
| bank_transaction_id | string (FK) | yes | `BT-5008` |
| journal_id | string (FK) | yes | `JE-8507` |
| status | string | yes | `mismatch` |

### PurchaseOrder (purchase_orders.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| po_number | string (PK) | yes | `PO-ACM-8842` |
| customer_id | string (FK) | yes | `CUST-1001` |
| po_date | date | yes | `2026-07-29` |
| currency | string | yes | `USD` |
| amount | float | yes | `12400.00` |
| status | string | yes | `fulfilled` |

### CreditNote (credit_notes.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| credit_note_id | string (PK) | yes | `CN-3001` |
| invoice_id | string (FK) | yes | `INV-1001` |
| customer_id | string (FK) | yes | `CUST-1001` |
| issue_date | date | yes | `2026-08-27` |
| amount | float | yes | `500.00` |
| currency | string | yes | `USD` |
| reason | string | yes | `Early-payment discount agreed verbally by Sales` |
| status | string | yes | `draft` |
| approval_id | string (FK) | no | `APR-6001` |
| approved_by | string (FK) | no | `` |
| journal_id | string (FK) | no | `` |

### Refund (refunds.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| refund_id | string (PK) | yes | `REF-4001` |
| customer_id | string (FK) | yes | `CUST-1005` |
| invoice_id | string (FK) | yes | `INV-1005` |
| refund_date | date | yes | `2026-08-30` |
| amount | float | yes | `1250.00` |
| currency | string | yes | `USD` |
| method | string | yes | `bank_transfer` |
| reason | string | yes | `Damaged depth gauge returned` |
| bank_transaction_id | string (FK) | no | `BT-5007` |
| journal_id | string (FK) | no | `` |
| approval_id | string (FK) | no | `` |
| status | string | yes | `paid_not_recorded` |

### Policy (policies.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| policy_id | string (PK) | yes | `POL-DISCOUNT-001` |
| title | string | yes | `Customer Discount Policy` |
| version | string | yes | `4.0` |
| effective_date | date | yes | `2026-04-01` |
| owner_employee_id | string (FK) | yes | `EMP-04` |
| document_path | string | yes | `knowledge/policies/discount_policy.md` |

### Approval (approvals.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| approval_id | string (PK) | yes | `APR-6001` |
| action_type | string | yes | `discount` |
| subject_id | string | yes | `INV-1001` |
| amount | float | yes | `500.00` |
| currency | string | yes | `USD` |
| requested_by | string (FK) | no | `EMP-06` |
| required_approver_role | string | yes | `Finance Manager` |
| approver_employee_id | string (FK) | no | `` |
| status | string | yes | `missing` |
| requested_at | date | no | `` |
| decided_at | date | no | `` |
| policy_id | string (FK) | yes | `POL-DISCOUNT-001` |
| note | string | no | `Never requested - root cause of DISC-0001` |

### Discrepancy (discrepancies.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| discrepancy_id | string (PK) | yes | `DISC-0001` |
| type | string | yes | `undocumented_discount_partial_payment` |
| detected_on | date | yes | `2026-09-01` |
| detected_by | string | yes | `bank_reconciliation_rule` |
| amount | float | yes | `500.00` |
| currency | string | yes | `USD` |
| accounting_period | string | yes | `2026-08` |
| severity | string | yes | `medium` |
| status | string | yes | `under_investigation` |
| root_cause_summary | string | yes | `Verbal 500 discount never approved or credited` |

### Investigation (investigations.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| investigation_id | string (PK) | yes | `INVG-7001` |
| discrepancy_id | string (FK) | yes | `DISC-0001` |
| opened_on | date | yes | `2026-09-01` |
| investigator | string | yes | `ai_agent+EMP-01` |
| status | string | yes | `complete` |
| confidence | float | yes | `0.92` |
| root_cause_code | string | yes | `RC-DISCOUNT-UNDOCUMENTED` |
| recommendation | string | yes | `Issue credit note CN-3001 for 500.00 after Finance Manager approval` |
| approval_id | string (FK) | no | `APR-6001` |
| adjustment_id | string (FK) | no | `ADJ-5001` |
| verified_on | date | no | `` |

### Adjustment (adjustments.csv)
| Property | Type | Required | Example |
| --- | --- | --- | --- |
| adjustment_id | string (PK) | yes | `ADJ-5001` |
| discrepancy_id | string (FK) | yes | `DISC-0001` |
| investigation_id | string (FK) | no | `INVG-7001` |
| proposed_on | date | yes | `2026-09-03` |
| accounting_period | string | yes | `2026-08` |
| debit_account | string (FK) | yes | `4200` |
| credit_account | string (FK) | yes | `1100` |
| amount | float | yes | `500.00` |
| currency | string | yes | `USD` |
| status | string | yes | `awaiting_approval` |
| requires_approval_role | string | yes | `Finance Manager` |
| approval_id | string (FK) | no | `APR-6001` |
| posted_journal_id | string (FK) | no | `` |
| verification_check | string | yes | `INV-1001 balance equals 0.00` |

## 3. Constraints and indexes

```cypher
// Uniqueness constraints (also create indexes implicitly)
CREATE CONSTRAINT company_id IF NOT EXISTS FOR (n:Company) REQUIRE n.company_id IS UNIQUE;
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (n:Customer) REQUIRE n.customer_id IS UNIQUE;
CREATE CONSTRAINT vendor_id IF NOT EXISTS FOR (n:Vendor) REQUIRE n.vendor_id IS UNIQUE;
CREATE CONSTRAINT employee_id IF NOT EXISTS FOR (n:Employee) REQUIRE n.employee_id IS UNIQUE;
CREATE CONSTRAINT department_id IF NOT EXISTS FOR (n:Department) REQUIRE n.department_id IS UNIQUE;
CREATE CONSTRAINT bank_account_id IF NOT EXISTS FOR (n:BankAccount) REQUIRE n.bank_account_id IS UNIQUE;
CREATE CONSTRAINT invoice_id IF NOT EXISTS FOR (n:Invoice) REQUIRE n.invoice_id IS UNIQUE;
CREATE CONSTRAINT invoice_line_id IF NOT EXISTS FOR (n:InvoiceLine) REQUIRE n.line_id IS UNIQUE;
CREATE CONSTRAINT payment_id IF NOT EXISTS FOR (n:Payment) REQUIRE n.payment_id IS UNIQUE;
CREATE CONSTRAINT bank_txn_id IF NOT EXISTS FOR (n:BankTransaction) REQUIRE n.bank_transaction_id IS UNIQUE;
CREATE CONSTRAINT account_id IF NOT EXISTS FOR (n:Account) REQUIRE n.account IS UNIQUE;
CREATE CONSTRAINT ledger_entry_id IF NOT EXISTS FOR (n:LedgerEntry) REQUIRE n.ledger_entry_id IS UNIQUE;
CREATE CONSTRAINT journal_id IF NOT EXISTS FOR (n:JournalEntry) REQUIRE n.journal_id IS UNIQUE;
CREATE CONSTRAINT expense_id IF NOT EXISTS FOR (n:Expense) REQUIRE n.expense_id IS UNIQUE;
CREATE CONSTRAINT po_number IF NOT EXISTS FOR (n:PurchaseOrder) REQUIRE n.po_number IS UNIQUE;
CREATE CONSTRAINT credit_note_id IF NOT EXISTS FOR (n:CreditNote) REQUIRE n.credit_note_id IS UNIQUE;
CREATE CONSTRAINT refund_id IF NOT EXISTS FOR (n:Refund) REQUIRE n.refund_id IS UNIQUE;
CREATE CONSTRAINT policy_id IF NOT EXISTS FOR (n:Policy) REQUIRE n.policy_id IS UNIQUE;
CREATE CONSTRAINT approval_id IF NOT EXISTS FOR (n:Approval) REQUIRE n.approval_id IS UNIQUE;
CREATE CONSTRAINT discrepancy_id IF NOT EXISTS FOR (n:Discrepancy) REQUIRE n.discrepancy_id IS UNIQUE;
CREATE CONSTRAINT investigation_id IF NOT EXISTS FOR (n:Investigation) REQUIRE n.investigation_id IS UNIQUE;
CREATE CONSTRAINT adjustment_id IF NOT EXISTS FOR (n:Adjustment) REQUIRE n.adjustment_id IS UNIQUE;

// Secondary indexes for common lookups
CREATE INDEX invoice_status IF NOT EXISTS FOR (n:Invoice) ON (n.status);
CREATE INDEX invoice_customer IF NOT EXISTS FOR (n:Invoice) ON (n.customer_id);
CREATE INDEX payment_reference IF NOT EXISTS FOR (n:Payment) ON (n.payment_reference);
CREATE INDEX bank_txn_counterparty IF NOT EXISTS FOR (n:BankTransaction) ON (n.counterparty_raw);
CREATE INDEX ledger_entry_account IF NOT EXISTS FOR (n:LedgerEntry) ON (n.account);
CREATE INDEX discrepancy_status IF NOT EXISTS FOR (n:Discrepancy) ON (n.status);
CREATE INDEX discrepancy_type IF NOT EXISTS FOR (n:Discrepancy) ON (n.type);
CREATE INDEX approval_status IF NOT EXISTS FOR (n:Approval) ON (n.status);
CREATE INDEX journal_period IF NOT EXISTS FOR (n:JournalEntry) ON (n.accounting_period);
```

## 4. ASCII schema overview

```text
Company
  |
  +-- Customer --< Invoice --< InvoiceLine
  |      |            |  \
  |      |            |   +--> PurchaseOrder
  |      |            |   +--> CreditNote --> Approval --> Employee
  |      |            |   +--> Refund
  |      |            |
  |      +-- Payment --+--> BankTransaction --> BankAccount
  |             |                 |
  |             |                 v
  |             +-----> LedgerEntry --> Account
  |                          ^
  |                          |
  |                    JournalEntry --> Employee (prepared_by / approved_by)
  |
  +-- Vendor --< Expense --< JournalEntry / BankTransaction
  |
  Employee --< Department
  Employee --< EMPLOYEE_HOLDS_AUTHORITY --> Policy (implicit via Approval)

Discrepancy --> Invoice / Payment / BankTransaction / LedgerEntry (DISCREPANCY_INVOLVES_*)
Discrepancy --> Policy (TRANSACTION_REQUIRES_POLICY, via linked transaction)
Investigation --> Discrepancy (INVESTIGATION_INVESTIGATES_DISCREPANCY)
Investigation --> Evidence nodes (INVESTIGATION_USED_EVIDENCE)
Adjustment --> Discrepancy (ADJUSTMENT_RESOLVES_DISCREPANCY)
Approval --> Action node (Adjustment/CreditNote/Refund/JournalEntry) (APPROVAL_APPROVES_ACTION)
```

## 5. CSV column → node property mapping (summary)

| CSV file | Node label | Key columns mapped 1:1 |
| --- | --- | --- |
| customers.csv | Customer | all columns → same-named properties |
| vendors.csv | Vendor | all columns → same-named properties |
| employees.csv | Employee, Department | employee_* columns → Employee; department_id/department → Department |
| bank_accounts.csv | BankAccount | all columns → same-named properties |
| invoices.csv | Invoice | all columns → same-named properties; `po_number` drives `INVOICE_REFERENCES_PURCHASE_ORDER` |
| invoice_lines.csv | InvoiceLine | all columns → same-named properties; `invoice_id` drives `INVOICE_HAS_LINE` |
| payments.csv | Payment | all columns → same-named properties; `customer_id` drives `CUSTOMER_MADE_PAYMENT` |
| payment_allocations.csv | (edge props) | feeds properties `allocated_amount`, `is_correct`, `method` on `INVOICE_PAID_BY` |
| bank_transactions.csv | BankTransaction | all columns → same-named properties |
| chart_of_accounts.csv | Account | all columns → same-named properties |
| ledger_entries.csv | LedgerEntry | all columns → same-named properties |
| journal_entries.csv | JournalEntry | all columns → same-named properties |
| expenses.csv | Expense | all columns → same-named properties |
| purchase_orders.csv | PurchaseOrder | all columns → same-named properties |
| credit_notes.csv | CreditNote | all columns → same-named properties |
| refunds.csv | Refund | all columns → same-named properties |
| policies.csv | Policy | all columns → same-named properties |
| approvals.csv | Approval | all columns → same-named properties |
| discrepancies.csv | Discrepancy | scalar columns → properties; `invoice_ids`/`payment_ids`/`bank_transaction_ids`/`ledger_entry_ids`/`policy_ids` (semicolon-delimited) → `DISCREPANCY_INVOLVES_*` / `TRANSACTION_REQUIRES_POLICY` edges; `investigation_id` → `INVESTIGATION_INVESTIGATES_DISCREPANCY` |
| investigations.csv | Investigation | all columns → same-named properties |
| adjustments.csv | Adjustment | all columns → same-named properties |
| entity_aliases.csv | (edge) | drives `ALIAS_OF` edges from raw string node to resolved Customer/Vendor |

See `graph_construction.md` for the full ingestion order and MERGE statements.
