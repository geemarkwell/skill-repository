---
name: prd-generator
description: >
  Generate structured PRD (Product Requirements Document) spec files in Markdown
  that a coding agent can use to implement features in a local codebase. Use this
  skill whenever the user wants to plan, spec out, define, or document what they
  want to build before handing it off to an agent. Trigger on phrases like "write
  a PRD", "spec this out", "help me plan this feature", "I need implementation
  instructions", "create a requirements doc", "write up what I need to build",
  "draft an implementation plan", or any time the user describes functionality
  they want implemented locally and needs a structured document for their agent.
  Also trigger when the user says things like "I want to build X", "I need to
  add Y to my app", or "help me think through how to implement Z" if they are
  describing work for a local codebase and want a deliverable document. Do not
  trigger for in-conversation code help, debugging, or when the user wants Codex
  to write the code directly.
---

# PRD Generator

Produce implementation-ready PRD documents in Markdown. These documents are
meant to be handed off to a coding agent working in the user's local codebase.
Define what to build and how it should behave. Do not prescribe file placement
or framework choices unless the user explicitly asks for that level of detail.

## Core Workflow

### 1. Interview the User

Do not jump straight to the PRD. Start by understanding what the user wants to
build. Ask clarifying questions to close the most important gaps before writing.

Your interview should uncover:

- What they are building: the feature, change, or workflow in plain terms, who
  it is for, and what problem it solves.
- Scope boundaries: what is in scope now, what is out of scope, and what should
  be deferred.
- Key behaviors: happy-path behavior plus the most important user-facing and
  system-facing outcomes.
- Integration points: existing systems, APIs, databases, services, or jobs this
  work depends on or modifies.
- Constraints: performance, security, compliance, access control, rollout, or
  other non-functional requirements.

Use judgment about how many questions to ask. For a small, well-defined feature,
2 or 3 targeted questions may be enough. For something vague or broad, ask a
larger batch. Prefer asking in a batch instead of dragging the user through many
round trips.

### 2. Assess Scope

Before writing, decide whether the request is too large for a single PRD. A good
PRD should be focused enough that an agent can execute it in one session without
losing context or collapsing multiple independent problems together.

Signs the scope is too large:

- Multiple independent features bundled together
- Several distinct user flows with little shared implementation
- Work that naturally spans many unrelated areas of the codebase
- A draft that naturally breaks into separate phases

If the scope is too large, say so and propose a clean split. Let the user decide
how to split it, then write each PRD separately.

### 3. Write the PRD

Produce a single `.md` file using this structure. Every section is required
unless marked optional.

```markdown
# [Feature/Change Name]

## Overview
A concise summary of what this feature does and why it matters. Keep this to
2 to 4 sentences.

## Background & Context
Explain why this is being built and what problem exists today. Include only the
context needed to guide correct implementation decisions.

## Requirements

### Functional Requirements
List the behaviors the implementation must support as clear, testable statements.
Group related requirements under subheadings when it improves readability.

### Non-Functional Requirements
Document performance, security, scalability, accessibility, reliability, or
compliance requirements only when they materially affect implementation.

## Architecture Overview
Describe the high-level shape of the solution:
- Key components or modules and what each is responsible for
- How data moves through the system
- Integration points with existing code or external services
- Any new abstraction that needs to exist and why

## Task Breakdown
Provide an ordered implementation plan. For each task, include:
- What to do
- Why it matters or what it unblocks
- Any dependencies on earlier tasks

## Acceptance Criteria
Provide a checklist of observable conditions that must all be true for the work
to be complete.

## Edge Cases & Error Handling
List edge cases and failure modes with the expected behavior for each one.

## Out of Scope
List what this PRD explicitly does not cover.

## Open Questions (optional)
Record unresolved decisions the user chose to defer.
```

## Writing Principles

### Be Specific, Not Prescriptive

Define what the system should do, not the exact code-level implementation. Favor
behavioral requirements over framework or file-organization instructions.

### Write for an Agent

Skip product-management fluff. Focus on what to build, how it should behave, and
what completion looks like.

### Be Concise but Complete

Every sentence should earn its place. Do not pad sections with generic filler,
but do not omit details that would cause implementation ambiguity.

### Use Examples When Helpful

When a requirement is subtle or easy to misread, include a short example showing
input and expected output or state transition.

## Quality Bar

Make sure the PRD:

- Is specific enough that an implementation agent can act without guessing
- Separates requirements from implementation details
- Covers happy path, failure path, and important boundaries
- States what is out of scope so the agent does not expand the work
- Contains acceptance criteria that a reviewer can verify directly

## Output

Save the PRD as a descriptive Markdown file name such as
`user-authentication-prd.md` or `webhook-retry-logic-prd.md`.

If the user specifies a location, use it. Otherwise, place the file in the
current working directory or an obvious docs folder in the workspace if one
already exists.

After presenting the file, ask whether anything should be adjusted before they
hand it off to their coding agent.
