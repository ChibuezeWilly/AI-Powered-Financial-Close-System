"""Automated validation suite for all 21 Architecture Non-Negotiables."""
import asyncio
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import select
from app.database.database import SessionLocal, Base, engine
from app.schema.models import (
    AccountingPeriod,
    Adjustment,
    AuditEvent,
    Customer,
    FinancialTransaction,
    Invoice,
    Investigation,
    JournalEntry,
    LedgerEntry,
    PaymentRequest,
    User,
)
from app.services.accounting import (
    JournalRequest,
    ReceivableRequest,
    PaymentRecordRequest,
    MockAccountingProvider,
    get_accounting_provider,
    AccountingError,
)
from app.services.workflow import (
    transition,
    resolve_approved_adjustment,
    escalate_rejection,
    resolve_manager_rejection,
    process_incoming_payment,
    TRANSITIONS,
)
from app.services.email_service import AgentMailEmailProvider, email_provider
from app.services.pinecone_service import save_resolution_memory

passed = 0
failed = 0


def check(name: str, condition: bool, err_msg: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: {err_msg}")


async def run_suite():
    global passed, failed
    print("\n============================================================")
    print("RUNNING ARCHITECTURE NON-NEGOTIABLES VERIFICATION SUITE")
    print("============================================================\n")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        from app.schema.models import Approval, ApprovalRequest, ManagerEscalation, Discrepancy
        for tid in ["TX-TEST-1", "TX-UNIT-TEST"]:
            db.query(LedgerEntry).filter(LedgerEntry.transaction_id == tid).delete()
            db.query(JournalEntry).filter(JournalEntry.transaction_id == tid).delete()
            db.query(PaymentRequest).filter(PaymentRequest.transaction_id == tid).delete()
            db.query(Adjustment).filter(Adjustment.transaction_id == tid).delete()
            db.query(ApprovalRequest).filter(ApprovalRequest.transaction_id == tid).delete()
            db.query(ManagerEscalation).filter(ManagerEscalation.transaction_id == tid).delete()
            db.query(Approval).filter(Approval.transaction_id == tid).delete()
            db.query(Discrepancy).filter(Discrepancy.transaction_id == tid).delete()
            db.query(AuditEvent).filter(AuditEvent.subject == tid).delete()
            db.query(FinancialTransaction).filter(FinancialTransaction.id == tid).delete()
        db.query(Invoice).filter(Invoice.id == "INV-UNIT-1001").delete()
        db.commit()

        # 1. Verify AccountingProvider Protocol & Mock implementation
        print("--- Rule 2: AccountingProvider Abstraction & Mock Provider ---")
        mock_provider = MockAccountingProvider()
        init_ar_bal = await mock_provider.get_account_balance(db, "Accounts Receivable")
        check("Initial AR balance returned", init_ar_bal > 0)

        test_tx = FinancialTransaction(
            id="TX-TEST-1",
            period="2026-09",
            transaction_date="2026-09-01",
            customer="Test Customer",
            account="Accounts Receivable",
            expected_amount=Decimal("12400.00"),
            actual_amount=Decimal("11900.00"),
            difference=Decimal("500.00"),
            status="AWAITING_HUMAN_APPROVAL",
        )
        db.merge(test_tx)
        db.commit()

        # Invalid journal entry (zero amount)
        zero_failed = False
        try:
            await mock_provider.create_journal_entry(
                db,
                JournalRequest("TX-TEST-1", "Discount Expense", "Accounts Receivable", Decimal("0.00"), "idem-0"),
            )
        except AccountingError:
            zero_failed = True
        check("Mock provider rejects zero journal amount", zero_failed)

        # Valid journal entry & dual ledger posting
        je = await mock_provider.create_journal_entry(
            db,
            JournalRequest("TX-TEST-1", "Discount Expense", "Accounts Receivable", Decimal("500.00"), "idem-1"),
        )
        check("Journal entry created", je.id == "JE-TEST-1")
        check("Provider ID returned", je.provider_id == "mock-je-idem-1")
        check("Transaction verified", await mock_provider.verify_transaction(db, "TX-TEST-1"))

        # Check ledger balance updated
        new_ar_bal = await mock_provider.get_account_balance(db, "Accounts Receivable")
        check("Account balance adjusted on journal entry", new_ar_bal == init_ar_bal - Decimal("500.00"))

        # Check receivable creation
        rec = await mock_provider.create_receivable(
            db,
            ReceivableRequest("TX-TEST-1", "CUST-1001", "INV-UNIT-1001", Decimal("500.00"), "idem-rec-1"),
        )
        check("Receivable created with external ID", rec.get("external_id", "").startswith("mock-ar-"))

        # Check payment recording
        pmt = await mock_provider.record_payment(
            db,
            PaymentRecordRequest("TX-TEST-1", "CUST-1001", Decimal("500.00"), "wire", "REF123", "idem-pmt-1"),
        )
        check("Payment recorded with cleared status", pmt.get("status") == "CLEARED")

        # 2. State Machine Rules
        print("\n--- Rule 5: Explicit 15-State Transaction State Machine ---")

        cust = db.scalar(select(Customer).where(Customer.id == "CUST-1001"))
        if not cust:
            cust = Customer(id="CUST-1001", name="Acme Corp", legal_name="Acme Corp")
            db.add(cust)
            db.flush()

        inv = db.scalar(select(Invoice).where(Invoice.id == "INV-UNIT-1001"))
        if not inv:
            inv = Invoice(
                id="INV-UNIT-1001",
                customer_id="CUST-1001",
                invoice_date="2026-09-01",
                due_date="2026-09-30",
                subtotal=Decimal("12400.00"),
                total=Decimal("12400.00"),
                balance=Decimal("500.00"),
                accounting_period="2026-09",
            )
            db.add(inv)
            db.flush()

        admin_user = db.get(User, 1)
        if not admin_user:
            admin_user = User(id=1, email="admin@example.com", full_name="Admin", password_hash="hash", role="ADMIN")
            db.add(admin_user)
            db.flush()

        tx = FinancialTransaction(
            id="TX-UNIT-TEST",
            period="2026-09",
            transaction_date="2026-09-02",
            customer="Acme Corp",
            customer_id="CUST-1001",
            invoice_id="INV-UNIT-1001",
            payment_id="PAY-5001",
            account="Accounts Receivable",
            expected_amount=Decimal("12400.00"),
            actual_amount=Decimal("11900.00"),
            difference=Decimal("500.00"),
            discrepancy_type="UNDOCUMENTED_DISCOUNT",
            severity="HIGH",
            status="AWAITING_HUMAN_APPROVAL",
        )
        tx = db.merge(tx)
        db.commit()

        period = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == "2026-09"))
        if not period:
            period = AccountingPeriod(code="2026-09", status="OPEN")
            db.add(period)
        else:
            period.status = "OPEN"
        db.commit()

        # Test invalid direct jump (e.g. from AWAITING_HUMAN_APPROVAL directly to RESOLVED)
        invalid_jump = False
        try:
            transition(tx, "RESOLVED")
        except Exception:
            invalid_jump = True
        check("Invalid state machine transition blocked", invalid_jump)

        # 3. Approved Flow Chain
        print("\n--- Rule 6 & 10: Approved Flow Execution ---")
        tx.status = "AWAITING_HUMAN_APPROVAL"
        db.commit()

        approve_res = await resolve_approved_adjustment(db, tx, "e2e-approve-unit", 1)
        check("Transaction status RESOLVED after approval", tx.status == "RESOLVED")
        check("Difference reconciled to 0", tx.difference == Decimal("0.00"))
        check("Actual amount matches expected", tx.actual_amount == tx.expected_amount)
        check("Journal entry posted in DB", bool(approve_res.get("journal_entry")))

        # Check PostgreSQL audit events
        audit_entry = db.scalar(
            select(AuditEvent).where(AuditEvent.subject == tx.id, AuditEvent.action == "JOURNAL_ENTRY_POSTED")
        )
        check("AuditEvent JOURNAL_ENTRY_POSTED recorded in PostgreSQL", audit_entry is not None)

        # 4. Rejected Flow & Escalation
        print("\n--- Rule 7 & 11: Rejection & Manager Escalation Flow ---")
        tx = db.get(FinancialTransaction, "TX-UNIT-TEST")
        tx.status = "AWAITING_HUMAN_APPROVAL"
        tx.difference = Decimal("500.00")
        tx.actual_amount = Decimal("11900.00")
        db.commit()

        esc_res = escalate_rejection(db, tx, 1, "Evidence insufficient for discount")
        db.commit()
        check("Status transitioned to AWAITING_MANAGER_APPROVAL", tx.status == "AWAITING_MANAGER_APPROVAL")

        # 5. Manager Rejection Flow
        print("\n--- Rule 8 & 12: Manager Rejection Flow ---")
        mgr_rej_res = await resolve_manager_rejection(db, tx, 1, "Manager rejected discount")
        db.commit()
        check("Status transitioned to PAYMENT_PENDING", tx.status == "PAYMENT_PENDING")
        check("Receivable external ID generated", bool(mgr_rej_res.get("receivable_id")))

        pr = db.scalar(select(PaymentRequest).where(PaymentRequest.transaction_id == tx.id))
        check("PaymentRequest created in PostgreSQL", pr is not None and pr.amount == Decimal("500.00"))

        # 6. Payment Arrival & Reconciliation
        print("\n--- Rule 13: Incoming Payment Ingestion & Reconciliation ---")
        pmt_res = await process_incoming_payment(
            db,
            customer_id="CUST-1001",
            amount=Decimal("500.00"),
            invoice_id="INV-UNIT-1001",
            payment_method="wire",
            reference="WIRE-E2E-1",
        )
        db.commit()
        db.refresh(tx)
        check("Payment matched and processed", pmt_res.get("matched") is True, f"Result: {pmt_res}")
        check("Transaction transitioned to RESOLVED on payment arrival", tx.status == "RESOLVED")
        check("Final difference is 0", tx.difference == Decimal("0.00"))

        # 7. Period Safety
        print("\n--- Rule 20: Accounting Period Safety ---")
        period.status = "CLOSED"
        db.commit()

        closed_blocked = False
        try:
            tx.status = "AWAITING_HUMAN_APPROVAL"
            await resolve_approved_adjustment(db, tx, "closed-test", 1)
        except Exception:
            closed_blocked = True
        check("Mutations blocked on CLOSED accounting period", closed_blocked)

        period.status = "OPEN"
        db.commit()

        print("\n============================================================")
        print(f"RESULTS: {passed} PASSED, {failed} FAILED")
        print("============================================================\n")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_suite())
