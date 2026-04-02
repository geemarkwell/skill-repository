# Audit Checklist - Python / FastAPI

This is the detailed checklist of patterns to look for, organized by priority. Not every item will apply to every codebase; use judgment about what is relevant given the project's architecture and scale.

## Table of Contents
1. Performance (Speed, Memory, Big-O)
2. Scalability (Concurrency, Caching, DB Patterns)
3. Code Quality (DRY, SOLID, Architecture)
4. Security & Reliability (Error Handling, Validation)

---

## 1. Performance (Speed, Memory, Big-O)

### Async / Event Loop Health

The single most common source of FastAPI performance problems is accidentally blocking the async event loop.

**Blocking calls in async endpoints.** Look for synchronous I/O inside `async def` route handlers or dependencies: `open()`, `requests.get()`, `time.sleep()`, synchronous ORM calls, subprocess without asyncio, file system operations without `aiofiles`. Any of these blocks the entire event loop thread, meaning no other requests can be processed while waiting. Fix by using an async equivalent such as `httpx`, `aiofiles`, or `asyncio.sleep`, or by moving the blocking call to a thread pool with `asyncio.to_thread()` or `run_in_executor`.

**Sync endpoints doing I/O.** FastAPI runs `def` endpoints in a thread pool automatically, which is acceptable for light I/O. If the endpoint is I/O-heavy and called frequently, the thread pool becomes the bottleneck. Convert it to async with proper async libraries or increase the thread pool size deliberately.

**CPU-bound work in request handlers.** Heavy computation such as image processing, data crunching, or ML inference in the request path blocks the handler. Offload it to background tasks, Celery workers, or `run_in_executor` with a `ProcessPoolExecutor`.

### Algorithmic Complexity

**O(n^2) or worse in request paths.** Look for nested loops over collections, repeated linear searches, and list membership checks with `in` on large lists. This is especially dangerous when `n` comes from user input or a database result that grows over time.

**Unnecessary repeated computation.** Look for functions that recompute the same value within a single request, such as re-parsing config or re-querying the same data. Prefer local variables or request-scoped caching.

**String concatenation in loops.** Building strings with `+=` in a loop creates a new string object each iteration. Use `"".join()` or `io.StringIO`.

### Memory

**Loading full datasets into memory.** Watch for `.all()` calls, missing `.limit()`, absent pagination, or lack of streaming. Query only what the caller actually needs.

**Large response serialization.** Returning huge lists of Pydantic models without pagination adds model-instantiation overhead and increases memory pressure.

**Accumulating state in module-level or global variables.** Unbounded lists, dicts, or caches in singleton or module-level patterns can leak memory over time if they are never cleared or capped.

**Generator opportunities.** Functions that build and return complete lists when lazy evaluation or streaming would work are candidates for generators.

---

## 2. Scalability (Concurrency, Caching, DB Patterns)

### Database

**N+1 queries.** Look for ORM queries inside loops after loading a parent list. Fix with eager loading such as `joinedload` or `selectinload`, or with batch queries.

**Missing indexes.** Flag columns used in `WHERE`, `ORDER BY`, `JOIN`, or `DISTINCT` clauses that likely lack indexes, especially filter columns in list endpoints and foreign keys.

**Connection pool exhaustion.** Check engine configuration for `pool_size`, `max_overflow`, and `pool_timeout`. Defaults are often inadequate under concurrency.

**Transaction scope too wide.** Transactions that stay open across HTTP calls, file I/O, or other slow work hold scarce connections and increase deadlock risk.

**Missing query optimization.** Watch for `SELECT *`, fetching more columns than needed, or unnecessary ordering on large tables.

### Caching

**No caching on hot paths.** Stable data such as config, profiles, or permissions should not always hit the database. Identify candidates for in-memory or distributed caching.

**Cache invalidation gaps.** Existing caches with no invalidation or ineffective TTLs can either serve stale data or provide little real benefit.

**Caching mutable objects.** Be careful with `@lru_cache` on functions that return dicts or lists. Callers can mutate the cached object and corrupt later reads.

### Concurrency Patterns

**Sequential async calls that could be concurrent.** Independent awaits should often be grouped with `asyncio.gather(...)`.

**Missing connection reuse.** Creating new HTTP client sessions per request wastes connection setup, DNS lookups, and TLS handshakes. Prefer a shared `httpx.AsyncClient`.

**No rate limiting or backpressure.** Unbounded outbound concurrency can overwhelm downstream services or trigger rate limits.

**Missing timeouts.** External calls without explicit timeouts can hang indefinitely and tie up worker capacity.

---

## 3. Code Quality (DRY, SOLID, Architecture)

### DRY Violations

**Duplicated business logic.** Repeated validation, transformation, or query logic makes optimization and bug fixes harder to apply consistently.

**Duplicated dependency injection.** Repeated dependency chains across routers should usually be extracted into shared dependencies.

### SOLID Principles

**Fat route handlers.** Endpoints that do validation, business logic, database work, external calls, and response formatting inline are hard to test and hard to optimize.

**God models.** Avoid single Pydantic or ORM classes that try to represent request, response, persistence, and internal state all at once.

**Tight coupling to infrastructure.** Business logic should receive database sessions, HTTP clients, and cache handles through dependency injection rather than importing them directly.

### Architecture

**Missing service layer.** Routes that directly manipulate ORM objects make it harder to add caching, logging, or business rules consistently.

**Circular imports or tangled dependency graphs.** These create fragile startup order and obscure data flow.

**Configuration scattered across files.** Centralize settings rather than hardcoding values across modules.

---

## 4. Security & Reliability (Error Handling, Validation)

### Error Handling

**Bare except clauses.** Catch specific exceptions when possible. At minimum, log failures rather than swallowing them silently.

**Missing error handling on external calls.** HTTP requests, database operations, and file I/O should not fail as raw 500s under transient errors.

**No retry logic on transient failures.** Idempotent external operations often need retries with backoff.

**Inconsistent error response format.** Standardize exception handling rather than mixing ad hoc error payloads with raw stack-driven failures.

### Input Validation

**Missing or weak Pydantic validation.** Prefer typed models over `dict` or `Any`, and add meaningful field constraints.

**Unbounded input sizes.** Add `max_items`, `max_length`, upload limits, and similar guards where payload size can grow without bound.

**Missing path/query parameter validation.** Use precise types such as positive integers, UUIDs, and constrained enums instead of overly broad `str` or `int`.

### Resilience

**No health check endpoint.** Services typically need `/health` or `/ready` style endpoints for orchestration and load balancers.

**No graceful shutdown handling.** Use lifespan hooks or equivalent shutdown handling to drain connections and finish in-flight work cleanly.

**No circuit breaker pattern.** Repeated calls to a failing downstream service can cause cascading failures without backoff or circuit breaking.
