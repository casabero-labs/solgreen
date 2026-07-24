"""PostgreSQL advisory lock manager for preventing overlapping sync operations."""

from __future__ import annotations

import enum
from typing import Any


class LockStatus(enum.Enum):
    ACQUIRED = "acquired"
    BUSY = "busy"
    ERROR = "error"
    RELEASED = "released"


def _hash_lock_key(plant_id: str, station_id: str) -> int:
    """Generate a deterministic, collision-resistant bigint lock key.

    Uses a composite of plant_id and station_id to avoid collisions
    between different plants/stations while staying within PostgreSQL's
    bigint range (9.2e18).
    """
    import hashlib

    composite = f"{plant_id}:{station_id}".encode()
    digest = hashlib.sha256(composite).digest()
    num = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return (num % (2**62)) + 1000000


class AdvisoryLock:
    """PostgreSQL advisory lock context manager.

    Uses pg_try_advisory_lock to acquire an exclusive lock without blocking.
    If the lock is busy, exits cleanly with SKIPPED_LOCKED status.
    Always releases the lock on context exit, even on exceptions.
    """

    def __init__(self, conn: Any, plant_id: str, station_id: str) -> None:
        self._conn = conn
        self._key = _hash_lock_key(plant_id, station_id)
        self._acquired = False

    def acquire(self) -> LockStatus:
        """Attempt to acquire the advisory lock (non-blocking)."""
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT pg_try_advisory_lock(%s)", (self._key,))
                result = cur.fetchone()
            if result and result[0]:
                self._acquired = True
                return LockStatus.ACQUIRED
            return LockStatus.BUSY
        except Exception:
            return LockStatus.ERROR

    def release(self) -> LockStatus:
        """Release the advisory lock."""
        if not self._acquired:
            return LockStatus.RELEASED
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s)", (self._key,))
            self._acquired = False
            return LockStatus.RELEASED
        except Exception:
            return LockStatus.ERROR

    def __enter__(self) -> AdvisoryLock:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._acquired:
            self.release()


def acquire_sync_lock(conn: Any, plant_id: str, station_id: str) -> tuple[AdvisoryLock, LockStatus]:
    """Acquire an advisory lock for the given plant/station.

    Returns (lock, status). If status is ACQUIRED, the lock is held.
    Caller must release on exit.
    """
    lock = AdvisoryLock(conn, plant_id, station_id)
    status = lock.acquire()
    return lock, status
