"""Deprecated stub.

The single-float ``compute_quality_score`` and ``build_quality_result``
APIs have been replaced in U1.2 by ``compute_temporal_dimensions`` and
``aggregate_quality_score`` returning a ``QualityDimensions`` model.

See:
- solgreen/quality/score.py
- solgreen/quality/_types.py (QualityDimensions, QualityResult)
- tests/unit/test_quality/test_dimensions.py

This file exists only to keep the deleted-path entry in the PR diff
visible for reviewers; ruff format --check still validates it because
the CI workflow includes any *.py file present in the diff range.
"""

from __future__ import annotations
