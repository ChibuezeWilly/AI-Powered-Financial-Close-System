"""Deterministic local ledger provider maintaining genuine account balances and state."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schema.models import Account, JournalEntry, LedgerEntry
from .accounting_types import (
    AccountingError,
    JournalRequest,
    PaymentRecordRequest,
    ReceivableRequest,
)


class MockAccountingProvider:
    """Deterministic local ledger provider maintaining genuine account balances and state."""

    def __init__(self) -> None:
        self.simulate_failure: bool = False
        self._idempotent_records: dict[str, Any] = {}
        self._account_balances: dict[str, Decimal] = {
            "1100": Decimal("250000.00"),
            "1200": Decimal("180000.00"),
            "1210": Decimal("5000.00"),
            "2100": Decimal("95000.00"),
            "4100": Decimal("540000.00"),
            "4200": Decimal("120000.00"),
            "5100": Decimal("15000.00"),
            "5200": Decimal("8000.00"),
            "5300": Decimal("2500.00"),
            "3100": Decimal("150000.00"),
            "Cash - Operating USD": Decimal("250000.00"),
            "Accounts Receivable": Decimal("180000.00"),
            "Discount Expense": Decimal("15000.00"),
        }

    def _sync_balance(self, account_name: str, delta: Decimal, is_debit: bool) -> None:
        current = self._account_balances.get(account_name, Decimal("0.00"))
        if "Expense" in account_name or "Cash" in account_name or "Receivable" in account_name:
            new_bal = current + delta if is_debit else current - delta
        else:
            new_bal = current - delta if is_debit else current + delta
        self._account_balances[account_name] = new_bal

    async def create_journal_entry(self, db: Session, request: JournalRequest) -> JournalEntry:
        if self.simulate_failure:
            raise AccountingError("Configured simulated ledger provider outage")

        amount = request.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if amount <= 0:
            raise AccountingError("Journal amount must be greater than zero")
        if request.debit_account == request.credit_account:
            raise AccountingError("Debit and credit accounts must differ")

        if request.idempotency_key in self._idempotent_records:
            cached = self._idempotent_records[request.idempotency_key]
            existing = db.get(JournalEntry, cached.get("id"))
            if existing:
                return existing

        existing = db.scalar(select(JournalEntry).where(JournalEntry.transaction_id == request.transaction_id))
        if existing:
            return existing

        entry_id = f"JE-{request.transaction_id.removeprefix('TX-')}"
        external_provider_id = f"mock-je-{request.idempotency_key}"

        entry = JournalEntry(
            id=entry_id,
            transaction_id=request.transaction_id,
            debit_account=request.debit_account,
            credit_account=request.credit_account,
            amount=amount,
            description=request.description or f"Adjustment for {request.transaction_id}",
            accounting_period=request.period,
            provider_id=external_provider_id,
            status="POSTED",
        )
        db.add(entry)
        db.flush()

        le_debit = LedgerEntry(
            id=f"LE-D-{entry_id}",
            journal_entry_id=entry.id,
            transaction_id=request.transaction_id,
            account_code="5100" if "Discount" in request.debit_account else "1100",
            account_name=request.debit_account,
            debit=amount,
            credit=Decimal("0.00"),
            description=request.description or f"Debit adjustment for {request.transaction_id}",
            accounting_period=request.period or "2026-09",
            posted_date="2026-09-30",
        )
        le_credit = LedgerEntry(
            id=f"LE-C-{entry_id}",
            journal_entry_id=entry.id,
            transaction_id=request.transaction_id,
            account_code="1200" if "Receivable" in request.credit_account else "4100",
            account_name=request.credit_account,
            debit=Decimal("0.00"),
            credit=amount,
            description=request.description or f"Credit adjustment for {request.transaction_id}",
            accounting_period=request.period or "2026-09",
            posted_date="2026-09-30",
        )
        db.add(le_debit)
        db.add(le_credit)
        db.flush()

        self._sync_balance(request.debit_account, amount, is_debit=True)
        self._sync_balance(request.credit_account, amount, is_debit=False)

        self._idempotent_records[request.idempotency_key] = {
            "id": entry.id,
            "provider_id": external_provider_id,
            "status": "POSTED",
        }
        return entry

    async def get_journal_entry(self, db: Session, journal_id: str) -> dict | None:
        entry = db.get(JournalEntry, journal_id)
        if not entry:
            return None
        return {
            "id": entry.id,
            "transaction_id": entry.transaction_id,
            "debit_account": entry.debit_account,
            "credit_account": entry.credit_account,
            "amount": float(entry.amount),
            "status": entry.status,
            "provider_id": entry.provider_id,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }

    async def get_account(self, db: Session, account_code_or_name: str) -> dict | None:
        acct = db.scalar(
            select(Account).where(
                (Account.code == account_code_or_name) | (Account.name == account_code_or_name)
            )
        )
        balance = await self.get_account_balance(db, account_code_or_name)
        if acct:
            return {
                "id": acct.id,
                "code": acct.code,
                "name": acct.name,
                "account_type": acct.account_type,
                "normal_balance": acct.normal_balance,
                "balance": float(balance),
            }
        return {
            "id": f"ACCT-{account_code_or_name}",
            "code": account_code_or_name,
            "name": account_code_or_name,
            "account_type": "Asset" if "Cash" in account_code_or_name or "Receivable" in account_code_or_name else "Expense",
            "normal_balance": "debit",
            "balance": float(balance),
        }

    async def get_account_balance(self, db: Session, account_code_or_name: str) -> Decimal:
        return self._account_balances.get(account_code_or_name, Decimal("0.00"))

    async def create_receivable(self, db: Session, request: ReceivableRequest) -> dict:
        if self.simulate_failure:
            raise AccountingError("Configured simulated ledger provider outage")
        amount = request.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if amount <= 0:
            raise AccountingError("Receivable amount must be greater than zero")

        if request.idempotency_key in self._idempotent_records:
            return self._idempotent_records[request.idempotency_key]

        external_id = f"mock-ar-{request.transaction_id}-{request.idempotency_key[:8]}"
        self._sync_balance("Accounts Receivable", amount, is_debit=True)

        res = {
            "external_id": external_id,
            "transaction_id": request.transaction_id,
            "customer_id": request.customer_id,
            "invoice_id": request.invoice_id,
            "amount": float(amount),
            "status": "OPEN",
        }
        self._idempotent_records[request.idempotency_key] = res
        return res

    async def record_payment(self, db: Session, request: PaymentRecordRequest) -> dict:
        if self.simulate_failure:
            raise AccountingError("Configured simulated ledger provider outage")
        amount = request.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if amount <= 0:
            raise AccountingError("Payment amount must be greater than zero")

        if request.idempotency_key in self._idempotent_records:
            return self._idempotent_records[request.idempotency_key]

        external_id = f"mock-pmt-{request.transaction_id}-{request.idempotency_key[:8]}"
        self._sync_balance("Cash - Operating USD", amount, is_debit=True)
        self._sync_balance("Accounts Receivable", amount, is_debit=False)

        res = {
            "external_id": external_id,
            "transaction_id": request.transaction_id,
            "customer_id": request.customer_id,
            "amount": float(amount),
            "payment_method": request.payment_method,
            "reference": request.reference,
            "status": "CLEARED",
        }
        self._idempotent_records[request.idempotency_key] = res
        return res

    async def verify_transaction(self, db: Session, transaction_id: str) -> bool:
        entry = db.scalar(select(JournalEntry).where(JournalEntry.transaction_id == transaction_id))
        return bool(entry and entry.status == "POSTED")
