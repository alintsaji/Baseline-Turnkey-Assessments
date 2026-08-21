# §10 — General Deployment Order of Operations

This is the rollout playbook. Follow these six steps in order; each step depends on the previous being stable.

The phases of v0 maturity are layered into step 3 (M-only → W → B) — that's the most operationally complex step. The other steps are sequential setup/extension work.

## Step 0 (prerequisite) — Wire directory integration

Before importing v0 datasets/policies, confirm directory integration is wired and producing `group_name` enrichment on events. Without this:

- Per-user analysis collapses to per-account.
- The threat-hunting payoff (§8) is unattainable.
- The `M1010` `group_name` placeholder cannot be replaced.

Wire Okta / Entra / Workday / Google Workspace per the customer's existing identity setup. Confirm test events from `NICHOLASDOBDC06` (or equivalent) include `group_name` field.

## Step 1 — Import all datasets + policies

Bulk-import the v0 D-series datasets (34 in proserv-staging baseline) and M-series policies (43 baseline including pre-existing `[SD] Super-Inspector` and `ScreenshotInspection`).

**Verify:**

- `manage_datasets action="list"` count = 34 (or matches the export source).
- `manage_policies action="list"` count = 43 enabled.
- `manage_policies` reverse-lookup via dataset `policy_ids` → 32 disabled W/B policies present.
- `[SD] Super-Inspector` and `ScreenshotInspection` either disabled or excluded if customer doesn't want legacy artifacts.

**Replace placeholders:**

- `M1010` rule contains `"//List of Directory Integration Groups for users with access to above tools"` — replace with real group names per customer.
- Any other `//`-prefixed placeholders in policy queries.

## Step 2 — Confirm OOTB lists are fit to the customer environment

Walk every list. Populate per customer.

### Priority lists to populate first

| List | Why first |
|---|---|
| `Users - Authorized - Internal User Suffixes [ends with]` | Defines who is "internal" for ~18 datasets/policies. Single highest leverage. |
| `Cloud Destination Accounts - Authorized [ends with]` | Drives Internal vs External on cloud channels. |
| `Websites - Authorized - Cloud Storage & Documents Domains [is]` | Sanctioned cloud-storage destinations. |
| `Websites - Authorized - Gen AI Domains - CAU [is]` | GenAI tools requiring corporate auth. |
| `Websites - Authorized - Gen AI Domains - No CAU [is]` | GenAI tools without auth requirement. |
| `Websites - Authorized - Source Code & Developer Tools Domains [is]` | Sanctioned SCM. |
| `Websites - Authorized - Webmail Domains [is]` | Sanctioned webmail. |
| `Websites - Authorized - Internal Sharepoint Domains [is]` | Internal SharePoint. |
| `Websites - Authorized - File Transfer Services Domains [is]` | Sanctioned file transfer. |
| `Websites - Authorized - Document Converter Domains [is]` | Sanctioned doc converters. |
| `Websites - Authorized - HR & Payroll [is]` | HR/Payroll SaaS. |
| `Websites - Authorized - IT and Security Domains [is]` | IT/Security tooling. |
| `Websites - Authorized - Global Domains [is]` / `Global URLs [contains]` | Catch-all corporate sites. |
| `USB - Authorized - Device IDs [is]` | Per-device whitelist. |
| `Printers - Authorized - Printer Names [is]` | Sanctioned printers. |
| `File Paths - Authorized - Internal Network Share [starts with]` / `External Network Share [starts with]` / `Sensitive Internal Network Share [contains]` | Drives D8000-D8011 splits. |

`[CH]`-prefixed lists are Cyberhaven-managed defaults — review only, do not edit.

**Verification per list:** Run `manage_lists action="get_items"`. Confirm each list either is populated with real values (no `//placeholder`) or is "intentionally empty for this customer" (and document the reason).

**Empty-list audit:** the customer cannot proceed to step 3 until all critical lists above are populated. Empty lists collapse the Internal/External bifurcation (see §9 edge case 2).

## Step 3 — Modify policy targeting by sensitivity as higher enforcement tiers are enabled

This is the most operationally complex step. The phase progression below walks you through it.

### Foundational rule

**Policies are mutually exclusive by tier within a channel.** When you enable a W or B for a channel, the channel's M policy cedes the relevant tier(s). Mutual exclusion is what guarantees one event matches at most one tier per channel — the prerequisite for predictable enforcement and clean risk scoring.

### Phase progression

#### Phase 1 — M only (the self-sufficient baseline)

- M covers `[0,1,2,3,4]` (all sensitivity tiers).
- Unauthorized/external low-sev M policies set `create_incident: true` (preferably with `disable_ai_incidents: false` for Linea-decides).
- M + D + lists alone provide rudimentary risk scoring.
- This is the post-step-2 default state.

#### Phase 2a — Add W, no B planned

- W covers `[2,3,4]` (warns on everything moderate-and-up).
- **M cedes `[2,3,4]`** and narrows to `[0,1]`.

When to choose: customer doesn't want hard blocks, or W coverage is expected to be the long-term stable state.

#### Phase 2b — Add W, B planned next

- W covers `[2]` only (moderate).
- **M cedes `[2]`** and narrows to `[0,1,3,4]` until B comes online.

When to choose: B is planned but not yet ready (e.g., business sign-off pending).

#### Phase 3 — B enabled

- B covers `[3,4]` (Web) or `[4]` only (non-Web).
- W stays at `[2]`.
- **M further narrows to `[0,1]`** (was `[0,1,3,4]` after Phase 2b).
- Final state per channel: `M=[0,1]`, `W=[2]`, `B=[3,4]` (or `[4]` for non-Web).

When to enable: false-positive rate from W is acceptable, business sign-off for blocking obtained, sensor versions meet minimum floor.

### Worked example — channel 1010 (Web GenAI)

Starting state (all phases):
- `M1010 - Web - AI & GenAI Tools Activity - Authorized` (M-tier, currently `[0,1,2,3,4]`)
- `M1011 - Web - AI & GenAI Tools Activity - Unauthorized` (M-tier, currently `[0,1,2,3,4]`)
- `W1011 - Web - AI & GenAI Tools Governance` (W-tier, sens `[2]`, **disabled**)
- `B1010 - Web - AI & GenAI Tools Control` (B-tier, sens `[3,4]`, **disabled**)

**Phase 1:** disable both W and B; M's stay at `[0,1,2,3,4]`. Set `M1011.create_incident = true` for Linea-decides.

**Phase 2b:** enable `W1011`. Update `M1010.dataset_sensitivities = [0,1,3,4]` and `M1011.dataset_sensitivities = [0,1,3,4]`. W1011 stays at `[2]`.

**Phase 3:** enable `B1010`. Update `M1010.dataset_sensitivities = [0,1]` and `M1011.dataset_sensitivities = [0,1]`. W1011 stays at `[2]`. B1010 stays at `[3,4]`.

End state: M provides visibility on unrestricted+low; W warns on moderate flows; B blocks on high+critical exfil events.

### Rollback procedure

To roll back from Phase 3 to Phase 2b:

1. Disable `B1010`.
2. Update `M1010.dataset_sensitivities = [0,1,3,4]` and `M1011.dataset_sensitivities = [0,1,3,4]`.

To roll back from Phase 2b to Phase 1:

1. Disable `W1011`.
2. Update `M1010.dataset_sensitivities = [0,1,2,3,4]` and `M1011.dataset_sensitivities = [0,1,2,3,4]`.

## Step 4 — Create additional Policy segments as needed

When a new user population, sub-channel, or risk group warrants distinct treatment beyond what the base templates provide.

**Procedure:**

1. Clone an existing policy. Preserve the M/W/B prefix and channel number, append a descriptor (e.g., `M1010-eng`, `W2010-departing`).
2. Adjust query rules — add `user_conditions` for group scoping, refine `location` or `list_references`, scope to specific event_types.
3. Bind to the appropriate dataset(s) — prefer `selection_type: "sensitivity"` when possible.
4. Set severity per §7 rules of thumb.
5. Validate via test event from `NICHOLASDOBDC06` (or equivalent test endpoint).

**Common cases worth documenting examples for:**

| Case | Pattern |
|---|---|
| Departing-employee Block on Cloud Storage External | Clone `B2000` → `B2000-departing`. Add `user_conditions: group_name in [departing-90d]`. |
| Executive Warn-only carve-out for normally-blocked channel | Clone `B1010` → `W1010-exec`. Change `incident_action: warn`. Add `user_conditions: group_name in [Exec-VPs]`. |
| Engineers with sanctioned ChatGPT Enterprise | Clone `M1010` → `M1010-eng`. Add `user_conditions: group_name in [Engineering]`. Set `M1010` (original) to exclude engineers via `negated`. |
| Per-group GenAI access (engineers vs general) | Two clones with mutually-exclusive `user_conditions` on group_name. |
| Contractor-tightened Email External | Clone `M3000` → `M3000-contractor`. Elevate severity, set `create_incident: true`. Add `user_conditions: group_name in [Contractors]`. |

## Step 5 — Create additional Dataset segments as needed

When CI tags, Document Labels, or metadata targeting need to layer in.

**Procedure mirrors §6:**

1. Choose Pattern A (intrinsic CI in dataset) or Pattern B (permissive dataset + paired specific policy).
2. Apply the mutual-exclusion principle: when adding `D####X` augmented variant, update the base dataset's query to exclude the augmenting factor.
3. Use the locked naming convention: `D####[A-Z] - <base channel/segment name> - <augmenting policy name>`.
4. If introducing a new sensitivity tier (e.g., bumping a moderate-base dataset's augmented variant to high), revisit step 3 phase progression if needed.

## Step 6 — Optional: Create custom CI rules using premade templates

The Cyberhaven CI template library has 52 system-managed `ci-*` policies (Pattern label set) covering regional PII, HIPAA, PCI, GDPR, CCPA, and many more. Use these as starting points.

**Procedure:**

1. Pick a premade CI template that covers the customer's compliance/risk surface.
2. Tune as needed (most templates are usable as-is).
3. **Always create an unrestricted-sensitivity dataset variant first** in the D0000 series, not a policy variant — for three reasons:
   - **(a)** Validate the rule's match population before raising the floor.
   - **(b)** Maintain due-diligence visibility over all possible matches (the production augmented dataset excludes its augmenting factor, so the D0000 visibility variant catches what would otherwise be invisible).
   - **(c)** Catch flows where we can see metadata but can't inspect content (e.g., unmanaged endpoints) — these can use 'dumb' heuristics like `path_basename contains 'confidential'` that wouldn't pass production CI standards.
4. Run the visibility variant for at least 2 weeks to assess match rate and FP rate.
5. Promote the rule into the production sensitivity-bump dataset only after the unrestricted variant shows acceptable precision.

## Verification checklist (end-to-end)

After completing all steps, verify the deployment:

- [ ] Directory integration produces `group_name` on events.
- [ ] All 34 datasets imported, all policies + bound correctly.
- [ ] All `//` placeholders in policy queries replaced with real values.
- [ ] All non-`[CH]` lists either populated or marked "intentionally empty for this customer."
- [ ] M-tier visibility events visible in dashboards.
- [ ] If Phase 1 baseline: unauthorized/external M policies producing Linea-decides incidents on test traffic.
- [ ] If Phase 2a/2b: W policies warn correctly on test traffic to non-sanctioned destinations.
- [ ] If Phase 3: B policies block on test exfil traffic of critical-tier content.
- [ ] User risk scores in IRM reflect segmented signal (not noise from broad policies).
- [ ] Threat-hunting workflows (§8) produce interpretable top-N user lists.
- [ ] Sensor-version compliance > 95% on managed endpoints.
- [ ] §9 edge cases reviewed; mitigations applied per customer environment.
