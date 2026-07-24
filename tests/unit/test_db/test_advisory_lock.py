from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from solgreen.db.advisory_lock import (
    AdvisoryLock,
    LockStatus,
    _hash_lock_key,
    acquire_sync_lock,
)


class TestHashLockKey:
    def test_same_input_same_hash(self) -> None:
        key1 = _hash_lock_key("plant1", "station1")
        key2 = _hash_lock_key("plant1", "station1")
        assert key1 == key2

    def test_different_input_different_hash(self) -> None:
        key1 = _hash_lock_key("plant1", "station1")
        key2 = _hash_lock_key("plant1", "station2")
        assert key1 != key2

    def test_hash_in_bigint_range(self) -> None:
        key = _hash_lock_key("plant1", "station1")
        assert 0 < key < (2**62)


class TestAdvisoryLock:
    @pytest.fixture
    def mock_conn(self) -> MagicMock:
        return MagicMock()

    def test_acquire_success(self, mock_conn: MagicMock) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (True,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        lock = AdvisoryLock(mock_conn, "plant1", "station1")
        status = lock.acquire()

        assert status == LockStatus.ACQUIRED
        assert lock._acquired is True

    def test_acquire_busy(self, mock_conn: MagicMock) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (False,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        lock = AdvisoryLock(mock_conn, "plant1", "station1")
        status = lock.acquire()

        assert status == LockStatus.BUSY
        assert lock._acquired is False

    def test_acquire_error(self, mock_conn: MagicMock) -> None:
        mock_conn.cursor.side_effect = Exception("DB error")

        lock = AdvisoryLock(mock_conn, "plant1", "station1")
        status = lock.acquire()

        assert status == LockStatus.ERROR

    def test_release_success(self, mock_conn: MagicMock) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (True,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        lock = AdvisoryLock(mock_conn, "plant1", "station1")
        lock.acquire()
        status = lock.release()

        assert status == LockStatus.RELEASED
        assert lock._acquired is False

    def test_release_not_acquired(self, mock_conn: MagicMock) -> None:
        lock = AdvisoryLock(mock_conn, "plant1", "station1")
        status = lock.release()

        assert status == LockStatus.RELEASED

    def test_context_manager_releases_on_success(self, mock_conn: MagicMock) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [(True,), (True,)]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with AdvisoryLock(mock_conn, "plant1", "station1") as lock:
            status = lock.acquire()
            assert status == LockStatus.ACQUIRED

        release_call = mock_cursor.execute.call_args_list[-1]
        assert "advisory_unlock" in release_call[0][0]

    def test_context_manager_releases_on_exception(self, mock_conn: MagicMock) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [(True,), (True,)]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        try:
            with AdvisoryLock(mock_conn, "plant1", "station1") as lock:
                lock.acquire()
                raise ValueError("test error")
        except ValueError:
            pass

        release_call = mock_cursor.execute.call_args_list[-1]
        assert "advisory_unlock" in release_call[0][0]


class TestAcquireSyncLock:
    def test_returns_lock_and_status(self) -> None:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (True,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        lock, status = acquire_sync_lock(mock_conn, "plant1", "station1")

        assert isinstance(lock, AdvisoryLock)
        assert status == LockStatus.ACQUIRED

    def test_busy_when_locked(self) -> None:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (False,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        _, status = acquire_sync_lock(mock_conn, "plant1", "station1")

        assert status == LockStatus.BUSY
