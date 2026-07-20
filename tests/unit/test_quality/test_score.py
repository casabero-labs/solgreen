
import pytest

from solgreen.quality.score import compute_quality_score


class TestComputeQualityScore:
    def test_perfect_batch_returns_one(self) -> None:
        score = compute_quality_score(total_rows=100, duplicate_count=0, gap_count=0)
        assert score == 1.0

    def test_zero_rows_returns_one(self) -> None:
        score = compute_quality_score(total_rows=0, duplicate_count=0, gap_count=0)
        assert score == 1.0

    def test_duplicates_penalize_score(self) -> None:
        score = compute_quality_score(total_rows=10, duplicate_count=6, gap_count=0)
        expected = 1.0 - (6 / 10 * 0.6)
        assert score == pytest.approx(expected, rel=1e-9)

    def test_gaps_penalize_score(self) -> None:
        score = compute_quality_score(total_rows=10, duplicate_count=0, gap_count=4)
        expected = 1.0 - (4 / 10 * 0.4)
        assert score == pytest.approx(expected, rel=1e-9)

    def test_combined_penalties_capped_at_zero(self) -> None:
        score = compute_quality_score(total_rows=10, duplicate_count=10, gap_count=10)
        assert score == 0.0

    def test_score_never_negative(self) -> None:
        score = compute_quality_score(total_rows=1, duplicate_count=100, gap_count=100)
        assert score >= 0.0
