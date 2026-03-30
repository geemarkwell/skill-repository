# Robust Data Ingestion Reference

> Patterns for reliable API clients, data pipelines, and file processing.

## Table of Contents

1. [Rate Limiting](#1-rate-limiting) — Token bucket, adaptive client-side throttling
2. [Retry Strategies](#2-retry-strategies) — Backoff, jitter, budgets
3. [Circuit Breaker](#3-circuit-breaker) — States, transitions, implementation
4. [Job State Management](#4-job-state-management) — Outbox pattern, state machines
5. [API Client Patterns](#5-api-client-patterns) — Session management, pagination, async
6. [File Processing Pipelines](#6-file-processing-pipelines) — Batch file ingestion, checkpointing, error isolation
7. [DuckDB Patterns](#7-duckdb-patterns) — Single writer, thread safety, batch inserts
8. [Observability](#8-observability) — Metrics, alerting, lightweight tracking
9. [Defense in Depth](#9-defense-in-depth) — Layered resilience
10. [Library Reference](#10-library-reference)

---

## 1. Rate Limiting

### Token Bucket Algorithm

A container holding tokens. Tokens added at a fixed rate. Each request consumes one
token. Empty bucket = wait.

```
tokens(t) = min(capacity, tokens(t-1) + (t - t_last) * rate)
```

Burst handling via bucket capacity. Sustained rate via fill rate. Global coordination
across workers.

**Source:** Stripe Engineering, "Scaling your API with rate limiters" (2017)

### Rate Limiter Types (Stripe Production)

| Type | Purpose |
|------|---------|
| Request Rate | Limit requests/second per user |
| Concurrent Request | Limit in-flight requests |
| Fleet Usage Load Shedder | Reserve capacity for critical requests |
| Worker Utilization Load Shedder | Protect individual workers |

### Adaptive Client-Side Throttling

When you don't control the server's rate limits, track accept/reject ratio over a
sliding window and pre-emptively back off:

```
P(reject) = max(0, (requests - K * accepts) / (requests + 1))
```

K = 2.0 typically. Drop requests client-side before they hit the server, reducing
load on an already-stressed backend.

**Source:** Google SRE Book, Chapter 21

> **Python Implementation**

```python
import time
import threading

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate          # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, timeout: float = 30.0) -> bool:
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                wait = (1 - self.tokens) / self.rate
            if time.monotonic() + wait > deadline:
                return False
            time.sleep(min(wait, 0.1))

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
```

---

## 2. Retry Strategies

### Exponential Backoff with Full Jitter

Pure exponential backoff creates synchronized retry bursts when many clients fail
simultaneously. Full jitter spreads retries uniformly across the backoff window.

```
delay = random.uniform(0, min(cap, base * 2^attempt))
```

**Source:** AWS Architecture Blog, "Exponential Backoff and Jitter" (2015, updated 2023)

### Retry Budgets

Retries amplify load on failing systems. Constrain them:

- **Per-request:** Max 3 attempts (1 original + 2 retries)
- **Per-client:** No more than 10% of total requests should be retries over any
  sliding window. If retry ratio exceeds budget, stop retrying and fail fast.

**Source:** Google SRE Book, Chapter 21

### What to Retry

| Status | Retry? | Reason |
|--------|--------|--------|
| 429 Too Many Requests | Yes | Respect `Retry-After` header if present |
| 500 Internal Server Error | Yes | Transient server issue |
| 502, 503, 504 | Yes | Infrastructure / gateway issues |
| 408 Request Timeout | Yes | Server timed out |
| Connection errors | Yes | Network blip |
| 400 Bad Request | No | Your request is wrong, retrying won't help |
| 401, 403 | No | Auth issue, retrying won't help |
| 404 | No | Resource doesn't exist |
| 422 | No | Validation failure |

> **Python Implementation**

```python
import random
import time
from typing import TypeVar, Callable

T = TypeVar("T")

def retry_with_backoff(
    fn: Callable[[], T],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable: tuple[type[Exception], ...] = (Exception,),
) -> T:
    for attempt in range(max_attempts):
        try:
            return fn()
        except retryable as e:
            if attempt == max_attempts - 1:
                raise
            cap = min(base_delay * (2 ** attempt), max_delay)
            delay = random.uniform(0, cap)  # full jitter
            time.sleep(delay)
    raise RuntimeError("unreachable")
```

---

## 3. Circuit Breaker

Wraps remote calls, monitors failures, fails fast when a backend is down. Prevents
cascading failures and gives the downstream time to recover.

### States and Transitions

```
CLOSED (normal) ──failures exceed threshold──▶ OPEN (failing fast)
                                                   │
                                           timeout expires
                                                   │
                                                   ▼
                                         HALF-OPEN (testing)
                                          │              │
                                   test succeeds    test fails
                                          │              │
                                          ▼              ▼
                                       CLOSED          OPEN
```

**Source:** Martin Fowler, "Circuit Breaker" (2014)

### Configuration Guidelines

| Parameter | Recommendation | Why |
|---|---|---|
| Failure threshold | 5-10 failures or 50% failure rate | Low enough to react fast, high enough to avoid flapping |
| Reset timeout | 10-60s | Time for downstream to recover |
| Half-open test count | 1-3 requests | Enough to confirm recovery without flooding |
| Sliding window | 50-100 calls (count-based) | Count-based is deterministic; time-based gets skewed by low traffic |

> **Python Implementation (pybreaker)**

```python
import pybreaker

# Open after 5 failures, wait 30s before testing recovery
breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    exclude=[
        pybreaker.CircuitBreakerError,
    ],
)

@breaker
def call_api(url: str) -> dict:
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()
    return response.json()

# Usage — catch the circuit-open case
try:
    data = call_api("https://api.example.com/data")
except pybreaker.CircuitBreakerError:
    data = get_cached_data()  # Circuit is open — use fallback
except httpx.HTTPStatusError:
    handle_error()  # Request went through but failed
```

---

## 4. Job State Management

### The Outbox Pattern

Store job state in the database as part of the same transaction as work. This gives
you atomic state transitions, queryable failed jobs, resumability, and audit trail.

**Source:** Chris Richardson, Microservices.io

### The Contract

The state store must satisfy:
- Every work unit has a unique ID
- Status is always one of: pending, in_progress, completed, failed
- Attempt count is tracked for retry decisions
- Last error is stored for debugging
- The state store is updated atomically with the work itself

### Implementation Varies by Stack

- **SQL database:** Job tracking table with status column
- **File-based:** Manifest file (JSON/CSV) alongside outputs
- **In-memory with persistence:** Dict/map checkpointed to disk periodically

### State Machine

```
PENDING ──▶ IN_PROGRESS ──▶ COMPLETED
                │
                ├──(attempts < max)──▶ PENDING  (retry)
                └──(attempts >= max)──▶ FAILED  (give up)
```

> **SQL Schema**

```sql
CREATE TABLE ingestion_jobs (
    job_id      VARCHAR PRIMARY KEY,
    entity_type VARCHAR NOT NULL,
    entity_id   VARCHAR NOT NULL,
    status      VARCHAR NOT NULL DEFAULT 'pending',
        -- 'pending', 'in_progress', 'completed', 'failed', 'skipped'
    attempts    INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_error  TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at  TIMESTAMP,
    completed_at TIMESTAMP,
    metadata    JSON
);

-- Index for finding work
CREATE INDEX idx_jobs_pending ON ingestion_jobs (status) WHERE status = 'pending';
```

> **Python Implementation**

```python
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def run_pending_jobs(conn, process_fn, batch_size: int = 50):
    """Pick up pending jobs, process them, track state."""
    jobs = conn.execute("""
        UPDATE ingestion_jobs
        SET status = 'in_progress',
            attempts = attempts + 1,
            started_at = ?
        WHERE job_id IN (
            SELECT job_id FROM ingestion_jobs
            WHERE status = 'pending'
            ORDER BY created_at
            LIMIT ?
        )
        RETURNING *
    """, [datetime.now(timezone.utc), batch_size]).fetchall()

    for job in jobs:
        try:
            result = process_fn(job)
            conn.execute("""
                UPDATE ingestion_jobs
                SET status = 'completed', completed_at = ?
                WHERE job_id = ?
            """, [datetime.now(timezone.utc), job["job_id"]])
        except Exception as e:
            logger.error("Job %s failed (attempt %d): %s",
                         job["job_id"], job["attempts"], e)
            new_status = (
                "pending" if job["attempts"] < job["max_attempts"]
                else "failed"
            )
            conn.execute("""
                UPDATE ingestion_jobs
                SET status = ?, last_error = ?
                WHERE job_id = ?
            """, [new_status, str(e), job["job_id"]])
```

---

## 5. API Client Patterns

### Session Management

Reuse connections, set global timeouts, and configure retry behavior in one place.
The pattern applies regardless of HTTP library — create a configured client once,
use it everywhere.

> **Python Implementation (httpx)**

```python
import httpx

def build_client(
    base_url: str,
    timeout: float = 30.0,
    headers: dict | None = None,
) -> httpx.Client:
    return httpx.Client(
        base_url=base_url,
        timeout=httpx.Timeout(timeout, connect=5.0),
        headers=headers or {},
        limits=httpx.Limits(
            max_connections=20,
            max_keepalive_connections=10,
            keepalive_expiry=30.0,
        ),
    )
```

### Pagination (Cursor-Based)

Most APIs paginate. Build a generic iterator that handles cursor-based pagination:

> **Python Implementation**

```python
from typing import Iterator

def paginate(
    client: httpx.Client,
    path: str,
    params: dict | None = None,
    page_key: str = "data",
    cursor_key: str = "next_cursor",
    cursor_param: str = "cursor",
    max_pages: int = 1000,
) -> Iterator[list[dict]]:
    params = dict(params or {})
    for _ in range(max_pages):
        resp = client.get(path, params=params)
        resp.raise_for_status()
        body = resp.json()

        page = body.get(page_key, [])
        if page:
            yield page

        cursor = body.get(cursor_key)
        if not cursor:
            break
        params[cursor_param] = cursor
```

### Pagination (Offset-Based)

> **Python Implementation**

```python
def paginate_offset(
    client: httpx.Client,
    path: str,
    params: dict | None = None,
    page_key: str = "results",
    page_size: int = 100,
    max_records: int = 100_000,
) -> Iterator[list[dict]]:
    params = {**(params or {}), "limit": page_size, "offset": 0}
    total = 0
    while total < max_records:
        resp = client.get(path, params=params)
        resp.raise_for_status()
        page = resp.json().get(page_key, [])
        if not page:
            break
        yield page
        total += len(page)
        if len(page) < page_size:
            break
        params["offset"] += page_size
```

### Async Client

For high-concurrency ingestion (many independent API calls), use async with
controlled concurrency. Always use a semaphore — unbounded `gather()` will overwhelm
both your machine and the target API.

> **Python Implementation**

```python
import asyncio
import httpx

async def fetch_all(
    urls: list[str],
    max_concurrent: int = 10,
    timeout: float = 30.0,
) -> tuple[list[dict], list[Exception]]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(client: httpx.AsyncClient, url: str):
        async with semaphore:
            resp = await client.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()

    async with httpx.AsyncClient() as client:
        tasks = [fetch_one(client, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]
    return successes, failures
```

---

## 6. File Processing Pipelines

For pipelines that process many files (e.g., extracting data from thousands of
documents), the key challenges are: tracking which files succeeded/failed, isolating
errors so one bad file doesn't kill the batch, and enabling resume after interruption.

### File Job Tracker

> **Python Implementation**

```python
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json

class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class FileJob:
    path: str
    status: FileStatus = FileStatus.PENDING
    error: str | None = None
    attempts: int = 0

@dataclass
class BatchTracker:
    jobs: dict[str, FileJob] = field(default_factory=dict)
    checkpoint_path: Path = Path("batch_checkpoint.json")

    def add_files(self, paths: list[str]):
        for p in paths:
            if p not in self.jobs:
                self.jobs[p] = FileJob(path=p)

    def pending(self) -> list[FileJob]:
        return [j for j in self.jobs.values() if j.status == FileStatus.PENDING]

    def mark(self, path: str, status: FileStatus, error: str | None = None):
        job = self.jobs[path]
        job.status = status
        job.error = error
        if status == FileStatus.FAILED:
            job.attempts += 1

    def save_checkpoint(self):
        data = {k: {"status": v.status, "error": v.error, "attempts": v.attempts}
                for k, v in self.jobs.items()}
        self.checkpoint_path.write_text(json.dumps(data, indent=2))

    def load_checkpoint(self) -> bool:
        if not self.checkpoint_path.exists():
            return False
        data = json.loads(self.checkpoint_path.read_text())
        for path, state in data.items():
            self.jobs[path] = FileJob(
                path=path,
                status=FileStatus(state["status"]),
                error=state.get("error"),
                attempts=state.get("attempts", 0),
            )
        return True

    def summary(self) -> dict[str, int]:
        from collections import Counter
        return dict(Counter(j.status.value for j in self.jobs.values()))
```

### Error-Isolated Batch Processing

Process each file independently so failures don't cascade:

> **Python Implementation**

```python
import logging

logger = logging.getLogger(__name__)

def process_batch(
    tracker: BatchTracker,
    process_fn,
    max_attempts: int = 2,
    checkpoint_every: int = 25,
):
    pending = tracker.pending()
    logger.info("Processing %d files", len(pending))

    for i, job in enumerate(pending):
        if job.attempts >= max_attempts:
            tracker.mark(job.path, FileStatus.SKIPPED,
                         f"Max attempts ({max_attempts}) exceeded")
            continue

        try:
            tracker.mark(job.path, FileStatus.PROCESSING)
            process_fn(job.path)
            tracker.mark(job.path, FileStatus.COMPLETED)
        except Exception as e:
            logger.error("Failed processing %s: %s", job.path, e)
            tracker.mark(job.path, FileStatus.FAILED, str(e))

        if (i + 1) % checkpoint_every == 0:
            tracker.save_checkpoint()
            logger.info("Checkpoint at %d/%d — %s", i + 1, len(pending),
                        tracker.summary())

    tracker.save_checkpoint()
    logger.info("Batch complete: %s", tracker.summary())
```

---

## 7. DuckDB Patterns

> Load this section only when the project uses DuckDB. These are stack-specific
> implementations of the universal patterns above.

### Single Writer Constraint

DuckDB allows only one writer process. Solutions:
1. Single writer process for all writes
2. Connection pooling within a single process
3. Write queue with single consumer thread

### Thread Safety

Do NOT write from multiple threads concurrently within a single process. Use a
producer-consumer pattern:

```python
from queue import Queue
from threading import Thread
from dataclasses import dataclass
import duckdb
import polars as pl

@dataclass
class WriteJob:
    table: str
    data: pl.DataFrame

def writer_loop(queue: Queue, db_path: str):
    """Single writer thread — holds the only DB connection for writes."""
    conn = duckdb.connect(db_path)
    while True:
        job = queue.get()
        if job is None:  # shutdown signal
            break
        try:
            conn.execute(f"INSERT INTO {job.table} SELECT * FROM job.data")
        except Exception as e:
            logging.error("Write failed for %s: %s", job.table, e)
        finally:
            queue.task_done()
    conn.close()

# Setup
write_queue: Queue[WriteJob | None] = Queue(maxsize=100)
writer = Thread(target=writer_loop, args=(write_queue, "data.duckdb"), daemon=True)
writer.start()

# Workers put jobs on the queue — never touch DB directly
write_queue.put(WriteJob(table="results", data=transformed_df))

# Shutdown
write_queue.put(None)
writer.join()
```

**Source:** DuckDB Documentation

### Batch Inserts

Always bulk insert. Row-by-row insertion is orders of magnitude slower.

```python
# Good — single bulk insert from DataFrame
conn.execute("INSERT INTO target SELECT * FROM df")

# Good — bulk insert from Parquet
conn.execute("INSERT INTO target SELECT * FROM read_parquet('data/*.parquet')")

# Bad — row-by-row
for row in rows:
    conn.execute("INSERT INTO target VALUES (?)", row)
```

### Checkpointing for Crash Recovery

For long-running jobs, periodically force WAL checkpoint:

```python
conn.execute("CHECKPOINT")
```

Flushes the write-ahead log to the main database file, ensuring data persists
even if the process crashes after the checkpoint.

### Job State Tracking

```sql
CREATE TABLE ingestion_jobs (
    job_id VARCHAR PRIMARY KEY,
    entity_type VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,  -- 'pending', 'in_progress', 'completed', 'failed'
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Metrics Storage

```sql
CREATE TABLE pipeline_metrics (
    run_id          VARCHAR,
    stage           VARCHAR,
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    records_in      INTEGER,
    records_out     INTEGER,
    records_failed  INTEGER,
    retries         INTEGER,
    p50_latency_ms  FLOAT,
    p99_latency_ms  FLOAT
);
```

---

## 8. Observability

### Key Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| `requests_total` | Counter | Total API calls |
| `requests_failed` | Counter | Failed calls |
| `requests_retried` | Counter | Retry attempts |
| `request_latency_seconds` | Histogram | Response time distribution |
| `success_rate` | Gauge | Rolling success percentage |
| `circuit_breaker_state` | Gauge | 0=closed, 1=open |
| `files_processed` | Counter | Files completed |
| `files_failed` | Counter | Files that errored |

### Alert Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| Success rate < 95% for 5 min | Warning | Investigate |
| Success rate < 80% for 5 min | Critical | Pause ingestion |
| p99 latency > 30s | Warning | Reduce rate |
| Circuit breaker open | Critical | Backend down |
| Batch failure rate > 10% | Warning | Check error log, common failure mode |

**Source:** Google SRE Book, Chapter 6

---

## 9. Defense in Depth

Layer protections so no single failure mode brings down the pipeline:

```
Layer 1: Global Rate Limiter (Token Bucket)
    └── Prevents overwhelming upstream APIs

Layer 2: Circuit Breaker (per endpoint)
    └── Fails fast when a dependency is down

Layer 3: Retry with Jitter (per request)
    └── Handles transient failures

Layer 4: Job State Tracking (per record/file)
    └── Enables resume, prevents duplicates

Layer 5: Metrics & Alerting
    └── Detects degradation before it becomes an outage
```

---

## 10. Library Reference

| Library | Purpose | When to use |
|---------|---------|-------------|
| `httpx` | HTTP client (sync + async) | API calls, replaces requests |
| `tenacity` | Flexible retry decorator | When retry logic is complex |
| `pybreaker` | Circuit breaker | Wrapping unreliable endpoints |
| `aiolimiter` | Async rate limiting | Async pipelines |
| `polars` | DataFrames | Data transformation, faster than pandas |
| `duckdb` | Embedded analytics DB | Local analytical queries, Parquet I/O |

### Sources

| Source | Key Contribution |
|--------|------------------|
| AWS Architecture Blog | Jitter algorithm comparison |
| Stripe Engineering | Rate limiter taxonomy |
| Google SRE Book Ch.21 | Client-side throttling, retry budgets |
| Martin Fowler | Circuit breaker pattern |
| Microservices.io | Outbox pattern |
| DuckDB Docs | Single-writer, WAL behavior |
