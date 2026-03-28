---
name: hipaa-audit
description: >
  Run a structured HIPAA compliance audit on a codebase, producing versioned report files.
  Use this skill whenever the user mentions HIPAA, PHI compliance, healthcare data security,
  protected health information auditing, or wants to check if their app meets HIPAA standards.
  Also trigger when the user references HIPAA_BAD, HIPAA_GOOD, HIPAA_v1, HIPAA_COMPLIANT,
  or asks to "run an audit", "check compliance", or "are we HIPAA compliant". This skill
  covers the full audit lifecycle from first scan through final compliance certification.
---

# HIPAA Compliance Audit Skill

This skill runs a structured, versioned HIPAA compliance audit against a codebase. It produces
a set of output files that track failures, passes, and incremental progress across audit
iterations until the codebase reaches full compliance.

## Architecture Context: The v1-First Approach

The backend has a primary module called `v1`. This is the main API surface the frontend depends on.
In some cases, `v1` reuses methods from older/legacy modules. The audit must respect this structure
to avoid wasting time on code that is never executed.

**Audit traversal order — follow this exactly:**

1. Map `v1` first — every route, controller, service, middleware, and model inside `v1`.
2. Trace outward — identify every import, call, or inheritance from `v1` into legacy modules.
3. Audit only the legacy methods that `v1` actually touches. Ignore the rest.
4. Flag untouched legacy modules as out-of-scope (recommend for deprecation).

Think of it as a call graph rooted at `v1`. If a code path is not reachable from `v1`, it is
not part of this audit. This keeps the audit focused and prevents rabbit-holing into dead code.

## Output Files

The audit produces four types of files. Create them in the project root (or a `/hipaa-audit/` directory if the user prefers).

### 1. `HIPAA_BAD.md` — Failures Report

Contains every checklist item that **failed** or is **not implemented**. This is the primary
remediation punch list. Structure it so a developer can pick it up and start fixing things.

```
# HIPAA Audit — Failures (HIPAA_BAD)

**Audit version:** v1
**Date:** YYYY-MM-DD
**Auditor:** [AI / human name]
**Module scope:** v1 + traced legacy dependencies

## Critical Failures (PHI exposure risk)
For each failure:
- **Category:** [e.g., Encryption, PHI Data Handling]
- **Checklist item:** [the specific item that failed]
- **Where:** [file path, function name, line number or range]
- **What's wrong:** [concrete description of the violation]
- **Risk level:** Critical / High / Medium / Low
- **Suggested fix:** [actionable remediation step]
- **Legacy dependency?** Yes/No — if yes, note which v1 code path calls it

## High Failures
[same structure]

## Medium Failures
[same structure]

## Low Failures
[same structure]

## Summary
- Total failures: X
- Critical: X | High: X | Medium: X | Low: X
- Legacy module failures: X (of total)
```

Organize failures by severity, not by checklist category. A developer triaging this file
should see the most dangerous issues first. Within each severity tier, group by category
if it helps readability.

### 2. `HIPAA_GOOD.md` — Passes Report

Contains every checklist item that **passed**. This serves as proof of compliance for the
items that are already handled, and gives the team confidence about what's working.

```
# HIPAA Audit — Passes (HIPAA_GOOD)

**Audit version:** v1
**Date:** YYYY-MM-DD
**Module scope:** v1 + traced legacy dependencies

## Passing Items

For each pass:
- **Category:** [e.g., Encryption]
- **Checklist item:** [the specific item that passed]
- **Evidence:** [file path, config, code snippet reference, or explanation of how it's implemented]
- **Verified in:** v1 / legacy module (specify which)

## Summary
- Total passes: X / Y checklist items
- Coverage: X% of checklist
```

### 3. `HIPAA_v{N}.md` — Versioned Audit Snapshot

Each audit run produces a versioned snapshot. The first audit creates `HIPAA_v1.md`.
Subsequent audits after remediation create `HIPAA_v2.md`, `HIPAA_v3.md`, etc.

This file is the **complete audit record** for that version — it combines pass/fail status
for every checklist item, the dependency map, and a delta from the previous version.

```
# HIPAA Audit — Version {N}

**Date:** YYYY-MM-DD
**Previous version:** v{N-1} (or "Initial audit" for v1)
**Module scope:** v1 + traced legacy dependencies

## v1 → Legacy Dependency Map
| v1 file/method | Calls into (legacy module) | Legacy method | PHI involved? |
|---|---|---|---|
| v1/routes/patient.js → | legacy/db/queries.js | getPatientById() | Yes |

## Checklist Results
For each of the 10 categories, list every item with:
- Status: ✅ Pass | ❌ Fail | ⚠️ Partial | 🔲 N/A
- Notes (brief)

## Delta from v{N-1} (skip for v1)
- Items fixed since last audit: [list]
- Items regressed since last audit: [list]
- New items added: [list]
- Net change: +X passes, -Y failures

## Audit Verdict
- **COMPLIANT**: No — X failures remain (move to v{N+1})
  OR
- **COMPLIANT**: Yes — all checklist items pass → generate HIPAA_COMPLIANT.md
```

### 4. `HIPAA_COMPLIANT.md` — Final Compliance Certificate

Only created when an audit version has **zero failures** across all checklist items.
This is the finish line.

```
# HIPAA Compliance — CERTIFIED

**Certified on:** YYYY-MM-DD
**Audit version that passed:** v{N}
**Module scope:** v1 + traced legacy dependencies

## Certification Statement
This codebase has been audited against the HIPAA compliance checklist
and all items have passed as of the above date.

## What Was Audited
- v1 module: [X routes, Y services, Z middleware]
- Legacy dependencies traced: [list]
- Legacy modules flagged out-of-scope: [list]

## Conditions
This certification is valid as of the audit date. Any of the following
invalidate it and require a re-audit (creating the next version):
- New routes or endpoints added to v1
- New third-party dependencies introduced
- Changes to authentication, authorization, or encryption logic
- Changes to any legacy method in the dependency map
- Infrastructure or cloud provider changes

## Full Checklist (all passing)
[Include the complete checklist with all items marked ✅]
```

## How to Run the Audit

### First audit (v1)

1. Read the checklist from `references/hipaa_checklist.md` (the full checklist with all 10 categories).
2. Scan the `v1` module. Map every route, controller, service, and middleware.
3. Build the dependency map (`v1 → legacy`). Only trace what `v1` imports or calls.
4. Evaluate each checklist item against the code. Be concrete — cite file paths, function names, line numbers.
5. Generate all three files: `HIPAA_BAD.md`, `HIPAA_GOOD.md`, `HIPAA_v1.md`.
6. If zero failures → also generate `HIPAA_COMPLIANT.md`.

### Subsequent audits (v2, v3, ...)

1. Read the previous version (`HIPAA_v{N-1}.md`) to understand what was already checked.
2. Focus on items that were in `HIPAA_BAD.md` — verify if they've been fixed.
3. Re-check passing items if the relevant code has changed (git diff if available).
4. Generate updated `HIPAA_BAD.md`, `HIPAA_GOOD.md`, and `HIPAA_v{N}.md`.
5. Include the delta section showing what changed between versions.
6. If zero failures → generate `HIPAA_COMPLIANT.md` and celebrate.

### Audit principles

- Be specific. "Encryption is missing" is useless. "v1/services/patient.service.js line 42 stores SSN in plaintext in Redis cache" is actionable.
- When auditing legacy code reached through v1, always note the call chain: `v1/routes/billing.js:23 → legacy/utils/format.js:buildInvoice() → legacy/db/raw.js:query()` so the developer can trace the full path.
- If you can't determine pass/fail for an item (e.g., you can't see infrastructure config), mark it ⚠️ Partial and explain what you'd need to verify.
- Err on the side of flagging. A false positive in HIPAA_BAD is better than a false negative in HIPAA_GOOD.
