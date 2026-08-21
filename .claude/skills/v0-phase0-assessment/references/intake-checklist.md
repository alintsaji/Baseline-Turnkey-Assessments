# Customer intake checklist

Generic categories to capture for any turnkey v0 customer during Phase 0. This is the
same shape of profile captured for G&W Electric — kept generic here so it transfers to
other customers. Store answers in project memory (`project_{customer}.md`) so Phase 1+
skills can reuse them without re-asking.

Ask only for categories not already answered in memory or in a prior audit. Skip
anything the analyst says isn't applicable to this customer, and note it as N/A rather
than leaving it blank.

## Identity & domains

- Internal email/user domains (all of them — include regional/subsidiary domains)
- Identity provider (Azure AD, Okta, Google Workspace, etc.)
- Directory-integration status (wired? producing `group_name` on events?)

## Productivity & storage

- Productivity suite (M365, Google Workspace, etc.)
- Cloud storage in use (Box, OneDrive, SharePoint, Google Drive, Dropbox, etc.)
- Internal SharePoint / Drive tenant URL(s)
- Core SaaS apps in scope (CRM, HR/payroll, ITSM, etc.) and their domains/instance URLs

## Browsers & GenAI

- Approved browsers
- Non-approved browsers allowed or blocked?
- Approved GenAI tools (ChatGPT, Copilot, Gemini, Claude, etc.)
- Network-layer GenAI controls already in place (VPN/SASE/proxy filtering)? Which
  product?

## Network & endpoints

- SIEM/logging destination
- Network filtering/SASE product in use
- Network share usage level and UNC paths (internal + external + sensitive
  subfolders)
- Printer names (friendly names of corporate-managed printers)
- Endpoint management (SCCM, Intune, Jamf, etc.) and endpoint count
- BYOD permitted?

## Removable media & file transfer

- USB/removable media policy (fully allowed / restricted / device allowlist)
- Approved USB device IDs, if any
- Approved file-transfer services, if any

## Data classification & compliance

- Existing data classification schema, if any
- MIP/AIP or equivalent sensitivity labels in use?
- Compliance requirements (GDPR, CMMC, HIPAA, PCI, CCPA, etc.)
- Sensitive data types of concern (PII, financial, M&A, HR, IP/engineering,
  credentials, etc.)
- Sensitive data identification methods available (naming conventions, keywords,
  locations, file types, data patterns)

## Risk & priorities

- Priority use cases, ranked (e.g. personal cloud upload, personal email, GenAI,
  USB, printing, shadow IT)
- High-risk roles/departments (Finance, Legal, HR, Executives, etc.)
- Past incidents (type, and whether insider/leaver-driven)

## Deployment shape

- Deployment style (all-at-once vs phased by group/region/function)
- Initial severity target (visibility-only vs warn vs block)
- Cutover / go-live target date
