from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from solgreen.db.migrations.runner import (
    DuplicateVersionError,
    MigrationFile,
    MigrationRunner,
    get_migration_runner,
)


class TestMigrationFile:
    def test_checksum_changes_with_content(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
            f.write("CREATE TABLE a();")
            f.flush()
            path_a = Path(f.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
            f.write("CREATE TABLE b();")
            f.flush()
            path_b = Path(f.name)

        try:
            mf_a = MigrationFile(name=path_a.stem, path=path_a, version=1)
            mf_b = MigrationFile(name=path_b.stem, path=path_b, version=2)
            assert mf_a.checksum != mf_b.checksum
        finally:
            path_a.unlink()
            path_b.unlink()


class TestMigrationRunner:
    def test_default_migrations_path_does_not_crash(self) -> None:
        runner = MigrationRunner(MagicMock())
        status = runner.status()
        assert status is not None

    def test_get_migration_runner(self) -> None:
        runner = get_migration_runner(MagicMock())
        assert isinstance(runner, MigrationRunner)

    def test_scan_empty_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = MigrationRunner(MagicMock())
            migrations = runner._scan_migrations(Path(tmpdir))
            assert migrations == []

    def test_scan_ignores_non_sql_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "readme.txt").write_text("not a migration")
            (p / "migration.py").write_text("not a migration")
            runner = MigrationRunner(MagicMock())
            migrations = runner._scan_migrations(p)
            assert migrations == []

    def test_scan_finds_sql_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "001_first.sql").write_text("-- first")
            (p / "002_second.sql").write_text("-- second")
            runner = MigrationRunner(MagicMock())
            migrations = runner._scan_migrations(p)
            assert len(migrations) == 2
            assert migrations[0].version == 1
            assert migrations[1].version == 2

    def test_scan_orders_by_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "003_third.sql").write_text("-- third")
            (p / "001_first.sql").write_text("-- first")
            (p / "002_second.sql").write_text("-- second")
            runner = MigrationRunner(MagicMock())
            migrations = runner._scan_migrations(p)
            assert [m.version for m in migrations] == [1, 2, 3]

    def test_duplicate_version_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "001_first.sql").write_text("-- first")
            (p / "001_duplicate.sql").write_text("-- duplicate")
            runner = MigrationRunner(MagicMock())
            with pytest.raises(DuplicateVersionError):
                runner._scan_migrations(p)

    def _make_cursor_mock(self, fetchone_results: list):
        fetchone_vals = list(fetchone_results)
        fetchone_iter = iter(fetchone_vals)

        def cursor_side_effect():
            cur = MagicMock()

            def fetchone_impl():
                try:
                    return next(fetchone_iter)
                except StopIteration:
                    return None

            cur.fetchone.side_effect = fetchone_impl
            cur.__enter__ = MagicMock(return_value=cur)
            cur.__exit__ = MagicMock(return_value=False)
            return cur

        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = cursor_side_effect
        return mock_conn

    def test_apply_concurrent_same_row_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "001_first.sql").write_text("-- first migration")
            runner = MigrationRunner(MagicMock())
            file_checksum = runner._scan_migrations(p)[0].checksum

            runner._get_applied = MagicMock(return_value={})

            mock_conn = self._make_cursor_mock(
                [
                    (1, "001_first", file_checksum),
                ],
            )
            runner._conn = mock_conn

            applied = runner.apply(p)
            assert len(applied) == 0
            mock_conn.rollback.assert_called()
            assert mock_conn.commit.call_count == 1

    def test_apply_concurrent_checksum_mismatch_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "001_first.sql").write_text("-- first migration")
            runner = MigrationRunner(MagicMock())

            runner._get_applied = MagicMock(return_value={})

            mock_conn = self._make_cursor_mock(
                [
                    (1, "001_first", "different_checksum_value"),
                ],
            )
            runner._conn = mock_conn

            with pytest.raises(RuntimeError, match="checksum drift"):
                runner.apply(p)

            mock_conn.rollback.assert_called()

    def test_apply_concurrent_name_mismatch_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "001_first.sql").write_text("-- first migration")
            runner = MigrationRunner(MagicMock())
            file_checksum = runner._scan_migrations(p)[0].checksum

            runner._get_applied = MagicMock(return_value={})

            mock_conn = self._make_cursor_mock(
                [
                    (1, "001_wrong_name", file_checksum),
                ],
            )
            runner._conn = mock_conn

            with pytest.raises(RuntimeError, match="name drift"):
                runner.apply(p)

            mock_conn.rollback.assert_called()

    def test_apply_insert_and_verify_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "001_first.sql").write_text("-- first migration")
            runner = MigrationRunner(MagicMock())
            file_checksum = runner._scan_migrations(p)[0].checksum

            runner._get_applied = MagicMock(return_value={})

            mock_conn = self._make_cursor_mock(
                [
                    None,
                    (1, "001_first", file_checksum),
                ],
            )
            runner._conn = mock_conn

            applied = runner.apply(p)
            assert len(applied) == 1
            mock_conn.commit.assert_called()
