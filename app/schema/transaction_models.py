"""Transaction and ledger models."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    DateTime, ForeignKey, Index, Integer, Numeric, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.database import Base
from .common import _utcnow

if TYPE_CHECKING:
    from .identity_models import User
    from .investigation_models import Approval, Discrepancy, Investigation


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.id"), index=True)
    invoice_date: Mapped[str] = mapped_column(String(10))
    due_date: Mapped[str] = mapped_column(String(10))
    po_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2))
    discount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    tax: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2))
    amount_paid: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="open")
    accounting_period: Mapped[str] = mapped_column(String(7), index=True)
    journal_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    financial_transactions: Mapped[list[FinancialTransaction]] = relationship(
        "FinancialTransaction", back_populates="invoice"
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(32), ForeignKey("invoices.id"), index=True)
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    account_code: Mapped[str | None] = mapped_column(String(20), nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.id"), index=True)
    invoice_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    payment_date: Mapped[str] = mapped_column(String(10))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    method: Mapped[str] = mapped_column(String(30), default="wire_transfer")
    reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    bank_transaction_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    accounting_period: Mapped[str] = mapped_column(String(7), index=True)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    bank_account_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    transaction_date: Mapped[str] = mapped_column(String(10))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(200), nullable=True)
    accounting_period: Mapped[str] = mapped_column(String(7), index=True)
    matched_payment_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="unmatched")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    journal_entry_id: Mapped[str | None] = mapped_column(
        ForeignKey("journal_entries.id"), nullable=True, index=True
    )
    transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("financial_transactions.id"), nullable=True, index=True
    )
    account_code: Mapped[str] = mapped_column(String(20), index=True)
    account_name: Mapped[str] = mapped_column(String(200))
    debit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    accounting_period: Mapped[str] = mapped_column(String(7), index=True)
    posted_date: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    journal_entry: Mapped[JournalEntry | None] = relationship("JournalEntry", back_populates="ledger_entries")
    transaction: Mapped[FinancialTransaction | None] = relationship(
        "FinancialTransaction", back_populates="ledger_entries"
    )


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("financial_transactions.id"), nullable=True, index=True
    )
    debit_account: Mapped[str] = mapped_column(String(120))
    credit_account: Mapped[str] = mapped_column(String(120))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accounting_period: Mapped[str | None] = mapped_column(String(7), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="POSTED")
    provider_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    transaction: Mapped[FinancialTransaction | None] = relationship(
        "FinancialTransaction", back_populates="journal_entries"
    )
    ledger_entries: Mapped[list[LedgerEntry]] = relationship("LedgerEntry", back_populates="journal_entry")


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    transaction_date: Mapped[str] = mapped_column(String(10))
    tx_type: Mapped[str] = mapped_column(String(40), default="invoice_payment")
    customer: Mapped[str] = mapped_column(String(160))
    customer_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    invoice_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("invoices.id"), nullable=True, index=True)
    payment_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bank_transaction_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    account: Mapped[str] = mapped_column(String(100))
    account_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    expected_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    actual_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    difference: Mapped[float] = mapped_column(Numeric(14, 2))
    discrepancy_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="NONE")
    status: Mapped[str] = mapped_column(String(40), default="RECONCILED")
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    user: Mapped[User | None] = relationship("User", back_populates="transactions")
    invoice: Mapped[Invoice | None] = relationship("Invoice", back_populates="financial_transactions")
    investigations: Mapped[list[Investigation]] = relationship("Investigation", back_populates="transaction")
    discrepancies: Mapped[list[Discrepancy]] = relationship("Discrepancy", back_populates="transaction")
    approvals: Mapped[list[Approval]] = relationship("Approval", back_populates="transaction")
    journal_entries: Mapped[list[JournalEntry]] = relationship("JournalEntry", back_populates="transaction")
    ledger_entries: Mapped[list[LedgerEntry]] = relationship("LedgerEntry", back_populates="transaction")

    __table_args__ = (
        Index("ix_ft_period_status", "period", "status"),
    )
