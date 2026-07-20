from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from solgreen.contracts.enums import ImportStatus, SourceType
from solgreen.quality._types import QualityResult

Sha256Hex = Annotated[
    str,
    StringConstraints(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"),
]
Semver = Annotated[
    str,
    StringConstraints(min_length=1, max_length=64, pattern=r"^\d+\.\d+\.\d+([-+].+)?$"),
]


class QualitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows_total: int = Field(ge=0)
    rows_parsed: int = Field(ge=0)
    rows_rejected: int = Field(ge=0)
    detected_columns: tuple[str, ...]
    missing_canonical_columns: tuple[str, ...] = Field(default_factory=tuple)
    quality_result: QualityResult | None = Field(default=None)


class ImportMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_type: SourceType
    original_filename: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    sha256: Sha256Hex
    byte_size: Annotated[int, Field(ge=0)]
    parser_id: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    parser_version: Semver
    imported_at: datetime


class ImportBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    plant_id: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    metadata: ImportMetadata
    status: ImportStatus = ImportStatus.PENDING
    quality_summary: QualitySummary | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
