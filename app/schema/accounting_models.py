"""Accounting and master entity models."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database.database import Base
from .common import _utcnow


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
