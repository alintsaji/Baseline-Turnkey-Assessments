# Report template — v0 Phase 1 (Monitoring Assessment) completion report

Skeleton for `report.md` and the client-facing `report.docx`, matched
section-for-section to the actual G&W Electric Phase 1 report
(`GW_Electric_Phase1_Assessment_Report.docx`). Unlike Phase 0 (where most of
§1–2.3 is reusable boilerplate about the Baseline Content Pack), almost
nothing here is generic — this report is a record of what the monitoring data
actually showed and what the analyst did about it. Every section is
customer-specific and needs fresh input each run.

---

# {Customer} — Cyberhaven Turnkey Implementation — Phase 1: Monitoring Assessment Report

**Report Date:** {Month D, YYYY}

## 1. Executive Summary

This report summarizes the Phase 1 monitoring assessment — validating that
the framework is functioning correctly, documenting tuning actions taken, and
identifying items that require {customer} input to continue optimization.

Key Results:
- All {N_use_cases} priority use cases are validated with live telemetry —
  {list the channels/use cases in one clause}
- {N_datasets_active} of {N_datasets_total} datasets are actively capturing
  matches
- {N_policies_active} of {N_policies_total} Monitor policies are actively
  firing
- {N_tuning_actions} tuning actions were applied to improve classification
  accuracy
- {N_lists_changed} lists were populated or updated to enable correct
  authorized vs. unauthorized splitting

Bottom line: {one-paragraph verdict — is the monitoring framework working as
designed, is authorized/unauthorized classification operational, is it ready
for Phase 2, and what's still pending}.

## 2. Use Case Validation

All {N_use_cases} of {customer}'s priority use cases have been validated with
live data:

| # | Use Case | Status | What We Observed |
|---|---|---|---|
| {n} | {use case} | Validated / Partial / Not Yet Validated | {what the telemetry actually showed — specific policy IDs, specific findings, any decision needed} |

## 3. Tuning Actions Applied

During the monitoring period, {N_tuning_actions} tuning actions were applied
to improve classification accuracy.

### 3.1 Exclusion Condition Fixes

Cases where a policy/dataset's exclusion logic didn't match real-world
telemetry (e.g. a `none of` exact-match condition missing subdomains — use
`does not contain` instead).

| Policy/Dataset | Issue | Fix Applied |
|---|---|---|
| {id} ({name}) | {what was misclassified and why} | {the specific config change made} |

### 3.2 Policy Replacement

Cases where the fix required creating a parallel test policy/dataset pair to
validate before replacing the original (e.g. when a dashboard shows
unexpected matches despite correct-looking configuration).

| Policy/Dataset | Issue | Resolution |
|---|---|---|
| {id} ({name}) | {symptom} | {what was created/replaced and the validation outcome} |

*(Omit this subsection if no policy replacements were needed this phase.)*

### 3.3 Lists Populated

New or updated list values discovered from live telemetry review (distinct
from Phase 0's initial population — these are the ones telemetry surfaced as
missing).

| List | Values Added | Impact |
|---|---|---|
| {list name} | {values} | {which dataset/policy activated, and the noise/accuracy improvement} |

## 4. Action Items for {Customer}

These items require {customer} input or decisions to continue optimization.
They are ordered by priority.

### Decisions Required

Binary/policy calls only {customer} can make (approve a tool, exclude a
category, etc.).

| # | Item | What We Need | Why It Matters |
|---|---|---|---|

### Information Required

Factual gaps that need {customer}'s knowledge of their own environment
(UNC paths, domain lists, etc.) — often carried forward from the Phase 0
report's §5.2.

| # | Item | What We Need | Why It Matters |
|---|---|---|---|

### Ongoing Maintenance

Standing items that don't need a one-time decision, just continued upkeep as
the environment changes.

| # | Item | Detail |
|---|---|---|

## 5. Dataset & Policy Summary

### 5.1 Datasets ({N_active} Active / {N_zero} Zero Matches)

Of {N_datasets_total} deployed datasets, {N_active} are actively capturing
matches. The {N_zero} datasets with zero matches are:

| Dataset | Reason | Action Needed? |
|---|---|---|
| {id} ({name}) | {why no matches — not a use case, list not populated yet, no activity observed} | Yes/No/Monitor |

### 5.2 Policies ({N_active} Active / {N_zero} Zero Matches)

Of {N_policies_total} deployed Monitor policies, {N_active} are actively
firing. The {N_zero} zero-match policies are accounted for:

| Category | Policies | Reason |
|---|---|---|
| {channel category} | {policy ids} | {why zero matches — missing list, no activity, out of scope} |

## 6. Next Steps & Timeline

| Step | Action | Owner | Target |
|---|---|---|---|
| {n} | {action} | {customer} + Cyberhaven / Cyberhaven only | {target date/window} |
