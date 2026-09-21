"""Email provider abstraction and decoupled notification delivery.

Adheres strictly to Architecture Non-Negotiables:
- Non-Negotiable #6 (send confirmation email)
- Non-Negotiable #12 (send customer payment request)
- Non-Negotiable #18 (failure semantics: notifications decoupled from financial ledger mutations)
"""
from __future__ import annotations

import logging
from typing import Protocol

from ..database.config import settings

logger = logging.getLogger(__name__)


class EmailProvider(Protocol):
    """Protocol for email delivery providers."""

    async def send_confirmation_email(
        self,
        to_email: str,
        transaction_id: str,
        amount: float,
        journal_entry_id: str,
        customer: str,
    ) -> dict: ...

    async def send_customer_payment_request(
        self,
        to_email: str,
        customer: str,
        amount: float,
        invoice_id: str,
        transaction_id: str,
    ) -> dict: ...


class AgentMailEmailProvider:
    """Production provider integrating with AgentMail service."""

    def __init__(self, api_key: str = "", inbox_id: str = "") -> None:
        self.api_key = api_key or settings.AGENTMAIL_API_KEY
        self.inbox_id = inbox_id or settings.AGENTMAIL_INBOX_ID

    async def send_confirmation_email(
        self,
        to_email: str,
        transaction_id: str,
        amount: float,
        journal_entry_id: str,
        customer: str,
    ) -> dict:
        try:
            import httpx
            url = f"https://api.agentmail.to/v0/inboxes/{self.inbox_id}/messages/send"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "to": [to_email],
                "subject": f"TallyFlow Resolution Confirmation: {transaction_id}",
                "text": (
                    f"Journal entry {journal_entry_id} for ${amount:,.2f} has reconciled "
                    f"transaction {transaction_id} for {customer}."
                ),
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.is_success:
                    return {"status": "SENT", "response": res.json()}
                return {"status": "FAILED", "error": res.text}
        except Exception as exc:
            logger.error("AgentMail confirmation email failed: %s", exc)
            return {"status": "FAILED", "error": str(exc)}

    async def send_customer_payment_request(
        self,
        to_email: str,
        customer: str,
        amount: float,
        invoice_id: str,
        transaction_id: str,
    ) -> dict:
        try:
            import httpx
            url = f"https://api.agentmail.to/v0/inboxes/{self.inbox_id}/messages/send"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "to": [to_email],
                "subject": f"Payment Request: Outstanding Balance for Invoice {invoice_id}",
                "text": (
                    f"Dear {customer},\n\n"
                    f"Your account has an outstanding balance of ${amount:,.2f} "
                    f"associated with invoice {invoice_id}.\n\n"
                    f"Please arrange payment of the remaining balance.\n\n"
                    f"Reference: {transaction_id}"
                ),
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.is_success:
                    return {"status": "SENT", "response": res.json()}
                return {"status": "FAILED", "error": res.text}
        except Exception as exc:
            logger.error("AgentMail payment request failed: %s", exc)
            return {"status": "FAILED", "error": str(exc)}

    async def send_customer_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        transaction_id: str,
    ) -> dict:
        try:
            if not self.api_key or not self.inbox_id:
                logger.info("Mocking AgentMail email delivery to %s for %s", to_email, transaction_id)
                return {"status": "SENT", "provider": "mock", "to": to_email, "subject": subject}
            import httpx
            url = f"https://api.agentmail.to/v0/inboxes/{self.inbox_id}/messages/send"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "to": [to_email],
                "subject": subject,
                "text": body,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.is_success:
                    return {"status": "SENT", "response": res.json()}
                return {"status": "FAILED", "error": res.text}
        except Exception as exc:
            logger.error("AgentMail custom email failed: %s", exc)
            return {"status": "FAILED", "error": str(exc)}


def get_email_provider() -> EmailProvider:
    """Factory selecting the active email provider."""
    return AgentMailEmailProvider()


email_provider: AgentMailEmailProvider = AgentMailEmailProvider()


async def safe_send_resolution_email(
    to_email: str,
    transaction_id: str,
    amount: float,
    journal_entry_id: str,
    customer: str,
) -> dict:
    """Non-throwing email sender enforcing Rule 18 failure isolation."""
    try:
        return await email_provider.send_confirmation_email(
            to_email=to_email,
            transaction_id=transaction_id,
            amount=amount,
            journal_entry_id=journal_entry_id,
            customer=customer,
        )
    except Exception as exc:
        logger.warning("Decoupled resolution email failed for %s: %s", transaction_id, exc)
        return {"status": "FAILED", "error": str(exc)}


async def safe_send_payment_request_email(
    to_email: str,
    customer: str,
    amount: float,
    invoice_id: str,
    transaction_id: str,
) -> dict:
    """Non-throwing email sender enforcing Rule 18 failure isolation."""
    try:
        return await email_provider.send_customer_payment_request(
            to_email=to_email,
            customer=customer,
            amount=amount,
            invoice_id=invoice_id,
            transaction_id=transaction_id,
        )
    except Exception as exc:
        logger.warning("Decoupled customer payment request email failed for %s: %s", transaction_id, exc)
        return {"status": "FAILED", "error": str(exc)}


async def safe_send_customer_email(
    to_email: str,
    subject: str,
    body: str,
    transaction_id: str,
) -> dict:
    """Send customer communication with decoupled failure semantics."""
    try:
        return await email_provider.send_customer_email(
            to_email=to_email,
            subject=subject,
            body=body,
            transaction_id=transaction_id,
        )
    except Exception as exc:
        logger.warning("Decoupled customer communication email failed for %s: %s", transaction_id, exc)
        return {"status": "FAILED", "error": str(exc)}

