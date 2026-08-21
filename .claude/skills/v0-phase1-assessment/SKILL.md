---
name: v0-phase1-assessment
description: Generate a Phase 1 (Monitoring Assessment) completion report for a v0 turnkey customer engagement. Validates each priority use case against live telemetry, documents tuning actions taken (exclusion-condition fixes, policy replacements, list additions), summarizes active vs. zero-match datasets/policies, and produces a prioritized action-item list (Decisions Required / Information Required / Ongoing Maintenance) for the customer — matching the real G&W Electric Phase 1 report structure exactly. Works either against a read-only-scoped tenant API connection, or fully from analyst-reported manual input when no API access is configured. Use when the user asks to generate a Phase 1 report, monitoring assessment report, telemetry validation report, or tuning-actions report for a customer.
---

# v0 Phase 1 Assessment

## When to invoke

- "Generate the Phase 1 report for {customer}"
- "Write up the monitoring assessment report"
- "What tuning actions have we made for {customer}"
- "Are we ready to move {customer} into Phase 2 (warn enablement)"

This is the generic, reusable version of the report produced for G&W Electric's
Phase 1 (Monitoring Assessment). Use it for any turnkey customer whose devices
have been onboarded long enough to produce a meaningful telemetry window.

If the user asks generically for "the assessment" or "the completion report"
without saying which phase, use `v0-turnkey-assessment` instead — it asks
which phase and routes here.

## What this skill does

Read-only against the tenant when API access exists; runs entirely from
analyst-reported input when it doesn't (no tool calls needed) — same two-mode
approach as `v0-phase0-assessment`. Builds on the Phase 0 report and saved
intake profile for this customer. The report itself is almost entirely
customer-specific — unlike Phase 0, there is no reusable boilerplate section
here; every section is a record of what this specific monitoring window
showed. Produces:

```
reports/{customer-or-instance}_{YYYY-MM-DD}_phase1-assessment/
├── report.md
└── report.docx
```

## Inputs

- Cyberhaven instance, if configured for this customer (optional — see Step 0)
  + analyst role (same as `v0-phase0-assessment`)
- The prior Phase 0 report and/or project-memory intake profile for this
  customer — needed for the priority-use-case list and the carried-forward
  §5.2 open items. If neither exists, tell the user to run
  `v0-phase0-assessment` first, or continue without a baseline and note that
  in the report.
- Analyst-reported telemetry/tuning observations: per-use-case validation
  status, what got fixed and why, active-vs-zero-match dataset/policy counts.
  **There is no API anywhere in this repo for incident/event counts or
  dashboard match volumes** — this data is always analyst-reported, in both
  modes. Ask for it directly; never invent numbers.

## Workflow

### Step 0 — Mode check, role, and banner

Same pattern as `v0-phase0-assessment` Step 0: check whether this customer's
instance is registered and has usable credentials → API mode; otherwise →
manual mode, a first-class path, not a fallback. Confirm role, and display the
matching banner before proceeding.

### Step 1 — Load the Phase 0 baseline

Pull the prior Phase 0 report (or project memory): the priority use-case list,
the §3.1 list values as they stood at Phase 0, and the §5.2 "Remaining Items"
table. Everything from here on is measured against that baseline.

### Step 2 — Use Case Validation (§2)

For each priority use case from the Phase 0 baseline, ask the analyst: has it
been validated with live telemetry (Validated / Partial / Not Yet), and what
did the data actually show — cite the specific policy IDs involved and any
decision now surfaced by real traffic (e.g. an unexpected-but-legitimate tool
showing up that needs an authorization call). This is always analyst-reported
— there's no event-count API to derive it from automatically, in either mode.

### Step 3 — Tuning Actions Applied (§3)

Ask the analyst what changed since Phase 0, split into the same three buckets
as the reference report:

- **§3.1 Exclusion condition fixes** — a policy/dataset's exclusion logic
  didn't match real telemetry (classic case: an exact-match `none of`
  condition missing subdomains — fixed with `does not contain`). Ask for the
  policy/dataset ID, the issue, and the exact fix applied.
- **§3.2 Policy replacement** — cases needing a parallel test policy/dataset
  pair to validate a fix before replacing the original. Omit this subsection
  entirely if none occurred this phase.
- **§3.3 Lists populated** — list values added or changed since Phase 0,
  distinct from Phase 0's initial population (these are ones telemetry
  surfaced as missing, not ones from the original intake).

**API mode enhancement:** before asking, diff the current tenant list
contents and M-policy exclusion conditions against the Phase 0 report's
captured `§3.1` snapshot (`manage_lists action="get_items"` /
`manage_policies action="get"`) to surface candidate changes automatically —
this narrows the questions to "confirm what changed and why" rather than
"recall everything from scratch." The *why* (the issue that prompted the fix)
is still analyst knowledge; the API only tells you *what* is different now.

### Step 4 — Action Items for {Customer} (§4)

Start from the Phase 0 report's §5.2 ("Remaining Items to Be Resolved in
Phase 1") and ask the analyst to update each: resolved, still open, or
superseded by something Step 2/3 surfaced. Then sort everything still open
into:

- **Decisions Required** — binary/policy calls only the customer can make
  (approve a tool, exclude a category).
- **Information Required** — factual gaps needing the customer's own
  environment knowledge (UNC paths, domain lists).
- **Ongoing Maintenance** — standing items needing continued upkeep, not a
  one-time decision.

### Step 5 — Dataset & Policy Summary (§5)

Ask the analyst for active-vs-zero-match counts on datasets and Monitor
policies (from the console/dashboards — no API for this). For each
zero-match item, ask why: not this customer's use case, a list not yet
populated, or genuinely no activity observed. Flag whether each needs action,
is just something to keep monitoring, or needs no action (e.g. an
intentionally-out-of-scope channel).

**API mode enhancement:** run `v0-coverage-gap-analysis`'s structural check
(`scripts/analyze_coverage.py`, with the same preview-diff-and-approve gate it
already uses) to distinguish a zero-match item caused by a genuine
configuration gap (fixable) from one that's structurally complete but simply
has no matching traffic yet (not fixable, just wait). Don't dump the raw
script output into the report — translate it into the "Reason" column.

### Step 6 — Next Steps & Timeline (§6)

Ask for the immediate next steps: resolving this report's Decisions
Required, populating any remaining lists, and the target date for Phase 2
(Warn enablement) kickoff. Table of Step / Action / Owner / Target, mirroring
the reference report.

### Step 7 — Write the report

Fill [`references/report-template.md`](references/report-template.md) into
`report.md`, section-for-section (1 through 6, matching the real G&W Phase 1
report's numbering and subsection structure exactly — do not reintroduce the
old generic "Validation results table" / "Coverage gap findings" / "Noise
flags" framing from earlier drafts of this skill).

### Step 8 — Generate the client deliverable

Write a short python-docx script rendering `report.md` into `report.docx` in
the same folder, matching the visual style used by `v0-phase0-assessment`'s
output (same title-block layout, heading levels, table styling) so the two
reports read as one continuous engagement record.

### Step 9 — Closing AskUserQuestion

> Phase 1 report complete at `{report_folder}/report.docx`. What's next?
> 1. Review before sending to the customer
> 2. Nothing else yet — check back once Phase 2 (Warn) work starts
> 3. Re-run after more tuning/telemetry data is available

## Outputs

```
reports/{customer-or-instance}_{YYYY-MM-DD}_phase1-assessment/
├── report.md
└── report.docx
```

## Critical files

- [`../v0-coverage-gap-analysis/SKILL.md`](../v0-coverage-gap-analysis/SKILL.md) — reused structural check, API mode only, Step 5 enhancement
- [`../../scripts/export.py`](../../scripts/export.py) — API mode only
- [`../../scripts/analyze_coverage.py`](../../scripts/analyze_coverage.py) — API mode only
- [`../v0-phase0-assessment/`](../v0-phase0-assessment/) — prior-phase report + intake profile this skill builds on
- [`references/report-template.md`](references/report-template.md)

## API mode vs. manual mode

Same guidance as `v0-phase0-assessment`: manual mode is a first-class path,
not a degraded one — it's how the original G&W Phase 1 report was produced.
API mode narrows the questions (diffing list/policy state to surface likely
changes, running the structural coverage check to classify zero-match items)
but never eliminates them — event/incident volume has no API in this repo
regardless of mode, so Steps 2, 3 (the "why"), 4, and 5 (the counts) are
always analyst-reported. The report's structure is identical either way.

## Hand-off

This report's §4 action items and §6 timeline are the inputs for whatever
Phase 2 (Warn enablement) assessment skill is built next, if the team decides
to extend this pattern further.
