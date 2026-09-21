"""Controlled accounting operations and multi-provider accounting adapters.

Adheres strictly to Architecture Non-Negotiable #2.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from sqlalchemy.orm import Session

from ..database.config import settings
from ..schema.models import JournalEntry
from .accounting_types import (
    AccountingError,
    AccountingProvider,
    JournalRequest,
    PaymentRecordRequest,
    ReceivableRequest,
)
from .mock_accounting import MockAccountingProvider

logger = logging.getLogger(__name__)


class ERPNextAccountingProvider:
    """Adapter for ERPNext REST API."""

    def __init__(self, base_url: str = "", api_key: str = "") -> None:
        self.base_url = base_url or settings.ACCOUNTING_BASE_URL
        self.api_key = api_key or settings.ACCOUNTING_API_KEY

    async def create_journal_entry(self, db: Session, request: JournalRequest) -> JournalEntry:
        raise NotImplementedError("ERPNext adapter configured in external integration mode")

    async def get_journal_entry(self, db: Session, journal_id: str) -> dict | None:
        raise NotImplementedError("ERPNext adapter configured in external integration mode")

    async def get_account(self, db: Session, account_code_or_name: str) -> dict | None:
        raise NotImplementedError("ERPNext adapter configured in external integration mode")

    async def get_account_balance(self, db: Session, account_code_or_name: str) -> Decimal:
        raise NotImplementedError("ERPNext adapter configured in external integration mode")

    async def create_receivable(self, db: Session, request: ReceivableRequest) -> dict:
        raise NotImplementedError("ERPNext adapter configured in external integration mode")

    async def record_payment(self, db: Session, request: PaymentRecordRequest) -> dict:
        raise NotImplementedError("ERPNext adapter configured in external integration mode")

    async def verify_transaction(self, db: Session, transaction_id: str) -> bool:
        raise NotImplementedError("ERPNext adapter configured in external integration mode")


class AkauntingAccountingProvider:
    """Adapter for Akaunting REST API."""

    def __init__(self, base_url: str = "", api_key: str = "") -> None:
        self.base_url = base_url or settings.ACCOUNTING_BASE_URL
        self.api_key = api_key or settings.ACCOUNTING_API_KEY

    async def create_journal_entry(self, db: Session, request: JournalRequest) -> JournalEntry:
        raise NotImplementedError("Akaunting adapter configured in external integration mode")

    async def get_journal_entry(self, db: Session, journal_id: str) -> dict | None:
        raise NotImplementedError("Akaunting adapter configured in external integration mode")

    async def get_account(self, db: Session, account_code_or_name: str) -> dict | None:
        raise NotImplementedError("Akaunting adapter configured in external integration mode")

    async def get_account_balance(self, db: Session, account_code_or_name: str) -> Decimal:
        raise NotImplementedError("Akaunting adapter configured in external integration mode")

    async def create_receivable(self, db: Session, request: ReceivableRequest) -> dict:
        raise NotImplementedError("Akaunting adapter configured in external integration mode")

    async def record_payment(self, db: Session, request: PaymentRecordRequest) -> dict:
        raise NotImplementedError("Akaunting adapter configured in external integration mode")

    async def verify_transaction(self, db: Session, transaction_id: str) -> bool:
        raise NotImplementedError("Akaunting adapter configured in external integration mode")


class SQLLedgerAccountingProvider:
    """Adapter for SQL-Ledger."""

    def __init__(self, base_url: str = "", api_key: str = "") -> None:
        self.base_url = base_url or settings.ACCOUNTING_BASE_URL
        self.api_key = api_key or settings.ACCOUNTING_API_KEY

    async def create_journal_entry(self, db: Session, request: JournalRequest) -> JournalEntry:
        raise NotImplementedError("SQL-Ledger adapter configured in external integration mode")

    async def get_journal_entry(self, db: Session, journal_id: str) -> dict | None:
        raise NotImplementedError("SQL-Ledger adapter configured in external integration mode")

    async def get_account(self, db: Session, account_code_or_name: str) -> dict | None:
        raise NotImplementedError("SQL-Ledger adapter configured in external integration mode")

    async def get_account_balance(self, db: Session, account_code_or_name: str) -> Decimal:
        raise NotImplementedError("SQL-Ledger adapter configured in external integration mode")

    async def create_receivable(self, db: Session, request: ReceivableRequest) -> dict:
        raise NotImplementedError("SQL-Ledger adapter configured in external integration mode")

    async def record_payment(self, db: Session, request: PaymentRecordRequest) -> dict:
        raise NotImplementedError("SQL-Ledger adapter configured in external integration mode")

    async def verify_transaction(self, db: Session, transaction_id: str) -> bool:
        raise NotImplementedError("SQL-Ledger adapter configured in external integration mode")


def get_accounting_provider() -> AccountingProvider:
    """Factory selecting the configured accounting provider."""
    provider_type = (settings.ACCOUNTING_PROVIDER or "mock").lower()
    if provider_type == "erpnext":
        return ERPNextAccountingProvider()
    elif provider_type == "akaunting":
        return AkauntingAccountingProvider()
    elif provider_type in {"sqlledger", "sql_ledger"}:
        return SQLLedgerAccountingProvider()
    return MockAccountingProvider()


accounting_provider: AccountingProvider = MockAccountingProvider()

__all__ = [
    "AccountingError",
    "AccountingProvider",
    "AkauntingAccountingProvider",
    "ERPNextAccountingProvider",
    "JournalRequest",
    "MockAccountingProvider",
    "PaymentRecordRequest",
    "ReceivableRequest",
    "SQLLedgerAccountingProvider",
    "accounting_provider",
    "get_accounting_provider",
]
