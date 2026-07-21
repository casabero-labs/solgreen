from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from solgreen.contracts.enums import SourceType
from solgreen.quality._types import (
    DuplicateTimestamp,
    OrderingInfo,
    QualityDimensions,
    QualityResult,
    TemporalGap,
)


def _dimensions(**kwargs: object) -> QualityDimensions:
    base: dict[str, object] = {
        "temporal_coverage": 1.0,
        "duplicate_integrity": 1.0,
    }
    base.update(kwargs)
    return QualityDimensions(**base)  # type: ignore[arg-type]


class TestDuplicateTimestamp:
    def test_frozen_model(self) -> None:
        dup = DuplicateTimestamp(
            index=0,
            timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
            count=2,
            indices=(0, 5),
        )
        with pytest.raises(ValidationError, match="frozen"):
            dup.index = 1  # type: ignore[misc]

    def test_fields(self) -> None:
        ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        dup = DuplicateTimestamp(index=0, timestamp=ts, count=3, indices=(0, 3, 7))
        assert dup.index == 0
        assert dup.timestamp == ts
        assert dup.count == 3
        assert dup.indices == (0, 3, 7)


class TestTemporalGap:
    def test_frozen_model(self) -> None:
        gap = TemporalGap(
            before_index=0,
            after_index=5,
            gap_duration=timedelta(minutes=30),
            expected_interval=timedelta(minutes=5),
            gap_ratio=6.0,
        )
        with pytest.raises(ValidationError, match="frozen"):
            gap.before_index = 1  # type: ignore[misc]

    def test_fields(self) -> None:
        gap = TemporalGap(
            before_index=2,
            after_index=8,
            gap_duration=timedelta(minutes=45),
            expected_interval=timedelta(minutes=5),
            gap_ratio=9.0,
        )
        assert gap.before_index == 2
        assert gap.after_index == 8
        assert gap.gap_duration == timedelta(minutes=45)
        assert gap.expected_interval == timedelta(minutes=5)
        assert gap.gap_ratio == 9.0


class TestOrderingInfo:
    def test_both_true(self) -> None:
        info = OrderingInfo(was_ordered=True, was_strict=True)
        assert info.was_ordered is True
        assert info.was_strict is True

    def test_both_false(self) -> None:
        info = OrderingInfo(was_ordered=False, was_strict=False)
        assert info.was_ordered is False
        assert info.was_strict is False


class TestQualityResult:
    def test_has_issues_false_when_clean(self) -> None:
        result = QualityResult(
            source_type=SourceType.SOLARMAN_INVERTER_TELEMETRY,
            total_rows=10,
            ordering=OrderingInfo(was_ordered=True, was_strict=True),
            duplicates=(),
            gaps=(),
            quality_score=1.0,
            dimensions=_dimensions(),
        )
        assert result.has_issues is False

    def test_has_issues_true_with_duplicates(self) -> None:
        dup = DuplicateTimestamp(
            index=0,
            timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
            count=2,
            indices=(0, 1),
        )
        result = QualityResult(
            source_type=SourceType.SOLARMAN_INVERTER_TELEMETRY,
            total_rows=10,
            ordering=OrderingInfo(was_ordered=True, was_strict=False),
            duplicates=(dup,),
            gaps=(),
            quality_score=0.9,
            dimensions=_dimensions(duplicate_integrity=0.5),
        )
        assert result.has_issues is True

    def test_has_issues_true_with_gaps(self) -> None:
        gap = TemporalGap(
            before_index=0,
            after_index=5,
            gap_duration=timedelta(minutes=30),
            expected_interval=timedelta(minutes=5),
            gap_ratio=6.0,
        )
        result = QualityResult(
            source_type=SourceType.SOLARMAN_PLANT_FLOW,
            total_rows=10,
            ordering=OrderingInfo(was_ordered=True, was_strict=True),
            duplicates=(),
            gaps=(gap,),
            quality_score=0.8,
            dimensions=_dimensions(temporal_coverage=0.7),
        )
        assert result.has_issues is True

    def test_model_dump_contains_all_required_fields(self) -> None:
        result = QualityResult(
            source_type=SourceType.SOLARMAN_INVERTER_TELEMETRY,
            total_rows=10,
            ordering=OrderingInfo(was_ordered=True, was_strict=True),
            duplicates=(),
            gaps=(),
            quality_score=0.94,
            dimensions=_dimensions(
                completeness=0.8,
                temporal_coverage=0.9,
                duplicate_integrity=1.0,
            ),
        )
        dumped = result.model_dump()
        assert "quality_score" in dumped
        assert "dimensions" in dumped
        dims = dumped["dimensions"]
        assert "temporal_coverage" in dims
        assert "duplicate_integrity" in dims
        assert "completeness" in dims
        assert "plausibility_score" in dims
        assert "consistency_score" in dims

    def test_model_dump_json_contains_all_required_fields(self) -> None:
        result = QualityResult(
            source_type=SourceType.SOLARMAN_INVERTER_TELEMETRY,
            total_rows=10,
            ordering=OrderingInfo(was_ordered=True, was_strict=True),
            duplicates=(),
            gaps=(),
            quality_score=0.94,
            dimensions=_dimensions(
                completeness=0.8,
                temporal_coverage=0.9,
                duplicate_integrity=1.0,
            ),
        )
        json_str = result.model_dump_json()
        for field in (
            "quality_score",
            "dimensions",
            "temporal_coverage",
            "duplicate_integrity",
            "completeness",
            "plausibility_score",
            "consistency_score",
        ):
            assert field in json_str, f"{field} missing from model_dump_json()"
