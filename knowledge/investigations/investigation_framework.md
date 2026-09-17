# Investigation Framework — Meridian Instruments Ltd (Period 2026-08)

This is the master specification for how a financial discrepancy becomes a
verified, approved, executed and re-verified adjustment. It governs every
other document in `knowledge/investigation/`. All IDs below are canon IDs
from `knowledge/CANON.md` and `data/*.csv`. Do not invent new ones.

## 1. The pipeline

```text
 SYMPTOM
   |  (discrepancy detected: data/discrepancies.csv row, e.g. DISC-0001)
   v
 HYPOTHESES
   |  (ranked candidate explanations; see hypothesis_generation.md)
   v
 EVIDENCE
   |  (SQL over ledger/bank tables, graph traversal, document RAG, policy RAG)
   v
 CONTRADICTIONS
   |  (check evidence against itself and against policy; see contradiction_detection.md)
   v
 ROOT CAUSE
   |  (five-whys / fault tree; assign RC-* code; see root_cause_analysis.md)
   v
 RECOMMENDATION
   |  (adjustment spec: accounts, amount, period; requires confidence >= threshold)
   v
 APPROVAL
   |  (must satisfy POL-APPROVAL-001 authority matrix; see approvals.csv)
   v
 EXECUTION
   |  (post the journal / credit note / refund referenced by adjustment_id)
   v
 VERIFICATION
   |  (re-run the reconciliation check that originally raised the symptom)
   v
 CLOSED
```

Each arrow is a **gate**: an agent may not move to the next stage until the
exit criteria of the current stage are met and the artifact for that stage
has been written to the Investigation record (schema in §4).

## 2. Hard rule

> **No adjustment is ever posted without (a) a root cause that has been
> verified against contradiction checks and carries a confidence score, and
> (b) an approval record that satisfies POL-APPROVAL-001 for the action type
> and amount band.**

This is enforced structurally: the `adjustment` object in the Investigation
record (§4) has required fields `root_cause_code`, `confidence`, and
`approval_id`, and `approval_id` must resolve to a row in `data/approvals.csv`
with `status = approved`. An adjustment with `approval_id: null` or an
approval whose `status` is `missing`, `pending`, or `absent` MUST remain in
state `awaiting_approval` or `proposed` and must not be posted. Examples in
canon: ADJ-5001 (APR-6001 is `missing`), ADJ-5004 (APR-6004 is `absent`) —
both are blocked from execution until a real approval is recorded.

## 3. Stage-by-stage specification

### 3.1 Symptom

- **Entry criteria:** a row exists in `data/discrepancies.csv` with
  `status` in `{under_investigation, pending_adjustment, pending_credit_note}`.
- **Actions:** load the discrepancy row; identify `type`, `amount`,
  `invoice_ids`, `payment_ids`, `bank_transaction_ids`, `ledger_entry_ids`,
  `policy_ids`.
- **Tools:** SQL read of `data/discrepancies.csv` (or its DB mirror).
- **Artifacts:** `Claim` record per discrepancy (schema §4).
- **Exit criteria:** a Claim object is instantiated with `discrepancy_id`
  populated and `status = open`.
- **Owner:** agent (fully automatable).

### 3.2 Hypotheses

- **Entry criteria:** Claim exists.
- **Actions:** apply the discrepancy-type → hypothesis lookup
  (see `hypothesis_generation.md`); rank by prior probability and
  amount-signature; select top 3–6 to carry forward.
- **Tools:** document RAG over `knowledge/accounting/26_common_reconciliation_errors.md`
  for pattern matching; no external tools needed.
- **Artifacts:** ordered list of `Hypothesis` objects attached to the
  Investigation record.
- **Exit criteria:** at least one hypothesis has an explicit discriminating
  test defined.
- **Owner:** agent, with human spot-check for novel discrepancy types.

### 3.3 Evidence

- **Actions:** run the discriminating test for each surviving hypothesis by
  pulling records: ledger entries (SQL), the customer/vendor/PO graph
  (graph query — e.g. "what invoices share PO-BLU-2210"), source documents
  (document RAG — invoice PDFs, remittance advice, emails), and policy text
  (policy RAG — e.g. POL-DISCOUNT-001 v4.0).
- **Tools:** SQL (`data/*.csv`), graph traversal (`knowledge/graph/`),
  document RAG (`knowledge/rag/`), policy RAG (`knowledge/policies/`).
- **Artifacts:** `Evidence` records (schema §4), each citing a source ID.
- **Exit criteria:** every surviving hypothesis is either confirmed, killed,
  or marked "insufficient evidence" (see `evidence_evaluation.md` for the
  sufficiency test).
- **Owner:** agent; human review if evidence is contradictory or missing.

### 3.4 Contradictions

- **Actions:** run the contradiction checks (record vs record, record vs
  document, document vs policy, claim vs evidence, temporal impossibility,
  arithmetic inconsistency) from `contradiction_detection.md`.
- **Tools:** SQL joins across `data/*.csv`; graph cycle/consistency checks.
- **Artifacts:** `Contradiction` list (empty list is a valid, and required,
  outcome before proceeding).
- **Exit criteria:** all contradictions are either resolved with a stated
  reason or escalated to a human (never silently averaged or dropped).
- **Owner:** agent detects; human resolves anything touching authority
  breaches or missing approvals (e.g. DISC-0007).

### 3.5 Root cause

- **Actions:** apply five-whys or fault-tree to the confirmed hypothesis;
  assign an `RC-*` code from `root_cause_analysis.md`; distinguish proximate
  vs systemic cause; classify control failure as design or operating.
- **Tools:** internal reasoning only, referencing evidence collected above.
- **Artifacts:** `RootCause` object with `code`, `proximate_cause`,
  `systemic_cause`, `control_classification`.
- **Exit criteria:** root cause code assigned and traceable to specific
  evidence IDs.
- **Owner:** agent proposes; Controller (EMP-03) reviews for `critical`
  severity discrepancies (e.g. DISC-0007).

### 3.6 Recommendation

- **Actions:** compute confidence score (`confidence_scoring.md`); if above
  the auto-recommend threshold, draft the adjustment spec (debit account,
  credit account, amount, period) referencing the row shape of
  `data/adjustments.csv`.
- **Artifacts:** `Recommendation` object (schema §4).
- **Exit criteria:** recommendation includes a fully specified adjustment
  and a named required approver role from POL-APPROVAL-001 / the authority
  table in CANON.md §17.
- **Owner:** agent.

### 3.7 Approval

- **Actions:** submit the adjustment for approval to the correct role and
  employee per the authority table; record the decision in
  `data/approvals.csv` shape.
- **Tools:** none beyond the approval matrix (policy RAG).
- **Artifacts:** `Approval` reference (`approval_id`).
- **Exit criteria:** `approval.status = approved` with a named
  `approver_employee_id`.
- **Owner:** human (the named approver). The agent may draft the approval
  request but must never self-approve outside its own authority (contrast
  APR-6003, self-approved by EMP-01 within their own <10,000 limit, which is
  valid, versus JE-9007/APR-6004, which has no approver at all and is a
  control breach).

### 3.8 Execution

- **Actions:** post the journal entry / credit note / refund described by
  the adjustment.
- **Tools:** ERP write (Ledgerline) — outside agent scope in this corpus;
  the agent emits the posting instruction only.
- **Artifacts:** `posted_journal_id` populated on the Adjustment record.
- **Exit criteria:** journal exists in the ledger with the exact debit/credit
  amounts specified.
- **Owner:** human/system-of-record (Ledgerline), triggered by agent.

### 3.9 Verification

- **Actions:** re-run the original detection rule (e.g.
  `bank_reconciliation_rule`, `ar_aging_review`) and confirm the discrepancy
  no longer reproduces; check the `verification_check` text on the
  Adjustment row (e.g. "INV-1001 balance equals 0.00").
- **Artifacts:** `verified_on` date populated on the Investigation record.
- **Exit criteria:** verification check passes; Investigation `status`
  moves to `complete`.
- **Owner:** agent verifies; human (Controller) signs off for critical items.

## 4. State machine

```text
open -> hypotheses_generated -> evidence_gathered -> contradictions_resolved
      -> root_cause_assigned -> recommendation_drafted -> pending_approval
      -> approved -> executed -> verified -> complete

pending_approval -> rejected -> recommendation_drafted   (loop back)
any_state -> escalated                                    (human takes over)
```

`escalated` is reachable from any state when a contradiction cannot be
resolved by the agent, when severity is `critical`, or when an approval is
`absent`/`missing` (e.g. INVG-7004 is `escalated`, not `complete`, precisely
because APR-6004 is absent for JE-9007).

## 5. Agent vs human roles

| Stage | Agent may do autonomously | Human required |
| --- | --- | --- |
| Symptom, Hypotheses, Evidence | Yes | No, unless data is missing/ambiguous |
| Contradictions | Detect, yes. Resolve minor ones, yes. | Resolve anything involving authority breach or missing approval |
| Root cause | Propose code | Controller review for `critical` severity |
| Recommendation | Draft adjustment spec | — |
| Approval | Draft request | Named approver per authority table decides |
| Execution | Emit posting instruction | Ledgerline posts; segregation of duties preserved |
| Verification | Run checks | Controller sign-off for critical/escalated cases |

## 6. JSON schemas

### 6.1 Investigation

```json
{
  "investigation_id": "INVG-7001",
  "discrepancy_id": "DISC-0001",
  "opened_on": "2026-09-01",
  "investigator": "ai_agent+EMP-01",
  "status": "complete",
  "state": "verified",
  "hypotheses": ["Hypothesis"],
  "evidence": ["Evidence"],
  "contradictions": [],
  "root_cause": {
    "code": "RC-DISCOUNT-UNDOCUMENTED",
    "proximate_cause": "string",
    "systemic_cause": "string",
    "control_classification": "design | operating"
  },
  "confidence": 0.92,
  "recommendation": "Recommendation",
  "approval_id": "APR-6001",
  "adjustment_id": "ADJ-5001",
  "verified_on": null
}
```

### 6.2 Claim

```json
{
  "claim_id": "string, e.g. CLAIM-DISC-0001-01",
  "discrepancy_id": "DISC-0001",
  "asserted_by": "hypothesis_id or evidence_id",
  "statement": "AR on INV-1001 exceeds cash received by 500.00",
  "supporting_evidence": ["EVID-..."],
  "contradicting_evidence": [],
  "status": "open | confirmed | refuted"
}
```

### 6.3 Evidence

```json
{
  "evidence_id": "EVID-DISC-0001-01",
  "source_type": "bank_statement | ledger | document | email | policy",
  "source_id": "BT-5004",
  "citation": "data/discrepancies.csv row DISC-0001; CANON.md sec 10",
  "content_summary": "Bank credited 11,900.00 on 2026-08-28, matched to PAY-2001",
  "strength": "primary | secondary | weak",
  "collected_at": "2026-09-01"
}
```

### 6.4 Recommendation

```json
{
  "recommendation_id": "REC-INVG-7001",
  "investigation_id": "INVG-7001",
  "action": "issue_credit_note",
  "adjustment": {
    "debit_account": "4200",
    "credit_account": "1100",
    "amount": 500.00,
    "currency": "USD",
    "period": "2026-08"
  },
  "required_approver_role": "Finance Manager",
  "policy_id": "POL-DISCOUNT-001",
  "confidence": 0.92,
  "rationale": "string with citations"
}
```

## 7. Full worked pass: DISC-0001 / INVG-7001

**Symptom.** `data/discrepancies.csv`: DISC-0001, type
`undocumented_discount_partial_payment`, amount 500.00 USD, period 2026-08,
records INV-1001, PAY-2001, BT-5004, LE-9001, LE-9026, policy
POL-DISCOUNT-001. Flagship trace confirms it (CANON.md §18): INV-1001 total
12,400.00, PAY-2001 11,900.00, BT-5004 11,900.00, AR balance 12,400.00,
difference 500.00.

**Hypotheses (ranked).**
1. Undocumented early-payment discount (prior: high — round number, draft CN exists)
2. Partial payment / short pay (prior: medium)
3. Credit note drafted but not posted (prior: high — CN-3001 exists in status draft)
4. Bank fee absorbed by customer (prior: low — no fee record)
5. Tax miscalculation (prior: low — tax line unaffected, 400.00 matches invoice)
6. Misallocated receipt (prior: low — PAY-2001 references INV-1001 explicitly)

**Evidence.**

| Evidence ID | Source | Finding |
| --- | --- | --- |
| EVID-0001-01 | INV-1001 (CANON §8) | Total 12,400.00, no discount recorded on invoice |
| EVID-0001-02 | PAY-2001 (CANON §9) | 11,900.00, reference `ACME INC INV1001 PMT` |
| EVID-0001-03 | BT-5004 (CANON §10) | Bank credit 11,900.00 on 2026-08-28, matches PAY-2001 |
| EVID-0001-04 | CN-3001 (CANON §11) | 500.00 credit note, status **draft — never issued** |
| EVID-0001-05 | APR-6001 (data/approvals.csv) | status `missing — never requested` |

**Contradictions.** None between records; the contradiction is
policy-vs-process: a discount was effectively granted (CN-3001 drafted) but
never approved (APR-6001 missing) and never posted. This is flagged, not
averaged away — the discount is real economically but is currently
**unauthorized**, so hypothesis 3 is confirmed and hypothesis 1 is the
underlying cause of hypothesis 3.

**Root cause.** RC-DISCOUNT-UNDOCUMENTED. Proximate cause: CN-3001 was
drafted 2026-08-27 but never issued/posted. Systemic cause: Sales Manager
EMP-06 granted a verbal 500 discount without initiating the POL-DISCOUNT-001
approval workflow (control design gap — no system block preventing verbal
discount promises before approval capture).

**Confidence.** 0.92 (matches `data/investigations.csv` INVG-7001). See
`confidence_scoring.md` §4 for the worked formula.

**Recommendation.** Issue and post CN-3001 for 500.00 USD (Dr 4200 Sales
Discounts / Cr 1100 AR), matching ADJ-5001 in `data/adjustments.csv`.
Required approver: Finance Manager EMP-02 (band 500–5,000, CANON §17).

**Approval.** APR-6001 must be requested from EMP-02 and move from `missing`
to `approved` before execution. Until then, ADJ-5001 stays
`awaiting_approval`.

**Execution.** Post CN-3001; journal reduces AR by 500.00, matching cash
received.

**Verification.** INV-1001 balance = 12,400.00 − 11,900.00 − 500.00 = 0.00.
Bank reconciliation for BANK-USD-01 ties out. `verified_on` populated,
Investigation status → `complete` (already `complete` in canon once
verification finished; `verified_on` is blank in the source data pending
that final tie-out step, so an agent resuming this file should populate it
once ADJ-5001 posts).
