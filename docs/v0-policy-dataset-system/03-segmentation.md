# §3 — Segmentation: How and Why

## What "segmentation" means in v0

Segmentation = dividing a channel's data flows into multiple datasets and policies along an additional axis beyond the base channel. v0 currently uses two primary segments out of the box, both **driven by the same underlying lists**:

1. **Authorized vs Unauthorized destination** — the destination is in (or not in) the corresponding Authorized list.
2. **Internal vs External** — corporate-controlled vs not (also list-driven).

When CI / Labels / metadata are layered in (§6 covers this), additional segments emerge along:

3. **Content class** — a CI rule has tagged the content (PII, Source Code, HIPAA, etc.).
4. **Document classification** — a Document Label has been applied at the object level.
5. **Sub-channel metadata** — a specific repo name, sensitive subfolder of an internal share, USB device ID, printer name, etc.

## Why segment

| Reason | Effect |
|---|---|
| Apply different sensitivity tiers to different sub-flows of the same channel | Lets the same M/W/B rules treat sanctioned-internal traffic differently from external exfil |
| Carve out approved corporate workflows from generic external traffic | Reduces false positives, focuses warns/blocks on real risk |
| Route distinct user populations through distinct policy logic | Per-group enforcement (engineers vs general, contractors vs employees) — see §8 |
| Make user risk scores meaningful | Narrower segments produce sharper signal-to-noise on per-user risk → enables real threat hunting (the v0 headline goal) |

## **Lists are the highest-leverage extension surface**

Both the Authorized/Unauthorized and Internal/External segments are list-driven. Updating one list (e.g., `Users - Authorized - Internal User Suffixes [ends with]`) propagates immediately into ~18 datasets and policies that reference it.

**This is the single most impactful action when fitting v0 to a new customer environment.** A customer doesn't need to write a single dataset or policy; they update the lists, and the existing taxonomy adapts. Document this prominently in onboarding.

### What lists customers must populate (proserv-staging baseline observation)

Most lists in proserv-staging today contain only `["//placeholder"]`. The Internal/External bifurcation is collapsed to "all External" by default until these are populated. Priority order for a fresh deployment:

| List | Why it matters first |
|---|---|
| `Users - Authorized - Internal User Suffixes [ends with]` | Defines who is "internal" for email/cloud-account checks across most policies. |
| `Cloud Destination Accounts - Authorized [ends with]` | Defines sanctioned cloud accounts (e.g., `@acme.com.box.com`) — drives Internal vs External on cloud channels. |
| `Websites - Authorized - Cloud Storage & Documents Domains [is]` | Defines sanctioned cloud-storage destinations (Box, Drive, Sharepoint). |
| `Websites - Authorized - Gen AI Domains - CAU [is]` | "Corporate Authenticated Use" — the GenAI tools where corporate auth is required. |
| `Websites - Authorized - Gen AI Domains - No CAU [is]` | GenAI tools without auth requirement. |
| `Websites - Authorized - Source Code & Developer Tools Domains [is]` | Sanctioned SCM (GitHub Enterprise, GitLab, Bitbucket). |
| `Websites - Authorized - Webmail Domains [is]` | Sanctioned webmail (Gmail Workspace, Outlook 365). |
| `Websites - Authorized - Internal Sharepoint Domains [is]` | Internal SharePoint origin domains. |
| `Websites - Authorized - File Transfer Services Domains [is]` | Sanctioned file transfer (WeTransfer Pro, Aspera). |
| `Websites - Authorized - Document Converter Domains [is]` | Sanctioned doc-converter services. |
| `Websites - Authorized - HR & Payroll [is]` | HR/Payroll SaaS apps. |
| `Websites - Authorized - IT and Security Domains [is]` | IT/Security tooling. |
| `Websites - Authorized - Global Domains [is]` / `Global URLs [contains]` | Catch-all corporate-allowed domains (intranet, marketing site, etc.). |
| `USB - Authorized - Device IDs [is]` | Per-device whitelist for removable media. |
| `Printers - Authorized - Printer Names [is]` | Sanctioned printers. |
| `File Paths - Authorized - Internal Network Share [starts with]` / `External Network Share [starts with]` / `Sensitive Internal Network Share [contains]` | Drives the D8000/D8010/D8011/D8020 split. |

`[CH]` lists (Cyberhaven-managed defaults) are already populated and should not be edited:

- `[CH] Endpoint Apps - Bluetooth/FTP/GenAI/Screenshot/Chat/P2P/Browsers/IT Admin [is]` — app-name lists used by M5010-M5080.
- `[CH] Emails - Personal Email Domains [contains]` — personal-email detection.

## Common circumstances that warrant a new segment

When the existing two-axis (channel + Internal/External) isn't enough:

| Circumstance | Approach |
|---|---|
| Customer has a third destination class (e.g., partner Sharepoint distinct from internal) | Add a sub-variant dataset + list. `D1031 - Web - Other - Internal Sharepoint` is an example already in v0 — distinct from the internal-corporate variant. |
| A specific group (engineers with sanctioned ChatGPT Enterprise) needs different treatment than the general user base | Add `user_conditions` to a cloned policy, scoping by `group_name` |
| A specific sub-channel emerges as high-risk (AI coding assistants vs general GenAI chat) | Add a dataset segment along the relevant CI/metadata axis (Pattern A or B in §6) |
| A specific repository or sensitive subfolder demands its own targeting | Add a metadata-augmented variant (`D1070A` style) |
| Regulated data flows need their own enforcement (HIPAA, PCI, GDPR) | Pattern A — intrinsic CI condition in the dataset (D0002 - HIPAA is the template) |

## How to segment — procedure

1. **Define the discriminator.** What axis are you segmenting on?
   - A list (most leverage) — add or curate a list, reference it from datasets.
   - A content tag (`content_tags` field) from a CI rule.
   - A document label (`label_id`).
   - A metadata attribute (subfolder path, repo name, cloud workspace, etc.).
   - A user/group condition (directory integration — see §8).

2. **Create the new dataset(s)** with the appropriate sensitivity tier.
   - For list-based segments: add a list-reference condition to a new sub-variant dataset (e.g., `D1041` for a CRM External variant alongside `D1040` Internal).
   - For CI/Label/metadata-based: see §6 patterns A and B.

3. **Apply mutual exclusion.**
   - The base dataset's query must **exclude** the augmenting factor (the base loses any flow that now belongs to the variant).
   - Do not let two datasets in the same channel match the same event (except for purpose-broad datasets like `D0100`).

4. **Bind policies to the new dataset(s).**
   - Prefer `selection_type: "sensitivity"` — auto-includes future datasets at that tier.
   - Use `selection_type: "dataset"` (explicit binding) only when the dataset is purpose-specific (e.g., M0100 → D0100 only).

5. **If introducing a new sensitivity tier, update existing channel policy targeting** if needed (see §10 step 3 — though typically the M-series stays broad and W/B claims new tiers).

6. **Validate.**
   - Trigger an event matching the new segment from a test endpoint (e.g., `NICHOLASDOBDC06`).
   - Confirm exactly one dataset matches within the channel.
   - Confirm the expected policy(s) generate the expected response (visibility / warn / block).

## Deployed segmentation patterns (mechanical taxonomy)

The conceptual axes above (Authorized/Unauthorized, Internal/External, content/label/metadata) get expressed in the deployed M/W/B/D resources via a small set of mechanical patterns. Knowing these patterns lets you read a policy's rules and immediately classify what kind of partition it's part of, and lets you reason about whether the union of policies on a channel is logically complete.

| Pattern | What it looks like in conditions | Deployed examples | Logical completeness |
|---|---|---|---|
| **Channel-umbrella** | Single rule, only `location` filter (no domain/account/event_type/etc.) | M1000 (33 web categories), M1080, M1090, M9000 | Always complete on its own — covers every event at the location. |
| **Inverted-umbrella + sub-channel positives** | Umbrella policy: `location` + `field list_is …list_id=L… negated=True` (subtracting a sub-set). Sub-channel policies: same `location` + same `list_id` `negated=False`. | **M5000 + M5010–M5080** (`endpoint_apps` with 8 app-name lists negated; M5010–M5080 each positive on one of those lists) | Complete iff the negated list set on the umbrella **equals** the union of positive list_ids across sub-channel policies. The analysis script has a Phase C consistency check for this. |
| **Clean Auth/Unauth pair** | Two policies on same `location`, both single-rule, sharing the **same `list_id`** with **opposite `negated` flags** | M6000/M6010 (printer_name list `019cc152`), M7000/M7010 (USB ID list `019c219c`) | Always complete — the partition is a tautology of the form `(x ∈ L) ∨ (x ∉ L)`. |
| **Multi-rule OR'd Auth/Unauth** | Auth: single rule with positive list refs (`domain` and/or `cloud_app_account`). Unauth: 2–3 OR'd rules covering the complement: domain-in-list with account-exception, plus domain-not-in-list. | M1010/M1011, M1020/M1021, M1070/M1071, M2000/M2010 (and parallel D-tier pairs D1010/D1011 etc.) | Complete in principle, but the heuristic checker can't symbolically prove it — flagged `complete-verify` for manual eyeball. |
| **Three-way direction-partitioned** | One Unauthorized policy that negates two lists in a single condition + two Authorized policies (Internal, External), each positive on one of those lists. | **M3000+M3010+M3020** (Email — list-ends-with on internal-suffix + external-suffix lists) and **M8000+M8010+M8020** (Shared Folders — path-starts-with on internal + external network-share lists) | Complete by convention. See "Three-way disjointness convention" below. |
| **Device-type-arm pair** | Two policies on `location=endpoint`, one with `device_type=managed`, one with `device_type=unmanaged`. | M4000 + M4010 (also D4000 + D4010) | Complete — every endpoint event is exactly one of {managed, unmanaged}. |
| **Augmented variant** | A dataset that takes a base dataset's query and narrows it on a content/label/metadata axis (`A` suffix). Not a partition arm — adds a sensitivity dimension. | D1070A (Source Code → Secrets & Tokens at critical sensitivity) | n/a — see §6 for the Pattern A vs Pattern B layering rules. |
| **Catch-all** | A dataset with `location is negated=True` against an explicit list of "already-covered" locations. Anything not in that list is caught here. Acts as the safety net for channels without dedicated datasets. | **D0000 - Enterprise Visibility** — currently catches `printer` and `email_body` (neither is in D0000's exclusion list). | Always covers any channel not in its exclusion list. |

### Why this taxonomy matters

When auditing whether a channel has full visibility coverage at the M tier:

- A **channel-umbrella** alone is sufficient — done.
- An **inverted-umbrella + sub-channel positives** is sufficient when consistent — verify list-set equality.
- A **clean Auth/Unauth pair** is sufficient.
- **Multi-rule OR'd** patterns require manual proof but are designed to be exhaustive (the OR'd unauth rules collectively cover the complement of the auth condition, including edge cases like empty/null account values).
- **Three-way direction-partitioned** patterns require list disjointness to be airtight.
- A **single Auth-arm with no Unauth counterpart and no umbrella** is an **incomplete partition** — flag it.
- A channel with no dedicated dataset but in the **catch-all**'s reach is fine.

### Three-way disjointness convention

The three-way direction-partitioned pattern (Email's `M3000+M3010+M3020`, Shared Folders' `M8000+M8010+M8020`) is logically complete **iff the Internal-list values and External-list values are disjoint** — i.e. no path/domain/account appears in both. If a collision occurred in production (e.g. an internal file share and an external file share both named `FS01`), both Authorized policies would fire on the same event (overlap, not a gap).

The convention is:

- Treat any name collision as a list-population error to be resolved by the customer-side list owner, OR
- Use additional metadata to disambiguate (a fully-qualified path prefix, a hostname suffix, a directory-integration group tag, etc.).

The Email three-way was previously broken by `M3010` and `M3020` only targeting `location=mail`, leaving `email_body` events on the Authorized side invisible. As of 2026-05-10 both have been updated to target `mail OR email_body`, restoring symmetric coverage with `M3000`.

This catalog lives next to the analysis tooling: see [scripts/analyze_coverage.py](../../scripts/analyze_coverage.py) and [.claude/skills/v0-coverage-gap-analysis/](../../.claude/skills/v0-coverage-gap-analysis/) for the automated check.

## Segmentation worked example: adding a "GenAI - Engineers Only" segment

**Goal:** Allow engineering team members to use ChatGPT Enterprise without warning, but warn everyone else who uses ChatGPT-personal.

**Procedure:**

1. **Discriminator:** A directory-group condition on the engineers' group, plus the existing GenAI Authorized/Unauthorized list logic.
2. **Dataset (no new dataset needed):** existing `D1010 - Web - AI & GenAI Tools - Internal` already covers the Authorized GenAI domains. The discrimination happens in the policy.
3. **Policy clone:** Clone `M1010` and `W1011` into:
   - `M1010-eng - Web - AI & GenAI Tools Activity - Authorized (Engineering)` with `user_conditions: group_name in [Engineering]`.
   - `W1011-non-eng - Web - AI & GenAI Tools Governance (Non-Engineering)` with `user_conditions: group_name not in [Engineering]`.
4. **Mutual exclusion:** Each policy has a user-condition; an event from a user fires exactly one of the two clones, not both.
5. **Validate:** trigger ChatGPT use from an engineer's account (M fires, no warn) and from a non-engineer's account (W fires, warn dialog appears).

This example shows that segmentation can happen at any layer — list, dataset, or policy — depending on the discriminator's nature.
