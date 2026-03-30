# Production Configuration Reference

> Standards for databases, caching, runtime tuning, security, containers, and observability.

## Table of Contents

1. [Configuration Management](#1-configuration-management) — 12-factor, secrets, immutable infra
2. [PostgreSQL Tuning](#2-postgresql-tuning) — Memory, WAL, autovacuum
3. [Connection Pooling](#3-connection-pooling) — Sizing, timeouts, stack-specific implementations
4. [Redis Configuration](#4-redis-configuration) — Eviction, persistence, hardening
5. [Runtime Tuning](#5-runtime-tuning) — Multi-runtime strategy, Python-specific
6. [Resilience Patterns](#6-resilience-patterns) — Circuit breakers, timeouts, retry, rate limiting
7. [Security](#7-security) — TLS, headers, secrets, JWT
8. [Containers and Deployment](#8-containers-and-deployment) — Docker, resource limits, probes, shutdown
9. [Kubernetes](#9-kubernetes) — Resource allocation, JVM, probes, deployment
10. [Observability](#10-observability) — Structured logging, metrics, tracing
11. [Linux Kernel Tuning](#11-linux-kernel-tuning) — Networking, file descriptors
12. [Production Checklist](#12-production-checklist)

---

## 1. Configuration Management

### 12-Factor Principles

Config varies by environment (dev, staging, prod). Never hardcode connection strings,
API keys, or environment-specific values.

- Inject via environment variables for portability
- Source secrets from a secrets manager (Vault, AWS SSM, GCP Secret Manager)
- Run migrations as separate commands or CI steps, never as embedded app endpoints

### Immutable Infrastructure

Config change = redeployment. Exceptions: feature flags and circuit breaker thresholds
can be fetched from a distributed store and adjusted at runtime.

### Multi-Runtime Strategy

| Workload | Runtime | Config Priorities |
|----------|---------|-------------------|
| I/O Bound (API gateways) | Async/non-blocking (Node, Go) | Concurrency limits, Keep-Alive, event loop monitoring |
| CPU Bound (data processing, ML) | Multi-threaded (Java, Rust) | Thread pool sizing, heap allocation, GC tuning |
| Serverless | Fast cold-start (Go, Rust, Python) | Minimal dependencies, cold start optimization |

> **Python Implementation (Pydantic Settings)**

Pydantic settings validates types at startup — a misspelled env var or missing
required config crashes immediately rather than failing silently at runtime.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    api_timeout: float = 30.0
    max_retries: int = 3
    log_level: str = "INFO"
    environment: str = "development"

    model_config = {"env_prefix": "APP_"}

settings = Settings()  # reads from env vars: APP_DATABASE_URL, etc.
```

---

## 2. PostgreSQL Tuning

### Memory

| Parameter | Recommendation | Why |
|-----------|----------------|-----|
| `shared_buffers` | 25-40% of RAM | PostgreSQL internal cache. Higher starves OS page cache. |
| `effective_cache_size` | 50-75% of RAM | Query planner hint. Too low causes sequential scans over index scans. |
| `work_mem` | 4-64MB | Per sort/hash operation. Formula: `(RAM - shared_buffers) / (max_connections * 3)` |
| `maintenance_work_mem` | 1-2GB | For VACUUM, CREATE INDEX. Few concurrent ops, can be large. |

### Write-Ahead Log (WAL)

| Parameter | Recommendation | Impact |
|-----------|----------------|--------|
| `max_wal_size` | 2-16GB | Larger = fewer checkpoints, better write throughput, longer recovery |
| `min_wal_size` | 1-2GB | Minimum recycled WAL segments |
| `checkpoint_completion_target` | 0.9 | Spread writes over 90% of interval to avoid I/O spikes |

### Autovacuum

| Parameter | Recommendation | Why |
|-----------|----------------|-----|
| `autovacuum_vacuum_scale_factor` | 0.05-0.1 | Default 0.2 allows 200GB dead rows on a 1TB table before cleanup |
| `autovacuum_vacuum_cost_limit` | 1000-2000 | Increase budget to keep up with high write rates |

---

## 3. Connection Pooling

### Pool Sizing Rule

**Optimal connections = (CPU cores x 2) + effective_spindle_count**

For SSD (no spindles): 10-20 connections usually saturates the hardware. More
connections = more lock contention + context switching. Keep pool small.

Set min = max (fixed pool). Dynamic resizing causes latency spikes during resize.

### Timeout Principles

| Parameter | Recommendation | Why |
|-----------|----------------|-----|
| Connection timeout | 1-2s | Fail fast if DB overloaded. Trigger circuit breaker. |
| Max lifetime | 30 min or less | Must be < firewall/NAT timeout to avoid dead connections |
| Idle timeout | 10 min | Not too low or pool churns connections |

### HikariCP (Java)

```
maximumPoolSize=10
minimumIdle=10            # fixed pool: min = max
connectionTimeout=2000
maxLifetime=1800000       # 30 min
idleTimeout=600000        # 10 min
prepStmtCacheSize=250
cachePrepStmts=true
```

> **Python Implementation (psycopg3)**

```python
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo="postgresql://user:pass@host/db",
    min_size=4,
    max_size=10,        # keep small: (cpu_cores * 2) + 1 is a good ceiling
    max_lifetime=1800,  # 30 min — recycle before firewall/NAT timeout
    max_idle=600,       # 10 min
    timeout=2.0,        # fail fast if pool exhausted
)

with pool.connection() as conn:
    rows = conn.execute("SELECT * FROM users WHERE active").fetchall()
```

> **Python Implementation (asyncpg)**

```python
import asyncpg

pool = await asyncpg.create_pool(
    dsn="postgresql://user:pass@host/db",
    min_size=4,
    max_size=10,
    max_inactive_connection_lifetime=600,
    command_timeout=30.0,
)

async with pool.acquire() as conn:
    rows = await conn.fetch("SELECT * FROM users WHERE active")
```

> **Python Implementation (SQLAlchemy)**

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg://user:pass@host/db",
    pool_size=10,
    max_overflow=5,      # temporary connections above pool_size
    pool_timeout=2.0,    # fail fast
    pool_recycle=1800,   # 30 min
    pool_pre_ping=True,  # test connection before use (prevents stale conn errors)
)
```

---

## 4. Redis Configuration

### Eviction Policies

| Use Case | Policy | Why |
|----------|--------|-----|
| Cache | `allkeys-lru` | Evict least-recently-used. Maximizes hit rate. |
| Session store | `noeviction` | Error on full rather than silent logout. Alert ops. |

Separate clusters for cache vs sessions — different eviction needs.

### Persistence

AOF with `appendfsync everysec`. Limits data loss to 1 second on crash. Avoid
`always` (kills throughput). For pure cache, persistence can be disabled.

### L2 Cache (Local + Remote)

For ultra-low-latency: local in-memory cache backed by Redis. Useful for small,
read-heavy reference data.

### Hardening

- Rename/disable dangerous commands: `FLUSHALL`, `FLUSHDB`, `KEYS`
- Configure slow log: `slowlog-log-slower-than 10000` (10ms)
- Enable lazy eviction: `lazyfree-lazy-eviction yes`
- Set `maxmemory` explicitly — don't let Redis consume all RAM

> **Python Implementation**

```python
import redis

pool = redis.ConnectionPool(
    host="localhost",
    port=6379,
    max_connections=20,
    socket_timeout=2.0,
    socket_connect_timeout=1.0,
    retry_on_timeout=True,
    decode_responses=True,
)
client = redis.Redis(connection_pool=pool)
```

---

## 5. Runtime Tuning

### ASGI Server (Python)

For web APIs and long-running services:

```bash
# Production: gunicorn manages worker processes, uvicorn handles async
gunicorn app:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers $(( $(nproc) * 2 + 1 )) \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --graceful-timeout 30 \
  --max-requests 1000 \
  --max-requests-jitter 50  # prevent all workers restarting simultaneously
```

Worker count formula: `(CPU cores x 2) + 1`. For I/O-bound workloads, can go higher.
For CPU-bound (ML inference), use 1 worker per core.

### Script / Pipeline Process Management (Python)

For data pipelines and scripts (not web servers):

```python
import signal
import sys

shutdown_requested = False

def handle_shutdown(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    print("Shutdown requested, finishing current batch...")

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# In your processing loop:
for batch in batches:
    if shutdown_requested:
        save_checkpoint()
        sys.exit(0)
    process(batch)
```

### Memory Management (Python)

For data-heavy pipelines, process in chunks rather than loading everything into memory:

```python
import polars as pl

# Good — streaming / chunked processing
reader = pl.read_csv_batched("huge_file.csv", batch_size=50_000)
while (batch := reader.next_batches(1)):
    process(batch[0])

# Good — lazy evaluation (Polars computes only what's needed)
result = (
    pl.scan_parquet("data/*.parquet")
    .filter(pl.col("status") == "active")
    .group_by("category")
    .agg(pl.col("revenue").sum())
    .collect()
)
```

---

## 6. Resilience Patterns

### Timeout Hierarchy

```
Client Timeout > Server Timeout > Database Timeout
```

Upstream must always wait longer than downstream. If your API has a 30s timeout, the
database query timeout should be <30s, and the client calling your API should wait >30s.

### Circuit Breaker Configuration

| Parameter | Recommendation | Why |
|---|---|---|
| Sliding window | COUNT_BASED, size 50-100 | Deterministic. Time-based gets skewed by low traffic. |
| Failure threshold | 50% | Half failing = effectively down |
| Wait in open state | 5-30s | Time for downstream to recover |
| Half-open test calls | 3-10 | Statistically meaningful recovery signal |

> **Java (Resilience4j)**

```
slidingWindowType=COUNT_BASED
slidingWindowSize=100
failureRateThreshold=50
waitDurationInOpenState=10s
permittedNumberOfCallsInHalfOpenState=10
```

### Retry Strategy

- **Exponential backoff:** `wait = base * multiplier^n`
- **Full jitter:** `random(0, backoff_cap)` — prevents thundering herd
- **Retry budget:** Max 3 attempts per request, max 10% of requests as retries

### Rate Limiting (Server-Side)

If you're building an API that others consume:

- **By IP:** Protects against single-source DoS
- **By API key:** Enforces quotas, prevents noisy neighbors
- **Algorithm:** Token bucket — allows steady rate + bursts for natural traffic

On 429 response, include: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`,
`X-RateLimit-Reset`.

---

## 7. Security

### TLS

TLS 1.3 only. Removes vulnerable primitives, 1-RTT handshake.

```nginx
ssl_protocols TLSv1.3;
ssl_ciphers TLS_AES_256_GCM_SHA384:TLS_AES_128_GCM_SHA256;
```

### HTTP Security Headers

| Header | Value | Purpose |
|--------|-------|---------|
| HSTS | `max-age=63072000; includeSubDomains; preload` | Force HTTPS, 2-year cache |
| CSP | `script-src 'nonce-{RANDOM}' 'strict-dynamic'` | XSS defense, nonce-based |
| X-Frame-Options | `DENY` or `frame-ancestors 'none'` | Clickjacking prevention |
| X-Content-Type-Options | `nosniff` | Prevents MIME sniffing |

### Secrets Management

- **Anti-pattern:** Hardcoded strings, `.env` files committed to git, env vars
  (leak via logs, `/proc`, debug endpoints)
- **Best practice:** Secrets manager (Vault, AWS SSM, GCP Secret Manager).
  In containers, mount as files via Secrets Store CSI Driver (tmpfs).
- **Rotation:** Automated, every 30-90 days

### JWT

- Lock algorithm explicitly: allow only RS256 or ES256. Prevents `alg:none` attacks.
- Store in HttpOnly; Secure; SameSite=Strict cookies. Never localStorage.
- Short expiry (15-60 min) with refresh token rotation.

---

## 8. Containers and Deployment

### Dockerfile Best Practices (Python)

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app

# Dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (changes more often)
COPY src/ src/

# Non-root user
RUN useradd --system appuser
USER appuser

CMD ["python", "-m", "src.main"]
```

### Resource Limits

| Resource | Request | Limit | Why |
|----------|---------|-------|-----|
| CPU | Based on p95 usage | 2-4x request or none | CPU is compressible; strict limits cause throttling |
| Memory | Measured value | = Request | Memory is incompressible. Request=Limit = Guaranteed QoS |

### Graceful Shutdown

1. App handles SIGTERM, stops accepting new work, finishes in-flight requests
2. `terminationGracePeriodSeconds` must exceed app shutdown timeout
3. Drain connections before exiting

---

## 9. Kubernetes

### Resource Allocation

| Resource | Request | Limit | Why |
|----------|---------|-------|-----|
| CPU | Based on p95 usage | Remove or 2-4x request | CPU is compressible. Strict limits cause unnecessary throttling. |
| Memory | Set value | = Request | Memory is incompressible. Request=Limit = Guaranteed QoS, survives node pressure. |

### JVM in Containers

```
-XX:MaxRAMPercentage=75.0
```

75% heap, 25% for non-heap (Metaspace, stacks, JIT, direct buffers). Higher triggers OOM kill.

### Probes

| Probe | Purpose | Key rule |
|-------|---------|---------|
| Liveness | Should I restart this pod? | Don't check external deps. Only internal health. |
| Readiness | Can this pod receive traffic? | Check internal health + critical dependencies. |
| Startup | Has this pod finished booting? | For slow-starting apps. Disables liveness until passed. |

### Deployment

| Parameter | Recommendation |
|-----------|----------------|
| `maxSurge` | 25% |
| `maxUnavailable` | 25% (or 0 for strict HA) |

---

## 10. Observability

### Structured Logging

**Format:** JSON always. Never unstructured text.

**Required fields:**
- `timestamp` (ISO-8601)
- `level`
- `service`
- `trace_id` (correlation)
- `message`
- `context` (relevant structured data)

Never log credentials, tokens, API keys, or PII without redaction.

> **Python Implementation**

```python
import logging
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "my-service",
            "message": record.getMessage(),
            "module": record.module,
            "trace_id": getattr(record, "trace_id", None),
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### Metrics (RED Method)

| Metric | What it measures |
|--------|-----------------|
| Rate | Requests / operations per second |
| Errors | Failed requests per second |
| Duration | Latency distribution: p50, p90, p99 |

Never track average latency — it hides outliers. A p99 of 5s with p50 of 50ms
tells you something is very wrong for 1% of users; an average of 200ms hides that.

### Tracing

For distributed systems, use OpenTelemetry. Tail sampling (decide after request
completes): keep 100% of errors and high-latency traces, sample 1-5% of
successful/fast traces.

---

## 11. Linux Kernel Tuning

### Networking

| Parameter | Recommendation | Why |
|-----------|----------------|-----|
| `net.ipv4.tcp_max_syn_backlog` | 4096+ | Default 128 drops connections during spikes |
| `net.core.somaxconn` | 4096+ | Queue for established connections |
| `net.ipv4.tcp_keepalive_time` | 300 | Default 7200s useless for detecting dead connections |
| `tcp_keepalive_intvl` | 60 | |
| `tcp_keepalive_probes` | 3 | |

### File Descriptors

```
ulimit -n 65535
```

Configure in `/etc/security/limits.conf` AND systemd service (`LimitNOFILE=65535`).

---

## 12. Production Checklist

### Configuration
- [ ] Config injected via env vars or secrets manager
- [ ] Migrations run as separate commands, not app endpoints
- [ ] Settings validated at startup (Pydantic or equivalent)
- [ ] Runtime matched to workload

### Database (Postgres)
- [ ] `shared_buffers` = 25-40% RAM
- [ ] `effective_cache_size` = 50-75% RAM
- [ ] Connection pool: fixed size, `max_lifetime` < network timeout
- [ ] `autovacuum_vacuum_scale_factor` = 0.05-0.1
- [ ] `pool_pre_ping` enabled (SQLAlchemy) or equivalent health check

### Cache (Redis)
- [ ] `allkeys-lru` for cache, `noeviction` for sessions
- [ ] AOF with `appendfsync everysec`
- [ ] Dangerous commands disabled
- [ ] `maxmemory` set explicitly

### Resilience
- [ ] Circuit breakers on external dependencies
- [ ] Exponential backoff + full jitter on retries
- [ ] Timeout hierarchy enforced (client > server > DB)
- [ ] Retry budget: max 3 per request, max 10% of traffic

### Security
- [ ] TLS 1.3 only
- [ ] HSTS with preload
- [ ] Secrets from secrets manager, not env vars
- [ ] Nonce-based CSP
- [ ] JWT algorithm locked to RS256/ES256

### Containers / Kubernetes
- [ ] Non-root container user
- [ ] Memory request = limit
- [ ] CPU limits relaxed or removed
- [ ] Health probes configured (liveness doesn't check external deps)
- [ ] Graceful shutdown handles SIGTERM
- [ ] JVM: `MaxRAMPercentage=75.0` (if applicable)

### Observability
- [ ] JSON structured logs with correlation IDs
- [ ] RED metrics: Rate, Errors, Duration (p50/p90/p99)
- [ ] No PII or secrets in logs
- [ ] Alerting on success rate < 95% and circuit breaker state
- [ ] Tail sampling for traces

### OS
- [ ] `ulimit -n` >= 65535
- [ ] TCP keepalive = 300s
- [ ] SYN backlog increased

---

## References

| Topic | Source |
|-------|--------|
| 12-Factor | 12factor.net |
| PostgreSQL | Percona, Mydbops, Instaclustr |
| HikariCP | GitHub wiki |
| Redis | redis.io, Adobe Commerce |
| Resilience4j | resilience4j.readme.io |
| Rate Limiting | Cloudflare, Zuplo |
| Security Headers | OWASP, MDN |
| Kubernetes | kubernetes.io |
| Observability | OpenTelemetry |
| Linux Tuning | Various kernel docs |
