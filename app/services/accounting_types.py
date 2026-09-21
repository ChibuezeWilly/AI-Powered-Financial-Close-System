"""Accounting protocol and request data types."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
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
    description: str | None = None
    period: str | None = None


@dataclass(frozen=True)
class ReceivableRequest:
    transaction_id: str
    customer_id: str
    invoice_id: str
    amount: Decimal
    idempotency_key: str
    due_date: str | None = None


@dataclass(frozen=True)
class PaymentRecordRequest:
    transaction_id: str
    customer_id: str
    amount: Decimal
    payment_method: str
    reference: str
    idempotency_key: str


class AccountingProvider(Protocol):
    """Protocol for external and mock accounting / ledger adapters."""

    async def create_journal_entry(self, db: Session, request: JournalRequest) -> JournalEntry: ...
    async def get_journal_entry(self, db: Session, journal_id: str) -> dict | None: ...
    async def get_account(self, db: Session, account_code_or_name: str) -> dict | None: ...
    async def get_account_balance(self, db: Session, account_code_or_name: str) -> Decimal: ...
    async def create_receivable(self, db: Session, request: ReceivableRequest) -> dict: ...
    async def record_payment(self, db: Session, request: PaymentRecordRequest) -> dict: ...
    async def verify_transaction(self, db: Session, transaction_id: str) -> bool: ...
