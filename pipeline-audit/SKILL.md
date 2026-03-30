---
name: pipeline-audit
description: Audit, evaluate, debug, analyze, and plan refactoring of data pipelines. Use this skill whenever the user asks to audit a pipeline, evaluate pipeline quality, debug pipeline issues, investigate extraction or transformation errors, find root causes of data issues, assess pipeline health at session start, review pipeline output quality, trace data flow through pipeline stages, analyze the blast radius of a bug, or plan how to generalize, white-label, or make a pipeline client-agnostic. Also trigger when the user says things like "catch me up on the pipeline", "what's the state of things", "something looks wrong in the output", "why is this failing", "how many files are affected", "run diagnostics", "check pipeline health", "start a new session on the pipeline", "how do I make this work for other clients", "audit for hardcoded assumptions", "what would need to change to support multiple clients", "white label the pipeline", or "plan the refactoring". This skill applies to any multi-stage data pipeline — extraction, transformation, validation, migration — not just a specific project.
metadata:
  domain: workflow
  languages: project specific
---

# Pipeline Audit, Evaluation & Analysis

This skill equips you to systematically audit, evaluate, and debug multi-stage data pipelines. It provides structured workflows for five scenarios: session-start audits (catching up on state), debugging and root cause analysis, quality evaluation, impact/blast-radius analysis, and generalization audits (identifying client-specific coupling and planning multi-client architecture).

The core philosophy: **evidence over intuition**. Every claim about pipeline state should be backed by data you can point to — file counts, error rates, sample outputs, log entries. When debugging, resist the urge to jump to fixes before you've actually isolated the cause. When auditing for generalization, resist the urge to propose abstractions before you've cataloged every concrete coupling point.

---

## Choosing Your Workflow

Before diving in, determine which mode fits the situation:

| Situation | Workflow | Section |
|---|---|---|
| Starting a new session, need to catch up | **Session Audit** | §1 |
| Something is broken or producing wrong output | **Debug & Root Cause** (defers to Debug Auditor) | §2 |
| Need to assess overall output quality | **Quality Evaluation** | §3 |
| Found a bug, need to know how bad it is | **Impact Analysis** | §4 |
| Need to make the pipeline work for multiple clients | **Generalization Audit** | §5 |

These aren't mutually exclusive. A session audit might surface an issue that flows into debugging, which leads to impact analysis. A generalization audit might reveal correctness issues that need debugging first. Follow the thread wherever it goes.

### When to Read `references/checklists.md`

The main SKILL.md covers the general workflow for any pipeline. The `references/checklists.md` file contains domain-specific checklists — extraction pipelines, regex/pattern library audits, LLM integration, cache systems, schema evolution, a catalog of common bug patterns (misattribution, boundary bleed, silent drops, etc.), and a generalization/coupling analysis checklist.

Read the reference file when:
- **Session Audit (§1), Step 2**: You've identified the pipeline type (extraction, transformation, migration) — load the matching checklist to guide your architecture review and state assessment.
- **Debug (§2)**: When Debug Auditor surfaces a root cause, cross-reference against the "Common Bug Patterns" section for pipeline-specific patterns (misattribution, boundary bleed, silent drops, etc.).
- **Quality Evaluation (§3), Step 1**: You're defining quality dimensions — the domain checklists enumerate what to look for in each pipeline type.
- **Generalization Audit (§5), Step 2**: You're cataloging coupling points — the "Generalization & Coupling Analysis" checklist (§9 in the reference) provides a systematic scan across code layers.
- **Any workflow**: The pipeline uses regex patterns, LLM calls, or a caching layer. The specialized audit checklists (§5–7 in the reference) go deeper than the main workflow on these subsystems.

If you're unsure, read it. It's cheaper to scan the reference and skip what's irrelevant than to miss a checklist item that would have caught the issue.

---

## §1 — Session Start Audit

The goal here is to quickly build a mental model of the pipeline's current state so the session can be productive from the first minute. Think of it as a pre-flight checklist.

### Step 1: Locate the Pipeline

Identify the pipeline codebase, configuration, and output locations. Look for:
- The main entry point or orchestrator script
- Configuration files (schema definitions, pattern libraries, environment configs)
- Output directories (processed files, logs, cache)
- Any status/progress tracking files (manifests, run logs, checkpoint files)

If the user has multiple pipelines, ask which one. If there's only one, proceed.

### Step 2: Read the Pipeline Architecture

Before touching any data, understand the pipeline's structure. Read through the codebase to identify:

- **Stages**: What are the discrete processing steps? (e.g., ingestion → conversion → extraction → validation → output)
- **Data flow**: What goes in and out of each stage? What format transformations happen?
- **Error handling**: How does each stage handle failures? Are errors logged, skipped, or fatal?
- **Dependencies**: External services, APIs, LLM calls, database connections
- **Caching**: Is there a caching layer? What's the cache key strategy? How do you invalidate?

Produce a brief architecture summary for the user — just enough to confirm you understand the system. Something like:

```
Pipeline: [name]
Stages: ingestion → [stage] → [stage] → output
Input: [format, source, count]
Output: [format, destination]
Key dependencies: [list]
```

### Step 3: Assess Current State

Now look at the actual data. Check:

- **Completeness**: How many inputs exist vs. how many have been processed? Are there unprocessed items?
- **Recency**: When was the last successful run? Are there stale outputs?
- **Error rate**: How many items failed in the most recent run? Is there a pattern in the failures?
- **Schema/config version**: What version of the schema or config is active? Has it changed recently?
- **Known issues**: Check for any TODO comments, issue tracking files, or documented known limitations

### Step 4: Produce the Audit Report

Synthesize findings into a structured summary. Keep it scannable — the user should be able to glance at this and know where things stand.

**Report template:**

```markdown
# Pipeline Audit — [Pipeline Name]
**Date**: [date]  **Session**: [session context if relevant]

## Status Overview
- **Pipeline health**: [Healthy / Degraded / Broken]
- **Last successful run**: [timestamp or "unknown"]
- **Processing coverage**: [X/Y items processed] ([Z%])
- **Current error rate**: [N failures out of M processed] ([P%])

## Architecture Snapshot
[Brief stage-by-stage summary from Step 2]

## Current Issues
[List any problems found, ordered by severity]

## Related Issues
[Cross-reference issues that share root causes, affect overlapping file sets, or have dependencies. E.g., "JIRA-312 (fee misattribution) and JIRA-247 (boundary bleed) share a root cause in section delimiter handling — remediating one may partially address the other. Consider batching."]

## Recommended Next Steps
[What should this session focus on?]
```

Adapt the template to the specific pipeline — don't force fields that don't apply.

---

## §2 — Debug & Root Cause Analysis

For general debugging and root cause analysis, defer to the **Debug Auditor** skill, which provides a comprehensive, language-agnostic diagnostic workflow with a philosophy of surgical restraint.

When using Debug Auditor for pipeline issues, supplement its diagnosis with pipeline-specific context:
- **Isolate the stage first**: Determine which pipeline stage introduces the error by working backwards from the bad output through intermediate results.
- **Rule out stale cache**: Before tracing code, check whether the bug is a caching artifact — stale cache is one of the most common false trails in pipeline debugging.
- **Estimate blast radius**: If the root cause affects more than the reported items, follow up with an Impact Analysis (§4).

---

## §3 — Quality Evaluation

When you need to assess the overall quality of pipeline output — not debugging a specific bug, but evaluating how well the pipeline is performing across the board.

### Step 1: Define Quality Dimensions

What does "good output" mean for this pipeline? Common dimensions:

- **Completeness**: Are all expected fields/items present?
- **Accuracy**: Do extracted/transformed values match the source?
- **Consistency**: Are similar inputs producing similar output structures?
- **Schema conformance**: Does output match the expected schema?
- **Coverage**: What percentage of inputs produce usable output?

Work with the user to weight these — not all dimensions matter equally for every pipeline.

### Step 2: Sample Selection

Don't evaluate everything — sample strategically:

- **Random sample**: Pull N items at random for a baseline quality assessment (N depends on total volume — 30–50 is often sufficient for a rough estimate, 100+ for higher confidence)
- **Stratified sample**: If there are known categories or difficulty tiers, sample proportionally from each
- **Edge case sample**: Deliberately include items that are likely to be hard (large files, unusual formatting, edge-case content)
- **Failure sample**: Include items from the error/failure bucket to understand failure modes

### Step 3: Evaluate

For each sample item, assess against your quality dimensions. Use a tiered approach when possible:

1. **Automated checks** (fast, exhaustive): Schema validation, field presence, type checking, value range validation
2. **Heuristic checks** (fast, approximate): Pattern-based validation, cross-field consistency, statistical outlier detection
3. **Spot-check with LLM** (moderate cost): Use a fast model to compare output against source for a subset
4. **Deep audit** (expensive, precise): Use a capable model or manual review for the hardest cases

### Step 4: Compute Metrics

Aggregate findings into actionable metrics:

- **Overall quality score**: Percentage of items passing all quality checks
- **Per-dimension scores**: Breakdown by each quality dimension
- **Error taxonomy**: Categorize failures by type with counts
- **Trend data**: If previous evaluations exist, show improvement/regression

### Step 5: Quality Report

```markdown
# Quality Evaluation — [Pipeline Name]
**Date**: [date]  **Sample size**: [N items]

## Summary
- **Overall quality**: [X%] of items pass all checks
- **Coverage**: [Y%] of inputs produce output

## Per-Dimension Scores
| Dimension | Score | Notes |
|---|---|---|
| Completeness | [%] | [brief note] |
| Accuracy | [%] | [brief note] |
| ... | ... | ... |

## Error Taxonomy
| Error Type | Count | % of Failures | Example |
|---|---|---|---|
| [type] | [N] | [%] | [brief example] |

## Related Issues
[Link error types back to known bugs or open investigations. E.g., "56% of Accuracy failures trace to JIRA-312 (fee misattribution). Resolving that issue would move overall quality from 81% to ~89%."]

## Recommendations
[Prioritized list of improvements, ordered by impact]
```

---

## §4 — Impact Analysis (Blast Radius)

When a bug is discovered, you need to know how bad it is before deciding how urgently to fix it and whether past outputs need correction.

### Step 1: Characterize the Bug

Define the precise conditions under which the bug manifests:
- What input characteristics trigger it?
- Which pipeline stage is affected?
- What is the nature of the incorrect output? (missing data, wrong values, corrupted structure, misattribution)

### Step 2: Build a Detection Query

Write a script or query that can identify all items affected by this bug. The detection should be:
- **Conservative**: Better to flag false positives than miss affected items
- **Fast**: It should run against the full dataset in reasonable time
- **Verifiable**: You should be able to spot-check results to confirm accuracy

### Step 3: Quantify the Impact

Run the detection across the full dataset and produce:

- **Count**: How many items are affected?
- **Percentage**: What fraction of total output?
- **Value impact**: If there's a quantifiable dimension (dollar amounts, record counts), what's the total magnitude?
- **Temporal distribution**: When were the affected items processed? Is this a recent regression or a long-standing issue?
- **Downstream effects**: Who or what consumes this output? What decisions might have been made based on incorrect data?

### Step 4: Impact Report

```markdown
# Impact Analysis — [Bug Title]
**Date**: [date]

## Bug Characterization
[What the bug does and when it triggers]

## Blast Radius
- **Items affected**: [N] out of [M] total ([%])
- **Value impact**: [if quantifiable, e.g., "$X in misattributed amounts"]
- **Time range**: [when this started, if determinable]

## Detection Method
[How affected items were identified — script, query, manual review]

## Confidence Level
[How confident are you in these numbers? What could you be missing?]

## Related Issues
[Other bugs that overlap in affected files, share root causes, or should be remediated together. Note the union/intersection of affected file sets and whether batching the fixes is more efficient than separate runs.]

## Recommended Response
- **Severity**: [Critical / High / Medium / Low]
- **Fix**: [brief description]
- **Remediation**: [Do past outputs need correction? How?]
```

---

## §5 — Generalization & Abstraction Audit

When the pipeline works for one client or context but needs to support multiple, this workflow identifies every point of client-specific coupling and produces a refactoring plan. The deliverable is a planning document — no code changes are made during this audit.

The trap in generalization work is premature abstraction. Building configurable systems before you've cataloged what actually varies leads to over-engineered code that's flexible in the wrong places and rigid where it matters. This workflow prevents that by enforcing a strict sequence: **catalog concrete coupling first, propose abstractions second**.

### When to Use This Workflow

This applies when:
- The pipeline was built for one client/context and needs to support others
- The user wants to "white-label" or make the pipeline "client-agnostic"
- The pipeline is being productized — moving from bespoke tool to reusable product
- The user wants a planning document before committing to refactoring

It does not apply when:
- The pipeline already supports multiple clients and you're adding another (that's configuration, not architecture)
- The issue is a bug in existing single-client logic (use §2)
- The user wants to refactor for code quality without changing the client model (standard refactoring, outside this skill's scope)

### Step 1: Establish the Baseline

Before auditing for generalization, confirm the pipeline works correctly for its current client. You can't generalize a broken pipeline — you'll just distribute the bugs.

Run a quick health check (abbreviated §1):
- Is the pipeline in a stable, working state?
- Are there known bugs that would need to be fixed before or during refactoring?
- What's the current processing coverage and error rate?

If the pipeline has significant correctness issues, flag them. The user decides whether to fix first or proceed with the audit (documenting known issues as constraints on the refactoring plan).

### Step 2: Catalog Client-Specific Coupling

This is the core of the audit. Read the entire codebase systematically and catalog every point where the pipeline assumes a specific client's conventions. Work through three layers, from surface to structural.

**Load the Generalization & Coupling Analysis checklist from `references/checklists.md` (§9) before starting this step.** The checklist provides a systematic scan pattern so you don't miss coupling points hiding in less obvious places.

#### Layer 1: Surface Coupling (Naming & References)

Scan for anything that names or references the specific client:

- **String literals**: Client name in filenames, log messages, comments, docstrings, error messages
- **Variable/function names**: Functions like `parse_axiom_header()` or variables like `acme_fee_categories`
- **File path assumptions**: Hardcoded paths that assume a specific directory structure or naming convention
- **Comments and documentation**: References that assume single-client context

For each finding, record:
- File and line number
- What it currently does
- Whether it's cosmetic (rename only) or functional (behavior depends on it)

Surface coupling is low-risk to fix but high-volume. Cataloging it thoroughly prevents surprises during refactoring.

#### Layer 2: Structural Coupling (Logic & Assumptions)

This is where the real complexity lives. Identify every place where processing logic assumes how a specific client's data is structured:

- **Schema assumptions**: Expected sheet names, column headers, field names, data types
- **Taxonomy assumptions**: Hardcoded category names, classification labels, fee types, status codes
- **Format assumptions**: Expected date formats, number formats, text patterns, delimiters
- **Layout assumptions**: Expected document structure, section ordering, header/footer patterns
- **Detection heuristics**: Logic that identifies document types, sections, or regions based on client-specific patterns

For each finding, record:
- File, function, and line range
- What the current hardcoded assumption is (be specific — "expects columns A-F to be..." not just "column assumptions")
- What would need to vary across clients
- **Blast radius**: What downstream logic depends on this assumption? Trace the dependency chain. If `parse_fee_table()` assumes Axiom's column layout, and `calculate_totals()` depends on `parse_fee_table()`'s output shape, both are in the blast radius.

#### Layer 3: Architectural Coupling (System Design)

Zoom out from individual code paths and look at the pipeline's architecture:

- **Configuration**: Is there a config system? Is it per-client or global? Can it support client-specific overrides?
- **Pipeline flow**: Are stages sequenced in a way that assumes one client's workflow? Would other clients need different stage ordering?
- **Output format**: Is the output schema client-specific or generic? Would other clients need different output structures?
- **State management**: Are there assumptions about processing volume, file counts, or batch sizes tied to one client?
- **External integrations**: Are downstream systems (Salesforce, databases, APIs) hardwired or configurable?

### Step 3: Identify What's Already Generic

Not everything needs to change. Explicitly catalog the parts of the pipeline that are already client-agnostic. This is important for three reasons:

1. It scopes the actual refactoring work (often smaller than it looks)
2. It identifies the stable foundation you're building on
3. It prevents unnecessary refactoring of code that already works

For each generic component, note:
- What it does
- Why it's already client-agnostic (operates on generic data structures, uses configuration, etc.)
- Whether it has any hidden assumptions that might break with different client data (e.g., a "generic" parser that happens to work because all current data shares a format)

### Step 4: Propose the Abstraction Architecture

Based on the coupling catalog from Steps 2–3, propose how the pipeline should be restructured. The goal is the minimum viable abstraction that unlocks multi-client support without over-engineering.

Address four questions:

**1. How are client-specific schemas/templates defined?**
Propose the format and location for client configuration. This could be config files (YAML/JSON), a schema registry, or a profile system. Whatever you propose should be concrete enough to implement — not "use a config system" but "a YAML file per client at `config/clients/{client_id}.yaml` containing these specific fields."

**2. How does the pipeline know which client profile to apply?**
Propose the detection or selection mechanism. Options range from explicit (user passes a client ID) to automatic (the pipeline infers the client from document characteristics). Recommend the simplest option that works — auto-detection is elegant but fragile.

**3. What shared logic remains universal?**
Identify the processing core that all clients share. This becomes the stable backbone of the pipeline. Be specific about which functions/modules stay unchanged.

**4. What becomes pluggable?**
Identify the logic that needs to vary per client. For each pluggable component, propose the interface (what goes in, what comes out) and note what the current single-client implementation would look like as the first "plugin."

When there's no second client yet, resist the urge to speculate about what future clients might need. Design the abstraction boundary based on what you've observed varies (the coupling catalog), not on imagined future requirements. The first client's implementation becomes the default behavior — generalization means making it configurable, not replacing it.

### Step 5: Build the Refactoring Roadmap

Sequence the proposed changes into an actionable plan. Order by three factors:

**Dependency order**: What must change before other changes are possible? Config system before client profiles. Client profiles before detection logic. Detection logic before per-client schema mapping.

**Risk level**: What's most likely to break existing functionality? High-blast-radius changes (Step 2, Layer 2 findings) need more careful sequencing and testing than cosmetic renames (Layer 1).

**Effort estimate**: Relative sizing (small/medium/large) is fine. The point is to give the user a sense of scope, not a precise timeline.

For each item in the roadmap:
- What changes
- Which coupling points it addresses (reference the catalog)
- What must be done before it (dependencies)
- Risk to existing functionality (low/medium/high)
- Effort (small/medium/large)
- How to verify it didn't break anything (test strategy)

### Step 6: Produce the Generalization Report

Save the report as a markdown file. This is the deliverable — it should be comprehensive enough that someone can execute the refactoring plan without needing the auditor present.

```markdown
# Generalization Audit — [Pipeline Name]
**Date**: [date]
**Current client**: [client name]
**Objective**: [what the user wants to achieve — e.g., "make pipeline client-agnostic for structural engineering firms"]

## Pipeline Health Baseline
[Brief summary from Step 1 — current state, known issues, constraints on refactoring]

## Coupling Catalog

### Layer 1: Surface Coupling (Naming & References)
| File | Line(s) | Current | Type | Notes |
|---|---|---|---|---|
| [file] | [lines] | [what it says/does] | Cosmetic / Functional | [any notes] |

### Layer 2: Structural Coupling (Logic & Assumptions)
| File | Function | Assumption | What Varies | Blast Radius |
|---|---|---|---|---|
| [file] | [function] | [specific assumption] | [what would differ per client] | [downstream dependencies] |

### Layer 3: Architectural Coupling (System Design)
[Narrative assessment of pipeline-level design decisions that assume single-client context]

## Already Generic
| Component | What It Does | Confidence |
|---|---|---|
| [module/function] | [description] | [High: truly generic / Medium: works by coincidence / Low: untested assumption] |

## Proposed Architecture
### Client Configuration
[How client profiles are defined and stored]

### Client Detection/Selection
[How the pipeline knows which profile to use]

### Shared Core
[What stays the same across all clients]

### Pluggable Components
| Component | Interface | Current Implementation | What Varies |
|---|---|---|---|
| [component] | [inputs → outputs] | [current single-client version] | [what changes per client] |

## Refactoring Roadmap
| Priority | Change | Addresses | Dependencies | Risk | Effort | Verification |
|---|---|---|---|---|---|---|
| 1 | [change] | [coupling points] | [none / what] | [L/M/H] | [S/M/L] | [how to test] |
| 2 | [change] | [coupling points] | [#1] | [L/M/H] | [S/M/L] | [how to test] |

## Constraints & Risks
[Known issues that affect refactoring, things to watch out for, assumptions made in this audit]
```

Adapt the template to the specific pipeline. If a section isn't relevant (e.g., the pipeline has no architectural coupling), say so briefly rather than forcing empty tables.

---

## General Principles

These apply across all five workflows:

**Start with data, not code.** Look at inputs, outputs, and intermediate results before reading code. Understanding what the data looks like tells you more than reading abstractions.

**Be precise about numbers.** "A lot of failures" is not useful. "137 out of 2,871 files (4.8%)" is. Whenever you can quantify something, do so.

**Preserve evidence.** Before making changes, capture the current state. Save failing examples, log outputs, and intermediate results. You'll need them to verify fixes and for the session record.

**Think in stages.** Pipelines are sequential by nature. Most bugs live in a single stage. Isolating the stage first dramatically narrows the search space.

**Check your assumptions.** The most common debugging trap is assuming you know what the data looks like without actually checking. Always verify.

**Document as you go.** Don't save reporting for the end. Write findings as you discover them — it helps organize your thinking and gives the user visibility into your progress.

---

## Working with the User

When the user invokes this skill, they might use very different phrasings:

- "Audit the pipeline" → Session Audit (§1)
- "Something's wrong with the extraction" → Debug (§2)
- "How good is the output?" → Quality Evaluation (§3)
- "How many files did that bug affect?" → Impact Analysis (§4)
- "How do I make this work for other clients?" → Generalization Audit (§5)
- "White label the pipeline" → Generalization Audit (§5)
- "What would need to change to support Company X?" → Generalization Audit (§5)
- "Catch me up" → Session Audit (§1)
- "Let's debug this" → Debug (§2)
- "Run diagnostics" → Start with Session Audit (§1), escalate if issues found
- "Plan the refactoring" → Generalization Audit (§5) if multi-client, otherwise clarify scope

If the intent is ambiguous, start with a Session Audit — it's the safest default and naturally surfaces issues that might need the other workflows.

When producing reports, save them as markdown files to the working directory so the user has a persistent record. Name them descriptively: `audit-report-[pipeline]-[date].md`, `debug-report-[issue]-[date].md`, `generalization-audit-[pipeline]-[date].md`, etc.

For reference material on report schemas and extended checklists, see `references/checklists.md`.