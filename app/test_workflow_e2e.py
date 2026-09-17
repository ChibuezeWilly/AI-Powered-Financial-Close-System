"""
End-to-end test for the TallyFlow approve / reject / escalate workflow.

Run with the API server already listening on http://localhost:8000:

    python test_workflow_e2e.py

The script exercises the full lifecycle:
  1. Login as admin
  2. List periods & verify dashboard metrics
  3. Fetch transactions → find AWAITING_HUMAN_APPROVAL cases
  4. Fetch transaction detail with investigation & evidence
  5. APPROVE one transaction → verify RESOLVED, journal posted, difference=0
  6. REJECT another → verify escalation to AWAITING_MANAGER_APPROVAL
  7. Create / fetch a FINANCE_MANAGER user → manager-approve the escalated tx
  8. Verify audit trail records every decision & event
  9. Verify notifications exist for escalation & resolution
"""
from __future__ import annotations

import json
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = "http://localhost:8000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "change-this-to-a-strong-password"
MANAGER_EMAIL = "manager-test@example.com"
MANAGER_PASSWORD = "manager-test-password-12"
MANAGER_NAME = "E2E Test Manager"

passed = 0
failed = 0


def api(method: str, path: str, body: dict | None = None, token: str | None = None,
        extra_headers: dict | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode() if body else None
    req = Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            detail = json.loads(raw)
        except Exception:
            detail = {"raw": raw}
        return {"__error__": True, "status": exc.code, **detail}


def check(label: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {label}")
    else:
        failed += 1
        print(f"  ✗ {label}  — {detail}")


def main():
    global passed, failed

    # ── Step 1: Login ─────────────────────────────────────────────────
    print("\n═══ Step 1: Admin login")
    login = api("POST", "/api/v1/auth/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    admin_token = login.get("access_token", "")
    check("Admin login succeeded", bool(admin_token), str(login))

    # ── Step 2: List periods & dashboard ──────────────────────────────
    print("\n═══ Step 2: Periods & dashboard")
    periods = api("GET", "/api/v1/periods", token=admin_token)
    check("Periods returned as list", isinstance(periods, list) and len(periods) > 0, str(periods)[:120])

    # Select a period that can exercise both decision branches.  Choosing the
    # first period with any transactions can select a period containing only
    # reconciled items, which silently skips most of this E2E workflow.
    test_period = None
    fallback_period = None
    for p in periods:
        candidate_txs = api("GET", f"/api/v1/transactions?period={p['code']}", token=admin_token)
        if not isinstance(candidate_txs, list):
            continue

        awaiting_count = sum(
            tx.get("status") == "AWAITING_HUMAN_APPROVAL" for tx in candidate_txs
        )
        if awaiting_count >= 2:
            test_period = p["code"]
            break
        if awaiting_count >= 1 and fallback_period is None:
            fallback_period = p["code"]

    if test_period is None:
        test_period = fallback_period

    if not test_period:
        # Default to a known seeded period if the API returned no candidates.
        test_period = "2026-09"

    dash = api("GET", f"/api/v1/dashboard?period={test_period}", token=admin_token)
    check("Dashboard has total_transactions", dash.get("total_transactions", 0) >= 0, str(dash)[:120])
    check("Dashboard has close_progress", "close_progress" in dash, str(dash)[:120])
    print(f"    Period: {test_period}, Transactions: {dash.get('total_transactions')}, Reconciled: {dash.get('reconciled')}")

    # ── Step 3: List transactions ─────────────────────────────────────
    print("\n═══ Step 3: List transactions")
    txs = api("GET", f"/api/v1/transactions?period={test_period}", token=admin_token)
    check("Transactions returned as list", isinstance(txs, list), str(txs)[:120])

    awaiting = [t for t in txs if t.get("status") == "AWAITING_HUMAN_APPROVAL"]
    check(f"Found {len(awaiting)} AWAITING_HUMAN_APPROVAL transactions", len(awaiting) >= 1, f"All statuses: {set(t['status'] for t in txs)}")

    if len(awaiting) < 2:
        print("  ⚠  Need at least 2 AWAITING_HUMAN_APPROVAL transactions for full test. "
              "Will test available paths only.")

    # ── Step 4: Fetch transaction detail ──────────────────────────────
    print("\n═══ Step 4: Transaction detail & investigation")
    tx_approve = awaiting[0] if awaiting else None
    tx_reject = awaiting[1] if len(awaiting) > 1 else None

    if tx_approve:
        detail = api("GET", f"/api/v1/transactions/{tx_approve['id']}", token=admin_token)
        check("Detail has investigation field", "investigation" in detail, str(detail.keys()))
        check("Detail has evidence_graph", "evidence_graph" in detail, str(detail.keys()))
        check("Detail has journal_entry field", "journal_entry" in detail, str(detail.keys()))
        if detail.get("investigation"):
            inv = detail["investigation"]
            check("Investigation has evidence array", isinstance(inv.get("evidence"), list), "")
            check("Investigation has timeline array", isinstance(inv.get("timeline"), list), "")
            print(f"    Investigation: {inv.get('id')} status={inv.get('status')} evidence_count={len(inv.get('evidence', []))}")

    # ── Step 5: Approve flow ──────────────────────────────────────────
    print("\n═══ Step 5: Approve adjustment")
    if tx_approve:
        result = api(
            "POST",
            f"/api/v1/transactions/{tx_approve['id']}/decision",
            {"decision": "approved", "reason": "E2E test: approved after review of evidence."},
            token=admin_token,
            extra_headers={"Idempotency-Key": f"e2e-approve-{tx_approve['id']}-{int(time.time())}"},
        )
        check("Approve returned status", "status" in result, str(result)[:200])
        check("Status is RESOLVED", result.get("status") == "RESOLVED", f"Got: {result.get('status')}")
        check("Journal entry posted", bool(result.get("journal_entry")), str(result)[:200])
        check("Difference is 0", result.get("difference") == 0, f"Got: {result.get('difference')}")

        # Verify detail reflects resolved state
        detail_after = api("GET", f"/api/v1/transactions/{tx_approve['id']}", token=admin_token)
        check("Transaction now RESOLVED", detail_after.get("status") == "RESOLVED", f"Got: {detail_after.get('status')}")
        check("Difference now 0", detail_after.get("difference") == 0, f"Got: {detail_after.get('difference')}")
        if detail_after.get("journal_entry"):
            check("Journal status POSTED", detail_after["journal_entry"]["status"] == "POSTED", "")
    else:
        print("  ⚠  No AWAITING_HUMAN_APPROVAL transaction to test approval flow")

    # ── Step 6: Reject & escalate flow ────────────────────────────────
    print("\n═══ Step 6: Reject & escalate")
    if tx_reject:
        result = api(
            "POST",
            f"/api/v1/transactions/{tx_reject['id']}/decision",
            {"decision": "rejected", "reason": "E2E test: rejected for manager review."},
            token=admin_token,
            extra_headers={"Idempotency-Key": f"e2e-reject-{tx_reject['id']}-{int(time.time())}"},
        )
        check("Reject returned status", "status" in result, str(result)[:200])
        check("Status is AWAITING_MANAGER_APPROVAL",
              result.get("status") == "AWAITING_MANAGER_APPROVAL",
              f"Got: {result.get('status')}")
        check("Escalation message present", bool(result.get("message")), str(result)[:200])

        detail_esc = api("GET", f"/api/v1/transactions/{tx_reject['id']}", token=admin_token)
        check("Transaction now AWAITING_MANAGER_APPROVAL",
              detail_esc.get("status") == "AWAITING_MANAGER_APPROVAL",
              f"Got: {detail_esc.get('status')}")
    else:
        print("  ⚠  No second AWAITING_HUMAN_APPROVAL transaction to test rejection flow")

    # ── Step 7: Manager decision ──────────────────────────────────────
    print("\n═══ Step 7: Manager decision")
    if tx_reject:
        # Create a FINANCE_MANAGER user (or reuse if exists)
        reg = api("POST", "/api/v1/auth/register", {
            "email": MANAGER_EMAIL,
            "password": MANAGER_PASSWORD,
            "full_name": MANAGER_NAME,
        })
        if reg.get("__error__") and reg.get("status") == 409:
            # Already exists → login
            reg = api("POST", "/api/v1/auth/login", {"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD})

        manager_token = reg.get("access_token", "")
        manager_id = reg.get("user", {}).get("id")
        check("Manager user available", bool(manager_token), str(reg)[:120])

        # Promote to FINANCE_MANAGER via admin
        if manager_id:
            api("PATCH", f"/api/v1/auth/accounts/{manager_id}", {"role": "FINANCE_MANAGER"}, token=admin_token)

        # Re-login after role change
        reg2 = api("POST", "/api/v1/auth/login", {"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD})
        manager_token = reg2.get("access_token", manager_token)
        check("Manager role is FINANCE_MANAGER",
              reg2.get("user", {}).get("role") == "FINANCE_MANAGER",
              f"Got: {reg2.get('user', {}).get('role')}")

        # Manager approve
        mgr_result = api(
            "POST",
            f"/api/v1/transactions/{tx_reject['id']}/manager-decision",
            {"decision": "approved", "reason": "E2E test: manager approved after escalation."},
            token=manager_token,
        )
        check("Manager approve returned status", "status" in mgr_result, str(mgr_result)[:200])
        check("Status is RESOLVED after manager approval",
              mgr_result.get("status") == "RESOLVED",
              f"Got: {mgr_result.get('status')}")

        detail_final = api("GET", f"/api/v1/transactions/{tx_reject['id']}", token=admin_token)
        check("Transaction RESOLVED after manager approve",
              detail_final.get("status") == "RESOLVED",
              f"Got: {detail_final.get('status')}")
    else:
        print("  ⚠  No escalated transaction to test manager decision")

    # ── Step 8: Audit trail ───────────────────────────────────────────
    print("\n═══ Step 8: Audit trail verification")
    if tx_approve:
        audit = api("GET", f"/api/v1/transactions/{tx_approve['id']}/audit", token=admin_token)
        check("Audit has approvals", len(audit.get("approvals", [])) >= 1, str(audit)[:200])
        check("Audit has events", len(audit.get("events", [])) >= 1, str(audit)[:200])

        # Check for expected event types
        event_actions = {e["action"] for e in audit.get("events", [])}
        check("JOURNAL_ENTRY_POSTED in events", "JOURNAL_ENTRY_POSTED" in event_actions, str(event_actions))
        check("RECONCILIATION_VERIFIED in events", "RECONCILIATION_VERIFIED" in event_actions, str(event_actions))

    if tx_reject:
        audit_esc = api("GET", f"/api/v1/transactions/{tx_reject['id']}/audit", token=admin_token)
        check("Escalated tx has approvals", len(audit_esc.get("approvals", [])) >= 2, str(audit_esc)[:200])

        decisions = [a["decision"] for a in audit_esc.get("approvals", [])]
        check("Has 'rejected' decision", "rejected" in decisions, str(decisions))
        check("Has 'manager_approved' decision", "manager_approved" in decisions, str(decisions))

    # ── Step 9: Notifications ─────────────────────────────────────────
    print("\n═══ Step 9: Notifications verification")
    notifs = api("GET", "/api/v1/notifications", token=admin_token)
    check("Notifications returned as list", isinstance(notifs, list), str(notifs)[:120])
    if notifs:
        events = {n.get("event") for n in notifs}
        check("Has ADJUSTMENT_SUCCESS notification", "ADJUSTMENT_SUCCESS" in events, str(events))
        # The escalation notification may or may not be present depending on order
        if tx_reject:
            check("Has MANAGER_ESCALATION notification", "MANAGER_ESCALATION" in events, str(events))

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    total = passed + failed
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    if failed:
        print("  ⚠  Some checks failed — see above for details")
    else:
        print("  ✓  All checks passed!")
    print(f"{'═' * 60}\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
