# Accounts Payable

**Document ID:** KA-04
**Type:** accounting_knowledge
**Period covered:** 2026-08
**Related canon IDs:** VEND-2002, EXP-7002, BT-5008, JE-8507, DISC-0009, account 2000
**Related policies:** POL-ADJUST-001, POL-APPROVAL-001

---

## 1. Definition

Accounts Payable (AP) is the money Meridian Instruments Ltd owes to its vendors for goods or services already received but not yet paid for (or, once paid, the record of that obligation being settled). It is tracked in an **AP subledger** (vendor-by-vendor, invoice/expense-by-expense) and rolled up into general ledger control account **2000**.

## 2. Why it exists

AP exists because vendors extend credit terms to Meridian (e.g., Northline Freight, VEND-2002, on Net 30 terms) rather than requiring immediate cash payment. AP lets the company manage its own cash outflows strategically while keeping an accurate obligation on its balance sheet as a liability.

## 3. Real-world example (canon)

Meridian's vendor Northline Freight (VEND-2002) delivers freight services in August, billed as **EXP-7002** on 2026-08-12 for **3,400.00 USD**, paid the same day via bank transaction **BT-5008**. However, the journal **JE-8507** recorded the expense as **3,040.00 USD** — a transposition of the digits — creating **DISC-0009**, a 360.00 USD understatement.

| Field | Correct | As recorded |
| --- | --- | --- |
| Amount | 3,400.00 | 3,040.00 |
| Ledger entries | Dr 6100 3,400.00 / Cr 2000 3,400.00 | LE-9033 Dr 6100 3,040.00 / LE-9034 Cr 2000 3,040.00 |
| Difference | | 360.00 understated |

## 4. Important fields

| Field | Type | Example value from canon | Notes |
| --- | --- | --- | --- |
| expense_id | string | EXP-7002 | AP subledger key |
| vendor_id | string | VEND-2002 (Northline Freight) | Vendor master reference |
| amount | decimal | 3,400.00 (actual) vs 3,040.00 (recorded) | Subject of DISC-0009 |
| po_number | string | (freight expenses may lack a PO) | Used for three-way match when present |
| account | string | 2000 | GL control account for AP |
| bank_transaction_id | string | BT-5008 | Confirms cash actually left the bank |
| journal_id | string | JE-8507 | Journal that posted the (incorrect) expense |

## 5. How it relates to other financial records

AP entries originate from vendor invoices/expenses and are settled via bank transactions (07), producing ledger entries (08) in account 2000. A robust AP process cross-checks the **purchase order**, the **goods/service receipt**, and the **vendor invoice** — the "three-way match" — before payment is approved.

### Three-way match

```text
   Purchase Order            Goods/Service Receipt         Vendor Invoice
   (what we ordered)         (what we received)            (what we're billed)
        |                          |                              |
        +----------- compare quantity, price, vendor -------------+
                              |
                     match? --+-- yes --> approve for payment
                              |
                              +-- no  --> hold, investigate (e.g., DISC-0009)
```

For EXP-7002, the freight service delivered matches Northline's invoice for 3,400.00 and the bank paid exactly 3,400.00 (BT-5008) — the match is clean *outside* the ledger. The failure is purely a **data-entry transposition** inside the accounting record (JE-8507), which is why the three-way match alone would not catch it; a bank-to-ledger comparison is required.

## 6. Common mistakes

- Keying amounts with transposed digits (3,400.00 → 3,040.00), a classic data-entry error.
- Paying an invoice twice due to duplicate vendor invoice numbers.
- Missing a three-way match step, letting an invoice for services never received be paid.
- Posting to the wrong expense account (6100 Freight vs 6200 Office Supplies).

## 7. How reconciliation uses it

AP reconciliation compares the vendor's statement (or the underlying expense records) to the GL account 2000 balance, and separately compares AP-driven bank outflows (BT-5008) to what the ledger says was paid. For EXP-7002, the bank paid 3,400.00 but the ledger shows only 3,040.00 posted to AP/expense — a clear mismatch caught by an **ap_to_bank_match** rule (the same detection method recorded against DISC-0009 in discrepancies.csv).

## 8. How discrepancies can occur

Transposition errors (DISC-0009) are a leading cause of AP discrepancies — a human keys 3,040.00 instead of 3,400.00. Other causes not present but structurally similar in this universe include duplicate vendor invoices, unmatched purchase orders, and unauthorized adjustments to account 2000 (paralleling the unauthorized AR adjustment pattern seen in DISC-0007).

## 9. Example database representation

```sql
CREATE TABLE ap_subledger (
    expense_id  VARCHAR(10) PRIMARY KEY,
    vendor_id   VARCHAR(10) NOT NULL,
    expense_date DATE NOT NULL,
    amount_actual NUMERIC(12,2) NOT NULL,
    amount_recorded NUMERIC(12,2) NOT NULL,
    bank_transaction_id VARCHAR(10),
    journal_id  VARCHAR(10),
    status      VARCHAR(20)
);

INSERT INTO ap_subledger VALUES
 ('EXP-7002','VEND-2002','2026-08-12',3400.00,3040.00,'BT-5008','JE-8507','paid; ledger mismatch');

CREATE TABLE ledger_entries_ap AS
SELECT * FROM (VALUES
 ('LE-9033','JE-8507','2026-08-12','6100',3040.00,0.00,'Freight EXP-7002 (keyed as 3040.00)'),
 ('LE-9034','JE-8507','2026-08-12','2000',0.00,3040.00,'AP - Northline Freight')
) AS t(ledger_entry_id, journal_id, entry_date, account, debit, credit, description);
```

## 10. Example investigation scenario

During month-end AP reconciliation, Staff Accountant EMP-01 compares the bank statement outflow BT-5008 (3,400.00 debit, description `NORTHLINE FREIGHT AUG`) against the AP ledger postings for VEND-2002 and finds only 3,040.00 booked via JE-8507. The 360.00 gap is flagged as **DISC-0009**, classified `expense_amount_mismatch`, low severity, root cause "transposition of 3400.00 to 3040.00." Per POL-ADJUST-001, EMP-01 (journal adjustments < 10,000 USD are within their authority) posts a correcting entry: **Dr 6100 Freight Expense 360.00 / Cr 2000 Accounts Payable 360.00**, bringing the recorded expense to the true 3,400.00 and closing the discrepancy.

## 11. Relevant terminology

| Term | Definition |
| --- | --- |
| AP subledger | Detailed record of amounts owed to each vendor |
| Three-way match | Comparing PO, receipt, and vendor invoice before payment |
| Transposition error | Swapping digits when keying a number (3400 -> 3040) |
| AP-to-bank match | Reconciling ledger-recorded payments to actual bank outflows |
| Control account | The single GL account (2000) summarizing a subledger |

## 12. Relationship to financial close

AP must be reconciled before close because understated liabilities/expenses (as with DISC-0009's 360.00 freight understatement) distort both the balance sheet (AP) and the income statement (Freight Expense). Though 360.00 is below Meridian's 2,500.00 materiality threshold, POL-ADJUST-001 still requires it to be corrected before the period locks on 2026-09-05, since uncorrected small errors accumulate and undermine control reliability.
