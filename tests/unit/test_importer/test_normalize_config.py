from __future__ import annotations

import pytest

from solgreen.importer.normalize import (
    SignNormalizationMode,
    build_normalization_context,
)


class TestConfiguration:
    def test_default_off_preserves_behavior(self) -> None:
        ctx = build_normalization_context(plant_id="SOLGREEN")
        assert ctx.registry_mode == SignNormalizationMode.OFF
        assert ctx.sign_registry is None
        assert ctx.effective_from is None

    def test_invalid_mode_fails(self) -> None:
        with pytest.raises(ValueError, match="Unknown sign normalization mode"):
            build_normalization_context(cli_mode="invalid", plant_id="test")

    def test_off_with_effective_from_fails(self) -> None:
        with pytest.raises(ValueError, match="OFF does not accept effective_from"):
            build_normalization_context(
                cli_mode="off",
                cli_effective_from="2026-08-01T00:00:00Z",
                plant_id="test",
            )

    def test_legacy_with_effective_from_fails(self) -> None:
        with pytest.raises(ValueError, match="LEGACY does not accept effective_from"):
            build_normalization_context(
                cli_mode="legacy",
                cli_effective_from="2026-08-01T00:00:00Z",
                plant_id="test",
            )

    def test_d10_without_effective_from_fails(self) -> None:
        with pytest.raises(ValueError, match="D10 requires effective_from"):
            build_normalization_context(cli_mode="d10", plant_id="test")

    def test_d10_with_naive_datetime_fails(self) -> None:
        with pytest.raises(ValueError, match="must be timezone-aware"):
            build_normalization_context(
                cli_mode="d10",
                cli_effective_from="2026-08-01T00:00:00",
                plant_id="test",
            )

    def test_d10_with_timezone_aware_works(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )
        assert ctx.registry_mode == SignNormalizationMode.D10
        assert ctx.sign_registry is not None
        assert ctx.sign_registry.count == 8
        assert ctx.effective_from is not None

    def test_legacy_without_effective_from_works(self) -> None:
        ctx = build_normalization_context(
            cli_mode="legacy",
            plant_id="SOLGREEN",
        )
        assert ctx.registry_mode == SignNormalizationMode.LEGACY
        assert ctx.sign_registry is not None
        assert ctx.sign_registry.count == 4
        assert ctx.effective_from is None

    def test_env_mode_fallback(self) -> None:
        ctx = build_normalization_context(
            env_mode="legacy",
            plant_id="SOLGREEN",
        )
        assert ctx.registry_mode == SignNormalizationMode.LEGACY

    def test_cli_overrides_env(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            env_mode="legacy",
            cli_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )
        assert ctx.registry_mode == SignNormalizationMode.D10

    def test_d10_accepts_offset_datetime(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-01T00:00:00+05:00",
            plant_id="SOLGREEN",
        )
        assert ctx.registry_mode == SignNormalizationMode.D10
        assert ctx.sign_registry is not None

    def test_d10_effective_from_env(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            env_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )
        assert ctx.effective_from is not None

    def test_cli_effective_from_overrides_env(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-15T00:00:00Z",
            env_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )
        assert ctx.effective_from is not None
        assert ctx.effective_from.isoformat() == "2026-08-15T00:00:00+00:00"
