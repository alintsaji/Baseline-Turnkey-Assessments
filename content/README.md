# Content snapshot

Version-controlled exports of the v0 datasets, policies, and lists deployed on the `proserv-staging` tenant. The accompanying conceptual documentation lives under [docs/v0-policy-dataset-system/](../docs/v0-policy-dataset-system/).

## Source

- **Tenant:** `proserv-staging` (https://proserv-staging.cyberhaven.io)
- **Exported:** 2026-05-10
- **Exporter:** [`scripts/export.py`](../scripts/export.py) — auth via macOS Keychain `cyberhaven-proserv-staging`

## Layout

```
content/
├── Datasets/
│   └── D/   34 datasets             (all D#### resources)
├── Policies/
│   ├── M/   41 monitor policies
│   ├── W/   15 warn policies         (currently disabled — Phase-1 baseline)
│   └── B/   17 block policies        (currently disabled — Phase-1 baseline)
└── Lists/
    └── L/   35 lists                 (metadata + items combined per file)
```

## File naming

Filenames mirror the resource's full name with ` - ` and remaining whitespace replaced by `_`. Path separators (`/`, `\`) are also replaced with `_` to keep filenames filesystem-safe. Other characters (`&`, `,`, `[`, `]`) are preserved.

Examples:
- `B1010 - Web - AI & GenAI Tools Control` → `B1010_Web_AI_&_GenAI_Tools_Control.json`
- `Websites - Authorized - Internal Sharepoint Domains [is]` → `Websites_Authorized_Internal_Sharepoint_Domains_[is].json`
- `Websites - Unauthorized - Incognito Domain/URL [contains]` → `Websites_Unauthorized_Incognito_Domain_URL_[contains].json`

## File format

JSON, raw API response (unwrapped from the `{resources: [...]}` envelope). Round-trips cleanly through the Cyberhaven `manage_datasets` / `manage_policies` / `manage_lists` MCP actions.

For lists, each file combines `/v2/lists/{id}` metadata with its `/v2/lists/{id}/items` payload under an `items` key.

## What's intentionally excluded

- **Legacy CI sentinels** (`[SD] Super-Inspector`, `ScreenshotInspection`) — type `content_inspection`, not part of the v0 model. These are deliberately skipped per onboarding guidance.
- **Content-inspection policies** themselves (the `ci-*` policies referenced by D000X augmentation) — out of scope for this snapshot.

## Re-exporting

```bash
python3 scripts/export.py
```

The script overwrites all files in place. Disabled W/B policies are discovered by walking each dataset's `policy_ids` and subtracting the enabled set, so you don't need to maintain a hardcoded UUID list. Cross-references (`policy_ids`, `dataset_ids`, `list_references`) are preserved as UUIDs so you can resolve them by reading the matching file in the sibling folder.

## Base coverage matrix

[`base_coverage_matrix.json`](base_coverage_matrix.json) is the design-level intent grid: 55 channels × 24 event-type actions, with each cell set to `"M"` (monitor), `"B"` (block), `"none"` (explicit no-coverage), or `null` (not specified). Imported from a spreadsheet maintained outside this repo.

Use it for:
- **Lookups** — `matrix["Cloud Storage"]["Copy/Pasted"]` → `"M"`
- **Gap analysis** — find cells set to `null` or `"none"` for sensitive channels
- **Cross-reference** — join channel/action against the deployed policies under `Policies/{M,W,B}/` (note: the deployed policies group multiple actions per policy, so this is a many-to-one mapping)

Note: this matrix uses only M and B — the W (Warn) tier from [`02-coverage-matrix.md`](../docs/v0-policy-dataset-system/02-coverage-matrix.md) is not represented here. Treat the JSON as the action-level intent and §2 as the deployed-state-with-warn-tier view.

Re-import from an updated CSV:

```bash
python3 scripts/import_coverage_matrix.py <csv_path>
```
