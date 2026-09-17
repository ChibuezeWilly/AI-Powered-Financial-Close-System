"""FastAPI application entry point for the TallyFlow financial close platform."""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .database.config import settings
from .database.database import Base, SessionLocal, engine
from .schema.models import AccountingPeriod, FinancialTransaction, Investigation, User
from .routers.auth import hash_password, router as auth_router
from .routers.financial_close import router as financial_close_router
from .routers.integrations import router as integrations_router, slack_callback_router
from .routers.transactions import router as transactions_router


def _seed_database() -> None:
    """Seed the database with initial data if empty."""
    Base.metadata.create_all(bind=engine)

    # Import and run the comprehensive seed data generator
    from .services.seed_data import seed_all as seed_financial_data

    with SessionLocal() as db:
        # Default admin user
        if not db.scalar(select(User).where(User.email == settings.DEFAULT_ADMIN_EMAIL.lower())):
            db.add(
                User(
                    email=settings.DEFAULT_ADMIN_EMAIL.lower(),
                    full_name="Platform Administrator",
                    password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                    role="ADMIN",
                )
            )

        current_year = date.today().year
        for year in range(current_year - 1, current_year + 2):
            for month in range(1, 13):
                code = f"{year}-{month:02d}"
                if not db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == code)):
                    db.add(AccountingPeriod(
                        code=code,
                        year=year,
                        month=month,
                        period_start=f"{year}-{month:02d}-01",
                        period_end=f"{year}-{month:02d}-28",
                    ))

        if not db.get(FinancialTransaction, "TX-1001"):
            db.add_all(
                [
                    FinancialTransaction(
                        id="TX-1001",
                        period="2026-09",
                        transaction_date="2026-09-02",
                        customer="Acme Corp",
                        invoice_id="INV-1001",
                        payment_id="PAY-5001",
                        account="Accounts Receivable",
                        currency="USD",
                        expected_amount=12400,
                        actual_amount=11900,
                        difference=500,
                        discrepancy_type="UNDOCUMENTED_DISCOUNT",
                        severity="HIGH",
                        status="AWAITING_HUMAN_APPROVAL",
                        root_cause="Customer discount without approved discount record.",
                        recommendation="Request discount approval. If approved, record a $500 adjustment; otherwise request the outstanding balance.",
                        confidence=0.91,
                    ),
                    FinancialTransaction(
                        id="TX-1002",
                        period="2026-09",
                        transaction_date="2026-09-04",
                        customer="Bluepeak Systems",
                        invoice_id="INV-1042",
                        payment_id="PAY-5042",
                        account="Cash - Operating USD",
                        currency="USD",
                        expected_amount=8750,
                        actual_amount=17500,
                        difference=-8750,
                        discrepancy_type="DUPLICATE_PAYMENT",
                        severity="CRITICAL",
                        status="INVESTIGATING",
                        root_cause="Duplicate payment run detected.",
                        recommendation="Park unapplied cash and confirm refund authorization.",
                        confidence=0.88,
                    ),
                    FinancialTransaction(
                        id="TX-1003",
                        period="2026-09",
                        transaction_date="2026-09-05",
                        customer="Corvus Health",
                        invoice_id="INV-1057",
                        payment_id="PAY-5057",
                        account="Accounts Receivable",
                        currency="USD",
                        expected_amount=4300,
                        actual_amount=4300,
                        difference=0,
                        discrepancy_type=None,
                        severity="NONE",
                        status="RECONCILED",
                        root_cause=None,
                        recommendation=None,
                        confidence=None,
                    ),
                ]
            )

            db.add(
                Investigation(
                    id="INVG-1001",
                    transaction_id="TX-1001",
                    status="AWAITING_APPROVAL",
                    evidence=json.dumps(
                        [
                            {
                                "source_type": "Invoice",
                                "source_id": "INV-1001",
                                "title": "INV-1001.pdf",
                                "page": 1,
                                "excerpt": "Customer discount: $500",
                                "relevance": 0.98,
                                "confidence": 0.99,
                                "retrieval_method": "SQL",
                            },
                            {
                                "source_type": "Policy",
                                "source_id": "FIN-042",
                                "title": "Discount authorization policy",
                                "page": 1,
                                "excerpt": "Discounts exceeding $250 require documented approval.",
                                "relevance": 0.96,
                                "confidence": 0.94,
                                "retrieval_method": "Hybrid",
                            },
                            {
                                "source_type": "Approval",
                                "source_id": "NONE",
                                "title": "Discount approval",
                                "page": None,
                                "excerpt": "No matching approval or credit note found.",
                                "relevance": 1,
                                "confidence": 1,
                                "retrieval_method": "SQL",
                            },
                        ]
                    ),
                    timeline=json.dumps(
                        [
                            "09:31 Discrepancy detected",
                            "09:32 Invoice analyzed",
                            "09:33 Ledger checked",
                            "09:34 Policy retrieved",
                            "09:35 Evidence graph built",
                            "09:35 Recommendation generated",
                        ]
                    ),
                )
            )

        db.commit()

        stats = seed_financial_data(db)
        if stats.get("status") != "already_seeded":
            print(f"Seed data: {stats}")

# REMOVE THIS LATER ON AFTER MAIN.PY STARTS

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
   
    _seed_database()

    ngrok_authtoken = settings.NGROK_AUTHTOKEN
    if ngrok_authtoken:
        try:
            import ngrok
            listener = await ngrok.forward(
                "localhost:8000",
                authtoken=ngrok_authtoken,
            )
            print(f"ngrok tunnel available at: {listener.url()}")
            app.state.ngrok_listener = listener
        except Exception as e:
            print(f"ngrok connection failed (non-fatal): {e}")
            app.state.ngrok_listener = None
    else:
        app.state.ngrok_listener = None

    try:
        yield
    finally:
        listener = getattr(app.state, "ngrok_listener", None)
        if listener is not None:
            try:
                await listener.close()
            except Exception:
                pass


app = FastAPI(
    title="TallyFlow API",
    description="AI-powered financial close and reconciliation platform.",
    version="0.3.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tallyflow-api"}

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)

# Route Registrations
app.include_router(auth_router)
app.include_router(financial_close_router)
app.include_router(transactions_router)
app.include_router(integrations_router)
app.include_router(slack_callback_router)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
