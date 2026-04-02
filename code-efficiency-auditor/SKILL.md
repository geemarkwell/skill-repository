---
name: code-efficiency-auditor
description: Audit Python and FastAPI codebases for performance bottlenecks, scalability risks, and code quality issues, producing a prioritized markdown report with concrete recommendations. Use when optimizing Python code, reviewing FastAPI endpoints for efficiency, investigating slow endpoints, latency, memory leaks, N+1 queries, blocking I/O, async anti-patterns, or preparing a service for enterprise-scale traffic. Also use when a generic request like "review my code" or "make this faster" is clearly about a Python or FastAPI codebase.
---

# Code Efficiency Auditor

## Overview

Perform a deep efficiency audit of a Python or FastAPI codebase. Identify real bottlenecks, prioritize findings by production impact, and produce a report the developer can act on immediately.

Focus on issues that matter under load: blocking work in request paths, expensive queries, poor concurrency patterns, unbounded memory growth, and architectural choices that become costly as traffic and data volume increase. Skip style nitpicks unless they affect performance, scalability, reliability, or maintainability in a measurable way.

## Workflow

### 1. Inventory the codebase first

Read the project structure before making recommendations. Identify:

- Entry points such as `main.py`, app factories, routers, and startup/lifespan hooks
- Database layers such as SQLAlchemy models, repositories, raw SQL, migrations, and session management
- External service calls such as HTTP clients, queues, storage APIs, and third-party SDKs
- Background tasks, schedulers, middleware, and caching layers
- Dependency injection patterns and shared dependencies
- Configuration loading and environment handling

Use that inventory to decide which parts of the codebase matter most for runtime efficiency. Do not recommend patterns that conflict with the actual architecture you find.

### 2. Read the audit checklist

Read `references/audit-checklist.md` before the main analysis. Use it as the baseline checklist, but apply judgment. Not every item will apply to every service.

Prioritize review in this order:

1. Critical request-path performance and event-loop health
2. Database and caching behavior
3. Concurrency and external I/O
4. Architectural and code-quality issues with performance implications
5. Reliability, validation, and resilience concerns

### 3. Analyze the codebase

For every meaningful issue:

- Record the file and line reference
- Describe the concrete problem
- Explain why it matters at scale
- Recommend a specific fix
- Estimate effort as `Low`, `Medium`, or `High`

Tailor findings to FastAPI and async Python behavior. Treat blocking calls inside `async def` handlers and dependencies as high-priority findings when they are on active request paths.

Do not invent problems. If an area is clean, say so implicitly by omission or explicitly in the summary when it builds confidence in the report.

## Report Output

Write the final report to `efficiency-audit-report.md` in the requested output directory. If the task does not define an output directory, default to the current working directory and state that assumption in the report.

Use exactly this structure:

```markdown
# Efficiency Audit Report

## Summary
One paragraph: overall health of the codebase, the most critical finding, and estimated effort to address the top issues.

## Critical Findings
Issues that will cause problems under production load. Each finding includes:
- **What**: Description of the issue
- **Where**: File and line reference
- **Why it matters**: Concrete impact
- **Fix**: Specific code change or pattern to adopt
- **Effort**: Low / Medium / High

## Performance Findings
Optimizations that improve speed, memory, or computational efficiency.

## Scalability Findings
Patterns that limit horizontal scaling or degrade under concurrent load.

## Code Quality Findings
DRY violations, SOLID principle issues, and architectural concerns that increase maintenance cost or bug risk.

## Security & Reliability Findings
Error handling gaps, input validation issues, and resilience concerns.

## Quick Wins
A short list of the easiest, highest-impact changes that can be done quickly.

## Recommended Prioritization
A numbered action plan ordered by impact and effort.
```

## Reporting Standards

Be specific. Avoid generic advice like "consider caching." Instead, point to the exact function, query, dependency, or endpoint and describe the concrete change.

Quantify impact when the code supports a reasonable estimate. Example patterns:

- Event-loop blocking duration per request
- Query-count reduction from eliminating N+1 behavior
- Complexity reduction such as `O(n^2)` to `O(n)`
- Memory reductions from pagination, streaming, or bounded caches

Tailor recommendations to the execution context:

- Distinguish request-path work from background-task work
- Distinguish CPU-bound bottlenecks from I/O-bound bottlenecks
- Distinguish sync FastAPI endpoints in thread pools from async endpoints on the event loop

Acknowledge strengths when relevant. If the database access layer is already disciplined or the async client reuse pattern is sound, note that briefly in the summary rather than manufacturing filler findings.

## Boundaries

Optimize for signal, not volume. A short report with five high-confidence findings is better than a long report full of speculation.

Prefer primary evidence from the codebase. If behavior is uncertain because a dependency, query plan, or deployment detail is missing, say that you are inferring risk from the code structure.
