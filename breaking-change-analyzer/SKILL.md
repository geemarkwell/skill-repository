---
name: breaking-change-analyzer
description: >
  Analyze proposed changes, PRDs, specs, and feature requirements to identify
  breaking changes, backwards-compatibility risks, rollout hazards, and likely
  regression points before implementation. Use when the user wants a pre-build
  safety review of a PRD, requirements doc, feature proposal, API change, schema
  change, or implementation plan. Trigger on requests like "will this break
  anything", "breaking change", "review this PRD", "backwards compatible",
  "what could go wrong", "review before I send to the agent", "check for
  breaking changes", "compatibility review", "impact analysis", "risk
  assessment", "sanity check these requirements", "review this spec", "will
  this introduce bugs", or "safe rollout". Also use even when the phrase
  "breaking change" is absent if the user wants to review a spec or set of
  requirements for safety, migration risk, regressions, or compatibility.
---

# Breaking Change Analyzer

Perform a pre-implementation compatibility and regression-risk analysis. Treat
every proposed change as potentially dangerous until the likely blast radius and
safe rollout path are clear.

## Goal

Help the user understand:

- What will definitely break
- What might break
- Which changes are safe
- How to preserve backwards compatibility where needed
- How to phase implementation to reduce rollout risk

This analysis happens before code is written. The output should be concrete
enough that the user can hand a revised, safer spec to a coding agent.

## Inputs

Expect one or more of:

- A PRD or spec document
- Feature requirements pasted in chat
- A plain-language description of a proposed change
- Optional codebase context such as files, repo structure, API docs, schemas, or
  architectural notes

If the user provides a document, read it fully before analyzing. If they
provide codebase context, use it to map contracts, dependencies, and likely
consumers before concluding what is safe.

## Workflow

### 1. Understand the Current State

Before assessing what breaks, understand what exists today.

If codebase context is available:

- Map the relevant modules, services, and boundaries
- Identify existing API contracts, including request and response shapes
- Identify data models, schema assumptions, serialization formats, and enums
- Trace dependency chains and key callers
- Note external integrations, webhooks, jobs, shared libraries, and config
  dependencies

If codebase context is missing, ask targeted questions before making strong
claims. At minimum, try to learn:

- The tech stack
- The architecture shape, such as monolith vs microservices
- Whether external consumers depend on any APIs, events, or file formats
- The current database and migration situation

### 2. Decompose the Proposed Change

Break the proposal into atomic changes. Classify each change as:

- `Additive`: new functionality that does not alter existing behavior
- `Modificative`: a change to existing behavior, contracts, or logic
- `Subtractive`: removal of existing behavior, fields, endpoints, or features

Treat modificative and subtractive changes as the highest-risk categories until
proven otherwise.

### 3. Detect Breaking Changes

For each risky change, trace impact through the system. Inspect these areas:

#### API Contract Breaks

- Renamed, removed, reordered, or retyped fields
- New required request parameters or stricter validation
- Changed status codes or error formats
- Changed authentication or authorization behavior
- Changed pagination, filtering, rate limiting, or default values

#### Data Model Breaks

- Column type changes
- New `NOT NULL` constraints without safe defaults
- Renamed or removed fields
- Changed relationships between entities
- Changed date, enum, identifier, or serialization formats

#### Behavioral Breaks

- Business logic changes that existing callers rely on
- Changed default behavior
- Changed ordering or sorting behavior
- Changed timing, async sequencing, retries, or side effects
- Changed fallback or error-handling behavior

#### Integration Breaks

- Shared library contract changes
- Event, queue, or webhook payload changes
- File format changes
- New config or environment requirements

#### UI and UX Breaks

- Removed or relocated features
- Changed validation or form behavior
- Changed navigation assumptions
- Changed component props or shared interface contracts

### 4. Assess Risk

For each identified breaking change, evaluate:

1. Severity
   Use `Critical`, `High`, `Medium`, or `Low`.
2. Probability
   Use `Certain`, `Likely`, `Possible`, or `Unlikely`.
3. Blast radius
   Identify every known or suspected dependent system, caller, consumer, or
   workflow.

Be explicit when the blast radius is uncertain because codebase context is
missing.

### 5. Propose Compatibility Strategies

For each risky change, recommend a concrete mitigation strategy. Common options:

- Versioned APIs
- Feature flags
- Additive-only contract changes
- Deprecation periods
- Adapter or shim layers
- Safe defaults for new required fields
- Reversible migration scripts
- Gradual replacement instead of big-bang cutover
- Contract tests and regression coverage

Choose the simplest practical strategy that fits the user's context. Do not
default to versioning if a smaller compatibility layer is enough.

## Output

Produce two deliverables.

### Deliverable 1: Breaking Change Risk Report

Write a Markdown report with this structure:

```markdown
# Breaking Change Risk Report

## Executive Summary
[2-3 sentences summarizing overall risk, number of breaking changes found, and
the top recommendation]

## Change Decomposition
[Table listing each atomic change, its classification, and its risk level]

## Breaking Changes Identified

### [Breaking Change Title]
**What changes:** [Precise description]
**What breaks:** [Affected behavior or contract]
**Severity:** [Critical/High/Medium/Low]
**Probability:** [Certain/Likely/Possible/Unlikely]
**Blast radius:** [Consumers and dependencies affected]
**Compatibility strategy:** [Safest pragmatic implementation path]

## Safe Changes
[List analyzed changes that appear non-breaking and briefly explain why]

## Recommended Implementation Order
[Sequence the work to minimize risk]

## Migration Checklist
[Concrete actions to include in the implementation plan]
```

### Deliverable 2: Revised PRD with Compatibility Notes

Produce an enhanced version of the original PRD or requirements that:

- Preserves all original requirements
- Adds inline compatibility warnings beside risky requirements using `⚠️`
- Adds a `Compatibility Requirements` section
- Adds a `Migration Plan` section when data or API migration is required
- Adds backwards-compatibility acceptance criteria
- Adds rollback criteria that define when the change should be halted or reversed

This revised document is the safer handoff artifact for the coding agent.

## Quality Bar

Apply these rules while analyzing:

- Be thorough but not alarmist
- Do not manufacture risk where none exists
- State uncertainty clearly when context is missing
- Think about second-order effects, not just direct call sites
- Consider existing tests, coverage gaps, and contract-test opportunities
- Prefer pragmatic rollout guidance over theoretically perfect but unrealistic
  solutions
- If a proposal is genuinely safe, say so directly

## Phasing Guidance

When recommending phased rollout, label phases logically as `Phase 1`,
`Phase 2`, and so on. Do not assign dates or week-based timelines unless the
user explicitly asks for scheduling help.
