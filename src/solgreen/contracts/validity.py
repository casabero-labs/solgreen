from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ValidityReason(StrEnum):
    NOT_MEASURED = "not_measured"
    NOT_APPLICABLE = "not_applicable"
    SUPPRESSED = "suppressed"
    PARSE_ERROR = "parse_error"
    OUT_OF_RANGE = "out_of_range"
    DUPLICATE = "duplicate"


class ValidityFlags(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    is_valid: bool = Field(default=True, description="True si la muestra es usable por análisis.")
    reasons: tuple[ValidityReason, ...] = Field(
        default_factory=tuple,
        description="Razones por las que la muestra no es válida.",
    )

    def with_reason(self, reason: ValidityReason) -> "ValidityFlags":
        if reason in self.reasons:
            return self
        return ValidityFlags(is_valid=self.is_valid and False, reasons=(*self.reasons, reason))
