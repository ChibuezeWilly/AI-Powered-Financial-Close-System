# Accounts Receivable

**Document ID:** KA-03
**Type:** accounting_knowledge
**Period covered:** 2026-08
**Related canon IDs:** INV-1001, INV-1006, INV-1007, CUST-1001, CUST-1003, account 1100, account 1190
**Related policies:** POL-RECON-001, POL-WRITEOFF-001, POL-DISCOUNT-001

---

## 1. Definition

Accounts Receivable (AR) is the money customers owe Meridian Instruments Ltd for goods or services already delivered but not yet paid for. It is tracked in two places that must agree: the **AR subledger** (the detailed, invoice-by-invoice record kept in Meridian Billing / invoices.csv) and the **general ledger control account 1100** (the single aggregated balance in Ledgerline).

## 2. Why it exists

AR exists because Meridian sells on credit terms (Net 15 to Net 30) rather than demanding cash on delivery. The subledger lets Collections (EMP-07 Lena Fischer) manage individual customer relationships and follow up on overdue invoices, while the GL control account lets accountants report a single receivables figure on the balance sheet without re-deriving it invoice by invoice every time.

## 3. Real-world example (canon)

As of 2026-08-31, Meridian's open (unpaid or partially unpaid) invoices are:

| Invoice | Customer | Invoice date | Due date | Total | Paid | Balance | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| INV-1001 | Acme Incorporated | 2026-08-03 | 2026-09-02 | 12,400.00 | 11,900.00 | 500.00 | partially_paid |
| INV-1006 | Acme Incorporated | 2026-08-18 | 2026-09-17 | 2,200.00 | 0.00 | 2,200.00 | open (wrongly shows unpaid — DISC-0006) |
| INV-1007 | Corvus Analytics LLC | 2026-08-21 | 2026-09-20 | 5,150.00 | 0.00 | 5,150.00 | open |

## 4. Important fields

| Field | Type | Example value from canon | Notes |
| --- | --- | --- | --- |
| invoice_id | string | INV-1001 | Primary key of the AR subledger |
| customer_id | string | CUST-1001 (Acme Incorporated) | Links to the customer master |
| balance | decimal | 500.00 (INV-1001) | Total minus amount_paid |
| due_date | date | 2026-09-02 | Drives aging bucket |
| aging_bucket | enum | current, 1-30, 31-60, 61-90, 90+ | Days past due_date |
| account | string | 1100 | GL control account for AR |
| allowance_account | string | 1190 | Contra-asset for expected uncollectible amounts |

## 5. How it relates to other financial records

AR is created by invoices (05) and reduced by payments (06) and credit notes (CN-3001, CN-3002). Every AR movement must have a mirrored ledger entry (08) in account 1100. Bank transactions (07) are the ultimate cash evidence that an AR balance should be reduced.

## 6. Common mistakes

- Booking a payment against the wrong invoice, leaving one invoice looking unpaid and another looking overpaid — exactly what happened with PAY-2010 (DISC-0006): it was applied to INV-1003 instead of INV-1006, so INV-1006 wrongly shows `open` while INV-1003 shows a negative balance of -2,200.00 (overpaid).
- Failing to post an agreed discount, leaving AR overstated (DISC-0001 on INV-1001).
- Not aging invoices correctly, which delays collections follow-up.
- Not maintaining the allowance for doubtful accounts (1190) in line with actual collectability.

## 7. How reconciliation uses it

The **AR-to-GL tie-out** compares the sum of all open invoice balances in the subledger to the ending balance of account 1100 in the general ledger. If they disagree by more than the tolerance (USD 1.00 or 0.1%), there is a posting error, a missing entry, or a misapplied payment somewhere in between. **DSO (Days Sales Outstanding)** — average days it takes customers to pay — is a KPI derived from AR to gauge collections efficiency.

### Worked AR-to-GL tie-out (August 2026)

Subledger open balances: INV-1001 (500.00) + INV-1006 (2,200.00) + INV-1007 (5,150.00) = **7,850.00**.

GL account 1100 activity for the period: total debits 50,500.00 (new invoices) minus total credits 34,150.00 (cash applications of 8,750+6,200+11,900+2,200+4,300+750 rounding... plus the unauthorized 14,000.00 JE-9007 credit) = 16,350.00. The GL balance (16,350.00) does **not** match the naive subledger sum (7,850.00) because JE-9007's unauthorized 14,000.00 credit to 1100 has no corresponding invoice-level event — this mismatch is exactly how DISC-0007 gets caught by AR-to-GL tie-out.

## 8. How discrepancies can occur

- Misapplied payments (DISC-0006) distort individual invoice balances without changing the *total* AR, so tie-outs at the total level can miss them — an invoice-level aging review is needed (as EMP performed via `ar_aging_review` to detect DISC-0006).
- Manual, unapproved adjustments direct to account 1100 (DISC-0007) break the link between the subledger and the GL entirely.
- Discounts promised but never posted (DISC-0001) leave AR permanently overstated until a credit note is issued.
- FX-rate errors on foreign-currency invoices (DISC-0004 on INV-1004) misstate the USD-equivalent AR balance.

## 9. Example database representation

```sql
CREATE TABLE ar_subledger (
    invoice_id   VARCHAR(10) PRIMARY KEY,
    customer_id  VARCHAR(10) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date     DATE NOT NULL,
    total        NUMERIC(12,2) NOT NULL,
    amount_paid  NUMERIC(12,2) NOT NULL DEFAULT 0,
    balance      NUMERIC(12,2) GENERATED ALWAYS AS (total - amount_paid) STORED,
    status       VARCHAR(20)
);

INSERT INTO ar_subledger (invoice_id, customer_id, invoice_date, due_date, total, amount_paid, status) VALUES
 ('INV-1001','CUST-1001','2026-08-03','2026-09-02',12400.00,11900.00,'partially_paid'),
 ('INV-1006','CUST-1001','2026-08-18','2026-09-17',2200.00,0.00,'open'),
 ('INV-1007','CUST-1003','2026-08-21','2026-09-20',5150.00,0.00,'open');
```

## 10. Example investigation scenario

Collections Analyst EMP-07 runs the August aging report and sees INV-1006 (Acme, 2,200.00, due 2026-09-17) as `open` with zero payment recorded, yet Acme's finance contact insists they already paid via a transfer referencing "8859" (Acme's internal PO tag for PO-ACM-8859, which underlies INV-1006). Cross-referencing payments.csv, PAY-2010 (2,200.00, reference `ACME INCORP 8859`) exists but its allocation is `2,200.00 → INV-1003`, a Corvus Analytics invoice — a different customer entirely. This is DISC-0006: an entity-resolution failure in the auto-matcher, which matched on amount rather than customer/reference. Resolution: Staff Accountant EMP-01 re-allocates PAY-2010 from INV-1003 to INV-1006, closing INV-1006 and returning INV-1003 to its correct paid (not overpaid) state.

## 11. Relevant terminology

| Term | Definition |
| --- | --- |
| AR subledger | Detailed record of amounts owed by each customer/invoice |
| Aging bucket | Grouping of receivables by how overdue they are |
| DSO | Days Sales Outstanding — average collection period |
| Allowance for doubtful accounts | Contra-asset estimating uncollectible receivables (1190) |
| AR-to-GL tie-out | Reconciliation of subledger total to the GL control account |
| Write-off | Removing an uncollectible receivable from the books (governed by POL-WRITEOFF-001) |

## 12. Relationship to financial close

AR is one of the first subledgers reconciled during close because it is the largest and most error-prone asset account. The August 2026 close cannot proceed until INV-1001's 500.00 gap (DISC-0001), INV-1006/INV-1003's misallocation (DISC-0006), and the unauthorized 14,000.00 JE-9007 adjustment (DISC-0007) are all resolved and account 1100 ties cleanly to the AR subledger.
