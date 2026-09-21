"""Endpoints for signed integration callbacks.

These endpoints never perform privileged financial actions.  Slack callbacks
are verified with Slack's signing secret and direct the user to the normal,
authenticated TallyFlow decision API.
"""
from __future__ import annotations

import json
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from ..services.slack_service import verify_slack_signature

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])
slack_callback_router = APIRouter(tags=["integrations"])


async def _handle_slack_events(request: Request):
    raw_body = await request.body()
    if not verify_slack_signature(
        request.headers.get("X-Slack-Request-Timestamp"),
        request.headers.get("X-Slack-Signature"),
        raw_body,
    ):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type:
        # Interactive Slack payloads are acknowledged only. They never invoke
        # a ledger operation; the button opens the authenticated web UI.
        parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        payload = json.loads(parsed.get("payload", ["{}"])[0])
    else:
        payload = json.loads(raw_body or b"{}")

    if payload.get("type") == "url_verification":
        return JSONResponse({"challenge": payload.get("challenge", "")})

    # When Slack interactive buttons (Approve/Reject) are clicked:
    # Direct manager to authenticate in TallyFlow to execute ledger mutation (Rule 11)
    if payload.get("type") == "block_actions":
        actions = payload.get("actions", [])
        action_val = actions[0].get("value", "") if actions else ""
        return JSONResponse({
            "response_type": "ephemeral",
            "text": (
                f"Action received: `{action_val}`. "
                "Per Financial Architecture Rule 11, financial mutations require authenticated backend credentials. "
                "Please review and submit authorization in TallyFlow."
            ),
        })

    return JSONResponse({"ok": True})


@router.post("/slack/events")
async def slack_events(request: Request):
    return await _handle_slack_events(request)


@slack_callback_router.post("/slack/events")
async def slack_events_legacy(request: Request):
    return await _handle_slack_events(request)
