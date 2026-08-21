# Baseline Turnkey Assessments

Claude Code skills for generating turnkey-engagement completion reports on the
v0 standard-content architecture. Extracted from the `v0-standard-content`
repo so they can be used as a standalone skill set.

## Skills

- **`v0-turnkey-assessment`** — entry point. Asks which phase to assess, then
  routes to the matching skill below.
- **`v0-phase0-assessment`** — Foundation + Policy Deployment completion
  report. Structure matches the real G&W Electric Phase 0 report.
- **`v0-phase1-assessment`** — Monitoring Assessment completion report
  (use-case validation, tuning actions applied, action items, dataset/policy
  summary). Structure matches the real G&W Electric Phase 1 report.
- **`v0-coverage-gap-analysis`** — reused by `v0-phase1-assessment` in API
  mode for its structural partition-completeness check.

## Two modes, always available

Every phase skill runs in **manual mode** out of the box — the analyst is
asked directly for every figure, no tooling required. This is how both
reference reports (G&W Phase 0 and Phase 1) were originally produced, so
manual mode is a first-class path, not a fallback.

**API mode** additionally automates dataset/policy/list counts and diffing
against the prior phase's report, but it requires two things this repo does
not and cannot provide:

1. **Cyberhaven analyst MCP tools** (`manage_server`, `manage_datasets`,
   `manage_policies`, `manage_lists`) connected in the Claude Code session.
   These are tenant integrations configured per Claude Code environment, not
   files in this repo.
2. A read-only-scoped API key for the target tenant, retrievable via
   `security find-generic-password -s cyberhaven-{instance} -a api-key -w`
   (macOS Keychain) by `scripts/export.py`.

Without both, the skills automatically fall back to manual mode — this is
expected behavior, not an error.

## Repository layout

```
.claude/skills/
├── v0-turnkey-assessment/       # router — start here
├── v0-phase0-assessment/
├── v0-phase1-assessment/
└── v0-coverage-gap-analysis/    # dependency of v0-phase1-assessment (API mode)
scripts/
├── export.py                    # tenant pull, API mode only
└── analyze_coverage.py          # structural coverage check, API mode only
content/                         # v0 catalog (datasets/policies/lists) —
                                  # source of truth for expected counts in API mode
docs/v0-policy-dataset-system/
├── 10-deployment-ooo.md         # priority-list table + M/W/B phase progression
└── 03-segmentation.md           # referenced by v0-coverage-gap-analysis
```

The relative paths inside each `SKILL.md` (`../../scripts/export.py`,
`../../content/`, etc.) assume this exact layout — `scripts/` and `content/`
must stay siblings of `.claude/` at the repo root for API mode's path
resolution to work.

## Origin

Pulled from `v0-standard-content` (the Cyberhaven v0 turnkey-migration
tooling repo) on 2026-08-21. Report templates were calibrated against the
actual G&W Electric Phase 0 and Phase 1 completion reports to guarantee
structural fidelity — not written generically and hoped to match.
