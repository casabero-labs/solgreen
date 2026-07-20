from collections.abc import Iterator
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import IO

from solgreen.contracts import ImportMetadata, SourceType

CHUNK_SIZE_BYTES = 1024 * 1024


def compute_sha256(source: Path | bytes | IO[bytes]) -> str:
    if isinstance(source, bytes):
        return _sha256_bytes(source)
    if isinstance(source, Path):
        return _sha256_path(source)
    return _sha256_stream(source)


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    digest = sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK_SIZE_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_stream(stream: IO[bytes]) -> str:
    digest = sha256()
    while chunk := stream.read(CHUNK_SIZE_BYTES):
        digest.update(chunk)
    return digest.hexdigest()


def iter_chunks(source: Path, chunk_size: int = CHUNK_SIZE_BYTES) -> Iterator[bytes]:
    with source.open("rb") as fh:
        while chunk := fh.read(chunk_size):
            yield chunk


def build_import_metadata(
    path: Path,
    source_type: SourceType,
    parser_id: str,
    parser_version: str,
    *,
    sha256_hex: str | None = None,
    byte_size: int | None = None,
    imported_at: datetime | None = None,
) -> ImportMetadata:
    resolved_sha = sha256_hex or compute_sha256(path)
    resolved_size = byte_size if byte_size is not None else path.stat().st_size
    return ImportMetadata(
        source_type=source_type,
        original_filename=path.name,
        sha256=resolved_sha,
        byte_size=resolved_size,
        parser_id=parser_id,
        parser_version=parser_version,
        imported_at=imported_at or datetime.now(UTC),
    )
