Yesterday 6:37 PM
Pasted markdown(2).md
File

create a prompt for my frontend.
it should have all reconcilation for the months of the year.
for the current month, it should it should be the active page.
have all discrepancies.
it should be dashboard that the finance admin can make use of
it should also show the financial transcations for that month.
it should have a bar on the same line that shows if theres a discrepancy in a transation.
when i click on one trasation it shows the full details.
it should be vertical and the details horizontal, with the main div haveing an overflow-x-hidden and the parent div of the transaction div have an overflow-x-auto.
on the frontend show the retriev docuemtns from the graph like my ai-incident-response-system that hshows the retrieved docs, discrepancies, the human approval buttons. each transaction clicked on should have this page.
shows alll evidences retutned from the frontend.
based on the recommendation, like if this
Request discount approval.

If approved:
record $500 adjustment.

If not approved:
request remaining $500 from customer.
implement tool calling for the last agent and it should.
color for the project
Deep Navy + Emerald — My strongest recommendation

Feels: Premium + financial + trustworthy + modern

Background: #071A2B

Surface: #0D2638

Primary: #19C37D

Secondary: #4ADE80

Text: #F5F7FA

Muted text: #8FA3B8

Border: #1B3A4D
color across pages. it should use react, next.js.

Where document intelligence fits

Financial data isn't clean.

You may have:

PDF invoices
scanned receipts
CSV bank statements
Excel spreadsheets
emails
contracts
credit notes
purchase orders

So you need an ingestion pipeline.

Something like:

              Documents
                  │
        ┌─────────┴─────────┐
        │                   │
       PDF                 CSV
        │                   │
       OCR             Structured parser
        │                   │
        └─────────┬─────────┘
                  ▼
           Normalization
                  │
                  ▼
          Financial records

For PDFs:

PDF
 ↓
OCR / document parser
 ↓
structured fields
 ↓
validation
 ↓
database

For CSV:

CSV
 ↓
schema validation
 ↓
normalization
 ↓
database

The important thing is that AI should not be responsible for everything.

A CSV parser shouldn't need an LLM.
i'm building it as a project.
so i want to know.
Root cause
The $500 discrepancy appears to result from a customer discount reflected in the invoice but not supported by an approved discount record.
Confidence
0.91

Evidence
INV-1001, page 1
Policy FIN-042
Ledger JE-9021
No matching credit note

Recommendation
Request discount approval.

If approved:
record $500 adjustment.

If not approved:
request remaining $500 from customer.

if it is a discount, then show buttons approval, and reject,
if approved, call tools, to write to create a ledger and then send confirmstion to the user that the discount has benn successfully resgistered.
update the db with the root cause of the dispcrepancy and solution.
then if rejected and escalated to the manager usel slack to send an email to the manager and wait for approval. it should approve the following transactions or reject to create a leger that the customer owes us.
then send cofirmation email to the user to request the remaining money.
       │
┌────┴────────────────────────┐
▼ ▼
[Approved] [Rejected]
│ │
├─ Tool: Ledger Adjustment ├─ Tool: Send Email
│ │ (Payment Request)
└─ Tool: Send Email │
(Confirmation) └─ Tool: Create Task
(AR Follow-up)

now if the user was discounted then it should show approve and reject and folllow that flow up buttons.
then for this it shoud use a different endpoint that does this and triggers the langgraph conditional flow again using the status of the transaction so each transcation sould have status. to perform the flow above and then it should the make use of other endpoints and at the end of it sould update the postgres db.
save a collection in pinecone about the issue and the details of the transaction and then the root cause and the solution.
if it is not discount then it should show the same buttons like approve and reject. then cals too to create a stance in ledger and then send the user an emaik that he owes and if apprved update the db and then add the root cause solution and the update status and if the user finanly pays and the payment and it is sent to the db, then up. then it should mimich the core functionality of the financial close agent appliation.
Where document intelligence fits
Financial data isn't clean.
You may have:

PDF invoices
scanned receipts
CSV bank statements
Excel spreadsheets
emails
contracts
credit notes
purchase orders

So you need an ingestion pipeline.
Something like:

          Documents
              │
    ┌─────────┴─────────┐
    │                   │
   PDF                 CSV
    │                   │
   OCR             Structured parser
    │                   │
    └─────────┬─────────┘
              ▼
       Normalization
              │
              ▼
      Financial records

For PDFs:

PDF
↓
OCR / document parser
↓
structured fields
↓
validation
↓
database

For CSV:

CSV
↓
schema validation
↓
normalization
↓
database

The important thing is that AI should not be responsible for everything.
A CSV parser shouldn't need an LLM.
for the vision use qwen 2-78vl
make sure to make it a prodcution .
the frontend and backend should sync. it should automate.
integrate slcak for escalting to manager, use tool calls or mcp servers. then search for free ledger systems my application can use from.
all the keys you need put them in the env file.
if a close has been closed show the current month.
ike we're in septemer, show september month, the transactions that exists, show if there are discrepancies already. when an admin clisks a transaction show the full transactions.
for toer months like the admin can select months and then view the transactions and then send a post request to signify that the month has been closed.
then it updates the db. so design a db schema that sould accomplish that.
then button to reopen the month. then to be able to print the report for each moneht. the report for each month should be genrated by an agent.
and saved in the db. it should only review month by month..

so the project should be an aid to the finance department. think of missing functinlities and then tell the ai to addd more dcuments and add things in the knowledge base and create transactions for 5 months. and make all documents t o have enough information, from data to customers to accounts to ledgers to knowledge graph and so on and so forth. create realistic companies and transactions their type of software, grades and how they pay and all tha. i want it to be very very very real.
list all external tools i need to create accounts in. i have the pinecone db creadetial already.
or use mcp servers.

Yes — I included those concepts in the master prompt, but not with the same level of explicitness and completeness as the list you just gave me.

Specifically:

PostgreSQL as source of truth → included.
MockAccountingProvider first → included.
Conditional status flows → included, but I would make the exact state transitions even more explicit.
Frontend → FastAPI → authorization → LangGraph → privileged tool → included.
Secrets never exposed to frontend → included.
Pinecone / Neo4j / Slack / Email / LLM / Qwen / Langfuse / Redis / PostgreSQL → all included.
External ledger adapters → included.
Idempotency, audit trail, failure recovery → included.

However, you're right to ask because these are architectural decisions, not minor implementation details. They deserve to be elevated into explicit non-negotiable requirements rather than being scattered throughout the prompt.

I would add this section near the very beginning of the master prompt, immediately after the technology stack, so the coding model sees it before it starts making architectural decisions:

Architecture Non-Negotiables — Add to Master Prompt
ARCHITECTURE NON-NEGOTIABLES

These rules are mandatory.

Do not violate them for convenience.

1. POSTGRESQL IS THE APPLICATION SOURCE OF TRUTH

PostgreSQL is the authoritative source of truth for:

financial transactions
invoices
payments
bank transactions
ledger entries
journal entries
accounts
customers
discrepancies
investigations
recommendations
approvals
adjustments
payment requests
transaction statuses
accounting periods
monthly reports
audit events

Pinecone is NOT the source of truth.

Neo4j is NOT the source of truth.

Redis is NOT the source of truth.

The frontend is NOT the source of truth.

External accounting software is NOT the source of truth for application state.

All important financial state must ultimately be persisted in PostgreSQL.

2. ACCOUNTING PROVIDER ABSTRACTION

Do not tightly couple the application to a single accounting/ledger provider.

Create:

class AccountingProvider(Protocol):
    async def create_journal_entry(...):
        ...

    async def get_journal_entry(...):
        ...

    async def get_account(...):
        ...

    async def get_account_balance(...):
        ...

    async def create_receivable(...):
        ...

    async def record_payment(...):
        ...

    async def verify_transaction(...):
        ...

Implement:

AccountingProvider
│
├── MockAccountingProvider
├── ERPNextAccountingProvider
├── AkauntingAccountingProvider
└── SQLLedgerAccountingProvider

The first working implementation MUST be:

MockAccountingProvider

The entire application must work end-to-end with the mock provider.

The mock provider must behave like a real accounting system:

validate journal entries
maintain account balances
create journal entries
return external IDs
reject invalid operations
support idempotency
return failures when configured
support transaction lookup
support verification

The mock provider must NOT simply return:

{
  "success": true
}

It should maintain an actual mock ledger state.

External accounting providers are adapters.

They are not required for the core application to function.

3. FRONTEND → BACKEND → LANGGRAPH → TOOL ARCHITECTURE

The frontend MUST NOT directly call privileged tools.

Never allow:

Browser
   ↓
Slack API

or:

Browser
   ↓
Ledger API

or:

Browser
   ↓
Pinecone

or:

Browser
   ↓
PostgreSQL

The architecture must be:

React / Next.js
      │
      │ authenticated HTTPS request
      ▼
FastAPI API
      │
      ├── authentication
      ├── authorization
      ├── validation
      ├── state validation
      ├── idempotency validation
      │
      ▼
LangGraph
      │
      ├── investigate
      ├── evaluate
      ├── conditional routing
      └── execute approved action
      │
      ▼
Controlled Backend Tool
      │
      ├── Ledger
      ├── Slack
      ├── Email
      ├── Payment Request
      └── Accounting Provider
      │
      ▼
PostgreSQL

The browser should only communicate with the application's API.

All privileged credentials remain on the backend.

4. HUMAN DECISION MUST CONTROL THE FINANCIAL ACTION

The AI can:

investigate
retrieve evidence
identify discrepancies
generate hypotheses
identify likely root causes
interpret policies
calculate confidence
recommend an action

The AI must NOT independently execute financial modifications.

Required flow:

AI Investigation
      ↓
Root Cause
      ↓
Recommendation
      ↓
Human Approval
      ↓
Backend Authorization
      ↓
Controlled Tool Call
      ↓
Ledger Operation
      ↓
Verification
5. EXPLICIT TRANSACTION STATE MACHINE

Every transaction must have a persisted status.

At minimum:

RECONCILED
DISCREPANCY_DETECTED
INVESTIGATING
AWAITING_HUMAN_APPROVAL
APPROVED
REJECTED
ESCALATED
AWAITING_MANAGER_APPROVAL
ADJUSTMENT_PENDING
ADJUSTED
PAYMENT_REQUESTED
PAYMENT_PENDING
PAYMENT_RECEIVED
RESOLVED
FAILED

Implement valid state transitions.

Do not allow the frontend to arbitrarily set a transaction status.

The backend controls state transitions.

6. APPROVED FLOW

For an approved financial recommendation:

AWAITING_HUMAN_APPROVAL
          ↓
APPROVED
          ↓
ADJUSTMENT_PENDING
          ↓
validate policy
          ↓
validate authorization
          ↓
validate accounting period
          ↓
validate journal entry
          ↓
AccountingProvider.create_journal_entry()
          ↓
ADJUSTED
          ↓
verify_reconciliation()
          ↓
RESOLVED

After successful execution:

update PostgreSQL
save journal entry
save external provider ID
save audit event
update investigation
save root cause
save final solution
re-run reconciliation
verify difference
save resolved investigation to Pinecone
send confirmation email
update frontend state
7. REJECTED FLOW

If the Finance Admin rejects the AI recommendation:

AWAITING_HUMAN_APPROVAL
          ↓
REJECTED
          ↓
ESCALATED
          ↓
AWAITING_MANAGER_APPROVAL

The backend should:

persist rejection
store rejection reason
create manager escalation
send Slack notification
create manager approval request
pause/wait for manager decision

The LangGraph workflow must support this interruption and later resume.

8. MANAGER APPROVAL FLOW

Manager approves:

AWAITING_MANAGER_APPROVAL
          ↓
APPROVED
          ↓
ADJUSTMENT_PENDING
          ↓
create ledger operation
          ↓
verify
          ↓
RESOLVED

Manager rejects:

AWAITING_MANAGER_APPROVAL
          ↓
REJECTED
          ↓
PAYMENT_REQUESTED
          ↓
send customer payment request
          ↓
PAYMENT_PENDING

When the customer eventually pays:

PAYMENT_PENDING
       ↓
payment received
       ↓
payment ingestion
       ↓
PostgreSQL
       ↓
reconciliation
       ↓
difference = $0
       ↓
PAYMENT_RECEIVED
       ↓
RESOLVED

The system must automatically detect the incoming payment when it enters the application's financial data.

9. DISCOUNT EXAMPLE

Example:

Invoice:

$12,400

Payment:

$11,900

Difference:

$500

Invoice contains:

$500 discount

Policy:

FIN-042 requires approval for discounts above the configured threshold.

No approval exists.

AI:

Root Cause:
Customer discount without approved discount record.

Confidence:
0.91

Evidence:
INV-1001
FIN-042
JE-9021
No matching credit note
No matching approval

Recommendation:

Request discount approval.

If approved:
record $500 adjustment.

If rejected:
request remaining $500 from customer.

Frontend shows:

[ Approve Discount ] [ Reject Discount ]
10. APPROVE DISCOUNT

Frontend:

POST /api/v1/transactions/{transaction_id}/decision

Body:

{
  "decision": "approved",
  "reason": "Discount approved after evidence review."
}

FastAPI:

authenticate
authorize
verify transaction state
verify approval permission
verify policy
verify amount
create idempotency key
resume LangGraph

LangGraph:

APPROVED
   ↓
validate_discount
   ↓
create_ledger_adjustment
   ↓
verify_reconciliation
   ↓
save_resolution
   ↓
send_confirmation_email
   ↓
save_pinecone_memory

Accounting tool:

create_ledger_adjustment()

Example:

Debit:
Discount Expense     $500

Credit:
Accounts Receivable  $500

Then verify:

Expected:
$12,400

Payment:
$11,900

Approved discount:
$500

Remaining:
$0

Transaction:

RESOLVED
11. REJECT DISCOUNT

Frontend:

POST /api/v1/transactions/{transaction_id}/decision

Body:

{
  "decision": "rejected",
  "reason": "No sufficient evidence to approve discount."
}

Backend:

REJECTED
↓
ESCALATED
↓
send_slack_manager_escalation()
↓
AWAITING_MANAGER_APPROVAL

Slack should contain:

customer
invoice
amount
discrepancy
root cause
evidence summary
recommendation
investigation URL

Where supported, provide:

[Approve]
[Reject]

buttons.

Slack actions MUST route back to authenticated backend endpoints.

Never execute ledger operations directly from Slack.

12. MANAGER REJECTION

If manager rejects:

The system determines that the customer owes the remaining amount.

Example:

Invoice:
$12,400

Payment:
$11,900

Outstanding:
$500

Call:

create_receivable()

Then:

send_payment_request()

Update:

transaction.status = PAYMENT_REQUESTED
invoice.outstanding_amount = 500

Send customer/user email:

Your account has an outstanding balance of $500 associated with invoice INV-1001.

Please arrange payment of the remaining balance.

Do not mark the transaction resolved until the outstanding amount has actually been reconciled.

13. PAYMENT ARRIVAL

When a new payment enters the system:

Payment ingestion
      ↓
schema validation
      ↓
normalization
      ↓
PostgreSQL
      ↓
matching engine
      ↓
find outstanding invoice
      ↓
reconcile

If:

outstanding = $500
payment = $500

then:

PAYMENT_RECEIVED
↓
reconciliation verified
↓
RESOLVED

Save:

root cause
original recommendation
human decisions
manager decision
payment request
payment received
final solution
final status
14. PINECONE RESOLUTION MEMORY

When an investigation is resolved, save a structured investigation memory to Pinecone.

The record should contain:

case_id
transaction_id
invoice_id
customer_id
period
discrepancy_type
expected_amount
actual_amount
difference
root_cause
root_cause_confidence
evidence_summary
policy
recommendation
human_decision
manager_decision
action_taken
final_solution
resolution_status
resolved_at

Pinecone is used for:

precedent retrieval
similar historical cases
investigation context
pattern discovery

It is NOT authoritative financial state.

15. REQUIRED EXTERNAL SERVICES

The architecture should support the following:

Service	Purpose	Status
PostgreSQL	Application source of truth	REQUIRED
Redis	queue/cache/workflow infrastructure	REQUIRED/RECOMMENDED
Pinecone	resolved-investigation memory	ALREADY AVAILABLE
Neo4j	knowledge graph / Graph RAG	RECOMMENDED
Slack	manager escalation	RECOMMENDED
Email provider	customer/manager notifications	REQUIRED FOR AUTOMATION
LLM provider	investigation/reasoning	REQUIRED
Qwen2-VL-72B	vision/document intelligence	REQUIRED FOR VISION PIPELINE
Langfuse	AI observability	RECOMMENDED
MockAccountingProvider	development accounting backend	REQUIRED
ERPNext/Akaunting/SQL-Ledger adapter	real accounting integration	OPTIONAL
16. SECRET MANAGEMENT

All credentials must be backend environment variables.

Create:

.env.example

Include:

DATABASE_URL=
REDIS_URL=

PINECONE_API_KEY=
PINECONE_INDEX=
PINECONE_NAMESPACE=

NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=

SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
SLACK_CHANNEL_ID=

EMAIL_PROVIDER=
EMAIL_API_KEY=
EMAIL_FROM=

LLM_PROVIDER=
LLM_API_KEY=

VISION_MODEL=

ACCOUNTING_PROVIDER=
ACCOUNTING_BASE_URL=
ACCOUNTING_API_KEY=

JWT_SECRET=

LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=

Never expose these variables through:

NEXT_PUBLIC_*
browser JavaScript
client components
frontend bundles
GitHub
17. IDEMPOTENCY

Every financial mutation must be idempotent.

For example:

If the administrator double-clicks:

Approve Discount

the system must NOT create:

JE-1001
JE-1002

for the same approval.

Create an idempotency key using the relevant:

transaction_id
approval_id
action_type
workflow_version

Store it in PostgreSQL.

Before executing:

Does this action already exist?

YES → return existing result.

NO → execute.
18. FAILURE SEMANTICS

Financial operations and notifications are separate.

Example:

Ledger succeeds.

Email fails.

The transaction MUST remain:

ADJUSTED

not:

FAILED

Record:

ledger_operation = SUCCESS
email_operation = FAILED

Then retry the email independently.

Similarly:

Slack failure must not roll back a successfully persisted financial decision unless the business operation explicitly requires atomic behavior.

19. FRONTEND STATE SYNCHRONIZATION

The frontend does not own financial state.

Use:

PostgreSQL
   ↓
FastAPI
   ↓
React Query
   ↓
React UI

For long-running workflows use:

SSE
WebSockets
polling

After approval/rejection:

invalidate:

transaction query
investigation query
approval query
discrepancy query
close-period query
dashboard query

The UI should automatically update.

No manual page refresh.

20. ACCOUNTING PERIOD SAFETY

Every transaction belongs to a close period.

Every accounting operation must validate:

Is this period OPEN?

If:

CLOSED

do not allow ordinary modifications.

If a closed period needs modification:

require:

REOPEN
+
authorized user
+
reason
+
audit event

Then perform the operation.

The system must never silently modify a closed period.

21. FINAL SYSTEM PRINCIPLE

The complete system should behave like this:

                 ┌───────────────────────┐
                 │      Next.js UI       │
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │       FastAPI         │
                 │ Auth / RBAC / API     │
                 └───────────┬───────────┘
                             │
                 ┌───────────▼───────────┐
                 │      PostgreSQL       │
                 │   Source of Truth     │
                 └───────────┬───────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   LangGraph  │
                      └──────┬───────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
       SQL/Data           RAG/Docs          Knowledge
        Tools             Pinecone           Graph
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                     Evidence + Root Cause
                             │
                             ▼
                       Recommendation
                             │
                             ▼
                      HUMAN APPROVAL
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
              APPROVE                 REJECT
                 │                       │
                 ▼                       ▼
          Ledger Tool               Slack
                 │                       │
                 ▼                       ▼
           Verification          Manager Approval
                 │                       │
                 ▼                 ┌─────┴─────┐
              RESOLVED              ▼           ▼
                                APPROVE       REJECT
                                   │             │
                                   ▼             ▼
                                Ledger       Receivable
                                   │             │
                                   │             ▼
                                   │       Payment Request
                                   │             │
                                   │             ▼
                                   │       Payment Received
                                   │             │
                                   └──────┬──────┘
                                          ▼
                                     Reconcile
                                          ▼
                                      RESOLVED

This architecture is mandatory.

The system should demonstrate controlled automation, not uncontrolled autonomous accounting.

So yes: add this section to the prompt. It makes the architecture much harder for another AI to accidentally simplify into "React dashboard + a few API endpoints."

And I especially want you to keep the distinction between these three:

PostgreSQL = truth
Pinecone = learned precedent/memory
Neo4j = relationships

while:

LangGraph = orchestration/state

and:

Tools = controlled actions

That separation is going to make the Financial Close project much stronger technically.

Today 2:36 PM
what open source models wouldbe best for the project. list one for each agent.

For your AI Financial Reconciliation & Investigation System, I would not use one model for every agent. The workload is mixed: structured reasoning, document understanding, classification, retrieval, embeddings, reranking, and explanation.

Here’s the stack I’d use.

Agent / Component	Open-source model	Why
Reconciliation Agent	Qwen3-8B	Strong structured reasoning; good for interpreting deterministic reconciliation results rather than doing the arithmetic itself
Investigation Agent	Qwen3-14B	More reasoning capacity for connecting discrepancies, transactions, policies, and evidence
Document Intelligence Agent	Qwen2.5-VL-72B-Instruct	Excellent fit for invoices, receipts, scanned documents, tables, and visual document understanding
Policy Agent	Qwen3-8B	Good at extracting/applying rules from policy documents when paired with retrieved policy text
Root Cause Agent	Qwen3-14B	This is where deeper multi-step reasoning is useful: evidence → hypotheses → contradictions → likely cause
Explanation / Reporting Agent	Qwen3-8B	Produces clear investigation summaries and financial explanations without needing the largest model
Verification Agent	Qwen3-8B	Can review structured verification results and determine whether the expected post-action state is satisfied
Entity Resolution	BGE-M3 + deterministic/fuzzy matching	Don't use an LLM as the primary matcher. Embeddings + normalized identifiers + deterministic rules are safer
Embeddings	BAAI/bge-m3	Strong multilingual/general-purpose embedding model; works well for hybrid retrieval
Reranker	BAAI/bge-reranker-v2-m3	Useful after BM25 + vector retrieval to rerank evidence
Prompt/Security Guard	Qwen3Guard-Gen-8B	Appropriate for checking potentially unsafe or adversarial content before it reaches sensitive agent workflows
The important part: don't make the LLM do accounting

I'd structure the agents like this:

                         ┌─────────────────────┐
                         │ Qwen2.5-VL-72B      │
                         │ Document Intelligence│
                         └──────────┬──────────┘
                                    │
                                    ▼
                            Structured Data
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Deterministic SQL   │
                         │ Reconciliation      │
                         └──────────┬──────────┘
                                    │
                         discrepancy detected
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Qwen3-14B           │
                         │ Investigation        │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
               SQL / Graph      Hybrid RAG      Pinecone
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ Qwen3-14B           │
                         │ Root Cause          │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ Qwen3-8B            │
                         │ Policy              │
                         └──────────┬──────────┘
                                    ▼
                         Recommendation
                                    │
                                    ▼
                         HUMAN APPROVAL
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                    Approved               Rejected
                         │                     │
                         ▼                     ▼
                  Accounting Tool          Manager
                         │                  Approval
                         ▼                     │
                    Verify ◄──────────────────┘
                         │
                         ▼
                    Qwen3-8B
                    Explanation
Why Qwen3 for most of the agents?

For this project, Qwen3 is particularly attractive because you don't need to build the architecture around a proprietary API. You can run different sizes according to task complexity.

I'd specifically use:

Qwen3-14B

Investigation
Root-cause analysis
Complex evidence synthesis

Qwen3-8B

Reconciliation interpretation
Policy application
Explanation/reporting
Verification
General orchestration/tool selection

And keep Qwen2.5-VL-72B-Instruct specifically for your document/vision workload, as you originally planned.

One architectural change I'd strongly recommend

Don't actually think of these as seven independent LLMs.

Think of them as specialized LangGraph nodes with different model requirements:

MODELS = {
    "document": "Qwen2.5-VL-72B-Instruct",
    "investigation": "Qwen3-14B",
    "root_cause": "Qwen3-14B",
    "policy": "Qwen3-8B",
    "reconciliation": "Qwen3-8B",
    "explanation": "Qwen3-8B",
    "verification": "Qwen3-8B",
}

Then your graph controls what each model is allowed to do.

For example, the Reconciliation Agent should receive:

Invoice:
12,400

Payment:
11,900

Ledger:
12,400

Difference:
500

and not be responsible for calculating the $500 itself.

Your Python/SQL reconciliation engine calculates it.

The LLM then reasons about:

"Why does this $500 difference exist?"

That separation makes the project much more credible as a financial system.

My final stack for your project

If I were building this with you, I'd go with:

Vision/document: Qwen2.5-VL-72B-Instruct
Complex reasoning: Qwen3-14B
General agent tasks: Qwen3-8B
Embeddings: BGE-M3
Reranking: BGE-reranker-v2-m3
Entity resolution: deterministic matching + BGE-M3, not LLM-first
Accounting calculations/reconciliation: Python + PostgreSQL
Structured relationship reasoning: Neo4j
Unstructured evidence: BM25 + BGE-M3 + reranker
Workflow: LangGraph
Memory: Pinecone
Guardrails: deterministic validation + Qwen3Guard where appropriate

That gives you a genuinely hybrid AI system, rather than a project where seven LLM calls are pretending to be seven agents.

Today 5:02 PM
create an archtectureal readme file for my financial close project. ists for gituhub it should be well documented from a to z. also use mermaid to show diagrgams and loops and write tradeoffs add frontend part too.

I created a full A-to-Z architectural README for the Financial Close project, including:

Complete system architecture
Backend + frontend architecture
Mermaid architecture, workflow, state-machine, sequence, ER, and investigation-loop diagrams
AI agent responsibilities and model assignments
Deterministic reconciliation vs LLM reasoning
Hybrid RAG + BM25 + vector + reranking
Neo4j Knowledge Graph
Investigation Evidence Graph
Qwen2.5-VL document pipeline
Human-in-the-loop approval
Manager escalation via Slack
Payment recovery loop
AccountingProvider abstraction
PostgreSQL source-of-truth design
Pinecone precedent memory
Redis/ARQ/LangGraph workflow architecture
Frontend/React Query synchronization
Idempotency and failure semantics
Accounting-period safety
Security boundaries
Observability
Evaluation and testing
Deployment architecture
.env.example
Repository structure
Detailed architecture tradeoffs
End-to-end worked financial discrepancy example
Design principles and future extensions

Download the complete FINANCIAL_CLOSE_ARCHITECTURE_README.md

I structured it so you can use it directly as the project's GitHub README, while also giving a future contributor enough architectural context to understand why each major component exists. 

FINANCIAL_CLOSE_ARCHITECTURE_README.md
Document