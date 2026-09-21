"""Seed data generator for TallyFlow — deterministic, realistic financial data."""
from __future__ import annotations

import random
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schema.models import (
    Account, BankAccount, BankTransaction, Customer, DiscrepancyGroundTruth,
    FinancialTransaction, Invoice, LedgerEntry, Organization, Payment,
)
from .seed_constants import ACCOUNTS, CUSTOMERS, DISCREPANCY_TYPES, SEED


def _random_amount(rng: random.Random, low: int = 1000, high: int = 25000) -> float:
    return round(rng.uniform(low, high), 2)


def _dates_in_month(year: int, month: int, rng: random.Random, count: int) -> list[date]:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) - timedelta(days=1) if month == 12 else date(year, month + 1, 1) - timedelta(days=1)
    days = (end - start).days
    return sorted([start + timedelta(days=rng.randint(0, days)) for _ in range(count)])


def seed_all(db: Session) -> dict:
    rng = random.Random(SEED)
    stats = {"customers": 0, "invoices": 0, "payments": 0, "transactions": 0, "discrepancies": 0}

    existing = db.scalar(select(FinancialTransaction).limit(1))
    if existing and db.scalar(select(Customer).limit(1)):
        return {"status": "already_seeded"}

    org = Organization(
        id="ORG-001",
        name="Northstar Technologies",
        legal_name="Northstar Technologies Inc",
        industry="Technology",
        country="USA",
    )
    db.merge(org)

    for cust_data in CUSTOMERS:
        db.merge(Customer(**cust_data))
        stats["customers"] += 1

    for acct_data in ACCOUNTS:
        db.merge(Account(**acct_data))

    db.merge(BankAccount(
        id="BANK-001",
        name="Primary Operating Account",
        bank_name="First National Bank",
        account_number_last4="4821",
        currency="USD",
        account_id="ACCT-1100",
    ))

    months = [(2026, 5), (2026, 6), (2026, 7), (2026, 8), (2026, 9)]
    tx_counter, inv_counter, pay_counter, bank_counter, je_counter, disc_counter = 2001, 2001, 3001, 4001, 5001, 1

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

            inv_id, pay_id, bank_id = f"INV-{inv_counter}", f"PAY-{pay_counter}", f"BANK-{bank_counter}"
            tx_id, je_id = f"TX-{tx_counter}", f"JE-{je_counter}"

            is_discrepancy = rng.random() < 0.15
            if is_discrepancy:
                disc_type, severity, account = rng.choice(DISCREPANCY_TYPES)
                if disc_type == "UNDOCUMENTED_DISCOUNT":
                    discount = round(rng.uniform(100, 2000), 2)
                    actual, diff = round(total - discount, 2), round(discount, 2)
                    root_cause = f"Customer applied ${discount:.2f} discount without documented approval per FIN-042."
                    recommendation = f"Request discount approval. If approved, record a ${discount:.2f} adjustment."
                elif disc_type == "PARTIAL_PAYMENT":
                    actual = round(total * rng.uniform(0.5, 0.9), 2)
                    diff = round(total - actual, 2)
                    root_cause = f"Partial payment of ${actual:.2f} received against invoice total of ${total:.2f}."
                    recommendation = f"Contact customer for remaining balance of ${diff:.2f}."
                elif disc_type == "DUPLICATE_PAYMENT":
                    actual, diff, severity = round(total * 2, 2), round(-total, 2), "CRITICAL"
                    root_cause = "Duplicate payment detected. Customer paid twice for the same invoice."
                    recommendation = f"Park ${total:.2f} as unapplied cash and process refund."
                elif disc_type == "OVERPAYMENT":
                    overage = round(rng.uniform(100, 3000), 2)
                    actual, diff = round(total + overage, 2), round(-overage, 2)
                    root_cause = f"Overpayment of ${overage:.2f} received."
                    recommendation = f"Hold ${overage:.2f} as unapplied cash and contact customer."
                elif disc_type == "TIMING_DIFFERENCE":
                    actual, diff, severity = total, 0, "LOW"
                    root_cause = "Payment received but recorded in different period."
                    recommendation = "No financial adjustment needed. Record timing note."
                elif disc_type == "BANK_FEE":
                    fee = round(rng.uniform(15, 75), 2)
                    actual, diff = round(total - fee, 2), round(fee, 2)
                    root_cause = f"Bank processing fee of ${fee:.2f} deducted from payment."
                    recommendation = f"Record ${fee:.2f} as bank fee expense."
                elif disc_type == "MISSING_PAYMENT":
                    actual, diff = 0, total
                    root_cause = "No payment received for invoice."
                    recommendation = f"Contact customer for payment of ${total:.2f}."
                else:
                    actual = round(total * rng.uniform(0.95, 1.05), 2)
                    diff = round(total - actual, 2)
                    root_cause = "Amount mismatch detected."
                    recommendation = "Investigate and resolve the difference."

                status = rng.choice(["DISCREPANCY_DETECTED", "INVESTIGATING", "AWAITING_HUMAN_APPROVAL"])
                confidence = round(rng.uniform(0.72, 0.96), 2)
            else:
                actual, diff, disc_type, severity, status = total, 0.0, None, "NONE", "RECONCILED"
                root_cause, recommendation, confidence, account = None, None, None, "Accounts Receivable"

            db.merge(Invoice(
                id=inv_id, customer_id=customer["id"],
                invoice_date=str(inv_date), due_date=str(due_date),
                po_number=f"PO-{rng.randint(1000, 9999)}", currency=customer.get("currency", "USD"),
                subtotal=expected, discount=0, tax=tax, total=total,
                amount_paid=actual, balance=round(total - actual, 2),
                status="paid" if diff == 0 else "partially_paid",
                accounting_period=period, journal_id=je_id,
            ))

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
                db.merge(BankTransaction(
                    id=bank_id, bank_account_id="BANK-001",
                    transaction_date=str(pay_date), amount=actual,
                    currency=customer.get("currency", "USD"),
                    description=f"Payment from {customer['name']}",
                    reference=pay_id, counterparty=customer["name"],
                    accounting_period=period, matched_payment_id=pay_id, status="matched",
                ))

            db.merge(LedgerEntry(
                id=f"LE-{je_counter}A", journal_entry_id=je_id,
                account_code="1200", account_name="Accounts Receivable",
                debit=total, credit=0, description=f"Invoice {inv_id}",
                reference=inv_id, accounting_period=period, posted_date=str(inv_date),
            ))
            db.merge(LedgerEntry(
                id=f"LE-{je_counter}B", journal_entry_id=je_id,
                account_code="4100", account_name="Revenue - Product Sales",
                debit=0, credit=total, description=f"Revenue for {inv_id}",
                reference=inv_id, accounting_period=period, posted_date=str(inv_date),
            ))

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
                db.merge(DiscrepancyGroundTruth(
                    case_id=f"DISC-{disc_counter:04d}", transaction_id=tx_id, invoice_id=inv_id,
                    expected_difference=diff, ground_truth_root_cause=disc_type or "UNKNOWN",
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
