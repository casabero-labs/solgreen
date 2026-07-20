from enum import StrEnum


class SourceType(StrEnum):
    SOLARMAN_PLANT_FLOW = "solarman_plant_flow"
    SOLARMAN_INVERTER_TELEMETRY = "solarman_inverter_telemetry"
    UNKNOWN = "unknown"


class ImportStatus(StrEnum):
    PENDING = "pending"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class ParserStatus(StrEnum):
    OK = "ok"
    PARTIAL = "partial"
    REJECTED = "rejected"


class SeverityLevel(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalKind(StrEnum):
    POWER_W = "power_w"
    ENERGY_WH = "energy_wh"
    VOLTAGE_V = "voltage_v"
    CURRENT_A = "current_a"
    FREQUENCY_HZ = "frequency_hz"
    SOC_PCT = "soc_pct"
    TEMPERATURE_C = "temperature_c"
    RATIO_PCT = "ratio_pct"
    TIME = "time"
    TEXT = "text"
    STATUS = "status"
    VERSION = "version"
    COUNT = "count"
