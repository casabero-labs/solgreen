"""Database migration runner with idempotent, checksum-verified execution."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

MIGRATION_PATTERN = re.compile(r"^(\d{3,})_(.+)$")


@dataclass(frozen=True)
class MigrationFile:
    name: str
    path: Path
    version: int

    @property
    def checksum(self) -> str:
        content = self.path.read_text(encoding="utf-8")
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass(frozen=True)
class AppliedMigration:
    version: int
    name: str
    checksum: str
    applied_at: datetime


class DuplicateVersionError(RuntimeError):
    pass


class MigrationRunner:
    """Idempotent migration runner with checksum verification and rollback on error."""

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def _ensure_control_table(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        self._conn.commit()

    def _get_applied(self) -> dict[int, AppliedMigration]:
        self._ensure_control_table()
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT version, name, checksum, applied_at FROM schema_migrations ORDER BY version"
            )
            rows = cur.fetchall()
        return {
            row[0]: AppliedMigration(
                version=row[0], name=row[1], checksum=row[2], applied_at=row[3]
            )
            for row in rows
        }

    def _parse_migration_file(self, f: Path) -> MigrationFile | None:
        name = f.stem
        match = MIGRATION_PATTERN.match(name)
        if not match:
            return None
        version_str, _ = match.groups()
        version = int(version_str)
        return MigrationFile(name=name, path=f, version=version)

    def _scan_migrations(self, migrations_path: Path) -> list[MigrationFile]:
        migrations: list[MigrationFile] = []
        seen_versions: set[int] = set()
        for f in sorted(migrations_path.glob("*.sql")):
            mf = self._parse_migration_file(f)
            if mf is None:
                continue
            if mf.version in seen_versions:
                raise DuplicateVersionError(
                    f"Duplicate migration version {mf.version} found in {f.name}"
                )
            seen_versions.add(mf.version)
            migrations.append(mf)
        return migrations

    def _get_pending(self, migrations_path: Path) -> list[MigrationFile]:
        applied = self._get_applied()
        all_migrations = self._scan_migrations(migrations_path)
        return [m for m in all_migrations if m.version not in applied]

    def status(
        self, migrations_path: Path | None = None
    ) -> tuple[list[AppliedMigration], list[MigrationFile]]:
        if migrations_path is None:
            migrations_path = Path(__file__).parent
        applied_map = self._get_applied()
        all_migrations = self._scan_migrations(migrations_path)
        applied = list(applied_map.values())

        drift_errors: list[str] = []
        for m in all_migrations:
            if m.version in applied_map:
                existing = applied_map[m.version]
                if m.checksum != existing.checksum:
                    drift_errors.append(
                        f"Migration {m.version} ({m.name}) checksum drift. "
                        f"File: {m.checksum[:16]}..., DB: {existing.checksum[:16]}..."
                    )
                if m.name != existing.name:
                    drift_errors.append(
                        f"Migration {m.version} name drift. File: {m.name}, DB: {existing.name}"
                    )

        if drift_errors:
            raise RuntimeError("; ".join(drift_errors))

        pending = [m for m in all_migrations if m.version not in applied_map]
        return applied, pending

    def apply(
        self, migrations_path: Path | None = None, target_version: int | None = None
    ) -> list[MigrationFile]:
        if migrations_path is None:
            migrations_path = Path(__file__).parent
        self._ensure_control_table()
        applied_map = self._get_applied()
        all_migrations = self._scan_migrations(migrations_path)

        for m in all_migrations:
            if m.version in applied_map:
                existing = applied_map[m.version]
                if m.checksum != existing.checksum:
                    raise RuntimeError(
                        f"Migration {m.version} ({m.name}) checksum mismatch. "
                        f"File: {m.checksum[:16]}..., DB: {existing.checksum[:16]}..."
                    )
                if m.name != existing.name:
                    raise RuntimeError(
                        f"Migration {m.version} name mismatch. File: {m.name}, DB: {existing.name}"
                    )

        pending = [m for m in all_migrations if m.version not in applied_map]
        if target_version is not None:
            pending = [m for m in pending if m.version <= target_version]

        applied: list[MigrationFile] = []
        for migration in pending:
            sql = migration.path.read_text(encoding="utf-8")
            try:
                with self._conn.cursor() as cur:
                    cur.execute(sql)
                with self._conn.cursor() as cur:
                    cur.execute(
                        "SELECT version, name, checksum FROM schema_migrations WHERE version = %s",
                        (migration.version,),
                    )
                    row = cur.fetchone()

                if row is not None:
                    _db_version, db_name, db_checksum = row
                    if db_checksum != migration.checksum:
                        self._conn.rollback()
                        raise RuntimeError(
                            f"Migration {migration.version} ({migration.name}) checksum drift detected "
                            f"during concurrent insert. File: {migration.checksum[:16]}..., DB: {db_checksum[:16]}..."
                        )
                    if db_name != migration.name:
                        self._conn.rollback()
                        raise RuntimeError(
                            f"Migration {migration.version} name drift during concurrent insert. "
                            f"File: {migration.name}, DB: {db_name}"
                        )
                else:
                    with self._conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO schema_migrations (version, name, checksum) VALUES (%s, %s, %s)",
                            (migration.version, migration.name, migration.checksum),
                        )
                    try:
                        with self._conn.cursor() as cur:
                            cur.execute(
                                "SELECT version, name, checksum FROM schema_migrations WHERE version = %s",
                                (migration.version,),
                            )
                            confirm = cur.fetchone()
                        if confirm is None:
                            self._conn.rollback()
                            raise RuntimeError(
                                f"Migration {migration.version} was not persisted by concurrent process"
                            )
                        _, confirm_name, confirm_checksum = confirm
                        if confirm_checksum != migration.checksum:
                            self._conn.rollback()
                            raise RuntimeError(
                                f"Migration {migration.version} checksum drift after concurrent insert. "
                                f"File: {migration.checksum[:16]}..., DB: {confirm_checksum[:16]}..."
                            )
                        if confirm_name != migration.name:
                            self._conn.rollback()
                            raise RuntimeError(
                                f"Migration {migration.version} name drift after concurrent insert. "
                                f"File: {migration.name}, DB: {confirm_name}"
                            )
                    except RuntimeError:
                        raise
                    except Exception as exc:
                        self._conn.rollback()
                        raise RuntimeError(
                            f"Migration {migration.version} concurrent insert verification failed: {exc}"
                        ) from exc

                self._conn.commit()
                applied.append(migration)
            except Exception:
                self._conn.rollback()
                raise

        return applied


def get_migration_runner(conn: Any) -> MigrationRunner:
    """Create a migration runner for the given database connection."""
    return MigrationRunner(conn)
