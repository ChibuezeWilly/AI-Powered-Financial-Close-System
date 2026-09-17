"""Seed data generator for TallyFlow — deterministic, realistic financial data.

Generates 500+ transactions across 5 months (May–Sep 2026) with a ~15% discrepancy rate.
Uses a fixed random seed for reproducibility.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import select

from ..schema.models import (
    Account, BankAccount, BankTransaction, Customer, FinancialTransaction,
    Invoice, LedgerEntry, Organization, Payment, AccountingPeriod,
    Investigation, DiscrepancyGroundTruth,
)

SEED = 42

# ── Customer definitions ───────────────────────────────────────────────

CUSTOMERS = [
    {"id": "CUST-1001", "name": "Acme Incorporated", "legal_name": "Acme Incorporated", "industry": "Manufacturing", "country": "USA", "currency": "USD", "customer_tier": "Enterprise", "payment_terms": "NET30", "credit_limit": 75000},
    {"id": "CUST-1002", "name": "Bluepeak Logistics GmbH", "legal_name": "Bluepeak Logistics GmbH", "industry": "Logistics", "country": "DEU", "currency": "USD", "customer_tier": "Enterprise", "payment_terms": "NET15", "credit_limit": 60000},
    {"id": "CUST-1003", "name": "Corvus Analytics LLC", "legal_name": "Corvus Analytics LLC", "industry": "Technology", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 35000},
    {"id": "CUST-1004", "name": "Dunmore Retail Group", "legal_name": "Dunmore Retail Group Ltd", "industry": "Retail", "country": "IRL", "currency": "EUR", "payment_terms": "NET30", "customer_tier": "Enterprise", "credit_limit": 80000},
    {"id": "CUST-1005", "name": "Eastport Marine Services", "legal_name": "Eastport Marine Services Inc", "industry": "Maritime", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 40000},
    {"id": "CUST-1006", "name": "Fenwick & Associates", "legal_name": "Fenwick & Associates LLP", "industry": "Legal", "country": "USA", "currency": "USD", "customer_tier": "Premium", "payment_terms": "NET45", "credit_limit": 50000},
    {"id": "CUST-1007", "name": "Greenfield Agricultural", "legal_name": "Greenfield Agricultural Co", "industry": "Agriculture", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 30000},
    {"id": "CUST-1008", "name": "Horizon Digital Media", "legal_name": "Horizon Digital Media Inc", "industry": "Media", "country": "USA", "currency": "USD", "customer_tier": "Growth", "payment_terms": "NET15", "credit_limit": 25000},
    {"id": "CUST-1009", "name": "Ironclad Security Systems", "legal_name": "Ironclad Security Systems LLC", "industry": "Security", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 45000},
    {"id": "CUST-1010", "name": "Juniper Biotech", "legal_name": "Juniper Biotechnology Corp", "industry": "Biotech", "country": "USA", "currency": "USD", "customer_tier": "Enterprise", "payment_terms": "NET30", "credit_limit": 100000},
    {"id": "CUST-1011", "name": "Kelvin Thermal Solutions", "legal_name": "Kelvin Thermal Solutions Inc", "industry": "Manufacturing", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 35000},
    {"id": "CUST-1012", "name": "Lumen Cloud Consulting", "legal_name": "Lumen Cloud Consulting LLC", "industry": "Technology", "country": "USA", "currency": "USD", "customer_tier": "Growth", "payment_terms": "NET15", "credit_limit": 20000},
    {"id": "CUST-1013", "name": "Meridian Healthcare", "legal_name": "Meridian Healthcare Partners", "industry": "Healthcare", "country": "USA", "currency": "USD", "customer_tier": "Premium", "payment_terms": "NET45", "credit_limit": 90000},
    {"id": "CUST-1014", "name": "Northwind Shipping Co", "legal_name": "Northwind Shipping Co Ltd", "industry": "Logistics", "country": "GBR", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 55000},
    {"id": "CUST-1015", "name": "Oakmont Financial Group", "legal_name": "Oakmont Financial Group Inc", "industry": "Finance", "country": "USA", "currency": "USD", "customer_tier": "Enterprise", "payment_terms": "NET30", "credit_limit": 120000},
]

ACCOUNTS = [
    {"id": "ACCT-1100", "code": "1100", "name": "Cash - Operating USD", "account_type": "Asset", "normal_balance": "debit"},
    {"id": "ACCT-1200", "code": "1200", "name": "Accounts Receivable", "account_type": "Asset", "normal_balance": "debit"},
    {"id": "ACCT-1210", "code": "1210", "name": "Allowance for Doubtful Accounts", "account_type": "Asset", "normal_balance": "credit"},
    {"id": "ACCT-2100", "code": "2100", "name": "Accounts Payable", "account_type": "Liability", "normal_balance": "credit"},
    {"id": "ACCT-4100", "code": "4100", "name": "Revenue - Product Sales", "account_type": "Revenue", "normal_balance": "credit"},
    {"id": "ACCT-4200", "code": "4200", "name": "Revenue - Services", "account_type": "Revenue", "normal_balance": "credit"},
    {"id": "ACCT-5100", "code": "5100", "name": "Discount Expense", "account_type": "Expense", "normal_balance": "debit"},
    {"id": "ACCT-5200", "code": "5200", "name": "Bad Debt Expense", "account_type": "Expense", "normal_balance": "debit"},
    {"id": "ACCT-5300", "code": "5300", "name": "Bank Fees", "account_type": "Expense", "normal_balance": "debit"},
    {"id": "ACCT-3100", "code": "3100", "name": "Retained Earnings", "account_type": "Equity", "normal_balance": "credit"},
]

DISCREPANCY_TYPES = [
    ("UNDOCUMENTED_DISCOUNT", "HIGH", "Accounts Receivable"),
    ("PARTIAL_PAYMENT", "MEDIUM", "Accounts Receivable"),
    ("DUPLICATE_PAYMENT", "CRITICAL", "Cash - Operating USD"),
    ("OVERPAYMENT", "HIGH", "Cash - Operating USD"),
    ("TIMING_DIFFERENCE", "LOW", "Accounts Receivable"),
    ("BANK_FEE", "LOW", "Cash - Operating USD"),
    ("MISSING_PAYMENT", "HIGH", "Accounts Receivable"),
    ("CURRENCY_MISMATCH", "MEDIUM", "Cash - Operating USD"),
]


def _random_amount(rng: random.Random, low: int = 1000, high: int = 25000) -> float:
    """Generate a realistic invoice amount rounded to cents."""
    return round(rng.uniform(low, high), 2)


def _dates_in_month(year: int, month: int, rng: random.Random, count: int) -> list[date]:
    """Generate sorted random dates within a month."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    days = (end - start).days
    dates = sorted([start + timedelta(days=rng.randint(0, days)) for _ in range(count)])
    return dates


def seed_all(db: Session) -> dict:
    """Seed the database with realistic financial data. Returns stats."""
    rng = random.Random(SEED)
    stats = {"customers": 0, "invoices": 0, "payments": 0, "transactions": 0, "discrepancies": 0}

    # Skip if already seeded
    existing = db.scalar(select(FinancialTransaction).limit(1))
    if existing and db.scalar(select(Customer).limit(1)):
        return {"status": "already_seeded"}

    # ── Organization ───────────────────────────────────────────────
    org = Organization(
        id="ORG-001",
        name="Northstar Technologies",
        legal_name="Northstar Technologies Inc",
        industry="Technology",
        country="USA",
    )
    db.merge(org)

    # ── Customers ──────────────────────────────────────────────────
    for cust_data in CUSTOMERS:
        db.merge(Customer(**cust_data))
        stats["customers"] += 1

    # ── Accounts ───────────────────────────────────────────────────
    for acct_data in ACCOUNTS:
        db.merge(Account(**acct_data))

    # ── Bank Account ───────────────────────────────────────────────
    db.merge(BankAccount(
        id="BANK-001",
        name="Primary Operating Account",
        bank_name="First National Bank",
        account_number_last4="4821",
        currency="USD",
        account_id="ACCT-1100",
    ))

    # ── Generate 5 months of data ──────────────────────────────────
    months = [(2026, 5), (2026, 6), (2026, 7), (2026, 8), (2026, 9)]
    tx_counter = 2001
    inv_counter = 2001
    pay_counter = 3001
    bank_counter = 4001
    je_counter = 5001
    disc_counter = 1

    for year, month in months:
        period = f"{year}-{month:02d}"
        tx_count = rng.randint(90, 120)
        invoice_dates = _dates_in_month(year, month, rng, tx_count)

        for i in range(tx_count):
            customer = rng.choice(CUSTOMERS)
            inv_date = invoice_dates[i]
            due_date = inv_date + timedelta(days=30)
            pay_date = inv_date + timedelta(days=rng.randint(5, 35))

            expected = _random_amount(rng)
            tax = round(expected * rng.uniform(0.03, 0.08), 2)
            total = round(expected + tax, 2)

            inv_id = f"INV-{inv_counter}"
            pay_id = f"PAY-{pay_counter}"
            bank_id = f"BANK-{bank_counter}"
            tx_id = f"TX-{tx_counter}"
            je_id = f"JE-{je_counter}"

            # Decide if this is a discrepancy (~15% rate)
            is_discrepancy = rng.random() < 0.15
            if is_discrepancy:
                disc_type, severity, account = rng.choice(DISCREPANCY_TYPES)
                if disc_type == "UNDOCUMENTED_DISCOUNT":
                    discount = round(rng.uniform(100, 2000), 2)
                    actual = round(total - discount, 2)
                    diff = round(discount, 2)
                    root_cause = f"Customer applied ${discount:.2f} discount without documented approval per FIN-042."
                    recommendation = f"Request discount approval. If approved, record a ${discount:.2f} adjustment (Debit: Discount Expense, Credit: A/R)."
                elif disc_type == "PARTIAL_PAYMENT":
                    actual = round(total * rng.uniform(0.5, 0.9), 2)
                    diff = round(total - actual, 2)
                    root_cause = f"Partial payment of ${actual:.2f} received against invoice total of ${total:.2f}."
                    recommendation = f"Contact customer for remaining balance of ${diff:.2f}."
                elif disc_type == "DUPLICATE_PAYMENT":
                    actual = round(total * 2, 2)
                    diff = round(-total, 2)
                    severity = "CRITICAL"
                    root_cause = "Duplicate payment detected. Customer paid twice for the same invoice."
                    recommendation = f"Park ${total:.2f} as unapplied cash and process refund after authorization."
                elif disc_type == "OVERPAYMENT":
                    overage = round(rng.uniform(100, 3000), 2)
                    actual = round(total + overage, 2)
                    diff = round(-overage, 2)
                    root_cause = f"Overpayment of ${overage:.2f}. Customer paid ${actual:.2f} against invoice of ${total:.2f}."
                    recommendation = f"Hold ${overage:.2f} as unapplied cash. Contact customer to apply to another invoice or process refund."
                elif disc_type == "TIMING_DIFFERENCE":
                    actual = total
                    diff = 0
                    severity = "LOW"
                    root_cause = "Payment received but recorded in different period."
                    recommendation = "No financial adjustment needed. Record timing note."
                elif disc_type == "BANK_FEE":
                    fee = round(rng.uniform(15, 75), 2)
                    actual = round(total - fee, 2)
                    diff = round(fee, 2)
                    root_cause = f"Bank processing fee of ${fee:.2f} deducted from payment."
                    recommendation = f"Record ${fee:.2f} as bank fee expense (Debit: Bank Fees, Credit: Cash)."
                elif disc_type == "MISSING_PAYMENT":
                    actual = 0
                    diff = total
                    root_cause = "No payment received for invoice. Payment may be misapplied or outstanding."
                    recommendation = f"Contact customer for payment of ${total:.2f}. Check for misapplied payments."
                else:
                    actual = round(total * rng.uniform(0.95, 1.05), 2)
                    diff = round(total - actual, 2)
                    root_cause = "Amount mismatch detected."
                    recommendation = "Investigate and resolve the difference."

                status = rng.choice([
                    "DISCREPANCY_DETECTED", "INVESTIGATING",
                    "AWAITING_HUMAN_APPROVAL", "AWAITING_HUMAN_APPROVAL",
                ])
                confidence = round(rng.uniform(0.72, 0.96), 2)
            else:
                actual = total
                diff = 0.0
                disc_type = None
                severity = "NONE"
                status = "RECONCILED"
                root_cause = None
                recommendation = None
                confidence = None
                account = "Accounts Receivable"

            # ── Create invoice ─────────────────────────────────────
            db.merge(Invoice(
                id=inv_id, customer_id=customer["id"],
                invoice_date=str(inv_date), due_date=str(due_date),
                po_number=f"PO-{rng.randint(1000, 9999)}", currency=customer.get("currency", "USD"),
                subtotal=expected, discount=0, tax=tax, total=total,
                amount_paid=actual, balance=round(total - actual, 2),
                status="paid" if diff == 0 else "partially_paid",
                accounting_period=period, journal_id=je_id,
            ))

            # ── Create payment ─────────────────────────────────────
            if actual > 0:
                db.merge(Payment(
                    id=pay_id, customer_id=customer["id"], invoice_id=inv_id,
                    payment_date=str(pay_date), amount=actual,
                    currency=customer.get("currency", "USD"),
                    method=rng.choice(["wire_transfer", "ach", "check", "credit_card"]),
                    reference=f"REF-{rng.randint(10000, 99999)}",
                    bank_transaction_id=bank_id, accounting_period=period,
                ))
                stats["payments"] += 1

            # ── Create bank transaction ────────────────────────────
            if actual > 0:
                db.merge(BankTransaction(
                    id=bank_id, bank_account_id="BANK-001",
                    transaction_date=str(pay_date), amount=actual,
                    currency=customer.get("currency", "USD"),
                    description=f"Payment from {customer['name']}",
                    reference=pay_id, counterparty=customer["name"],
                    accounting_period=period,
                    matched_payment_id=pay_id, status="matched",
                ))

            # ── Create ledger entries ──────────────────────────────
            db.merge(LedgerEntry(
                id=f"LE-{je_counter}A", journal_entry_id=je_id,
                account_code="1200", account_name="Accounts Receivable",
                debit=total, credit=0,
                description=f"Invoice {inv_id} to {customer['name']}",
                reference=inv_id, accounting_period=period,
                posted_date=str(inv_date),
            ))
            db.merge(LedgerEntry(
                id=f"LE-{je_counter}B", journal_entry_id=je_id,
                account_code="4100", account_name="Revenue - Product Sales",
                debit=0, credit=total,
                description=f"Revenue for {inv_id}",
                reference=inv_id, accounting_period=period,
                posted_date=str(inv_date),
            ))

            # ── Create financial transaction ───────────────────────
            db.merge(FinancialTransaction(
                id=tx_id, period=period, transaction_date=str(inv_date),
                customer=customer["name"], customer_id=customer["id"],
                invoice_id=inv_id, payment_id=pay_id if actual > 0 else None,
                bank_transaction_id=bank_id if actual > 0 else None,
                account=account, account_code="1200",
                currency=customer.get("currency", "USD"),
                expected_amount=total, actual_amount=actual,
                difference=diff, discrepancy_type=disc_type,
                severity=severity, status=status,
                root_cause=root_cause, recommendation=recommendation,
                confidence=confidence,
            ))
            stats["transactions"] += 1
            if is_discrepancy:
                stats["discrepancies"] += 1

            # ── Ground truth for discrepancies ─────────────────────
            if is_discrepancy:
                db.merge(DiscrepancyGroundTruth(
                    case_id=f"DISC-{disc_counter:04d}",
                    transaction_id=tx_id,
                    invoice_id=inv_id,
                    expected_difference=diff,
                    ground_truth_root_cause=disc_type or "UNKNOWN",
                    required_policy="FIN-042" if "DISCOUNT" in (disc_type or "") else "FIN-001",
                    expected_action="approve_adjustment" if "DISCOUNT" in (disc_type or "") else "investigate",
                ))
                disc_counter += 1

            stats["invoices"] += 1
            inv_counter += 1
            pay_counter += 1
            bank_counter += 1
            tx_counter += 1
            je_counter += 1

    db.commit()
    return stats
