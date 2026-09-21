"""Investigation, approvals, escalations, and discrepancy models."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.database import Base
from .common import _utcnow, _uuid

if TYPE_CHECKING:
    from .identity_models import User
    from .transaction_models import FinancialTransaction


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(
        ForeignKey("financial_transactions.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    evidence: Mapped[str] = mapped_column(Text, default="[]")
    agent_findings: Mapped[str] = mapped_column(Text, default="[]")
    timeline: Mapped[str] = mapped_column(Text, default="[]")
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_email_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_escalation_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    transaction: Mapped[FinancialTransaction | None] = relationship(
        "FinancialTransaction", back_populates="investigations"
    )


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
    agent_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
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

    transaction: Mapped[FinancialTransaction | None] = relationship(
        "FinancialTransaction", back_populates="discrepancies"
    )


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

    transaction: Mapped[FinancialTransaction | None] = relationship(
        "FinancialTransaction", back_populates="approvals"
    )
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
