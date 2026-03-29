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

## ⛔ HARD CONSTRAINT — READ THIS FIRST ⛔

**The ONLY checklist you may use is `references/hipaa_checklist.md` in this skill's directory.**
Read it before doing anything else. DO NOT invent, import, recall from memory, or use any
other checklist. If you find yourself scoring 40-50+ items, or using item IDs like "1.1",
"2.3", "5.1", "9.4" — STOP. You are using the wrong checklist.

The checklist contains ONLY the 26 implementation specifications that the HIPAA Security Rule
(45 CFR Part 164, Subpart C, Appendix A) marks as **(R) = Required**. These are the only
items that can be scored as pass or fail.

**The following category names are BANNED from the audit output.** They do not correspond
to HIPAA required specifications. If you find yourself writing any of these headers, STOP:

- ❌ "Encryption" (encryption at rest/transit are ADDRESSABLE, not required)
- ❌ "PHI Data Handling" (not a Security Rule category)
- ❌ "API & Network Security" (not a Security Rule category)
- ❌ "Third-Party & Infrastructure" (not a Security Rule category)
- ❌ "Development Practices" (not a Security Rule category)
- ❌ "Breach Detection & Notification" (separate rule, not Security Rule technical audit)
- ❌ "Physical & Administrative Safeguards" (as a single combined blob)

**The following items are NOT HIPAA REQUIRED and must NEVER appear as failures:**

- Encryption at rest or in transit
- Field-level encryption of database columns
- De-identification or tokenization of PHI within your own system
- Rate limiting / throttling
- Automatic logoff / session timeout
- MFA / multi-factor authentication
- Penetration testing
- Secure SDLC / peer review policy
- Developer HIPAA training
- Password complexity policy
- Dependency vulnerability scanning
- Network segmentation
- Mobile device encryption / remote wipe
- CORS policy
- Input validation / injection prevention (as a standalone HIPAA item)

If you want to *mention* any of the above, they go in an **"Addressable Recommendations"**
section clearly labeled as non-blocking. They NEVER go in HIPAA_BAD.md.

## How to Start

1. **Read the checklist:** `view` the file at `references/hipaa_checklist.md` in this skill's
   directory. This is your sole source of truth for what to audit.
2. Follow the audit procedure below.

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
not part of this audit.

## Output Files

The audit produces four types of files. Create them in the project root (or a `/hipaa-audit/`
directory if the user prefers).

### 1. `HIPAA_BAD.md` — Failures Report

Contains every **required** checklist item that **failed** or is **not implemented**.

```
# HIPAA Audit — Failures (HIPAA_BAD)

**Audit version:** v1
**Date:** YYYY-MM-DD
**Auditor:** [AI / human name]
**Module scope:** v1 + traced legacy dependencies
**Scope:** REQUIRED implementation specifications only (per 45 CFR 164 Appendix A)

## Critical Failures
For each failure:
- **ID:** [checklist ID, e.g., T1]
- **Spec:** [e.g., Unique User Identification]
- **CFR citation:** [e.g., §164.312(a)(2)(i)]
- **Where:** [file path, function name, line number or range]
- **What's wrong:** [concrete description]
- **Risk level:** Critical / High / Medium / Low
- **Suggested fix:** [actionable remediation step]
- **Legacy dependency?** Yes/No

## High / Medium / Low Failures
[same structure]

## Summary
- Total failures: X (of 26 required items)
- Critical: X | High: X | Medium: X | Low: X
```

### 2. `HIPAA_GOOD.md` — Passes Report

Contains every **required** checklist item that **passed**.

```
# HIPAA Audit — Passes (HIPAA_GOOD)

**Audit version:** v1
**Date:** YYYY-MM-DD
**Scope:** REQUIRED implementation specifications only

## Passing Items
For each pass:
- **ID:** [checklist ID]
- **Spec:** [name]
- **CFR citation:** [citation]
- **Evidence:** [file path, config, or explanation]

## Summary
- Total passes: X / 26 required items
```

### 3. `HIPAA_v{N}.md` — Versioned Audit Snapshot

```
# HIPAA Audit — Version {N}

**Date:** YYYY-MM-DD
**Previous version:** v{N-1} (or "Initial audit" for v1)
**Scope:** REQUIRED implementation specifications only (per 45 CFR 164 Appendix A)

## v1 → Legacy Dependency Map
[table]

## Required Checklist Results (IDs A1–D4)
For each required item: ID, CFR, Status (✅❌⚠️🔲), Notes

## Addressable Recommendations (informational only — not scored)
[Optional. Clearly labeled non-blocking.]

## Delta from v{N-1}
[skip for v1]

## Audit Verdict
- COMPLIANT: No — X required failures remain
  OR
- COMPLIANT: Yes — all 26 required items pass → generate HIPAA_COMPLIANT.md
```

### 4. `HIPAA_COMPLIANT.md` — Final Compliance Certificate

Only created when **zero required failures** exist.

```
# HIPAA Compliance — CERTIFIED

**Certified on:** YYYY-MM-DD
**Audit version:** v{N}
**Scope:** All REQUIRED implementation specifications per 45 CFR 164 Appendix A

## Certification Statement
All 26 required implementation specifications have passed.
Addressable specs were not scored — organizations should assess them separately
per §164.306(d)(3).

## Conditions
This certification is invalidated by: new endpoints, new dependencies, changes to
auth/encryption/access logic, changes to legacy methods in the dependency map,
or infrastructure changes.

## Full Required Checklist (all ✅)
[complete list]
```

## CRITICAL: Write-Path Tracing (Do NOT Audit Models/DTOs/Interfaces in Isolation)

**This is the single most important rule in this audit.** Encryption, masking, and PHI
protection typically happen in the **service layer**, NOT at the model, DTO, schema, or
interface level. A database model column defined as `String` or a DTO field typed as `str`
tells you **nothing** about whether the data stored there is encrypted or plaintext.

**The wrong way (causes false positives):**
- See `message.py` model has `content = Column(String)` → flag as "plaintext PHI in DB" ❌
- See a Pydantic schema with `content: str` → flag as "unencrypted PHI field" ❌
- See a repository method that does `db.add(message)` → flag as "stores plaintext" ❌

**The right way (trace the live write path):**
1. Start at the **controller/route** that receives the PHI data.
2. Follow the call into the **service layer** — this is where encryption, hashing, or
   masking typically happens before persistence.
3. Confirm what the service passes to the **repository/data-access layer**.
4. Only THEN look at the model/schema to understand storage format.
5. On the read side, confirm the service **decrypts after retrieval**.

**Rules for judging compliance on required items:**

- **Models, schemas, DTOs, interfaces are NOT evidence of a violation.** A `String` column
  can hold AES-256 ciphertext. You must check what is actually written to it.
- **Services are the source of truth.** Always read the service method before judging.
- **If a service encrypts before write and decrypts after read, the item PASSES** even if
  every layer below it uses plain `String`/`Text` types.
- **If you cannot find the write path**, mark ⚠️ Partial — not ❌ Fail.
- **Only flag failure when you can show the full write path and confirm no protection exists.**

**Apply write-path tracing to ALL PHI-related items**, not just encryption.

## How to Run the Audit

### First audit (v1)

1. **Read `references/hipaa_checklist.md`** — this is your sole checklist.
2. Scan the `v1` module. Map every route, controller, service, and middleware.
3. Build the dependency map (`v1 → legacy`). Only trace what `v1` imports or calls.
4. For every PHI-related item, trace the full write/read path through the service layer.
5. Evaluate each **required** item against the code. Cite file paths, function names, lines.
6. **Do NOT fail the codebase for addressable items.** Optional recommendations only.
7. Generate: `HIPAA_BAD.md`, `HIPAA_GOOD.md`, `HIPAA_v1.md`.
8. If zero required failures → also generate `HIPAA_COMPLIANT.md`.

### Subsequent audits (v2, v3, ...)

1. Read `HIPAA_v{N-1}.md` to understand what was already checked.
2. Focus on items in `HIPAA_BAD.md` — verify if fixed.
3. Re-check passing items if relevant code changed.
4. Generate updated files with delta section.
5. If zero required failures → generate `HIPAA_COMPLIANT.md`.

### Audit principles

- **Only required items can fail.** This is the law per §164.306(d).
- **Trace the live path, not the type signature.** #1 source of false positives.
- **Be specific.** Cite complete call chains with file paths and line numbers.
- **If evidence is inconclusive, mark ⚠️ Partial, not ❌ Fail.** Noise erodes trust.
- **Encryption at rest and in transit are ADDRESSABLE, not required.** Never fail for these.

## ⛔ FINAL SELF-CHECK — Run Before Generating Any Output ⛔

Before writing any output file, verify ALL of these:

1. **Does every scored item use an ID from the checklist (A1–A12, P1–P4, T1–T4, O1–O2, D1–D4)?**
   If you have IDs like "1.1", "2.3", "5.1" — you used the WRONG checklist. Start over.
2. **Is total scored items ≤ 26?** If 40-50+, you invented items. Remove them.
3. **Do any failures reference encryption, MFA, rate limiting, pen testing, de-identification,
   password policy, session timeout, SDLC, or developer training?** Move to recommendations.
4. **Are section headers the Security Rule categories** (Administrative Safeguards, Physical
   Safeguards, Technical Safeguards, Organizational Requirements, Policies & Documentation)?
5. **For every ❌ Fail, did you trace the write/read path through the service layer?**

If any check fails, revise before outputting.
