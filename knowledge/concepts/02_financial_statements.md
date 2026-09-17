# Financial Statements

**Document ID:** KA-02
**Type:** accounting_knowledge
**Period covered:** 2026-08
**Related canon IDs:** all invoices INV-1001..INV-1008, all ledger entries LE-9001..LE-9036, DISC-0001..DISC-0009
**Related policies:** POL-CLOSE-001, POL-PERIOD-001, POL-RECON-001

---

## 1. Definition

Financial statements are the formal, structured reports that summarize a company's financial position and performance for a period. The three core statements are the **balance sheet** (position at a point in time), the **income statement** (performance over a period), and the **cash flow statement** (cash movements over a period). A **trial balance** is the internal working document — a list of every ledger account and its debit/credit balance — used to prepare the statements and to prove that total debits equal total credits.

## 2. Why it exists

Financial statements exist to communicate, in a standardized format, whether a business is solvent, profitable, and generating cash. Meridian's investors, lenders, tax authorities, and internal management all need a single, comparable snapshot rather than raw transaction data. They also form the basis for the **financial close**: a period isn't "closed" until statements can be produced and are believed to be materially accurate (materiality threshold: USD 2,500).

## 3. Real-world example (canon)

Using Meridian's August 2026 ledger, the trial balance sums to (before any discrepancy corrections):

| Account | Debit | Credit |
| --- | --- | --- |
| 1000 Cash — USD | 33,350.00 | |
| 1010 Cash — EUR (USD equiv.) | 9,819.00 | |
| 1100 Accounts Receivable | 50,500.00 | 34,150.00 |
| 1900 Suspense | 14,000.00 | |
| 2000 Accounts Payable | | 3,040.00 |
| 2200 Sales Tax Payable | | 1,715.00 |
| 4000 Product Revenue | | 41,735.00 |
| 4100 Service Revenue | | 9,200.00 |
| 6100 Freight Expense | 3,040.00 | |
| 6900 FX Gain/Loss | | 369.00 |

(Figures derived by summing `ledger_entries.csv` by account for period 2026-08.) Net AR movement: debits 50,500.00 (new invoices) less credits 34,150.00 (cash applications + the unauthorized JE-9007 write-down) = **16,350.00** closing AR — which is *not* the correct receivable balance because of the nine embedded discrepancies.

## 4. Important fields

| Field | Type | Example value | Notes |
| --- | --- | --- | --- |
| statement_type | enum | balance_sheet, income_statement, cash_flow | Identifies which report |
| account | string | 1100 | Ledger account feeding the line |
| period | string | 2026-08 | Reporting period |
| opening_balance | decimal | 0.00 (new period) | Balance brought forward |
| period_movement | decimal | +16,350.00 (net AR) | Sum of debits minus credits (or vice versa) for the period |
| closing_balance | decimal | 16,350.00 | Opening + movement |
| statement_currency | ISO code | USD | Meridian's reporting currency |

## 5. How it relates to other financial records

Statements are built entirely from the general ledger (document 08), which in turn is built from journal entries (document 09) sourced from invoices (05), payments (06) and bank transactions (07). The trial balance is the pivot point: `SUM(debit) = SUM(credit)` across all accounts for the period is a structural check inherited from double-entry bookkeeping (document 10).

## 6. Common mistakes

- Pulling statement numbers before all subledgers (AR, AP, bank) are reconciled, baking in discrepancies.
- Treating the trial balance as "proof" the books are correct — it only proves debits equal credits, not that the *right* accounts were used (e.g., JE-9007's Dr 1900 / Cr 1100 balances perfectly but is still wrong because it was unauthorized).
- Ignoring FX translation on EUR-denominated invoices (INV-1004), which distorts revenue if the wrong rate is used.
- Recognizing revenue on disputed/duplicate invoices (INV-1008) that should not count.

## 7. How reconciliation uses it

Reconciliation is what gives management confidence to publish statements. Before the August close, AR reconciliation (document 03) must tie the sum of open invoice balances to account 1100's ledger balance; bank reconciliation (document 12) must tie 1000/1010 to the bank statements. Only after DISC-0001 through DISC-0009 are investigated can a materially accurate balance sheet and income statement be produced.

## 8. How discrepancies can occur, and their statement impact

| Discrepancy | Statement affected | Misstatement if unresolved |
| --- | --- | --- |
| DISC-0001 (500.00 undocumented discount) | Balance sheet (AR overstated by 500.00) | Assets overstated |
| DISC-0002 (8,750.00 duplicate payment) | Balance sheet (cash overstated; a liability to refund is missing) | Liabilities understated |
| DISC-0003 (4,300.00 timing difference) | None if treated as reconciling item; cash overstated if mis-cut-off | Explained, not a misstatement |
| DISC-0004 (315.00 FX error) | Income statement (revenue/FX gain misstated); balance sheet (AR understated by 315.00) | Both statements slightly wrong |
| DISC-0005 (1,250.00 missing refund entry) | Balance sheet (cash overstated by 1,250.00, since bank shows the outflow but ledger doesn't) | Assets overstated |
| DISC-0006 (2,200.00 misapplied payment) | Balance sheet (INV-1006 AR overstated, INV-1003 shows a credit balance/overpaid) | AR subledger internally wrong even though total AR is right |
| DISC-0007 (14,000.00 unauthorized JE) | Balance sheet (AR understated by 14,000.00, Suspense overstated) | Assets misclassified, control breach |
| DISC-0008 (8,750.00 duplicate invoice) | Income statement (revenue overstated by 8,500.00); Balance sheet (AR overstated by 8,750.00) | Both statements overstated |
| DISC-0009 (360.00 transposition) | Income statement (freight expense understated by 360.00); Balance sheet (AP understated by 360.00) | Both statements understated |

## 9. Example database representation

```sql
CREATE TABLE trial_balance (
    account         VARCHAR(4),
    accounting_period VARCHAR(7),
    total_debit     NUMERIC(14,2),
    total_credit    NUMERIC(14,2),
    PRIMARY KEY (account, accounting_period)
);

-- Derived via aggregation from ledger_entries
INSERT INTO trial_balance
SELECT account, accounting_period, SUM(debit), SUM(credit)
FROM ledger_entries
WHERE accounting_period = '2026-08'
GROUP BY account, accounting_period;
```

Sample resulting rows:

| account | accounting_period | total_debit | total_credit |
| --- | --- | --- | --- |
| 1100 | 2026-08 | 50,500.00 | 34,150.00 |
| 4000 | 2026-08 | 0.00 | 41,735.00 |
| 1900 | 2026-08 | 14,000.00 | 0.00 |

## 10. Example investigation scenario

The Controller (EMP-03) reviews the draft August income statement and notices Product Revenue (4000) of 41,735.00 looks high relative to invoice volume. Drilling into the ledger, she finds LE-9005 (8,500.00 for INV-1002) is legitimate, but LE-9004's twin — an equivalent posting for INV-1008 (JE-8008) — represents a duplicate invoice for the same PO-BLU-2210. This is DISC-0008. Because INV-1008 has not been credited (CN-3002 is only "proposed"), revenue is overstated by 8,500.00 and AR by 8,750.00 until Finance Director EMP-04 approves the credit note.

## 11. Relevant terminology

| Term | Definition |
| --- | --- |
| Balance sheet | Statement of assets, liabilities and equity at a point in time |
| Income statement | Statement of revenue and expenses over a period (also called P&L) |
| Cash flow statement | Statement of cash inflows/outflows over a period |
| Trial balance | List of all accounts with their debit/credit totals, used to prove balance |
| Materiality | The threshold above which an error is considered significant (USD 2,500 at Meridian) |
| Misstatement | An incorrect amount on a financial statement |

## 12. Relationship to financial close

Financial statements are the *output* of the close process. The close cannot be signed off until the trial balance is proven, all subledgers reconcile to the GL, and every discrepancy above materiality (all except DISC-0003 and DISC-0009, which are below/at the edge of the 2,500 threshold) has a documented resolution. Only then can Meridian's August 2026 balance sheet and income statement be considered final.
