"""Slack integration for manager escalation and notifications."""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

from ..database.config import settings
from .connections import get_slack_client

logger = logging.getLogger(__name__)


def verify_slack_signature(timestamp: str | None, signature: str | None, raw_body: bytes) -> bool:
    """Validate Slack's signed request before processing any callback.

    Slack actions are notifications only in this service. A valid Slack
    signature never grants authority to post a journal entry; managers still
    authenticate through the application's own API before a financial action.
    """
    secret = settings.SLACK_SIGNING_SECRET
    if not secret or not timestamp or not signature:
        return False
    try:
        request_time = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - request_time) > 60 * 5:
        return False
    base = f"v0:{timestamp}:".encode("utf-8") + raw_body
    expected = "v0=" + hmac.new(secret.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _review_url(transaction_id: str) -> str:
    query = urlencode({"transaction": transaction_id, "source": "slack"})
    return f"{settings.FRONTEND_ORIGIN.rstrip('/')}/transactions/{transaction_id}?{query}"


def send_escalation_message(
    transaction_id: str,
    customer: str,
    amount: float,
    reason: str,
    invoice_id: str | None = None,
) -> dict | None:
    """Send a manager escalation message to Slack.

    Returns message metadata on success, None on failure.
    Never claims success unless the Slack API confirms delivery.
    """
    client = get_slack_client()
    if client is None:
        logger.warning("Slack unavailable – escalation for %s not sent.", transaction_id)
        return None

    channel = settings.SLACK_CHANNEL_ID
    if not channel:
        logger.warning("SLACK_CHANNEL_ID not set – cannot send escalation.")
        return None

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔔 Discount Approval Required",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Transaction:*\n{transaction_id}"},
                {"type": "mrkdwn", "text": f"*Invoice:*\n{invoice_id or 'N/A'}"},
                {"type": "mrkdwn", "text": f"*Customer:*\n{customer}"},
                {"type": "mrkdwn", "text": f"*Amount:*\n${amount:,.2f}"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Reason:*\n{reason}",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Review the evidence and authenticate in TallyFlow before making a decision.",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Review in TallyFlow"},
                    "url": _review_url(transaction_id),
                    "action_id": "review_financial_case",
                }
            ],
        },
    ]

    try:
        response = client.chat_postMessage(
            channel=channel,
            text=f"Discount approval required for {transaction_id} – {customer} – ${amount:,.2f}",
            blocks=blocks,
        )
        if response.get("ok"):
            logger.info("Slack escalation sent for %s (ts=%s)", transaction_id, response.get("ts"))
            return {
                "channel": response.get("channel"),
                "message_id": response.get("ts"),
                "ok": True,
            }
        else:
            logger.error("Slack API error: %s", response.get("error"))
            return None
    except Exception as e:
        logger.error("Slack message failed for %s: %s", transaction_id, e)
        return None


def send_resolution_message(
    transaction_id: str,
    customer: str,
    journal_entry_id: str,
    amount: float,
) -> dict | None:
    """Send a resolution confirmation to Slack."""
    client = get_slack_client()
    if client is None:
        return None

    channel = settings.SLACK_CHANNEL_ID
    if not channel:
        return None

    try:
        response = client.chat_postMessage(
            channel=channel,
            text=f"✅ {transaction_id} resolved – Journal {journal_entry_id} posted (${amount:,.2f}) for {customer}.",
        )
        return {"ok": response.get("ok", False), "ts": response.get("ts")} if response.get("ok") else None
    except Exception as e:
        logger.error("Slack resolution message failed: %s", e)
        return None


def send_payment_request_message(
    transaction_id: str,
    customer: str,
    amount: float,
    invoice_id: str | None = None,
) -> dict | None:
    """Notify Slack that a payment request has been sent to the customer."""
    client = get_slack_client()
    if client is None:
        return None

    channel = settings.SLACK_CHANNEL_ID
    if not channel:
        return None

    try:
        response = client.chat_postMessage(
            channel=channel,
            text=(
                f"💰 Payment request sent to {customer} for ${amount:,.2f} "
                f"(invoice {invoice_id or transaction_id}). "
                f"Transaction {transaction_id} status → PAYMENT_REQUESTED."
            ),
        )
        return {"ok": response.get("ok", False), "ts": response.get("ts")} if response.get("ok") else None
    except Exception as e:
        logger.error("Slack payment request message failed: %s", e)
        return None
