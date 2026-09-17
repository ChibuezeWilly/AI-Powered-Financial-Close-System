"""Controlled accounting operations; workflows never write ledger rows directly."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schema.models import JournalEntry


class AccountingError(ValueError):
    """A safe, business-level rejection from the accounting boundary."""


@dataclass(frozen=True)
class JournalRequest:
    transaction_id: str
    debit_account: str
    credit_account: str
    amount: Decimal
    idempotency_key: str


class AccountingProvider(Protocol):
    def create_journal_entry(self, db: Session, request: JournalRequest) -> JournalEntry: ...
    def verify_transaction(self, db: Session, transaction_id: str) -> bool: ...


class MockAccountingProvider:
    """A deterministic local ledger adapter with validation and idempotency."""

    def create_journal_entry(self, db: Session, request: JournalRequest) -> JournalEntry:
        amount = request.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if amount <= 0:
            raise AccountingError("Journal amount must be greater than zero")
        if request.debit_account == request.credit_account:
            raise AccountingError("Debit and credit accounts must differ")
        existing = db.scalar(select(JournalEntry).where(JournalEntry.transaction_id == request.transaction_id))
        if existing:
            return existing
        entry = JournalEntry(
            id=f"JE-{request.transaction_id.removeprefix('TX-')}",
            transaction_id=request.transaction_id,
            debit_account=request.debit_account,
            credit_account=request.credit_account,
            amount=amount,
            provider_id=f"mock:{request.idempotency_key}",
            status="POSTED",
        )
        db.add(entry)
        db.flush()
        return entry

    def verify_transaction(self, db: Session, transaction_id: str) -> bool:
        entry = db.scalar(select(JournalEntry).where(JournalEntry.transaction_id == transaction_id))
        return bool(entry and entry.status == "POSTED")


accounting_provider: AccountingProvider = MockAccountingProvider()
