#!/usr/bin/env python3
"""Export all datasets, policies, and lists from a Cyberhaven tenant.

Default behavior (preview mode): pulls into a staging directory under .export-staging/
and prints a diff against the live content/ folder. No files in content/ are touched.

With --apply: writes directly to content/{Datasets,Policies,Lists}/, overwriting in place.

Workflow for human-in-the-loop on proserv-staging (the v0 reference tenant):
    python3 scripts/export.py            # preview: pulls to staging, prints diff
    python3 scripts/export.py --apply    # commit: writes directly to content/

Workflow for auditing a non-v0 tenant (the migration audit skill uses this):
    python3 scripts/export.py --instance acme-prod \
        --target-dir reports/acme-prod_2026-05-10_v0-migration/tenant_export/ \
        --read-only-shape

Excludes content_inspection-typed policies (legacy CI sentinels).
Includes disabled W/B policies discovered via dataset.policy_ids reverse lookup.
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

DEFAULT_INSTANCE = "proserv-staging"
REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
STAGING_DIR = REPO_ROOT / ".export-staging"


def base_url(instance):
    return f"https://{instance}.cyberhaven.io/public"


def get_api_key(instance):
    out = subprocess.run(
        ["security", "find-generic-password", "-s", f"cyberhaven-{instance}", "-a", "api-key", "-w"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(
            f"Could not find API key in keychain for instance '{instance}'. "
            f"Expected service='cyberhaven-{instance}', account='api-key'. "
            f"Stderr: {out.stderr.strip()}"
        )
    return out.stdout.strip()


def get_token(instance, refresh):
    out = subprocess.run(
        ["curl", "-sf", "-X", "POST", f"{base_url(instance)}/v2/auth/token/access",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"refresh_token": refresh})],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)["access_token"]


def api_get(instance, token, path, retries=3):
    """GET with simple retry on transient curl failures (timeouts, transient 5xx)."""
    last_err = None
    for attempt in range(retries):
        out = subprocess.run(
            ["curl", "-sf", "--max-time", "30", "--retry", "2", "--retry-delay", "1",
             f"{base_url(instance)}{path}", "-H", f"Authorization: Bearer {token}"],
            capture_output=True, text=True,
        )
        if out.returncode == 0:
            return json.loads(out.stdout)
        last_err = f"rc={out.returncode} stderr={out.stderr.strip()}"
    raise RuntimeError(f"curl failed for {path} after {retries} attempts: {last_err}")


def slugify(name):
    """Replace ' - ' (space-dash-space), remaining whitespace, and path separators with underscores."""
    s = re.sub(r"\s+-\s+", "_", name)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[/\\]", "_", s)
    return s


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def unwrap(resp):
    """API returns {resources:[{...}], errors, size}. Return resources[0]."""
    if "resources" in resp and resp["resources"]:
        return resp["resources"][0]
    return resp


EXPORT_SUBDIRS = ("Datasets", "Policies", "Lists")


def parse_v0_identity(name):
    """Extract a v0 identity block from a resource name.

    For names like 'D1070A - Web - Source Code - Secrets & Tokens', returns:
        {
          "tier": "D",
          "code": "1070",
          "sub_variant": "A",
          "full_code": "D1070A",
          "name": "D1070A - Web - Source Code - Secrets & Tokens",
          "channel": "Web - Source Code - Secrets & Tokens",
        }

    For non-v0 names (no matching prefix) returns None — callers should fall back to
    using the name as-is when building cross-tenant comparison shapes.
    """
    m = re.match(r"^([DMWB])(\d{4})([A-Z]?)\s*-\s*(.*)$", name or "")
    if not m:
        return None
    tier, code, sub_variant, channel = m.group(1), m.group(2), m.group(3) or "", m.group(4).strip()
    return {
        "tier": tier,
        "code": code,
        "sub_variant": sub_variant,
        "full_code": f"{tier}{code}{sub_variant}",
        "name": name,
        "channel": channel,
    }


def shape_payload(obj, read_only_shape):
    """If --read-only-shape is set, strip tenant-specific UUIDs and metadata so the
    file is portable for cross-tenant comparison. Adds a _v0_identity block (or None
    if the name doesn't match a v0 pattern).

    Stripped fields: id, version, created_at, last_modified, created_by, last_modified_by,
    policy_ids, last_modified_at, updated_at, updated_by. The query/rule body and other
    semantic content are preserved verbatim.

    When read_only_shape is False, returns the object unchanged.
    """
    if not read_only_shape:
        return obj
    shaped = dict(obj)
    for k in ("id", "version", "created_at", "last_modified", "created_by",
              "last_modified_by", "policy_ids", "updated_at", "updated_by"):
        shaped.pop(k, None)
    shaped["_v0_identity"] = parse_v0_identity(obj.get("name", ""))
    return shaped


def compute_diff(staging: Path, content: Path):
    """Return (added, removed, modified) lists of relative paths comparing staging vs content."""
    def relfiles(root):
        if not root.exists():
            return set()
        out = set()
        for sub in EXPORT_SUBDIRS:
            d = root / sub
            if d.exists():
                out.update(p.relative_to(root) for p in d.rglob("*.json"))
        return out

    staging_files = relfiles(staging)
    content_files = relfiles(content)
    added = sorted(staging_files - content_files)
    removed = sorted(content_files - staging_files)
    modified = []
    for rel in sorted(staging_files & content_files):
        try:
            staging_obj = json.loads((staging / rel).read_text())
            content_obj = json.loads((content / rel).read_text())
            if staging_obj != content_obj:
                modified.append(rel)
        except Exception:
            modified.append(rel)
    return added, removed, modified


def print_diff(added, removed, modified):
    print("\n=== diff: staging vs content/ ===", file=sys.stderr)
    print(f"  added (new in tenant):     {len(added)}", file=sys.stderr)
    print(f"  removed (gone from tenant): {len(removed)}", file=sys.stderr)
    print(f"  modified:                  {len(modified)}", file=sys.stderr)
    for label, items in [("added", added), ("removed", removed), ("modified", modified)]:
        if items:
            print(f"\n  [{label}]", file=sys.stderr)
            for rel in items:
                print(f"    {rel}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--instance", default=DEFAULT_INSTANCE,
                        help=f"Cyberhaven tenant instance name (default: {DEFAULT_INSTANCE}). "
                             f"Used both for the API URL and for keychain lookup "
                             f"(service=cyberhaven-{{instance}}, account=api-key).")
    parser.add_argument("--target-dir", default=None, type=Path,
                        help="Override the output directory. Defaults to .export-staging/ for the "
                             "preview workflow on proserv-staging; required for cross-tenant audit pulls.")
    parser.add_argument("--read-only-shape", action="store_true",
                        help="Strip tenant-specific UUIDs/metadata and add a _v0_identity block per "
                             "resource. Use this when pulling a tenant for v0 migration audit so the "
                             "snapshot is portable. NOTE: incompatible with --apply.")
    parser.add_argument("--apply", action="store_true",
                        help="Write directly to content/. Without this flag, writes to the target "
                             "directory for review. proserv-staging only — refused for other instances.")
    parser.add_argument("--delete-removed", action="store_true",
                        help="With --apply, also delete files in content/ that no longer exist in the tenant. "
                             "Interactive: lists each candidate and prompts y/N before deleting.")
    args = parser.parse_args()

    if args.apply and args.read_only_shape:
        parser.error("--apply and --read-only-shape are mutually exclusive: --apply writes to content/ "
                     "which must contain full tenant payloads (not stripped shapes).")
    if args.apply and args.instance != DEFAULT_INSTANCE:
        parser.error(f"--apply writes to the version-controlled content/ catalog and is only safe for "
                     f"the v0 reference tenant ({DEFAULT_INSTANCE}). Got --instance {args.instance!r}. "
                     f"For other tenants, pull with --target-dir to an audit folder instead.")

    instance = args.instance
    target = args.target_dir if args.target_dir else STAGING_DIR

    # Wipe the staging target before re-pulling so partial older runs don't leak through.
    # Never wipe a non-staging target unless the caller explicitly opted in by pointing at
    # a fresh folder; we treat the target as authoritative and merge into it.
    if target == STAGING_DIR and target.exists():
        shutil.rmtree(target)

    mode_label = "APPLY" if args.apply else "PREVIEW"
    shape_label = " (read-only-shape)" if args.read_only_shape else ""
    print(f"{mode_label} mode: instance={instance}, target={target}{shape_label}", file=sys.stderr)

    token = get_token(instance, get_api_key(instance))

    # ---------------- Datasets ----------------
    print("Fetching datasets list...", file=sys.stderr)
    ds_list = api_get(instance, token, "/v2/datasets")
    ds_resources = ds_list.get("resources", ds_list.get("datasets", []))
    print(f"  {len(ds_resources)} datasets", file=sys.stderr)

    all_policy_ids_from_datasets = set()
    written = {"D": 0, "M": 0, "W": 0, "B": 0, "L": 0, "skipped": [],
               "datasets_non_v0": 0, "policies_non_v0": 0}

    for d in ds_resources:
        ds_id = d["id"]
        full = unwrap(api_get(instance, token, f"/v2/datasets/{ds_id}"))
        name = full["name"]
        for pid in full.get("policy_ids", []):
            all_policy_ids_from_datasets.add(pid)
        if not re.match(r"^D\d", name):
            if args.read_only_shape:
                # In audit mode we still want non-v0 datasets so the classifier can see them.
                # Slug them into a parallel directory so the v0 D/ folder stays clean.
                path = target / "Datasets" / "_non_v0" / f"{slugify(name)}.json"
                write_json(path, shape_payload(full, args.read_only_shape))
                written["datasets_non_v0"] += 1
            else:
                written["skipped"].append(("D-not-D-prefix", name))
            continue
        path = target / "Datasets" / "D" / f"{slugify(name)}.json"
        write_json(path, shape_payload(full, args.read_only_shape))
        written["D"] += 1

    # ---------------- Policies (enabled) ----------------
    print("Fetching policies list (enabled only)...", file=sys.stderr)
    pol_list = api_get(instance, token, "/v2/policies")
    pol_resources = pol_list.get("resources", pol_list.get("policies", []))
    print(f"  {len(pol_resources)} enabled policies", file=sys.stderr)

    enabled_ids = {p["id"] for p in pol_resources}

    for p in pol_resources:
        pid = p["id"]
        full = unwrap(api_get(instance, token, f"/v2/policies/{pid}"))
        name = full["name"]
        ptype = full.get("type", "")
        if ptype != "data_protection":
            written["skipped"].append((f"non-data-protection ({ptype})", name))
            continue
        m = re.match(r"^([MWB])\d", name)
        if not m:
            if args.read_only_shape:
                path = target / "Policies" / "_non_v0" / f"{slugify(name)}.json"
                write_json(path, shape_payload(full, args.read_only_shape))
                written["policies_non_v0"] += 1
            else:
                written["skipped"].append(("policy-no-MWB-prefix", name))
            continue
        bucket = m.group(1)
        path = target / "Policies" / bucket / f"{slugify(name)}.json"
        write_json(path, shape_payload(full, args.read_only_shape))
        written[bucket] += 1

    # ---------------- Policies (disabled, via reverse lookup) ----------------
    disabled_ids = all_policy_ids_from_datasets - enabled_ids
    print(f"Fetching {len(disabled_ids)} disabled policies (W/B)...", file=sys.stderr)

    for pid in sorted(disabled_ids):
        try:
            full = unwrap(api_get(instance, token, f"/v2/policies/{pid}"))
        except RuntimeError as e:
            written["skipped"].append(("fetch-error", f"{pid}: {e}"))
            continue
        name = full.get("name", "")
        ptype = full.get("type", "")
        if ptype != "data_protection":
            written["skipped"].append((f"disabled-non-DP ({ptype})", name))
            continue
        m = re.match(r"^([MWB])\d", name)
        if not m:
            if args.read_only_shape:
                path = target / "Policies" / "_non_v0" / f"{slugify(name)}.json"
                write_json(path, shape_payload(full, args.read_only_shape))
                written["policies_non_v0"] += 1
            else:
                written["skipped"].append(("disabled-no-MWB-prefix", name))
            continue
        bucket = m.group(1)
        path = target / "Policies" / bucket / f"{slugify(name)}.json"
        write_json(path, shape_payload(full, args.read_only_shape))
        written[bucket] += 1

    # ---------------- Lists ----------------
    print("Fetching lists...", file=sys.stderr)
    lst_list = api_get(instance, token, "/v2/lists")
    lst_resources = lst_list.get("resources", lst_list.get("lists", []))
    print(f"  {len(lst_resources)} lists", file=sys.stderr)

    for l in lst_resources:
        lid = l["id"]
        meta = unwrap(api_get(instance, token, f"/v2/lists/{lid}"))
        items_resp = api_get(instance, token, f"/v2/lists/{lid}/items")
        items = items_resp.get("resources", [])
        # Combine metadata + items for a self-contained per-list file
        combined = dict(meta)
        combined["items"] = items
        name = meta["name"]
        path = target / "Lists" / "L" / f"{slugify(name)}.json"
        write_json(path, shape_payload(combined, args.read_only_shape))
        written["L"] += 1

    print("\n--- summary ---", file=sys.stderr)
    print(f"D: {written['D']}", file=sys.stderr)
    print(f"M: {written['M']}", file=sys.stderr)
    print(f"W: {written['W']}", file=sys.stderr)
    print(f"B: {written['B']}", file=sys.stderr)
    print(f"L: {written['L']}", file=sys.stderr)
    if args.read_only_shape:
        print(f"non-v0 datasets: {written['datasets_non_v0']}", file=sys.stderr)
        print(f"non-v0 policies: {written['policies_non_v0']}", file=sys.stderr)
    if written["skipped"]:
        print(f"\nskipped ({len(written['skipped'])}):", file=sys.stderr)
        for reason, name in written["skipped"]:
            print(f"  [{reason}] {name}", file=sys.stderr)

    # Diff workflow only applies when target is the default staging dir AND we're not in audit mode.
    # For audit/migration pulls, the target IS the canonical snapshot — no diff against content/.
    if args.read_only_shape or target != STAGING_DIR:
        print(f"\nSnapshot written to {target}", file=sys.stderr)
        return

    added, removed, modified = compute_diff(target, CONTENT_DIR)
    print_diff(added, removed, modified)

    if not (added or removed or modified):
        print(f"\nNo changes — content/ is in sync with the tenant.", file=sys.stderr)
        return

    if not args.apply:
        print(f"\nTo apply these changes to content/: python3 scripts/export.py --apply", file=sys.stderr)
        if removed:
            print(f"  (add --delete-removed to also delete tenant-removed files; interactive confirmation per file)",
                  file=sys.stderr)
        return

    print(f"\nApplying {len(added) + len(modified)} added/modified file(s) to content/...", file=sys.stderr)
    for rel in added + modified:
        src = target / rel
        dst = CONTENT_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print(f"  done.", file=sys.stderr)

    if removed:
        if args.delete_removed:
            prune_stale_files(removed)
        else:
            print(f"\n{len(removed)} file(s) exist in content/ but are gone from the tenant.", file=sys.stderr)
            print(f"  Re-run with --apply --delete-removed to confirm deletion of each.", file=sys.stderr)


def prune_stale_files(removed_paths):
    """Interactively confirm and delete each stale file."""
    print(f"\n{len(removed_paths)} tenant-removed file(s) — confirming each:", file=sys.stderr)
    for rel in removed_paths:
        full = CONTENT_DIR / rel
        try:
            ans = input(f"  Delete {rel}? [y/N]: ").strip().lower()
        except EOFError:
            ans = ""
        if ans == "y":
            full.unlink()
            print(f"    deleted", file=sys.stderr)
        else:
            print(f"    kept", file=sys.stderr)


if __name__ == "__main__":
    main()
