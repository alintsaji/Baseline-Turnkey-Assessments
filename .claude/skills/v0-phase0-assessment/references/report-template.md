# Report template — v0 Phase 0 (Foundation + Policy Deployment) completion report

Skeleton for `report.md` and the client-facing `report.docx`, matched section-for-
section to the actual G&W Electric Phase 0 report (`G&W_Electric_Phase0_Completion_Report.docx`).
Sections 1–2.3 are structurally the same for every customer — they describe the v0
Baseline Content Pack itself, which doesn't change. Only the counts and the
"relevance" annotations are customer-specific there. Sections 3 onward are fully
customer-specific and need fresh discovery input each time.

**Interview order this skill follows:**
1. Ask for the customer's initial-discovery information first (the intake
   checklist / the Q&A that becomes §5.1).
2. Walk sections 1–2.3 by *confirming numbers* against what's actually deployed
   (dataset/policy/list counts, M/W/B split) — don't re-derive the boilerplate
   explanatory text, just confirm the figures.
3. From §3 onward, ask fresh questions to collect what's needed — none of this is
   reusable boilerplate.

---

# {Customer} — Cyberhaven Turnkey Implementation — Phase 0: Completion Report

**Report Date:** {Month D, YYYY}

## 1. Executive Summary

Phase 0 (Foundation) of the {Customer} Cyberhaven turnkey implementation has been
completed. During this phase, we deployed Cyberhaven's Baseline Content Pack to
{Customer}'s tenant and configured the foundational lists that personalize the
entire policy framework to {Customer}'s environment.

Key outcomes:
- {N_policies} data protection policies deployed across Monitor, Warn, and Block
  tiers
- {N_datasets} datasets deployed covering all major data flow channels
- {N_lists} critical lists populated with {Customer}-specific values
- All Monitor-tier (M) policies are now active and will begin capturing data flows
  once endpoint sensors are deployed
- Warn (W) and Block (B) policies are deployed but disabled, to be enabled in
  later phases after monitoring data is reviewed
- All {N_use_cases} priority use cases have their foundational configuration
  completed

## 2. What Was Deployed

### 2.1 The Baseline Content Pack

*(Boilerplate — reuse verbatim; this doesn't change per customer.)*

The Baseline Content Pack is Cyberhaven's pre-built, best-practice framework for
data protection. It provides comprehensive visibility and control across every
channel where sensitive data can move. The pack is organized in three enforcement
tiers:

| Tier | Purpose | Count | Current State |
|---|---|---|---|
| Monitor (M) | Silent logging of data flows for visibility and tuning | {N_M} policies | Active |
| Warn (W) | User-facing dialog prompting justification before action | {N_W} policies | Deployed, disabled |
| Block (B) | Prevents the action entirely | {N_B} policies | Deployed, disabled |
| Datasets (D) | Classification rules that identify and categorize data | {N_datasets} datasets | Active |
| Lists (L) | Customer-specific allow/deny values that personalize policies | {N_lists_total} lists | {N_lists_populated} populated |

### 2.2 Datasets Deployed ({N_datasets} Total)

Datasets define what Cyberhaven watches. Each dataset captures data flows for a
specific channel or category — *(the category list below is the standard v0
catalog; only the "What They Capture" annotations for this customer's specific
tools/domains change)*:

| Category | Datasets | What They Capture |
|---|---|---|
| Enterprise Visibility | D0000 | All file activity across the organization |
| Web - AI & GenAI | D1010, D1011 | Data flows from authorized vs. unauthorized GenAI tools |
| Web - Cloud Storage | D1020, D1021 | Data flows from authorized vs. unauthorized cloud storage |
| Web - SharePoint | D1031 | Data flows from {customer} internal SharePoint |
| Web - CRM & Sales | D1040, D1041 | Data flows from authorized vs. unauthorized CRM tools |
| Web - HR & Payroll | D1050, D1051 | Data flows from HR/payroll platforms |
| Web - IT & Security | D1060, D1061 | Data flows from IT/security tools |
| Web - Source Code | D1070, D1071 | Data flows from developer tools |
| Web - Webmail | D1080, D1081 | Data flows from authorized vs. unauthorized webmail |
| Web - Other | D1000, D1030 | General web activity and uncategorized web destinations |
| Cloud Accounts | D2000, D2001 | Cloud storage by account: corporate vs. personal |
| Email | D3000 | Email flows — internal vs. external recipients |
| Endpoints | D4000, D4001 | Managed vs. unmanaged endpoint activity |
| Endpoint Apps | D5000 | Application-level data flow tracking |
| Removable Media | D7000 | USB and removable media activity |
| Shared Folders | D8000, D8001, D8010, D8020 | Network share activity — internal, external, and sensitive shares |
| Cloud Apps | D9000 | Cloud application activity |

Add/remove rows only if this customer's deployment doesn't include a channel
(e.g. no Salesforce → drop CRM row, or note it as out of scope), or has a custom
dataset (e.g. a content-inspection dataset for a customer-specific keyword —
mirrors G&W's `D0003 - Confidential Keyword`).

### 2.3 Policies Deployed ({N_policies} Total)

Policies define what action to take when data flows are detected. The
{N_policies} policies cover every data egress channel:

**Monitor Policies ({N_M}) — Currently Active:**

These are silently logging all data movement. Highlights relevant to
{Customer}'s priority use cases:

| Policy ID | Name | {Customer} Relevance |
|---|---|---|
| {policy pairs} | {name} | {which priority use case this maps to, and why} |

**Warn Policies ({N_W}) — Deployed, Disabled:**

Will be enabled in Phase 2 after monitoring data is reviewed with {customer}.
Users will see an on-screen dialog asking them to justify their action before
proceeding.

**Block Policies ({N_B}) — Deployed, Disabled:**

Will be enabled selectively in Phase 2 after Warn data proves policy accuracy.
These will prevent the action entirely.

## 3. Lists Populated in Phase 0

Lists are the customization engine of the v0 framework. By populating a single
list, every dataset and policy that references it automatically adjusts its
behavior. Below are the {N_lists_populated} lists populated during Phase 0.

### 3.1 Lists Configuration Summary

| # | List Name | Values Populated | Datasets Activated | Policies Activated | Status |
|---|---|---|---|---|---|
| 1 | {list name} | {actual values for this customer} | {dataset ids} | {policy ids} | Done |

### 3.2 Coverage Impact

By populating these lists, the following coverage chains are now operational
across the entire framework:

| Coverage Area | What Is Now Active | Key Policies |
|---|---|---|
| {coverage area} | {what became active} | {policy ids} |

## 4. Use Case Readiness Summary

The table below maps {Customer}'s priority use cases to their current state
after Phase 0:

| # | Use Case | Monitor Ready | Phase 0 Status |
|---|---|---|---|
| {n} | {use case} | Yes/No | {status narrative} |

## 5. Information Collected & Open Items

### 5.1 Items Resolved via {Customer} Follow-Up

The following items were answered by {customer} during the discovery follow-up
and are now resolved:

| # | Item | {Customer} Response | Action Taken |
|---|---|---|---|
| {n} | {discovery question} | {their answer} | {what was done with it} |

### 5.2 Remaining Items to Be Resolved in Phase 1

The following items are known gaps that will be addressed through monitoring
data and Phase 1 tuning:

| # | Item | Current Status | Resolution Path | Needed For |
|---|---|---|---|---|
| {n} | {open item} | {status} | {how it'll get resolved} | {policy/dataset ids blocked} |

## 6. Next: Phase 1

Phase 1: Visibility ({date range})
Validation of the monitoring policies and tuning them.

Key dependencies:
- Require more devices to be onboarded and actively used to generate sufficient
  telemetry for tuning
- {any other channel-specific prerequisite, e.g. browser extension deployment
  for web-based monitoring}

| Task | Description | Target |
|---|---|---|
| {n} | {phase 1 task} | {target date range} |
