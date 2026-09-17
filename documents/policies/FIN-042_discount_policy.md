# FIN-042: Discount Authorization Policy

**Policy ID:** FIN-042
**Version:** 1.4
**Effective Date:** 2024-09-01
**Owner:** Finance Department — Controller
**Last Review:** 2026-07-15

## Scope

This policy establishes rules and approval requirements for all customer discounts applied to invoices, payments, or account balances at Northstar Technologies.

## Definitions

- **Discount**: Any reduction applied to an invoice amount, whether upfront, retroactive, or as a credit.
- **Authorized Discount**: A discount supported by a documented approval record signed by a person with sufficient authority.
- **Unauthorized Discount**: A discount reflected in payment or accounting records without a corresponding approval record.
- **Discount Approval Record**: A formal document or system entry that authorizes a specific discount amount for a specific invoice or customer.

## Rules

1. **All customer discounts must have a documented approval record before they are applied.**
2. Discounts up to $250 may be approved by a Finance Analyst.
3. **Discounts exceeding $250 require documented approval from a Finance Manager or higher.**
4. Discounts exceeding $2,500 require Controller approval.
5. Discounts exceeding $10,000 require CFO approval.
6. Volume discounts and contractual discounts must reference the governing contract or agreement.
7. Retroactive discounts (applied after invoice issuance) require Finance Manager approval regardless of amount.
8. Seasonal or promotional discounts must be pre-approved by the Sales Director and Finance Manager.
9. Discount approval records must include: customer name, invoice reference, discount amount, reason, approver name, and date.
10. No discount may be applied to a closed accounting period without reopening the period with Controller approval.

## Thresholds

| Discount Amount | Required Approver |
|----------------|-------------------|
| $0 – $250 | Finance Analyst |
| $251 – $2,500 | Finance Manager |
| $2,501 – $10,000 | Controller |
| > $10,000 | CFO |

## Required Approvals

- Every discount must have an approval record stored in the system before the accounting adjustment is created.
- If a payment reflects an unapproved discount, an investigation must be opened and the difference must remain as an accounts receivable balance until the discount is either approved or the balance is collected.

## Exceptions

- Contractual discounts with pre-approved terms do not require per-transaction approval, but the contract reference must be documented.
- Early payment discounts (e.g., 2/10 NET 30) follow the terms of the customer agreement and are considered pre-approved.

## Escalation

1. Analyst detects discount without approval → Creates investigation
2. Investigation generates recommendation → Sent to Finance Manager
3. Finance Manager reviews evidence → Approves or rejects
4. If rejected → Customer is contacted for the remaining balance
5. If dispute arises → Escalated to Controller

## Audit Requirements

- All discount approvals are logged with full audit trail.
- Monthly discount analysis is included in the financial close report.
- Quarterly audit samples 100% of discounts exceeding $1,000.
- Annual external audit reviews discount policy compliance.

## Examples

**Example 1: Compliant Discount**
Customer Acme Corp negotiates a $200 discount on INV-2045. Finance Analyst approves (under $250 threshold), creates approval record, and applies the discount. Audit trail is complete.

**Example 2: Non-Compliant Discount (INVESTIGATION TRIGGER)**
INV-1001 for $12,400 is paid as $11,900. The $500 difference appears to be a customer-applied discount. No approval record exists. Because $500 exceeds the $250 analyst threshold, this triggers an investigation. The system recommends requesting Finance Manager approval. If approved, a $500 journal entry is created (Debit: Discount Expense, Credit: Accounts Receivable). If rejected, the $500 remains as an outstanding receivable.

**Example 3: Contractual Discount**
Customer has a 5% volume discount per contract CTR-8821. The discount is pre-approved under the contract terms. Each invoice automatically applies 5%, and the contract reference is logged as the approval source.
