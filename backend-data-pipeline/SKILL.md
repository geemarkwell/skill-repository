---
name: backend-data-pipeline
description: Data engineering skill for building reliable ETL pipelines, data extraction, transformation, ingestion, ML feature engineering, and backend data processing. Use this skill whenever building or modifying data pipelines, writing extraction or transformation scripts, processing files (Excel, CSV, JSON, XML, PDF, Word), building API clients for data ingestion, designing database schemas or migrations, setting up background jobs or scheduled tasks, building ML data pipelines or feature engineering, or any backend data work. Also trigger when the user says things like "build a pipeline", "extract data from", "process these files", "write an ingestion script", "set up ETL", "transform and load", "batch process", "parse and store", "write a script to pull data", or "ingest into the database". Also trigger for requests involving retries, rate limiting, circuit breakers, or pipeline observability. NOT for UI, frontend, or anything rendered in a browser.
metadata:
  domain: backend
  languages: project specific
---

# Backend Data Pipeline

Build data systems that are correct, resilient, and observable.

## Scope

**Use for:**
- Data extraction, transformation, loading (ETL/ELT)
- Database queries, schemas, migrations
- API clients and data ingestion
- Feature engineering and ML pipelines
- Data validation and quality checks
- Background jobs and scheduled tasks
- CLI tools and scripts

**NOT for:**
- User interfaces or visual components
- Browser-rendered code
- Styling, layout, or visual design
- User interaction patterns
- Anything the end user sees directly

## Boundary Rule

If the output renders in a browser for a human to interact with, this is the wrong skill.

## Stack Independence

This skill covers patterns, not implementations. The patterns — retry, circuit breaking, job state, validation, file processing safety — apply regardless of language or database. When implementing, use the project's actual stack and idioms. Don't default to Python or DuckDB because the reference files use them as examples. If the project is TypeScript, implement in TypeScript. If it's Rust, implement in Rust. The pattern is the requirement; the language is the project's choice.

Reference files include stack-specific implementation notes (marked as such). Load only the sections that match your project's infrastructure.

---

# The Problem

You will generate code that works in development. Your training has seen thousands of scripts, pipelines, and API clients. The patterns are strong.

You can follow best practices — add retries, write tests, log errors — and still produce systems that fail in production. Silent data corruption. Cascading failures. Undetected drift. "It worked on my machine" at scale.

This happens because production stresses are invisible in development. The gap between "runs successfully" and "runs reliably" is where failures hide.

The process below helps. But process alone doesn't guarantee reliability. You have to anticipate failure.

---

# Where Failures Hide

Failures don't announce themselves. They disguise as edge cases — the parts that feel like they'll "probably never happen."

**Network calls feel atomic.** Make request, get response, move on. But networks partition, APIs rate-limit, connections hang. A request without timeout, retry, and circuit breaker isn't reliable — it's lucky. If you're writing `requests.get(url)` without wrapping it, you're not engineering.

**Data feels trustworthy.** The API returns JSON, parse it, store it. But schemas drift, nulls appear where they shouldn't, duplicates sneak in. Data without validation isn't clean — it's unchecked. The question is: what happens when the 10,000th record violates assumptions the first 9,999 upheld?

**Processes feel isolated.** Run the script, update the database, done. But what if it crashes mid-write? What if another process is writing? What if the disk fills? A process without state tracking, locking, and graceful shutdown isn't complete — it's fragile.

**Logs feel sufficient.** Print errors, check logs later. But logs without structure can't be queried. Logs without correlation can't be traced. Logs without metrics can't alert. If you're writing `print(f"Error: {e}")`, you're not observing — you're hoping someone reads it.

**"Works locally" feels like validation.** But local has no latency, no concurrent users, no resource limits, no network partitions. The moment you stop asking "what if this fails?" is the moment production surprises you.

---

# Defense in Depth

Before writing code, understand the failure modes. Not abstractly — specifically for this system.

**What external dependencies exist?**
Every API, database, file system, message queue. Each is a failure point. What happens when each is unavailable? Slow? Returning errors? Returning wrong data?

**What state must be consistent?**
Identify the invariants. If a record exists in table A, must it exist in table B? If a job starts, must it complete or be marked failed? What happens on partial failure?

**What happens on restart?**
If the process dies mid-execution, what state is it in? Can it resume? Will it duplicate work? Corrupt data? How do you know what completed?

If you cannot answer these with specifics, stop. Investigate. Do not assume everything will succeed.

## Every System Must Handle

1. **Transient failures** — Network blips, temporary unavailability. Solution: Retry with exponential backoff + jitter.

2. **Persistent failures** — Downstream is down and staying down. Solution: Circuit breaker, graceful degradation.

3. **Partial failures** — Some records succeed, some fail. Solution: Job state tracking, atomic batches, resumability.

4. **Data corruption** — Invalid input, schema drift, duplicates. Solution: Validation on ingest, idempotency keys, constraints.

5. **Resource exhaustion** — Memory, connections, file descriptors. Solution: Limits, pooling, slowing intake when processing can't keep up.

---

# Operational Safety

## Single-Writer Constraints

Many databases (DuckDB, SQLite) allow only one writer. Many resources (files, locks) require exclusive access.

**Before any write operation:**
- Verify no other process holds the lock
- Use explicit locking mechanisms
- Handle lock contention gracefully

**Never assume** you're the only writer. Verify it.

## Process Management

**Long-running tasks:**
- Never run >30 second tasks in foreground
- Use background processes with progress tracking
- Implement graceful shutdown (handle SIGTERM)
- Track what you start, stop it before starting another

**State tracking:**
- Every job has a status: pending, in_progress, completed, failed
- Track attempts count for retry logic
- Store last error for debugging
- Enable resume from failure point

## Graceful Degradation

When dependencies fail:
- Return cached/stale data when appropriate
- Shed non-critical load
- Maintain core functionality
- Alert on degraded state

---

# File Processing Safety

When the data source is files (Excel, CSV, JSON, XML, PDF, Word) rather than APIs, the failure modes shift. Network resilience patterns don't help when the problem is a corrupted workbook or a file locked by another process.

## Atomic Writes

Writing directly to the output path means a crash mid-write produces a corrupted file. The pattern is write-to-temp-then-rename: write to a temporary file in the same directory, then rename atomically to the final path. Rename is atomic on the same filesystem. This guarantees every output file is either complete or doesn't exist — never half-written.

## Defensive Reads

Files from external sources can be corrupted, oversized, or in unexpected formats. Before processing:
- Verify the file can be opened without error
- Check file size against reasonable bounds before loading into memory
- Detect encoding before reading text content — don't assume UTF-8
- For Excel/Word: use read-only or streaming modes for large files to avoid loading the entire document into memory

A 50MB Excel file can consume significantly more RAM than its file size when fully loaded. Libraries often support streaming or read-only modes that reduce memory footprint.

## Encoding Safety

Files from different sources have different encodings. Silent mojibake (encoding corruption) is a data integrity failure the same as any other.

- Detect encoding explicitly rather than assuming
- Validate that decoded text doesn't contain replacement characters or byte sequences that indicate misinterpretation
- When writing output, specify encoding explicitly
- If the pipeline reads files from multiple sources, expect mixed encodings and handle per-file

## File Locking

Files open in other applications (e.g., Excel on Windows, another process reading/writing) can cause permission errors or read stale data. This is especially relevant in cross-environment setups (WSL accessing Windows files, network shares).

- Catch permission errors explicitly and report them with the file path
- Consider retry with delay for transient lock conflicts
- Never assume exclusive access to shared file systems

## Incremental Processing

When processing large file sets, you need to know which files need work and be able to resume from failure without restarting from scratch.

**Manifest-based tracking:** Maintain an explicit list of files with their processing status. Query the manifest to find unprocessed or failed items. This integrates with the state tracking pattern (pending/in_progress/completed/failed) from Process Management.

**Hash-based skip:** Content-hash each input, compare against already-processed hashes, skip matches. Handles renamed files and detects content changes even when modification times are unreliable.

**Timestamp-based skip:** Compare file modification time against last processing time. Simpler but fragile — files can change without mtime update, or mtime can change without content change. Use as a fast pre-filter, not the sole mechanism.

**Progress tracking for large sets:** When processing thousands of files, emit progress at regular intervals. A failure at file 2,847 of 3,000 should report exactly where it stopped and enable resume from that point.

---

# Data Correctness

## Validate Everything

**On ingest:**
- Schema validation (types, required fields, formats)
- Business rule validation (ranges, relationships, constraints)
- Deduplication checks (idempotency keys)

**On transform:**
- Row count validation (input vs output)
- Null checks on required fields
- Referential integrity

**On output:**
- Sanity checks (reasonable ranges, no obvious errors)
- Comparison to previous runs (dramatic changes = investigate)

## No Look-Ahead Bias

In time-series and ML pipelines:
- Rolling calculations must use `.shift(1)` or equivalent
- Never include future data in historical features
- Test by checking: could this value have been known at this timestamp?

## Idempotency

Operations should be safely re-runnable:
- Same input = same output
- Use idempotency keys for external calls
- Design for "at least once" delivery
- Handle duplicates gracefully

---

# Common Data Engineering Bugs

Recurring patterns in data pipeline bugs. When debugging or reviewing, scan this list to check whether your code is susceptible. Format follows the pipeline-audit skill's convention: symptom, common causes, prevention.

## Off-by-One in Ranges
**Symptom:** Missing the first or last item in a date range, row range, or batch boundary.
**Common causes:** Inclusive vs exclusive bounds mismatch. Fence-post errors in windowing.
**Prevention:** Be explicit about whether bounds are inclusive or exclusive. Test with single-item ranges and boundary values.

## Timezone Confusion
**Symptom:** Times shifted by hours, duplicate or missing records around DST transitions, dates off by one.
**Common causes:** Mixing naive and timezone-aware datetimes. Assuming UTC when data is local time. Storing timestamps without timezone info and inferring it later.
**Prevention:** Convert to timezone-aware representations at the boundary (ingest). Never compare naive and aware datetimes. Test with data spanning DST transitions.

## Float Comparison
**Symptom:** Equality checks fail on values that should match. Aggregations drift from expected totals.
**Common causes:** Using `==` on floating point values. Accumulating rounding errors across many additions. Currency stored as float instead of decimal/integer cents.
**Prevention:** Use epsilon-based comparison or decimal types for exact arithmetic. For currency, use integer cents or a decimal type. When aggregating, compare with tolerance.

## Silent Type Coercion
**Symptom:** Leading zeros stripped from IDs. Dates converted to serial numbers. Strings silently become numbers.
**Common causes:** Pandas/Excel reading "001234" as integer 1234. Excel storing dates as serial numbers. CSV readers inferring types incorrectly.
**Prevention:** Specify dtypes explicitly when reading data. Validate types after loading. For IDs and codes, always read as string.

## Encoding Round-Trip Corruption
**Symptom:** Garbled characters appearing several pipeline stages after the data was ingested correctly.
**Common causes:** Reading as one encoding, writing as another. Double-encoding (UTF-8 bytes interpreted as Latin-1, then re-encoded as UTF-8).
**Prevention:** Detect and record encoding at ingest. Specify encoding explicitly on every read and write. Validate output contains no replacement characters.

## Join Amplification
**Symptom:** Row count unexpectedly increases after a merge or join. Aggregations produce inflated totals.
**Common causes:** Many-to-many join when one-to-one or one-to-many was expected. Duplicate keys in the join table.
**Prevention:** Assert expected cardinality before joining. Check row count before and after joins. Deduplicate join keys if appropriate.

---

# Observability

## Structured Logging

**Format:** JSON always. Never unstructured text.

**Required fields:**
```
{
  "timestamp": "ISO-8601",
  "level": "INFO|WARN|ERROR",
  "service": "service-name",
  "trace_id": "correlation-id",
  "message": "what happened",
  "context": { "relevant": "data" }
}
```

**Never log:**
- Credentials, tokens, API keys
- PII without redaction
- High-cardinality data in hot paths

## Metrics

Track the RED signals:
- **Rate:** Operations per second
- **Errors:** Failures per second
- **Duration:** Latency percentiles (p50, p90, p99)

Never track averages — they hide outliers.

## Alerting

| Condition | Severity | Action |
|-----------|----------|--------|
| Success rate < 95% for 5 min | Warning | Investigate |
| Success rate < 80% for 5 min | Critical | Pause, intervene |
| p99 latency > threshold | Warning | Check resource contention |
| Circuit breaker open | Critical | Downstream is down |

---

# The Mandate

**Before calling code complete, ask yourself:**

"If this runs for a week unattended, what will break?"

That thing you just thought of — handle it first.

Your first implementation probably only handles the success case — when the network responds, the data is valid, and nothing crashes. That's normal. The work is handling all the failure cases before production finds them.

## The Checks

Run these before considering work complete:

- **The failure test:** What happens when each external call fails? Times out? Returns garbage? If you haven't handled it, you haven't finished.

- **The restart test:** Kill the process mid-execution. What state is it in? Can it recover? Will it duplicate work?

- **The scale test:** What happens with 10x the data? 100x? Where are the bottlenecks? Memory? Connections? Time?

- **The observability test:** If this fails at 3am, can you debug it from logs alone? Do you have the context you need?

- **The idempotency test:** Run it twice with the same input. Is the output correct? Are there duplicates?

If any check fails, iterate before shipping.

---

# Workflow

## Handling Ambiguity

Ambiguous instructions are where silent failures start. If you guess wrong about what the user wants, you'll build something that looks correct but does the wrong thing — and the user won't know until they've invested time downstream.

When you encounter unclear requirements — vague scope, missing parameters, undefined success criteria — pause and ask before proceeding. A 30-second clarification question is cheaper than a 30-minute wrong implementation.

That said, use judgment. If the context makes the answer obvious (file format is in the extension, directory structure implies the pipeline stage, the project's existing patterns show the convention), don't ask questions you can answer yourself. The goal is to avoid silent assumptions about things that matter, not to require explicit permission for everything.

## Communication

Be direct. State findings and recommendations clearly.

**Never say:** "Let me check if there might be issues..."

**Instead:** "This needs retry logic on the API call. Adding exponential backoff with 3 attempts."

## Before Writing Code

0. **Profile the data** — Before designing the pipeline, sample the actual inputs. What formats exist? What's the variance in structure? Where are the edge cases? Run basic stats: file count, size distribution, format variants. Open 5-10 representative files and examine them. The pipeline design should be informed by what the data actually looks like, not what you assume it looks like.
1. **Identify dependencies** — What external systems does this touch?
2. **Map failure modes** — What can go wrong with each?
3. **Define state** — What must be tracked for resumability?
4. **Plan observability** — What metrics and logs are needed?

## After Writing Code

1. **Test failure paths** — Simulate network errors, invalid data, resource exhaustion
2. **Run the checks** — Failure, restart, scale, observability, idempotency
3. **Document operations** — How to monitor, how to recover, what alerts mean

### Testing Data Pipelines

Knowing what to test and how matters as much as having tests.

**Fixture-based testing:** Save a known input file and its expected output. Run the pipeline on the input, diff against expected. This is the most valuable test pattern for extraction and transformation pipelines — it catches regressions concretely.

**Property-based testing:** For transforms, assert invariants rather than specific values. "Row count is preserved." "All dates are valid." "No null values in required fields." "Output total equals sum of parts." These catch unexpected violations without requiring a complete expected-output fixture.

**Corruption injection:** Deliberately feed malformed inputs — truncated files, wrong encoding, missing columns, empty files, oversized files — and verify the pipeline handles them gracefully. The goal is graceful failure (clear error, no data corruption), not successful processing.

**Regression testing:** When a bug is found and fixed, add the failing input to the test fixtures. This prevents the same bug from recurring and builds a library of edge cases over time.

---

# Patterns Quick Reference

These are abbreviated summaries. For implementation details, code examples, and sourced theory, see `references/robust-ingestion.md`. For production infrastructure configuration, see `references/production-config.md`.

## Retry with Backoff

```
delay = min(base * 2^attempt, max_delay)
jitter = random(0, delay)
sleep(jitter)
```

## Circuit Breaker States

```
CLOSED (normal) → failures exceed threshold → OPEN (failing fast)
OPEN → timeout expires → HALF-OPEN (testing)
HALF-OPEN → test succeeds → CLOSED
HALF-OPEN → test fails → OPEN
```

## Job State Machine

```
PENDING → IN_PROGRESS → COMPLETED
                     ↘ FAILED (attempts >= max)
                     ↘ PENDING (attempts < max, retry)
```

## Timeout Hierarchy

```
Client > Server > Database
```

Upstream waits longer than downstream.

---

# Reference Files

The reference files contain deeper treatment of patterns summarized above. Load them selectively based on what the current task needs.

- `references/robust-ingestion.md` — Rate limiting, retries, circuit breakers, job state management, API client patterns, file processing pipelines, DuckDB patterns. Contains both universal patterns and stack-specific implementation notes (marked). Skip the implementation notes if the project uses a different stack.
- `references/production-config.md` — Database tuning, connection pooling, caching, runtime tuning, resilience patterns, security, containers, Kubernetes, observability, kernel tuning. Organized by technology with stack-specific subsections. Consult only the sections matching your project's infrastructure.


