---
name: create-plan
description: Turn a user prompt into a single actionable implementation plan delivered in the final assistant message. Use when Codex should inspect a codebase or repo context, stay read-only, and produce a scoped plan with ordered action items, validation steps, and rollout or risk coverage instead of making code changes.
---

# Create Plan

Turn the user's request into one execution-ready plan. Remain read-only for the entire workflow: inspect context, read files, and reason about likely changes, but do not create, modify, or delete files.

## Workflow

### 1. Scan context quickly

Read the smallest set of materials needed to plan responsibly:

- `README.md`
- `docs/` entries that look directly relevant
- `CONTRIBUTING.md`
- `ARCHITECTURE.md`
- likely touchpoints for the requested work

Identify:

- primary language and framework
- likely modules or directories involved
- test and validation commands
- deployment, migration, or rollout shape
- explicit constraints from the repo or request

Do not over-research. Stop once the plan can be specific and defensible.

### 2. Ask follow-ups only if blocked

Ask at most 1 or 2 follow-up questions, and only when a responsible plan depends on missing information that cannot be inferred from local context.

Prefer concise multiple-choice questions when you must ask. If uncertainty is not blocking, make a reasonable assumption and continue.

### 3. Define scope before steps

Make scope explicit and narrow:

- what work is included
- what work is excluded
- any assumptions that keep the plan bounded

If the request is broad, convert it into the smallest practical implementation slice instead of planning an open-ended rewrite.

### 4. Build ordered action items

Create 6 to 10 checklist items by default. Keep them atomic, concrete, and ordered from discovery to implementation to validation to rollout.

Checklist item rules:

- start with a verb
- mention likely files, modules, or commands when helpful
- avoid vague placeholders like "handle backend"
- avoid implementation snippets
- include at least one validation or test step
- include an edge-case, migration, or rollout-risk step when relevant

Good patterns:

- `Add request parsing in src/...`
- `Refactor the service layer in app/...`
- `Verify behavior with npm test`
- `Ship behind a feature flag`

### 5. Output exactly one plan

Return only the plan in the final assistant message. Do not preface it with commentary, reasoning, or meta explanation.

Use this template exactly:

# Plan

<1-3 sentences: what we're doing, why, and the high-level approach.>

## Scope
- In:
- Out:

## Action items
[ ] <Step 1>
[ ] <Step 2>
[ ] <Step 3>
[ ] <Step 4>
[ ] <Step 5>
[ ] <Step 6>

## Open questions
- <Question 1>
- <Question 2>
- <Question 3>

## Output constraints

- Keep the opening paragraph to 1 to 3 sentences.
- Fill `## Open questions` only when real unknowns remain; otherwise write `- None.`
- Keep the plan implementation-agnostic unless naming files or commands makes the step meaningfully more actionable.
- If rollout is irrelevant, use the later checklist items for validation and edge cases instead.
- Do not include code blocks unless the user explicitly asks for them.
- Do not write or update files while producing the plan.
