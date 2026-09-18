"""Production-grade SQLAlchemy models for the TallyFlow financial close platform."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, Index, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────── Enums ──────────────────────────────────


class Role(str, Enum):
    ADMIN = "ADMIN"
    FINANCE_ADMIN = "FINANCE_ADMIN"
    FINANCE_MANAGER = "FINANCE_MANAGER"
    ANALYST = "ANALYST"
    REGULAR_USER = "REGULAR_USER"


class PeriodStatus(str, Enum):
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class TransactionStatus(str, Enum):
    RECONCILED = "RECONCILED"
    DISCREPANCY_DETECTED = "DISCREPANCY_DETECTED"
    INVESTIGATING = "INVESTIGATING"
    AWAITING_HUMAN_APPROVAL = "AWAITING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    AWAITING_MANAGER_APPROVAL = "AWAITING_MANAGER_APPROVAL"
    ADJUSTMENT_PENDING = "ADJUSTMENT_PENDING"
    ADJUSTED = "ADJUSTED"
    PAYMENT_REQUESTED = "PAYMENT_REQUESTED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"
    REJECTED_MANAGER = "REJECTED_MANAGER"


class InvestigationStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class Severity(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTING = "EXTRACTING"
    VALIDATING = "VALIDATING"
    NORMALIZED = "NORMALIZED"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


# ─────────────────────── Core Identity ──────────────────────────────────


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    legal_name: Mapped[str] = mapped_column(String(300))
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(3), default="USA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default=Role.ANALYST.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    organization_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    transactions: Mapped[list[FinancialTransaction]] = relationship("FinancialTransaction", back_populates="user")
    approvals: Mapped[list[Approval]] = relationship("Approval", back_populates="decider")


class RevokedSession(Base):
    __tablename__ = "revoked_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


# ────────────────────── Financial Entities ───────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    legal_name: Mapped[str] = mapped_column(String(300))
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(3), default="USA")
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    customer_tier: Mapped[str] = mapped_column(String(20), default="Standard")
    payment_terms: Mapped[str] = mapped_column(String(20), default="NET30")
    billing_cycle: Mapped[str] = mapped_column(String(20), default="monthly")
    credit_limit: Mapped[float] = mapped_column(Numeric(14, 2), default=50000)
    contact_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    legal_name: Mapped[str] = mapped_column(String(300))
    country: Mapped[str] = mapped_column(String(3), default="USA")
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    payment_terms: Mapped[str] = mapped_column(String(20), default="NET30")
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    department: Mapped[str] = mapped_column(String(80))
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    head_employee_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    account_type: Mapped[str] = mapped_column(String(40))  # Asset, Liability, Equity, Revenue, Expense
    normal_balance: Mapped[str] = mapped_column(String(10), default="debit")
    parent_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    bank_name: Mapped[str] = mapped_column(String(200))
    account_number_last4: Mapped[str] = mapped_column(String(4))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    account_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ──────────────────── Accounting Period ─────────────────────────────────


class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(7), unique=True, index=True)  # YYYY-MM
    year: Mapped[int] = mapped_column(Integer, default=2026)
    month: Mapped[int] = mapped_column(Integer, default=9)
    period_start: Mapped[str | None] = mapped_column(String(10), nullable=True)
    period_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="OPEN")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reopened_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reopen_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ──────────────────── Transactions ──────────────────────────────────────


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

    financial_transactions: Mapped[list[FinancialTransaction]] = relationship("FinancialTransaction", back_populates="invoice")


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
    journal_entry_id: Mapped[str | None] = mapped_column(ForeignKey("journal_entries.id"), nullable=True, index=True)
    transaction_id: Mapped[str | None] = mapped_column(ForeignKey("financial_transactions.id"), nullable=True, index=True)
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
    transaction: Mapped[FinancialTransaction | None] = relationship("FinancialTransaction", back_populates="ledger_entries")


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

    transaction: Mapped[FinancialTransaction | None] = relationship("FinancialTransaction", back_populates="journal_entries")
    ledger_entries: Mapped[list[LedgerEntry]] = relationship("LedgerEntry", back_populates="journal_entry")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    vendor_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    employee_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    expense_date: Mapped[str] = mapped_column(String(10))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    category: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    account_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    accounting_period: Mapped[str] = mapped_column(String(7), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    vendor_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    po_date: Mapped[str] = mapped_column(String(10))
    total: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CreditNote(Base):
    __tablename__ = "credit_notes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(32), index=True)
    customer_id: Mapped[str] = mapped_column(String(32), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_date: Mapped[str] = mapped_column(String(10))
    accounting_period: Mapped[str] = mapped_column(String(7))
    status: Mapped[str] = mapped_column(String(20), default="issued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(32), index=True)
    customer_id: Mapped[str] = mapped_column(String(32), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    refund_date: Mapped[str] = mapped_column(String(10))
    accounting_period: Mapped[str] = mapped_column(String(7))
    status: Mapped[str] = mapped_column(String(20), default="processed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ──────────────────── Core Reconciliation ───────────────────────────────


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


# ──────────────────── Investigation ─────────────────────────────────────


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(
        ForeignKey("financial_transactions.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    evidence: Mapped[str] = mapped_column(Text, default="[]")
    timeline: Mapped[str] = mapped_column(Text, default="[]")
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    transaction: Mapped[FinancialTransaction | None] = relationship("FinancialTransaction", back_populates="investigations")


class InvestigationStep(Base):
    __tablename__ = "investigation_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id"), index=True)
    step_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)


class InvestigationEvidence(Base):
    __tablename__ = "investigation_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(40))
    source_id: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(300))
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relevance: Mapped[float] = mapped_column(Numeric(4, 2), default=0)
    confidence: Mapped[float] = mapped_column(Numeric(4, 2), default=0)
    retrieval_method: Mapped[str] = mapped_column(String(20), default="SQL")
    document_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Discrepancy(Base):
    __tablename__ = "discrepancies"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("financial_transactions.id"), index=True)
    discrepancy_type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    expected_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    actual_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    difference: Mapped[float] = mapped_column(Numeric(14, 2))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    accounting_period: Mapped[str] = mapped_column(String(7), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    transaction: Mapped[FinancialTransaction | None] = relationship("FinancialTransaction", back_populates="discrepancies")


# ──────────────────── Approvals & Actions ───────────────────────────────


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(
        ForeignKey("financial_transactions.id"), index=True
    )
    decision: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    decided_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    transaction: Mapped[FinancialTransaction | None] = relationship("FinancialTransaction", back_populates="approvals")
    decider: Mapped[User | None] = relationship("User", back_populates="approvals")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("financial_transactions.id"), index=True)
    requested_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approver_role: Mapped[str] = mapped_column(String(32), default="FINANCE_MANAGER")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Adjustment(Base):
    __tablename__ = "adjustments"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("financial_transactions.id"), index=True)
    journal_entry_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    debit_account: Mapped[str] = mapped_column(String(120))
    credit_account: Mapped[str] = mapped_column(String(120))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IdempotentAction(Base):
    __tablename__ = "idempotent_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(160), unique=True)
    result: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ManagerEscalation(Base):
    __tablename__ = "manager_escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("financial_transactions.id"), index=True)
    escalated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    slack_message_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    slack_channel: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("financial_transactions.id"), index=True)
    customer_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ──────────────────── Notifications & Audit ─────────────────────────────


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
    transaction_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    subject: Mapped[str] = mapped_column(String(160))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ──────────────────── Documents & Knowledge ─────────────────────────────


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(String(300))
    document_type: Mapped[str] = mapped_column(String(40))  # invoice, policy, procedure, etc.
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="UPLOADED")
    uploaded_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    invoice_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    accounting_period: Mapped[str | None] = mapped_column(String(7), nullable=True)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[str] = mapped_column(String(32), ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(300))
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    effective_date: Mapped[str] = mapped_column(String(10))
    owner: Mapped[str | None] = mapped_column(String(160), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    document_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(300))
    doc_type: Mapped[str] = mapped_column(String(40))  # concept, policy, procedure
    content: Mapped[str] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    status: Mapped[str] = mapped_column(String(20), default="active")
    embedding_status: Mapped[str] = mapped_column(String(20), default="pending")
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ──────────────────── Reports ───────────────────────────────────────────


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[str] = mapped_column(String(7), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT")
    payload: Mapped[str] = mapped_column(Text)
    generated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ──────────────────── External Integrations ─────────────────────────────


class ExternalIntegration(Base):
    __tablename__ = "external_integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(40))
    external_id: Mapped[str] = mapped_column(String(200))
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ──────────────────── Agent Observability ───────────────────────────────


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    investigation_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    agent_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="running")
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_run_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    tool_name: Mapped[str] = mapped_column(String(80))
    arguments: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ──────────────────── Ground Truth (evaluation only) ────────────────────


class DiscrepancyGroundTruth(Base):
    __tablename__ = "discrepancy_ground_truth"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    transaction_id: Mapped[str] = mapped_column(String(32), index=True)
    invoice_id: Mapped[str] = mapped_column(String(32))
    expected_difference: Mapped[float] = mapped_column(Numeric(14, 2))
    ground_truth_root_cause: Mapped[str] = mapped_column(String(80))
    required_policy: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expected_action: Mapped[str] = mapped_column(String(40))
    expected_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
