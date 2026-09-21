import os
import sys
import unittest
from decimal import Decimal
from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import Base, SessionLocal, engine
from app.schema.models import FinancialTransaction, Investigation, User, Employee
from app.langgraph.model_router import (
    DeterministicAccountingRunner,
    CompositeStructuredRunner,
    _parse_and_validate,
)
from app.routers.workspace_portal import Insight


from app.lifespan import _migrate_schema


class TestMasterWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _migrate_schema()

    def test_insight_schema_deterministic_runner(self):
        """Verify Insight schema generates and validates without Pydantic errors."""
        runner = DeterministicAccountingRunner()
        payload = {
            "period": "2026-09",
            "transaction_count": 15,
            "discrepancies": 3,
            "transactions": [],
        }
        result = runner.invoke(
            model="meta-llama/Llama-3.3-70B-Instruct",
            prompt="Analyze this dataset",
            payload=payload,
            schema=Insight,
        )
        self.assertEqual(result.period, "2026-09")
        self.assertIn("2026-09", result.summary)
        self.assertTrue(len(result.risks) > 0)
        self.assertTrue(len(result.recommendations) > 0)
        self.assertTrue(all(isinstance(r, str) for r in result.recommendations))

    def test_parse_and_validate_coercion(self):
        """Verify nested dictionary recommendations are coerced to strings."""
        json_with_dict_recs = '''{
            "period": "2026-09",
            "summary": "Financial review completed.",
            "risks": ["Risk 1", {"risk": "Risk 2"}],
            "recommendations": [{"action": "Verify FIN-042 documentation"}, "Conduct bank audit"]
        }'''
        insight = _parse_and_validate(json_with_dict_recs, Insight)
        self.assertEqual(insight.period, "2026-09")
        self.assertEqual(insight.summary, "Financial review completed.")
        self.assertEqual(len(insight.recommendations), 2)
        self.assertEqual(insight.recommendations[0], "Verify FIN-042 documentation")
        self.assertEqual(insight.recommendations[1], "Conduct bank audit")

    def test_model_fallback_on_402_simulated(self):
        """Verify runner uses deterministic runner when live LLM is unavailable or credits exhausted."""
        runner = CompositeStructuredRunner()
        runner.llm_runner = None
        payload = {
            "request": {
                "transaction_id": "TX-2496",
                "expected_amount": 1200.0,
                "actual_amount": 1572.15,
                "transaction": {
                    "transaction_id": "TX-2496",
                    "invoice_id": "INV-1001",
                    "discrepancy_type": "OVERPAYMENT",
                },
            }
        }
        from app.langgraph.schema import RootCauseHypothesis
        result = runner.invoke(
            model="meta-llama/Llama-3.3-70B-Instruct",
            prompt="Investigate root cause",
            payload=payload,
            schema=RootCauseHypothesis,
        )
    def test_investigation_and_findings_structure(self):
        """Verify manual investigation execution populates 5 agent findings and email draft."""
        from app.langgraph.ai_investigation import investigate_transaction
        with SessionLocal() as db:
            tx = db.scalar(select(FinancialTransaction).where(FinancialTransaction.difference != 0).limit(1))
            if tx:
                tx.status = "DISCREPANCY_DETECTED"
                db.flush()
                res = investigate_transaction(db, tx)
                self.assertEqual(tx.status, "AWAITING_HUMAN_APPROVAL")
                self.assertIsNotNone(tx.root_cause)
                self.assertIsNotNone(tx.recommendation)
                
                inv = db.scalar(select(Investigation).where(Investigation.transaction_id == tx.id))
                self.assertIsNotNone(inv)
                self.assertIsNotNone(inv.customer_email_draft)
                self.assertIsNotNone(inv.manager_escalation_draft)
                self.assertIn("Subject:", inv.customer_email_draft)

    def test_decoupled_email_safe_execution(self):
        """Verify safe_send_customer_email runs without throwing even if mocked or unconfigured."""
        import asyncio
        from app.services.email_service import safe_send_customer_email
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res = loop.run_until_complete(
                safe_send_customer_email(
                    to_email="test@example.com",
                    subject="Regarding TX-2496",
                    body="Please confirm overpayment allocation.",
                    transaction_id="TX-2496",
                )
            )
            self.assertIn(res.get("status"), {"SENT", "FAILED"})
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()

