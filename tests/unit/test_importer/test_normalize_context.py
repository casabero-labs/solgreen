from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.importer.normalize import (
    SignNormalizationMode,
    build_normalization_context,
    normalize_telemetry_signals,
)


class TestDependencyInjection:
    def test_registry_built_once_per_context(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        registry = ctx.sign_registry
        assert registry is not None
        assert registry.count == 4

    def test_two_contexts_produce_distinct_registries(self) -> None:
        ctx1 = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        ctx2 = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        assert ctx1.sign_registry is not ctx2.sign_registry
        assert ctx1.sign_registry is not None
        assert ctx2.sign_registry is not None

    def test_multiple_files_reuse_same_context(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")

        sample1 = InverterTelemetrySample(
            timestamp_original=datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
            timestamp_utc=datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
            signals={"potencia_de_bateria_w": 100.0},
        )
        sample2 = InverterTelemetrySample(
            timestamp_original=datetime(2026, 7, 21, 10, 5, tzinfo=UTC),
            timestamp_utc=datetime(2026, 7, 21, 10, 5, tzinfo=UTC),
            signals={"potencia_de_bateria_w": 200.0},
        )

        results1, s1 = normalize_telemetry_signals([sample1], ctx)
        results2, s2 = normalize_telemetry_signals([sample2], ctx)

        assert s1.normalized_count == 1
        assert s2.normalized_count == 1
        _ = results1, results2
        assert ctx.registry_mode == SignNormalizationMode.LEGACY

    def test_no_global_state_between_tests(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="A")
        ctx2 = build_normalization_context(
            cli_mode="d10", cli_effective_from="2026-08-01T00:00:00Z", plant_id="B"
        )

        assert ctx.registry_mode == SignNormalizationMode.LEGACY
        assert ctx2.registry_mode == SignNormalizationMode.D10
        assert ctx2.effective_from is not None

    def test_off_context_has_none_registry(self) -> None:
        ctx = build_normalization_context(plant_id="SOLGREEN")
        assert ctx.registry_mode == SignNormalizationMode.OFF
        assert ctx.sign_registry is None

    def test_context_is_frozen_dataclass(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        with pytest.raises(FrozenInstanceError):
            ctx.plant_id = "other"  # type: ignore[misc]
