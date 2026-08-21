---
name: v0-coverage-gap-analysis
description: Run logical coverage-completeness analysis comparing the v0 base coverage matrix intent (content/base_coverage_matrix.json) against deployed datasets (content/Datasets/D/) and policies (content/Policies/{M,W,B}/) on the proserv-staging tenant. Identifies M-tier partition gaps (Auth/Unauth completeness), D-tier dataset gaps (missing partition arms or whole channels), and B-tier action gaps (intent-required event_types not in any deployed B policy). Use when the user asks about coverage gaps, logical coverage, partition completeness, Auth/Unauth verification, "what's missing", "do I have full coverage", channel coverage audit, or any v0 deployment audit phrasing.
---

# v0 Coverage Gap Analysis

## When to invoke

User asks any of:
- "Do I have any logical gaps?"
- "Is my coverage complete?"
- "Audit my v0 deployment"
- "Where is my Auth/Unauth coverage incomplete?"
- "What channels are missing datasets/policies?"
- "Run the coverage analysis"
- Anything about partition completeness or channel coverage at the v0 level.

## What this skill does

Compares the **intent** matrix (`content/base_coverage_matrix.json`, 55 channels × 24 actions, with cells of `M`/`B`/`none`/`null`) against the **deployed** state (datasets and policies under `content/`) and reports three classes of gaps:

1. **M-tier partition gaps** — channels where the union of M policies doesn't cover the full Auth ∪ Unauth space.
2. **D-tier partition gaps** — channels with policies but missing or one-sided datasets, or channels with both Auth and Unauth datasets but the Unauth arm uses `negated=False` (a misconfiguration).
3. **B-tier action gaps** — `(channel, action)` cells with intent=B where no deployed B policy includes the matching `event_type`.

## Inputs (read-only)

- [`content/base_coverage_matrix.json`](../../../content/base_coverage_matrix.json) — intent
- [`content/Datasets/D/*.json`](../../../content/Datasets/D/) — deployed datasets
- [`content/Policies/M/*.json`](../../../content/Policies/M/) — deployed monitor policies
- [`content/Policies/B/*.json`](../../../content/Policies/B/) — deployed block policies
- (W policies are loaded but only for completeness — they don't fill M-tier gaps because W is unauthorized-scoped by design.)

## Out of scope (do not flag)

- **`M0100`, `D0100`** — paired cross-channel hygiene policy + dataset. M0100 is bound exclusively to D0100 to avoid enforcement overlap with the v0 main system.
- **`D0001`, `D0002`** — CI-augmented content-class datasets (Software Keys & Tokens, HIPAA). Selected by sensitivity-typed policies, not channel-partition arms.
- **Empty Auth lists** (lists populated only with `//placeholder`) — intentional onboarding state.
- **Disabled-status of W and B policies** — treat W and B as if enabled.
- **`M1090` having no `D1090`** — by design; incognito-as-source isn't a tracked concern.

## In scope, but special

- **`D0000` (Enterprise Visibility)** is the universal catch-all dataset. Its query is `location is negated=True` against an explicit set of "covered-by-dedicated-dataset" locations; anything not in that exclusion list (e.g. `printer`, `email_body`) is caught by D0000. The script detects this and assigns `complete-via-catchall` to channels that have policies but no dedicated dataset. **Do not flag a `complete-via-catchall` channel as a gap.**

## How to run

Always re-pull the tenant state first so the analysis runs against current configurations.

**Step 1 — preview the re-pull** (writes to `.export-staging/`, prints diff vs `content/`, does NOT touch `content/`):

```bash
python3 scripts/export.py
```

**Step 2 — summarize the diff for the user in chat** and **ask for approval** before overwriting. Surface anything surprising (cascade edits from sensitivity changes, removed resources, etc.).

**Step 3 — apply** (only after user approves):

```bash
python3 scripts/export.py --apply
```

**Step 4 — run the analysis** against the freshly-pulled state:

```bash
python3 scripts/analyze_coverage.py
```

The script (located at [scripts/analyze_coverage.py](../../../scripts/analyze_coverage.py)) prints a markdown-formatted report covering all three phases. After reading, summarize the findings for the user in chat — don't dump the raw script output unless they ask.

**Important:** never run `python3 scripts/export.py --apply` without first running the preview and getting user confirmation. The `content/` JSON files are version-controlled source-of-truth for the deployed state; overwriting silently would hide real edits made in the tenant console.

## Heuristics encoded in the script

**M/D-tier partition role classifier:**
- **channel-umbrella** = location-only filter (covers full channel).
- **inverted-umbrella** = location + a `negated=true` list filter (covers everything except the named subset).
- **authorized-arm** = location + positive list reference (`negated=false`).
- **unauthorized-arm-multirule** = multi-rule OR'd policy with both positive and negative list refs.
- **device-type-arm** = location + `device_type` filter (Endpoints).

**Verdict priority order:**
1. Channel-umbrella exists → ✓ `complete-clean`.
2. Auth + Unauth pair using **same `list_id` with opposite `negated` flags** (M6000/M6010, M7000/M7010 pattern) → ✓ `complete-clean`.
3. Inverted-umbrella + matching sub-channel positives (M5000 + M5010–M5080) → ✓ `complete-clean` (Phase C verifies list-set equality).
4. **Multi-rule OR'd Unauth** complementing Auth on the same list set (M1010/M1011 family) → ✓ `complete-clean`. Confirmed by tenant owner as by-design exhaustive: combines (a) negated list reference, (b) empty/null-account backstop rule, (c) catch-all on `domain ∉ list`.
5. **Three-way Internal/External/Unauthorized partition** (M3000+M3010+M3020 for Email, M8000+M8010+M8020 for Shared Folders) → ✓ `complete-clean`. Relies on the convention that the Internal-list and External-list values are disjoint; if a collision ever occurs in production, additional metadata is expected to distinguish (e.g. external `FS01` vs internal `FS01`).
6. Auth-arm only with no Unauth/umbrella → ✗ `incomplete`.
7. Unauth-arm only with no Auth/umbrella → △ `partial` (auth slice has no visibility).
8. No matching dedicated resource → if D0000 catches the channel via its catch-all rule → ◎ `complete-via-catchall`; otherwise → — `none`.

**B-tier event_type mapping:** see `EVENT_TYPE_MAP` in the script. Notable mappings: `Opened File` → `app_access`; `Exported File` → `save_as` (Office Save-As-with-format-change uses Cyberhaven's `save_as` event); `Sent File` → `send` ∪ `attachment_send` ∪ `sent_email`.

## Report sections

1. **Bottom-line summary** — counts of each verdict.
2. **Per-channel coverage table** — channel × M-verdict × D-verdict.
3. **True M-tier gaps** — channels with `incomplete` or `partial` M-verdict.
4. **True D-tier gaps** — channels with `incomplete`, `partial`, or `none` D-verdict (e.g. Printer with no D6000; CRM with both D1040 and D1041 misconfigured as auth).
5. **Channels needing manual verification** — `complete-verify` channels with rule structure printed inline.
6. **B-tier action gaps** — gap list with deployed event_type set per channel for context.
7. **Phase C diagnostics** — sub-channel/inverted-umbrella consistency check (M5000 ↔ M5010–M5080).

## Common follow-up actions the user may request

- **Fix a misconfigured Auth/Unauth pair** — edit the offending dataset to flip its `negated` flag (e.g. D1041 should be `negated: True` on its domain list, matching the D1051 pattern).
- **Add a missing channel dataset** — only when intentional; many channels rely on D0000 catch-all.
- **Expand a B policy's `event_type` set** — when a B intent action isn't covered.

For any policy/dataset mutation back to the tenant, route via the Cyberhaven analyst MCP tools (`manage_datasets`, `manage_policies`) rather than editing the JSON in `content/` alone — those JSON files are exports, not authoritative state.

## See also

- [docs/v0-policy-dataset-system/03-segmentation.md](../../../docs/v0-policy-dataset-system/03-segmentation.md) — conceptual segmentation reference and the catalog of deployed segmentation patterns.
