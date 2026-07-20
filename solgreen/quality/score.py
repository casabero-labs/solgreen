from solgreen.quality._types import QualityResult


def compute_quality_score(
    total_rows: int,
    duplicate_count: int,
    gap_count: int,
) -> float:
    if total_rows == 0:
        return 1.0

    dup_penalty = duplicate_count / total_rows * 0.6
    gap_penalty = gap_count / total_rows * 0.4

    score = 1.0 - max(dup_penalty + gap_penalty, 0.0)
    return max(score, 0.0)


def build_quality_result(
    result: QualityResult,
) -> QualityResult:
    dup_total = sum(d.count - 1 for d in result.duplicates)
    score = compute_quality_score(
        total_rows=result.total_rows,
        duplicate_count=dup_total,
        gap_count=len(result.gaps),
    )
    return QualityResult(
        source_type=result.source_type,
        total_rows=result.total_rows,
        ordering=result.ordering,
        duplicates=result.duplicates,
        gaps=result.gaps,
        quality_score=score,
    )
