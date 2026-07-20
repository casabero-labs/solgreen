from datetime import UTC, datetime
from pathlib import Path

import pytest

from solgreen.contracts import ImportMetadata, SourceType
from solgreen.core.hashing import (
    build_import_metadata,
    compute_sha256,
    iter_chunks,
)


def test_compute_sha256_path_deterministic(tmp_path: Path) -> None:
    file_path = tmp_path / "data.csv"
    file_path.write_bytes(b"solarman fixture bytes")
    expected = compute_sha256(b"solarman fixture bytes")
    assert compute_sha256(file_path) == expected
    assert compute_sha256(file_path) == expected


def test_compute_sha256_distinct_inputs(tmp_path: Path) -> None:
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    a.write_bytes(b"alpha")
    b.write_bytes(b"beta")
    assert compute_sha256(a) != compute_sha256(b)


def test_compute_sha256_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        compute_sha256(tmp_path / "absent.csv")


def test_iter_chunks_streams_file(tmp_path: Path) -> None:
    file_path = tmp_path / "big.bin"
    payload = b"x" * 5000
    file_path.write_bytes(payload)
    collected = b"".join(iter_chunks(file_path, chunk_size=1024))
    assert collected == payload
    assert compute_sha256(file_path) == compute_sha256(payload)


def test_build_import_metadata_uses_path_when_sha_not_provided(tmp_path: Path) -> None:
    file_path = tmp_path / "flow.csv"
    file_path.write_bytes(b"flow-bytes")
    metadata = build_import_metadata(
        file_path,
        source_type=SourceType.SOLARMAN_PLANT_FLOW,
        parser_id="solarman_flow_csv",
        parser_version="0.1.0",
    )
    assert isinstance(metadata, ImportMetadata)
    assert metadata.sha256 == compute_sha256(b"flow-bytes")
    assert metadata.byte_size == len(b"flow-bytes")
    assert metadata.original_filename == "flow.csv"
    assert metadata.source_type == SourceType.SOLARMAN_PLANT_FLOW


def test_build_import_metadata_respects_overrides(tmp_path: Path) -> None:
    file_path = tmp_path / "x.csv"
    file_path.write_bytes(b"ignored")
    custom_sha = "f" * 64
    fixed_dt = datetime(2026, 7, 20, 0, 0, tzinfo=UTC)
    metadata = build_import_metadata(
        file_path,
        source_type=SourceType.SOLARMAN_INVERTER_TELEMETRY,
        parser_id="p",
        parser_version="1.2.3",
        sha256_hex=custom_sha,
        byte_size=9999,
        imported_at=fixed_dt,
    )
    assert metadata.sha256 == custom_sha
    assert metadata.byte_size == 9999
    assert metadata.imported_at == fixed_dt
