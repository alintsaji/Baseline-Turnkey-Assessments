---
name: v0-turnkey-assessment
description: Single entry point for turnkey engagement completion-report assessments. Asks which phase to assess — Phase 0 (Foundation + Policy Deployment) or Phase 1 (Monitoring Assessment) — then runs the matching skill (`v0-phase0-assessment` or `v0-phase1-assessment`) in full. Use whenever the user asks generically for "the assessment," "the completion report," or "run the turnkey assessment" for a customer without already naming a phase.
---

# v0 Turnkey Assessment

This is the front door for the turnkey assessment report skills. It doesn't
contain its own report logic — it routes to whichever phase skill applies and
lets that skill's own workflow run unchanged. The two phase skills stay the
single source of truth for their respective report structures
(`v0-phase0-assessment` mirrors the real G&W Phase 0 report;
`v0-phase1-assessment` mirrors the real G&W Phase 1 report) — this skill is
just the disambiguation step in front of them.

## When to invoke

- "Run the turnkey assessment for {customer}"
- "Generate the assessment report for {customer}"
- "Do the completion report" (phase unspecified)
- Any request for "the assessment" / "the phase report" that doesn't already
  say Phase 0 or Phase 1

If the user's request already names the phase explicitly ("run the Phase 0
assessment," "generate the Phase 1 report") — invoke that phase skill
directly instead of routing through here; there's nothing to disambiguate.

## Workflow

### Step 1 — Determine which phase

If the invocation already specifies the phase, skip straight to Step 2 with
that phase selected.

Otherwise, ask via `AskUserQuestion`:

> Which assessment do you want to run?
> 1. **Phase 0 — Foundation + Policy Deployment.** Verifies the v0 pack is
>    deployed, priority lists are populated, and produces the foundational
>    completion report (sections: Executive Summary, What Was Deployed,
>    Lists Populated, Use Case Readiness, Information Collected & Open
>    Items, Next: Phase 1).
> 2. **Phase 1 — Monitoring Assessment.** Validates priority use cases
>    against live telemetry, documents tuning actions taken since Phase 0,
>    and produces the monitoring assessment report (sections: Executive
>    Summary, Use Case Validation, Tuning Actions Applied, Action Items,
>    Dataset & Policy Summary, Next Steps & Timeline).

### Step 2 — Run the matching skill

- **Phase 0 selected** → invoke `v0-phase0-assessment` and follow its
  workflow in full (mode check → discovery info → confirm §1–2.3 figures →
  collect §3–6 specifics → write report → generate `.docx` → closing
  question).
- **Phase 1 selected** → invoke `v0-phase1-assessment` and follow its
  workflow in full (mode check → load Phase 0 baseline → use case validation
  → tuning actions → action items → dataset/policy summary → next steps →
  write report → generate `.docx` → closing question).

Do not re-implement either workflow here — read and execute the selected
skill's `SKILL.md` exactly as if it had been invoked directly. This skill
adds nothing to the report content or structure; it only decides which of
the two to run.

### Step 3 — Everything else is unchanged

Output location, API-mode-vs-manual-mode handling, report structure, and the
closing question all come from whichever phase skill was selected — see that
skill's own documentation. This skill has no outputs of its own.

## Critical files

- [`../v0-phase0-assessment/SKILL.md`](../v0-phase0-assessment/SKILL.md)
- [`../v0-phase1-assessment/SKILL.md`](../v0-phase1-assessment/SKILL.md)

## Why a router instead of a merge

The two phase reports have almost nothing in common structurally — Phase 0 is
built around reusable Baseline Content Pack boilerplate with customer-specific
figures; Phase 1 is a from-scratch tuning/action-item log with no boilerplate
at all. Merging their logic into one file would mean duplicating two
unrelated workflows behind a single set of section numbers, which breaks the
"matches the real report exactly" guarantee both skills were built around.
Keeping them as separate, independently-correct skills — with this thin
router in front — gets the "one thing to invoke" behavior the analyst wants
without that risk. If a Phase 2+ assessment skill gets built later, add it as
a third option here, not as a new umbrella.
