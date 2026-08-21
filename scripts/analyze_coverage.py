#!/usr/bin/env python3
"""Logical coverage-completeness analysis for the v0 base coverage matrix vs deployed
datasets and policies on the proserv-staging tenant.

Reports:
  Phase A1 — M-tier partition completeness per channel (Auth + Unauth coverage of full space)
  Phase A2 — D-tier dataset partition completeness per channel (mirror of A1)
  Phase B  — B-tier event_type coverage per (channel, action) cell with intent=B
  Phase C  — diagnostic side-checks (sub-channel/inverted-umbrella consistency)

Out of scope: 0000s-range hygiene/CI resources (M0100, D0100, D0000-D0002, etc).
W and B policies are treated as if enabled, but they only cover unauthorized flows
by design — they cannot fill an M-tier gap on the authorized side.

Usage:
    python3 scripts/analyze_coverage.py
    python3 scripts/analyze_coverage.py --content-dir reports/.../post_export/

The --content-dir flag points at any v0-shaped folder (must contain Datasets/D/,
Policies/{M,W,B}/, and base_coverage_matrix.json). Used after deploy to verify the
target tenant's exported state produces clean coverage verdicts.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_argparser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                     add_help=True)
_argparser.add_argument("--content-dir", default=None, type=Path,
                        help="Path to a v0-shaped folder (defaults to repo content/). Use post-deploy "
                             "to verify a target tenant export against the same coverage rules.")
_argparser.add_argument("--matrix-from-repo", action="store_true",
                        help="When --content-dir is set, still read base_coverage_matrix.json and "
                             "enforcement_matrix.json from the repo's content/ folder (the intent "
                             "matrix is repo-canonical and rarely lives in tenant exports).")
_args, _ = _argparser.parse_known_args()

if _args.content_dir:
    ROOT = _args.content_dir.resolve()
    if not ROOT.exists():
        print(f"ERROR: --content-dir does not exist: {ROOT}", file=sys.stderr)
        sys.exit(1)
else:
    ROOT = Path(__file__).resolve().parent.parent / "content"

# The intent matrix and enforcement matrix are repo-canonical, not tenant-specific.
# When analyzing a non-repo content dir, fall back to the repo's copies unless they
# also exist alongside the tenant export.
_REPO_CONTENT = Path(__file__).resolve().parent.parent / "content"
_MATRIX_ROOT = _REPO_CONTENT if (_args.matrix_from_repo or not (ROOT / "base_coverage_matrix.json").exists()) else ROOT


# -------- I/O ---------------------------------------------------------------

def load_dir(p):
    return [json.loads(f.read_text()) for f in sorted(p.iterdir()) if f.suffix == ".json"]


matrix_data = json.loads((_MATRIX_ROOT / "base_coverage_matrix.json").read_text())
matrix = matrix_data["matrix"]
intent_channels = matrix_data["channels"]
intent_actions = matrix_data["actions"]

datasets_all = load_dir(ROOT / "Datasets" / "D")
M_all = load_dir(ROOT / "Policies" / "M")
W_all = load_dir(ROOT / "Policies" / "W")
B_all = load_dir(ROOT / "Policies" / "B")


def code(name):
    """Parse code prefix from a name like 'M1010 - ...' or 'D1070A - ...'."""
    m = re.match(r"^([DMWB])(\d{4})([A-Z]?)", name or "")
    return (m.group(1), m.group(2) + (m.group(3) or "")) if m else (None, None)


CATCHALL_DATASET_NAME_PREFIX = "D0000"  # Enterprise Visibility — covers any channel without a dedicated dataset

# Cross-channel hygiene/CI resources to exclude (paired with each other, not part of v0 channel-coverage model)
HYGIENE_EXCLUSIONS = {
    "M0100",   # Passwords in the Wild — paired with D0100
    "D0001",   # CI-augmented: Software Keys and Tokens
    "D0002",   # CI-augmented: HIPAA
    "D0100",   # Common Plaintext Documents — paired with M0100
}


def is_in_scope(name):
    """Out of scope: cross-channel hygiene/CI resources (M0100, D0001/D0002/D0100).
    D0000 (Enterprise Visibility) IS in scope — it acts as the catch-all dataset for
    any channel without a dedicated dataset segment (e.g., Printer, Email Body)."""
    tier, num = code(name)
    if tier is None:
        return False
    code_prefix = f"{tier}{num}"
    return code_prefix not in HYGIENE_EXCLUSIONS


def filter_in_scope(items):
    return [x for x in items if is_in_scope(x.get("name", ""))]


datasets = filter_in_scope(datasets_all)
M = filter_in_scope(M_all)
W = filter_in_scope(W_all)
B = filter_in_scope(B_all)
all_policies = M + W + B


# -------- Channel ↔ deployed location mapping ------------------------------

CHANNEL_TO_LOCATIONS = {
    "AI Apps": ["genai_apps"],
    "Cloud Apps": ["cloud_apps"],
    "Cloud Storage": ["cloud_storage"],
    "Email": ["mail", "email_body"],
    "Email Body": ["email_body"],
    "Endpoint - Managed": ["endpoint"],
    "Endpoint - Unmanaged": ["endpoint"],
    "Endpoint Apps": ["endpoint_apps"],
    "Printers": ["printer"],
    "Removable Media": ["removable_media"],
    "Shared Folders": ["share"],
    "Website - AI & GenAI Tools": ["website.Generative AI"],
    "Website - Analytics & BI": ["website.Analytics and BI"],
    "Website - Banking & Personal Finances": ["website.Banking"],
    "Website - CAD & Engineering": ["website.CAD and Engineering"],
    "Website - Cloud Computing and Tools": ["website.Cloud Computing and Tools"],
    "Website - Cloud Storage and Documents": ["website.Cloud Storage"],
    "Website - Commercial & Industrial Equipment Supplier": ["website.Commercial & Industrial Equipment Supplier"],
    "Website - Consumer Messaging and Video": ["website.Consumer Instant Messaging"],
    "Website - Content Delivery Networks": ["website.Content Delivery Networks"],
    "Website - Corporate Financial": ["website.Corporate Financial"],
    "Website - Corporate Messaging and Conferencing": ["website.Corporate Messaging and Conferencing"],
    "Website - CRM, Sales and Marketing Tools": ["website.Sales and CRM"],
    "Website - Customer Support Tools": ["website.Customer Support Tools"],
    "Website - Document Converters": ["website.File converters"],
    "Website - Document Signing Services": ["website.Document Signing Services"],
    "Website - File Transfer Services": ["website.File Transfer Services"],
    "Website - Governance, Risk and Compliance": ["website.Governance, Risk and Compliance"],
    "Website - Government & Military": ["website.Government and Military"],
    "Website - Graphics and Design": ["website.Graphics, Design and CAD"],
    "Website - Health & Medicine": ["website.Health and Medicine"],
    "Website - Health Record and Clinical Trial Management": ["website.Health Record and Clinical Trial Management"],
    "Website - HR, Payroll, and Expenses": ["website.HR and Payroll"],
    "Website - Incognito": ["website.Incognito"],
    "Website - IT and Security Tools": ["website.IT and Security Tools"],
    "Website - Job Boards and Recruiting": ["website.Job Boards and Recruiting"],
    "Website - Laboratory Management and Research Tools": ["website.Laboratory Management and Research Tools"],
    "Website - Legal and Law": ["website.Legal and Law"],
    "Website - Logistics, Shipping and Printing": ["website.Logistics, Shipping and Printing"],
    "Website - News and Media": ["website.News and Media"],
    "Website - Other": ["website.Other"],
    "Website - Professional Networks": ["website.Professional Networks"],
    "Website - Project Management and Collaboration": ["website.Project Management and Collaboration"],
    "Website - Science and Education": ["website.Research and Development"],
    "Website - Search Engines": ["website.Search Engines"],
    "Website - Shopping": ["website.Shopping"],
    "Website - Social Media": ["website.Social Media"],
    "Website - Software Downloads": ["website.Software Downloads"],
    "Website - Source Code and Developer Tools": ["website.Source Code Management"],
    "Website - Translation and Grammar Tools": ["website.Translation and Grammar Tools"],
    "Website - Travel and Entertainment": ["website.Travel and Entertainment"],
    "Website - Vendor Management": ["website.Vendor Management"],
    "Website - VPN and Proxies": ["website.VPN and Proxies"],
    "Website - Web Mail and Calendar": ["website.Web Mail"],
}

# Action → expected event_type values in Cyberhaven policies
# Action → canonical Cyberhaven event_type.
# Source-of-truth: content/enforcement_matrix.json (loaded below). The hardcoded fallback here
# mirrors the matrix at import time; re-sync via scripts/import_enforcement_matrix.py if the
# enforcement matrix changes.
EVENT_TYPE_MAP_FALLBACK = {
    "Attached File": ["attachment_add"],
    "Cloned Repository": ["clone"],
    "Compressed File": ["zip"],
    "Copied File": ["copy"],
    "Copy/Pasted": ["clipboard_copypaste"],
    "Created File": ["create"],
    "Deleted": ["delete"],
    "Downloaded File": ["download"],
    "Edited File": ["edit"],
    "Exported File": ["save_as"],
    "Extracted File": ["unzip"],
    "Fetched File": ["fetch"],
    "Moved File": ["move"],
    "Opened File": ["app_access"],
    "Printed": ["sent_to_printer"],
    "Pushed File": ["pushed"],
    "Received File": ["recieved_email"],  # Note: Cyberhaven event_type itself is misspelled
    "Renamed File": ["rename"],
    "Saved Email Attachment": ["attachment_save"],
    "Sent File": ["sent_email"],
    "Shared File": ["share"],
    "Shared Page": [],  # Not a discrete event_type per the enforcement matrix
    "Uploaded File": ["upload"],
}


def _norm(s):
    """Normalize action name for cross-matrix lookup (handles 'Sent [File]' vs 'Sent File')."""
    return s.lower().replace("[", "").replace("]", "").strip()


def load_event_type_map():
    """Load EVENT_TYPE_MAP from content/enforcement_matrix.json if present; fall back to hardcoded."""
    matrix_path = _MATRIX_ROOT / "enforcement_matrix.json"
    if not matrix_path.exists():
        return EVENT_TYPE_MAP_FALLBACK
    em = json.loads(matrix_path.read_text())
    out = dict(EVENT_TYPE_MAP_FALLBACK)  # start with fallback for any missing rows
    norm_to_canonical = {_norm(k): k for k in EVENT_TYPE_MAP_FALLBACK}
    for a in em.get("actions", []):
        key = norm_to_canonical.get(_norm(a["action"]), a["action"])
        ev = a["event_type"].strip()
        out[key] = [ev] if ev else []
    return out


EVENT_TYPE_MAP = load_event_type_map()


# -------- Helpers: rule structure summary ----------------------------------

def loc_matches_value(loc, value):
    """True if a channel location matches a location-condition value.
    Cyberhaven treats the bare `website` value as the umbrella covering all `website.*`
    sub-categories (Generative AI, Cloud Storage, etc.) — it is NOT a literal leaf value.
    All other location values are leaves (no hierarchical semantics)."""
    if loc == value:
        return True
    if value == "website" and loc.startswith("website."):
        return True
    return False


def rule_conditions_for(resource, loc_patterns):
    """Yield (rule_index, list_of_condition_dicts) for rules whose location condition
    actually fires on the given channel locations.

    Respects the `negated` flag and the `website` hierarchical-prefix semantic:
      - `location is X negated=False` fires iff event.location is matched by any X.
      - `location is X negated=True`  fires iff event.location is matched by NO X.
    """
    for ri, rule in enumerate(resource.get("query", {}).get("rules", [])):
        loc_match = False
        out = []
        for c in rule.get("conditions", []):
            field = c.get("field_name")
            entry = {
                "field": field,
                "operator": c.get("operator"),
                "negated": c.get("negated", False),
                "values": [v.get("value") for v in c.get("values", [])],
                "list_id": next((v.get("list_id") for v in c.get("values", []) if v.get("list_id")), None),
            }
            if field == "location":
                values = [v.get("value") for v in c.get("values", [])]
                if c.get("negated"):
                    # Rule fires when location is NOT matched by any value; matches the channel
                    # iff none of the channel's loc_patterns is matched by any value.
                    if loc_patterns and not any(loc_matches_value(loc, v) for loc in loc_patterns for v in values):
                        loc_match = True
                else:
                    if any(loc_matches_value(loc, v) for loc in loc_patterns for v in values):
                        loc_match = True
            out.append(entry)
        if loc_match:
            yield ri, out


def classify_resource(resource, loc_patterns, kind):
    """Classify a policy or dataset's role for a given channel.
    Returns: (role_label, signals_dict) where signals_dict captures useful context
    (negation list_ids, presence of event_type filter, etc).
    """
    rules = list(rule_conditions_for(resource, loc_patterns))
    if not rules:
        return None, {}

    # Aggregate signals across all matching rules
    has_event_type_filter = False
    has_positive_list = False
    has_negative_list = False
    has_device_type = False
    has_app_name_negated = False
    list_ids_positive = set()
    list_ids_negative = set()
    sub_channel_filters = []  # list of (field, list_id, negated)

    for ri, conds in rules:
        for c in conds:
            if c["field"] == "event_type":
                has_event_type_filter = True
            if c["field"] == "device_type":
                has_device_type = True
            if c["field"] == "app_name" and c["negated"]:
                has_app_name_negated = True
            if c["field"] in {"domain", "cloud_app_account", "email_account", "path",
                              "printer_name", "removable_device_usb_id", "cloud_shared_with",
                              "url", "browser_page_title", "app_name"}:
                if c["list_id"]:
                    if c["negated"]:
                        has_negative_list = True
                        list_ids_negative.add(c["list_id"])
                    else:
                        has_positive_list = True
                        list_ids_positive.add(c["list_id"])
                    sub_channel_filters.append((c["field"], c["list_id"], c["negated"]))

    only_location = not (has_event_type_filter or has_positive_list or has_negative_list
                        or has_device_type or has_app_name_negated)

    if only_location:
        role = "channel-umbrella"
    elif has_app_name_negated and not has_positive_list:
        # M5000 pattern: location + multiple app_name negations
        role = "inverted-umbrella"
    elif has_negative_list and not has_positive_list:
        role = "inverted-umbrella"
    elif has_positive_list and has_negative_list:
        # Multi-rule mix (M1011 pattern)
        role = "unauthorized-arm-multirule"
    elif has_positive_list:
        # device_type=managed/unmanaged is also a "positive" categorization
        role = "authorized-arm" if not has_device_type else "device-type-arm"
    elif has_device_type:
        role = "device-type-arm"
    else:
        role = "other"

    return role, {
        "list_ids_positive": list_ids_positive,
        "list_ids_negative": list_ids_negative,
        "has_event_type_filter": has_event_type_filter,
        "sub_channel_filters": sub_channel_filters,
        "rule_count": len(rules),
    }


def channel_partition_verdict(channel, resources, kind):
    """Determine partition completeness verdict for the given channel.
    `resources` is the list of policies (kind='M') or datasets (kind='D') in scope.
    Returns: (verdict, role_summary, members) where:
      verdict ∈ {complete-clean, complete-verify, incomplete, partial, none}
      role_summary: list of (resource_name, role)
      members: full classification dicts for each in-channel resource
    """
    locs = CHANNEL_TO_LOCATIONS.get(channel, [])
    members = []
    for r in resources:
        role, signals = classify_resource(r, locs, kind)
        if role is None:
            continue
        members.append({"name": r["name"], "role": role, "signals": signals})

    if not members:
        return "none", [], []

    role_summary = [(m["name"], m["role"]) for m in members]
    roles = {m["role"] for m in members}

    # Channel-umbrella present → complete
    if "channel-umbrella" in roles:
        return "complete-clean", role_summary, members

    # Inverted-umbrella alone or with sub-channel positives.
    # If sub-channel positives are present alongside the inverted-umbrella, treat as complete-clean
    # (the M5000 + M5010-M5080 pattern; Phase C verifies list-set consistency).
    if "inverted-umbrella" in roles:
        if any(m["role"] == "authorized-arm" for m in members):
            return "complete-clean", role_summary, members
        return "complete-verify", role_summary, members

    # Direction-partitioned: Email or Shared Folders three-way (Internal + External + Unauthorized).
    # Confirmed by user as by-design exhaustive when the unauthorized policy negates BOTH the
    # internal and external lists in a single condition. Disjointness convention noted in §3 docs.
    has_internal = any("Internal" in m["name"] for m in members)
    has_external = any("External" in m["name"] for m in members)
    has_unauth_string = any("Unauthorized" in m["name"] for m in members)
    if has_internal and has_external and has_unauth_string:
        return "complete-clean", role_summary, members

    # Auth/Unauth pair: complete iff same list_id appears positively in Auth and negatively in Unauth.
    # Multi-rule OR'd Unauth policies (M1011 family) are confirmed by user to be exhaustive: they
    # combine (a) negated list reference, (b) empty/null backstop, (c) catch-all on domain∉list.
    auth_members = [m for m in members if m["role"] == "authorized-arm"]
    unauth_members = [m for m in members if m["role"] in {"inverted-umbrella", "unauthorized-arm-multirule"}]
    if auth_members and unauth_members:
        auth_pos_ids = set().union(*(m["signals"]["list_ids_positive"] for m in auth_members))
        unauth_neg_ids = set().union(*(m["signals"]["list_ids_negative"] for m in unauth_members))
        if auth_pos_ids & unauth_neg_ids:
            # Same list_id, opposite negation — clean partition.
            return "complete-clean", role_summary, members
        # Different lists — Auth list isn't the one being negated by Unauth → real gap.
        return "incomplete", role_summary, members

    # device-type-arm pairs (Managed + Unmanaged): complete coverage of endpoints
    dt_members = [m for m in members if m["role"] == "device-type-arm"]
    if len(dt_members) >= 2:
        return "complete-clean", role_summary, members
    if len(dt_members) == 1:
        return "partial", role_summary, members  # only one device_type covered

    # Only Auth-arm exists, no Unauth → incomplete
    if auth_members and not unauth_members:
        return "incomplete", role_summary, members

    # Only Unauth-arm exists, no Auth → partial (auth slice missing visibility)
    if unauth_members and not auth_members:
        return "partial", role_summary, members

    return "complete-verify", role_summary, members


# -------- Phase B helpers --------------------------------------------------

def b_event_types_for_channel(channel):
    """Return (event_types_set, has_umbrella_b) for B policies targeting this channel."""
    locs = CHANNEL_TO_LOCATIONS.get(channel, [])
    events = set()
    has_umbrella = False
    b_policies_hit = []
    for p in B:
        for ri, conds in rule_conditions_for(p, locs):
            ev_in_rule = set()
            event_filter_in_rule = False
            for c in conds:
                if c["field"] == "event_type":
                    event_filter_in_rule = True
                    ev_in_rule |= set(c["values"])
            if not event_filter_in_rule:
                has_umbrella = True
            else:
                events |= ev_in_rule
            if p["name"] not in b_policies_hit:
                b_policies_hit.append(p["name"])
    return events, has_umbrella, b_policies_hit


# -------- Main analysis ----------------------------------------------------

VERDICT_SYMBOL = {
    "complete-clean": "✓",
    "complete-verify": "≈",
    "partial": "△",
    "incomplete": "✗",
    "none": "—",
}

print(f"# v0 Coverage Gap Analysis — proserv-staging\n")
print(f"## Input scale\n")
print(f"- Intent matrix: {len(intent_channels)} channels × {len(intent_actions)} actions\n"
      f"- In-scope policies: M={len(M)}, W={len(W)}, B={len(B)}\n"
      f"- In-scope datasets: D={len(datasets)}\n"
      f"- Out-of-scope (0000s): "
      f"{[p['name'] for p in M_all if not is_in_scope(p['name'])] + [d['name'] for d in datasets_all if not is_in_scope(d['name'])]}\n")

# Channels with intent (M or B in any cell)
channels_with_intent = []
for ch in intent_channels:
    if ch == "Global":
        continue
    cells = matrix.get(ch, {})
    if any(v in ("M", "B") for v in cells.values()):
        channels_with_intent.append(ch)

# Phase A1 + A2 — per-channel verdicts
print("## Phase A1+A2 — per-channel partition verdicts (M-tier and D-tier)\n")
print(f"| Channel | M policies | M verdict | D datasets | D verdict |")
print(f"|---|---|---|---|---|")

per_channel_results = {}
for ch in channels_with_intent:
    m_verdict, m_roles, m_members = channel_partition_verdict(ch, M, "M")
    d_verdict, d_roles, d_members = channel_partition_verdict(ch, datasets, "D")
    per_channel_results[ch] = {
        "m_verdict": m_verdict, "m_roles": m_roles, "m_members": m_members,
        "d_verdict": d_verdict, "d_roles": d_roles, "d_members": d_members,
    }
    m_names = ", ".join(name.split(" - ")[0] for name, _ in m_roles) or "—"
    d_names = ", ".join(name.split(" - ")[0] for name, _ in d_roles) or "—"
    print(f"| {ch} | {m_names} | {VERDICT_SYMBOL[m_verdict]} {m_verdict} "
          f"| {d_names} | {VERDICT_SYMBOL[d_verdict]} {d_verdict} |")

# True M-tier gaps
print("\n## Phase A1 — True M-tier coverage gaps\n")
m_gaps = [(ch, r) for ch, r in per_channel_results.items()
          if r["m_verdict"] in ("incomplete", "partial", "none")]
if not m_gaps:
    print("_None — every in-scope channel has at least partial M-tier coverage and the partition heuristic doesn't flag any incompletes._\n")
else:
    for ch, r in m_gaps:
        print(f"### {ch} → {VERDICT_SYMBOL[r['m_verdict']]} {r['m_verdict']}")
        for name, role in r["m_roles"]:
            print(f"  - `{name}` — {role}")
        print()

# True D-tier gaps
print("## Phase A2 — True D-tier coverage gaps\n")
d_gaps = [(ch, r) for ch, r in per_channel_results.items()
          if r["d_verdict"] in ("incomplete", "partial", "none")]
if not d_gaps:
    print("_None._\n")
else:
    for ch, r in d_gaps:
        print(f"### {ch} → {VERDICT_SYMBOL[r['d_verdict']]} {r['d_verdict']}")
        if not r["d_roles"]:
            print(f"  - **No dataset targets this channel.** M policies on `{','.join(CHANNEL_TO_LOCATIONS.get(ch, []))}` "
                  f"will only fire on whatever dataset they happen to be linked to (often a broader umbrella like D1000).")
        for name, role in r["d_roles"]:
            print(f"  - `{name}` — {role}")
        print()

# Manual verify
print("## Channels needing manual verification (multi-rule OR'd partitions)\n")
verify_channels = [(ch, r) for ch, r in per_channel_results.items()
                   if r["m_verdict"] == "complete-verify" or r["d_verdict"] == "complete-verify"]
if not verify_channels:
    print("_None._\n")
else:
    for ch, r in verify_channels:
        m_v = r["m_verdict"]
        d_v = r["d_verdict"]
        print(f"### {ch}")
        if m_v == "complete-verify":
            print(f"  M-tier (≈ likely complete, manual verify):")
            for m in r["m_members"]:
                sigs = m["signals"]
                pos = sorted(sigs["list_ids_positive"])
                neg = sorted(sigs["list_ids_negative"])
                print(f"    - `{m['name']}` ({m['role']}, rules={sigs['rule_count']}) "
                      f"pos_lists={[x[:8] for x in pos]} neg_lists={[x[:8] for x in neg]}")
        if d_v == "complete-verify":
            print(f"  D-tier (≈ likely complete, manual verify):")
            for m in r["d_members"]:
                sigs = m["signals"]
                pos = sorted(sigs["list_ids_positive"])
                neg = sorted(sigs["list_ids_negative"])
                print(f"    - `{m['name']}` ({m['role']}, rules={sigs['rule_count']}) "
                      f"pos_lists={[x[:8] for x in pos]} neg_lists={[x[:8] for x in neg]}")
        print()

# Phase B — B-tier action gaps
print("## Phase B — B-tier action coverage gaps\n")
b_gaps = []
for ch in channels_with_intent:
    cells = matrix[ch]
    b_actions = [a for a, v in cells.items() if v == "B" and a != "Global"]
    if not b_actions:
        continue
    deployed_events, has_umbrella_b, b_pols = b_event_types_for_channel(ch)
    for action in b_actions:
        expected = set(EVENT_TYPE_MAP.get(action, []))
        if has_umbrella_b or (expected & deployed_events):
            continue
        if not expected:
            # Enforcement matrix has no canonical event_type for this action — neither a
            # coverage gap we can fix nor a clean ✓; flag as undefined for human review.
            b_gaps.append((ch, action,
                f"no canonical event_type defined in enforcement matrix — verify whether intent=B is realizable",
                deployed_events, b_pols))
        else:
            b_gaps.append((ch, action, f"expected event_type ∈ {sorted(expected)}", deployed_events, b_pols))

if not b_gaps:
    print("_None._\n")
else:
    by_channel = defaultdict(list)
    for ch, action, reason, deployed, pols in b_gaps:
        by_channel[ch].append((action, reason, deployed, pols))
    for ch, items in by_channel.items():
        print(f"### {ch}")
        first = items[0]
        print(f"  - Deployed B policies: `{', '.join(first[3]) or '(none)'}`")
        print(f"  - Deployed B event_types: `{sorted(first[2]) or '(umbrella / none)'}`")
        for action, reason, _, _ in items:
            print(f"  - **{action}** → ❌ {reason}")
        print()

# Phase C — diagnostic
print("## Phase C — diagnostic side-checks\n")

# Sub-channel + inverted-umbrella consistency: M5000 vs M5010-M5080
m5000 = next((p for p in M if p["name"].startswith("M5000")), None)
m5_subs = [p for p in M if re.match(r"^M50[1-8]0", p["name"])]
if m5000 and m5_subs:
    # Collect negated app_name list_ids in M5000
    m5000_neg_lists = set()
    for rule in m5000.get("query", {}).get("rules", []):
        for c in rule.get("conditions", []):
            if c.get("field_name") == "app_name" and c.get("negated"):
                for v in c.get("values", []):
                    if v.get("list_id"):
                        m5000_neg_lists.add(v["list_id"])
    # Collect positive app_name list_ids across M5010-M5080
    sub_pos_lists = set()
    for p in m5_subs:
        for rule in p.get("query", {}).get("rules", []):
            for c in rule.get("conditions", []):
                if c.get("field_name") == "app_name" and not c.get("negated"):
                    for v in c.get("values", []):
                        if v.get("list_id"):
                            sub_pos_lists.add(v["list_id"])
    only_in_umbrella = m5000_neg_lists - sub_pos_lists
    only_in_subs = sub_pos_lists - m5000_neg_lists
    if not only_in_umbrella and not only_in_subs:
        print(f"### M5000 ↔ M5010–M5080 consistency: ✓ matched ({len(m5000_neg_lists)} lists)")
    else:
        print(f"### M5000 ↔ M5010–M5080 consistency: ⚠ mismatch")
        print(f"  - Excluded by M5000 but no sub-channel covers it: {sorted(only_in_umbrella)}")
        print(f"  - Sub-channel covers but M5000 doesn't exclude: {sorted(only_in_subs)}")
    print()
