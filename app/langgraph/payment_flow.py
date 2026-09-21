"""Payment request and incoming payment reconciliation flows per Non-Negotiables #8, #12, #13."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schema.models import (
    AuditEvent,
    Customer,
    FinancialTransaction,
    Invoice,
    Investigation,
    Notification,
    Payment,
    PaymentRequest,
)
from ..services.accounting import PaymentRecordRequest, ReceivableRequest, accounting_provider
from ..services.email_service import safe_send_payment_request_email
from ..services.pinecone_service import save_resolution_memory
from ..services.slack_service import send_payment_request_message
from .state_machine import transition, validate_period_open

logger = logging.getLogger(__name__)


async def resolve_manager_rejection(
    db: Session,
    tx: FinancialTransaction,
    actor_id: int,
    reason: str,
) -> dict[str, Any]:
    """Execute manager rejection: create receivable & issue payment request (Non-Negotiables #8 & #12)."""
    validate_period_open(db, tx.period)

    transition(tx, "REJECTED")
    transition(tx, "PAYMENT_REQUESTED")

    outstanding_amount = Decimal(str(abs(tx.difference)))

    rec_result = await accounting_provider.create_receivable(
        db,
        ReceivableRequest(
            transaction_id=tx.id,
            customer_id=tx.customer_id or tx.customer,
            invoice_id=tx.invoice_id or tx.id,
            amount=outstanding_amount,
            idempotency_key=f"rec:{tx.id}",
        ),
    )

    invoice = db.get(Invoice, tx.invoice_id) if tx.invoice_id else None
    if invoice:
        invoice.balance = outstanding_amount

    pr = PaymentRequest(
        transaction_id=tx.id,
        customer_id=tx.customer_id,
        amount=outstanding_amount,
        currency=tx.currency,
        email_sent=True,
        status="pending",
    )
    db.add(pr)

    customer_email = None
    if tx.customer_id:
        cust = db.get(Customer, tx.customer_id)
        if cust and cust.contact_email:
            customer_email = cust.contact_email

    recipient = customer_email or f"{tx.customer.lower().replace(' ', '')}@example.com"
    await safe_send_payment_request_email(
        to_email=recipient,
        customer=tx.customer,
        amount=float(outstanding_amount),
        invoice_id=tx.invoice_id or tx.id,
        transaction_id=tx.id,
    )

    transition(tx, "PAYMENT_PENDING")

    db.add(AuditEvent(actor_id=actor_id, action="PAYMENT_REQUEST_ISSUED", subject=tx.id))
    db.add(
        Notification(
            user_id=actor_id,
            event="PAYMENT_REQUESTED",
            message=f"Payment request issued to {tx.customer} for ${float(outstanding_amount):,.2f}.",
            status="SENT",
        )
    )

    try:
        send_payment_request_message(
            transaction_id=tx.id,
            customer=tx.customer,
            amount=float(outstanding_amount),
            invoice_id=tx.invoice_id,
        )
    except Exception as exc:
        logger.warning("Decoupled Slack payment notification failed: %s", exc)

    db.flush()
    return {
        "status": tx.status,
        "receivable_id": rec_result.get("external_id"),
        "outstanding_amount": float(outstanding_amount),
        "message": "Receivable created and customer payment request dispatched.",
    }


async def process_incoming_payment(
    db: Session,
    customer_id: str,
    amount: Decimal,
    invoice_id: str | None = None,
    payment_method: str = "wire_transfer",
    reference: str = "EXT-PMT",
) -> dict[str, Any]:
    """Ingest and reconcile an incoming payment (Non-Negotiables #8 & #13)."""
    amount = Decimal(str(amount))

    pmt_id = f"PAY-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    payment = Payment(
        id=pmt_id,
        customer_id=customer_id,
        invoice_id=invoice_id,
        payment_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        amount=amount,
        currency="USD",
        method=payment_method,
        reference=reference,
        accounting_period="2026-09",
        status="completed",
    )
    db.add(payment)
    db.flush()

    query = select(FinancialTransaction).where(
        FinancialTransaction.status.in_(["PAYMENT_PENDING", "PAYMENT_REQUESTED"])
    )
    if invoice_id:
        query = query.where(FinancialTransaction.invoice_id == invoice_id)
    else:
        query = query.where(
            (FinancialTransaction.customer_id == customer_id) | (FinancialTransaction.customer == customer_id)
        )

    tx = db.scalar(query)
    if not tx:
        return {"payment_id": payment.id, "matched": False, "status": "UNMATCHED"}

    if abs(tx.difference) == amount:
        await accounting_provider.record_payment(
            db,
            PaymentRecordRequest(
                transaction_id=tx.id,
                customer_id=customer_id,
                amount=amount,
                payment_method=payment_method,
                reference=reference,
                idempotency_key=f"pmt-recv:{tx.id}",
            ),
        )

        if tx.status == "PAYMENT_REQUESTED":
            transition(tx, "PAYMENT_PENDING")
        transition(tx, "PAYMENT_RECEIVED")

        tx.actual_amount = tx.expected_amount
        tx.difference = Decimal("0.00")
        transition(tx, "RESOLVED")

        if tx.invoice:
            tx.invoice.balance = Decimal("0.00")
            tx.invoice.amount_paid = tx.invoice.total
            tx.invoice.status = "paid"

        pr = db.scalar(select(PaymentRequest).where(PaymentRequest.transaction_id == tx.id))
        if pr:
            pr.status = "COMPLETED"

        inv = db.scalar(select(Investigation).where(Investigation.transaction_id == tx.id))
        if inv:
            inv.status = "RESOLVED"
            inv.completed_at = datetime.now(timezone.utc)

        db.add(AuditEvent(actor_id=None, action="PAYMENT_RECEIVED_AND_RECONCILED", subject=tx.id))
        db.add(
            Notification(
                user_id=None,
                event="PAYMENT_RECEIVED",
                message=f"Outstanding balance of ${float(amount):,.2f} received for {tx.id}. Transaction is now RESOLVED.",
                status="SENT",
            )
        )

        save_resolution_memory(
            tx=tx,
            inv=inv,
            human_decision="rejected_escalated",
            manager_decision="rejected_payment_requested",
            action_taken="CUSTOMER_PAYMENT_RECEIVED",
            final_solution=f"Customer paid remaining balance of ${float(amount):,.2f}",
        )

        db.flush()
        return {
            "payment_id": payment.id,
            "transaction_id": tx.id,
            "matched": True,
            "status": tx.status,
            "difference": 0,
        }

    return {"payment_id": payment.id, "matched": False, "status": "AMOUNT_MISMATCH"}
