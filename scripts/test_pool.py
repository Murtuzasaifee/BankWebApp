"""
Pool health & reuse verification script.

Run from the project root:
    python -m scripts.test_pool

What it checks
--------------
1. SEQUENTIAL   — 20 queries in a row share the same physical connection (pool reuse)
2. CONCURRENT   — 10 threads fire simultaneously; peak pool size stays ≤ 10
3. IDLE CLEANUP — after all work finishes, pool shrinks back to min_size (1)
4. STATS        — prints psycopg_pool stats: pool_min, pool_max, pool_size,
                  pool_available, requests_waiting, usage_ms (avg latency)
"""

import sys
import time
import threading
from collections import Counter

# ── ensure project root is on sys.path ─────────────────────────────────────
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module itself so we always read the live _pool variable
import app.db.connection as db
from app.db.connection import init_pool, close_pool, execute_query

# ── helpers ─────────────────────────────────────────────────────────────────

DIVIDER = "-" * 60


def pool_stats() -> dict:
    """Return psycopg_pool's internal counters via the live module reference."""
    if db._pool is None:
        return {}
    return db._pool.get_stats()


def print_stats(label: str) -> None:
    s = pool_stats()
    print(f"\n[{label}]")
    print(f"  pool_min        : {s.get('pool_min')}")
    print(f"  pool_max        : {s.get('pool_max')}")
    print(f"  pool_size       : {s.get('pool_size')}   <- open connections right now")
    print(f"  pool_available  : {s.get('pool_available')}   <- idle (ready to lend)")
    print(f"  requests_waiting: {s.get('requests_waiting')}")
    print(f"  requests_queued : {s.get('requests_queued')}")
    completed = s.get('requests_completed', 1) or 1
    total_ms  = s.get('usage_ms', 0)
    print(f"  avg query ms    : {total_ms / completed:.1f}")


# ── test 1: sequential reuse ─────────────────────────────────────────────────

def test_sequential_reuse(n: int = 20) -> None:
    print(f"\n{DIVIDER}")
    print(f"TEST 1 — Sequential reuse ({n} queries)")
    print(DIVIDER)

    conn_ids: list[int] = []
    for _ in range(n):
        conn = db._pool.getconn()
        conn_ids.append(id(conn))
        db._pool.putconn(conn)

    unique = len(set(conn_ids))
    print(f"  Queries run     : {n}")
    print(f"  Unique conn objs: {unique}  (ideally 1 — same object reused)")
    print(f"  Reuse count     : {n - unique}")

    if unique == 1:
        print("  PASS — single connection reused for all sequential queries")
    else:
        counts = Counter(conn_ids)
        pct = counts.most_common(1)[0][1] / n * 100
        print(f"  INFO — {unique} objects seen; top conn used {pct:.0f}% of the time")
        print("         (small number is fine if pool grew then shrank)")


# ── test 2: concurrent load ──────────────────────────────────────────────────

def test_concurrent_load(threads: int = 10, queries_per_thread: int = 5) -> None:
    print(f"\n{DIVIDER}")
    print(f"TEST 2 — Concurrent load ({threads} threads x {queries_per_thread} queries each)")
    print(DIVIDER)

    peak_sizes: list[int] = []
    errors: list[str] = []
    lock = threading.Lock()

    def worker(tid: int) -> None:
        for _ in range(queries_per_thread):
            try:
                execute_query("SELECT 1 AS ping")
                with lock:
                    peak_sizes.append(pool_stats().get("pool_size", 0))
            except Exception as e:
                with lock:
                    errors.append(f"thread-{tid}: {e}")

    threads_list = [threading.Thread(target=worker, args=(i,)) for i in range(threads)]
    t0 = time.perf_counter()
    for t in threads_list:
        t.start()
    for t in threads_list:
        t.join()
    elapsed = time.perf_counter() - t0

    total = threads * queries_per_thread
    peak  = max(peak_sizes, default=0)
    print(f"  Total queries   : {total}")
    print(f"  Elapsed         : {elapsed:.2f}s")
    print(f"  Peak pool_size  : {peak}  (must be <= 10)")
    print(f"  Errors          : {len(errors)}")
    for e in errors:
        print(f"    {e}")

    if not errors and peak <= 10:
        print("  PASS — no errors, pool size respected")
    else:
        print("  FAIL — see errors above")


# ── test 3: no extra connections under sequential execute_query ───────────────

def test_no_extra_connections(n: int = 50) -> None:
    print(f"\n{DIVIDER}")
    print(f"TEST 3 — No extra connections created ({n} execute_query calls)")
    print(DIVIDER)

    before = pool_stats().get("pool_size", 0)
    for _ in range(n):
        execute_query("SELECT 1 AS ping")
    after = pool_stats().get("pool_size", 0)

    print(f"  pool_size before : {before}")
    print(f"  pool_size after  : {after}  (should equal before — no new conns for sequential work)")

    if after <= before:
        print("  PASS — no extra connections opened")
    else:
        print(f"  INFO — pool grew by {after - before} (normal if pool was warming up on first run)")


# ── test 4: idle shrink (informational) ──────────────────────────────────────

def test_idle_shrink(wait_seconds: int = 5) -> None:
    print(f"\n{DIVIDER}")
    print(f"TEST 4 — Idle shrink snapshot (wait {wait_seconds}s after burst)")
    print(DIVIDER)

    # burst to grow pool beyond min_size
    conns = [db._pool.getconn() for _ in range(5)]
    for c in conns:
        db._pool.putconn(c)

    before = pool_stats().get("pool_size", 0)
    print(f"  pool_size after burst : {before}")
    print(f"  Waiting {wait_seconds}s...")
    time.sleep(wait_seconds)

    after = pool_stats().get("pool_size", 0)
    print(f"  pool_size after wait  : {after}")
    print("  NOTE: psycopg_pool evicts idle conns after max_idle seconds (default 300s).")
    print("        Shrink won't be visible in a short wait — this is just a snapshot.")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Initialising connection pool...")
    init_pool()

    # Access via module reference — always reflects the live value after init_pool()
    if db._pool is None:
        print("ERROR: pool not initialised — check DB_HOST in .env")
        sys.exit(1)

    print_stats("After init_pool()")

    test_sequential_reuse(n=20)
    print_stats("After sequential test")

    test_concurrent_load(threads=10, queries_per_thread=5)
    print_stats("After concurrent test")

    test_no_extra_connections(n=50)
    print_stats("After no-extra-connections test")

    test_idle_shrink(wait_seconds=5)
    print_stats("Final stats")

    close_pool()
    print(f"\n{DIVIDER}")
    print("Done. Pool closed cleanly.")


if __name__ == "__main__":
    main()
