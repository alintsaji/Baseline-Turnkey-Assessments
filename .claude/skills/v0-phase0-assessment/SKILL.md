---
name: v0-phase0-assessment
description: Generate a Phase 0 (Foundation + Policy Deployment) completion report for a v0 turnkey customer engagement. Verifies the v0 pack is deployed (dataset/policy counts vs. the catalog), audits priority-list population status (populated / placeholder / intentionally empty per docs §10 step 2), captures the customer intake profile, and produces a client-facing Word (.docx) completion report of what's done and what's still needed from the customer before Phase 1 (device onboarding) begins. Works either against a read-only-scoped tenant API connection, or fully from analyst-reported manual input when no API access is configured. Use when the user asks to generate a Phase 0 report, foundation completion report, deployment completion report, or turnkey kickoff report for a customer.
---

# v0 Phase 0 Assessment

## When to invoke

- "Generate the Phase 0 report for {customer}"
- "Write up the foundation/deployment completion report"
- "What's our deployment status for {customer}"
- "Draft the kickoff completion report"

This is the generic, reusable version of the report produced for G&W Electric's
Phase 0 (Foundation + Policy Deployment). Use it for any turnkey customer, not just
G&W.

If the user asks generically for "the assessment" or "the completion report"
without saying which phase, use `v0-turnkey-assessment` instead — it asks
which phase and routes here.

## What this skill does

Read-only against the tenant when API access exists — only `list`/`get`/`get_items`
calls, never `create`/`update`/`delete`. When no API access is configured for this
customer, runs entirely on analyst-reported input instead (no tool calls needed).
Either way it produces:

```
reports/{customer-or-instance}_{YYYY-MM-DD}_phase0-assessment/
├── report.md
└── report.docx
```

`report.docx` is the client-facing deliverable. `report.md` is the working/version-
controllable source it's generated from.

## Inputs

- Cyberhaven instance, if this customer has one configured (from `manage_server`,
  `servers.json`, or explicit name) — optional, see Step 0 mode check below.
- Analyst role (from memory `analyst_role.md`; ask once if missing, same options as
  `v0-migration-audit`)
- Customer intake profile — check project memory first for a `project_{customer}.md`
  file. If one exists, reuse it and only ask about gaps. If none exists, walk the
  categories in [`references/intake-checklist.md`](references/intake-checklist.md)
  with the analyst, then save the answers as a project memory so Phase 1+ can reuse
  them without re-asking.

## Workflow

### Step 0 — Mode check, role, and banner

1. Determine mode:
   - Check whether this customer's instance is registered (`servers.json` /
     `manage_server`) **and** has usable credentials. If both are true → **API
     mode**.
   - If either is missing → **manual mode**. Do not treat this as a blocker or ask
     the analyst to go set up API access first — manual mode is a fully supported,
     first-class path, not a fallback of last resort. This is how the original G&W
     Phase 0 report was produced.
   - If it's ambiguous, ask the analyst directly which mode to use rather than
     guessing.
2. Load or ask for analyst role.
3. Display and confirm via `AskUserQuestion`:

**API mode:**
```
About to assess Phase 0 status for tenant: {instance} ({url})
This is READ-ONLY. No changes will be made to the tenant.
Report will be written to:
  reports/{instance}_{today}_phase0-assessment/
```

**Manual mode:**
```
No API connection configured for {customer} — running Phase 0 assessment from
analyst-reported input. I'll ask for deployment status, list population, and
policy state directly.
Report will be written to:
  reports/{customer}_{today}_phase0-assessment/
```

The report structure matches the actual G&W Electric Phase 0 report exactly
(sections 1–6, see [`references/report-template.md`](references/report-template.md)).
Sections 1–2.3 describe the v0 Baseline Content Pack itself, which is the same
for every customer — only the counts and relevance annotations change. Sections
3–6 are fully customer-specific. The interview follows that split:

### Step 1 — Discovery information first

Before touching the boilerplate sections, collect (or load from project memory
if a `project_{customer}.md` already exists) the customer's initial-discovery
profile — walk [`references/intake-checklist.md`](references/intake-checklist.md)
for anything not already answered. This becomes §5.1 ("Items Resolved via
{Customer} Follow-Up") and feeds the customer-specific annotations in §2.2/2.3
and the list values in §3.1. Save/update the project memory afterward so
`v0-phase1-assessment` can reuse it.

### Step 2 — Confirm §1–2.3 figures (deployment counts, M/W/B split)

This is a confirmation pass, not a discovery pass — the Baseline Content Pack's
structure doesn't change, so don't re-derive the explanatory text in
§2.1/§2.2/§2.3 of the template. Just confirm the numbers:

**API mode:**

```bash
python3 scripts/export.py --instance {instance} \
    --target-dir reports/{instance}_{today}_phase0-assessment/tenant_export/ \
    --read-only-shape
```

Compare deployed dataset/policy counts against the v0 catalog
(`content/Datasets/`, `content/Policies/`) to get exact M/W/B/dataset/list
counts — this fully answers §1 and §2.1's table with zero questions asked. Call
`manage_lists action="get_items"` on every non-`[CH]` list to capture the actual
values in each populated list (not just a populated/placeholder/empty flag),
cross-referenced against the priority-list table in
[`docs/v0-policy-dataset-system/10-deployment-ooo.md`](../../../docs/v0-policy-dataset-system/10-deployment-ooo.md)
(§10 Step 2). This also pre-fills most of §3.1's "Values Populated" column —
carry it forward into Step 3 instead of re-asking for it. Cross-reference each
populated list against the v0 catalog JSON to find which dataset/policy IDs
reference it (`list_id`/`list_references` fields) — this pre-fills §3.1's
"Datasets/Policies Activated" columns too. Confirm M-tier policies are enabled
at `dataset_sensitivities=[0,1,2,3,4]` and W/B exist but `disabled: true`.

**Manual mode:** ask the analyst directly to confirm: total policies deployed
and the M/W/B split, total datasets deployed, total lists populated vs. catalog
total, and whether any channel is out of scope for this customer (e.g. no
Salesforce → drop the CRM dataset row). Take their word for it — don't try to
independently verify without API access.

### Step 3 — Collect §3–6 specifics

None of this is reusable boilerplate. In **API mode**, §3.1's values and
activated-dataset/policy columns already came from Step 2 — don't re-ask for
them. What's left to ask either way is the business/tuning context the API
can't supply:

- **§3.2 (Coverage impact)** — the one-line "what this unlocks" narrative per
  list, tied to the customer's priority use cases (mirrors G&W's Table 4). In
  **manual mode**, also ask for §3.1's raw values themselves, since there's no
  API to pull them from.
- **§4 (Use case readiness)** — for each of the customer's priority use cases
  (from the intake profile): is it Monitor-ready, and what's the Phase 0 status
  narrative (mirrors G&W's Table 5, including any custom content-inspection use
  case like G&W's confidential-keyword dataset).
- **§5.2 (Remaining open items)** — anything not resolved in §5.1: current
  status, resolution path, and which policy/dataset IDs it blocks (mirrors G&W's
  Table 7).
- **§6 (Next: Phase 1)** — target date range, key dependencies (device
  onboarding, browser extension deployment, etc.), and the Phase 1 task list
  with target dates (mirrors G&W's Table 8).

### Step 4 — Write the report

Fill [`references/report-template.md`](references/report-template.md) into
`report.md` using everything gathered in Steps 1–3, section-for-section (1
through 6, matching the real G&W report's numbering exactly — do not
reintroduce the old generic "Still needed" / "Priority use cases roadmap"
framing from earlier drafts of this skill).

### Step 5 — Generate the client deliverable

Write a short python-docx script (python-docx is installed) that renders
`report.md`'s content into `report.docx` in the same folder — same title block,
heading levels, and table layouts as the reference G&W report. Plain
paragraphs/bullets for narrative text, tables for every section that has one in
the template.

This is a client-facing document — keep tone professional, no internal jargon
(UUIDs, script names) unless the analyst's role calls for that level of detail.

### Step 6 — Closing AskUserQuestion

> Phase 0 report complete at `{report_folder}/report.docx`. What's next?
> 1. Review before sending to the customer
> 2. Nothing else yet — check back once devices start onboarding
> 3. Re-run after the customer responds with outstanding items

## Outputs

```
reports/{customer-or-instance}_{YYYY-MM-DD}_phase0-assessment/
├── tenant_export/        # API mode only, if re-pulled
├── report.md
└── report.docx
```

## Critical files

- [`../../scripts/export.py`](../../scripts/export.py) — API mode only
- [`../../content/`](../../content/) — v0 catalog (source of truth for expected
  counts, API mode only)
- [`../../docs/v0-policy-dataset-system/10-deployment-ooo.md`](../../docs/v0-policy-dataset-system/10-deployment-ooo.md) — §10 priority-list table + Phase 1 M baseline (used in both modes)
- [`references/intake-checklist.md`](references/intake-checklist.md)
- [`references/report-template.md`](references/report-template.md)

## API mode vs. manual mode — which to use

Manual mode is not a lesser option — it's the mode that produced the original G&W
report, and it works for any customer regardless of whether Cyberhaven has issued
API credentials yet. Prefer API mode when it's available because the deployment
counts and list-population state come back verified instead of recalled, which
matters if a customer ever questions a number later. But don't block report
generation on getting API access set up — run manual mode now and switch later if
credentials land. A report generated in manual mode and one generated in API mode
use the identical `report.md`/`report.docx` structure; only where Steps 1–3 got
their facts differs, and that's not something a customer reading the report would
ever see.

## Hand-off

`v0-phase1-assessment` picks up this report's §5.2 ("Remaining Items to Be
Resolved in Phase 1") table and the saved project-memory intake profile once
device onboarding begins.
