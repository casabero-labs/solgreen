from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from solgreen.contracts import (
    SIGNAL_SPECS,
    ImportBatch,
    ImportMetadata,
    ImportStatus,
    InverterTelemetrySample,
    PlantFlowSample,
    QualitySummary,
    SeverityLevel,
    SignalKind,
    SourceType,
    ValidityFlags,
    ValidityReason,
)


def test_signal_specs_complete_and_unique() -> None:
    indices = [s.index for s in SIGNAL_SPECS]
    names = [s.canonical_name for s in SIGNAL_SPECS]

    assert len(SIGNAL_SPECS) == 120
    assert indices == list(range(1, 121))
    assert len(set(indices)) == 120
    assert len(set(names)) == 120


def test_signal_specs_groups_and_kinds_known() -> None:
    known_groups = {
        "identificacion",
        "pv_mppt",
        "salida_ac",
        "red",
        "cargas",
        "bus",
        "bateria",
        "temperaturas",
        "estados",
        "generador",
        "paralelo",
    }
    for spec in SIGNAL_SPECS:
        assert spec.kind in SignalKind
        assert spec.group in known_groups
        assert spec.unit
        assert spec.original_es


def test_priority_subset_non_empty_and_subset() -> None:
    priority = {s.canonical_name for s in SIGNAL_SPECS if s.priority}
    assert priority
    assert priority.issubset({s.canonical_name for s in SIGNAL_SPECS})


def test_validity_flags_default_is_valid() -> None:
    flags = ValidityFlags()
    assert flags.is_valid is True
    assert flags.reasons == ()


def test_validity_flags_with_reason_marks_invalid() -> None:
    flags = ValidityFlags().with_reason(ValidityReason.PARSE_ERROR)
    assert flags.is_valid is False
    assert flags.reasons == (ValidityReason.PARSE_ERROR,)


def test_validity_flags_idempotent_reason() -> None:
    flags = (
        ValidityFlags()
        .with_reason(ValidityReason.NOT_MEASURED)
        .with_reason(ValidityReason.NOT_MEASURED)
    )
    assert flags.reasons == (ValidityReason.NOT_MEASURED,)


def test_validity_flags_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        ValidityFlags(is_valid=True, extra_field=True)  # type: ignore[call-arg]


def test_plant_flow_sample_minimal() -> None:
    ts = datetime(2026, 7, 17, 12, 37, tzinfo=UTC)
    sample = PlantFlowSample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        potencia_de_produccion_w=4200.0,
        soc_pct=72.5,
    )
    assert sample.timestamp_utc == ts
    assert sample.potencia_de_produccion_w == 4200.0
    assert sample.validity.is_valid


def test_plant_flow_sample_soc_out_of_range_rejected() -> None:
    ts = datetime(2026, 7, 17, 12, 37, tzinfo=UTC)
    with pytest.raises(ValidationError):
        PlantFlowSample(
            timestamp_original=ts,
            timestamp_utc=ts,
            timezone_source="UTC",
            soc_pct=150.0,
        )


def test_plant_flow_sample_extra_forbidden() -> None:
    ts = datetime(2026, 7, 17, 12, 37, tzinfo=UTC)
    with pytest.raises(ValidationError):
        PlantFlowSample(
            timestamp_original=ts,
            timestamp_utc=ts,
            timezone_source="UTC",
            unknown_field=1.0,  # type: ignore[call-arg]
        )


def test_inverter_telemetry_sample_round_trip_get_float() -> None:
    ts = datetime(2026, 7, 17, 12, 37, tzinfo=UTC)
    sample = InverterTelemetrySample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="America/Bogota",
        device_name="INV-001",
        serial_redacted="redacted:abc",
        signals={
            "voltaje_cc_pv1_v": 312.4,
            "potencia_cc_pv1_w": 2100.0,
            "soc_pct": 71.2,
            "current_state_of_machine": "running",
        },
    )
    assert sample.get_float("voltaje_cc_pv1_v") == 312.4
    assert sample.get_float("soc_pct") == 71.2
    assert sample.get_float("not_a_signal") is None
    assert sample.get_float("current_state_of_machine") is None


def test_inverter_telemetry_sample_get_text_returns_str_value() -> None:
    ts = datetime(2026, 7, 17, 12, 37, tzinfo=UTC)
    sample = InverterTelemetrySample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        signals={"current_state_of_machine": "Standby"},
    )
    assert sample.get_text("current_state_of_machine") == "Standby"


def test_inverter_telemetry_sample_get_text_returns_none_when_missing() -> None:
    ts = datetime(2026, 7, 17, 12, 37, tzinfo=UTC)
    sample = InverterTelemetrySample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        signals={},
    )
    assert sample.get_text("current_state_of_machine") is None


def test_inverter_telemetry_sample_get_text_returns_none_when_numeric() -> None:
    ts = datetime(2026, 7, 17, 12, 37, tzinfo=UTC)
    sample = InverterTelemetrySample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        signals={"current_state_of_machine": 0},
    )
    assert sample.get_text("current_state_of_machine") is None


def test_inverter_telemetry_sample_get_text_strips_whitespace() -> None:
    ts = datetime(2026, 7, 17, 12, 37, tzinfo=UTC)
    sample = InverterTelemetrySample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        signals={"current_state_of_machine": "  Standby  "},
    )
    assert sample.get_text("current_state_of_machine") == "Standby"


def test_inverter_telemetry_sample_rejects_unknown_signal_name() -> None:
    ts = datetime(2026, 7, 17, 12, 37, tzinfo=UTC)
    with pytest.raises(ValidationError):
        InverterTelemetrySample(
            timestamp_original=ts,
            timestamp_utc=ts,
            timezone_source="UTC",
            signals={"invented_signal": 1.0},
        )


def test_quality_summary_requires_rows_non_negative() -> None:
    with pytest.raises(ValidationError):
        QualitySummary(rows_total=-1, rows_parsed=0, rows_rejected=0, detected_columns=())


def test_import_metadata_validates_sha256() -> None:
    base = {
        "source_type": SourceType.SOLARMAN_PLANT_FLOW,
        "original_filename": "flow.csv",
        "sha256": "z" * 64,
        "byte_size": 1024,
        "parser_id": "solarman_flow_csv",
        "parser_version": "0.1.0",
        "imported_at": datetime.now(UTC),
    }
    with pytest.raises(ValidationError):
        ImportMetadata(**base)

    base["sha256"] = "a" * 64
    metadata = ImportMetadata(**base)
    assert metadata.sha256 == "a" * 64


def test_import_batch_default_id_and_status() -> None:
    batch = ImportBatch(
        plant_id="casabero",
        metadata=ImportMetadata(
            source_type=SourceType.SOLARMAN_PLANT_FLOW,
            original_filename="flow.csv",
            sha256="a" * 64,
            byte_size=2048,
            parser_id="solarman_flow_csv",
            parser_version="0.1.0",
            imported_at=datetime.now(UTC),
        ),
    )
    assert isinstance(batch.id, UUID)
    assert batch.status == ImportStatus.PENDING
    assert batch.quality_summary is None


def test_import_batch_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        ImportBatch(
            plant_id="casabero",
            metadata=ImportMetadata(
                source_type=SourceType.SOLARMAN_PLANT_FLOW,
                original_filename="flow.csv",
                sha256="a" * 64,
                byte_size=1,
                parser_id="x",
                parser_version="0.1.0",
                imported_at=datetime.now(UTC),
            ),
            extra_field="nope",  # type: ignore[call-arg]
        )


def test_severity_levels_present() -> None:
    assert {s.value for s in SeverityLevel} == {"info", "low", "medium", "high", "critical"}


def test_naive_then_aware_timestamp_distinguishable() -> None:
    naive = PlantFlowSample(
        timestamp_original=datetime(2026, 7, 17, 12, 37),
        timestamp_utc=datetime(2026, 7, 17, 17, 37, tzinfo=UTC),
        timezone_source="America/Bogota",
    )
    assert naive.timestamp_original.tzinfo is None
    assert naive.timestamp_utc.tzinfo is UTC
    assert naive.timestamp_utc.tzinfo == UTC
