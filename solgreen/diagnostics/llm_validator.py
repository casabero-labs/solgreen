from __future__ import annotations

from solgreen.diagnostics.llm_input import LLMEpisodeInput
from solgreen.diagnostics.llm_output import LLMInterpretation


def validate_interpretation(
    interp: LLMInterpretation,
    input_data: LLMEpisodeInput,
) -> list[str]:
    errors: list[str] = []

    if not interp.summary.strip():
        errors.append("summary must not be empty")

    fired_evidence_count = sum(len(r.evidence) for r in input_data.fired_rules if r.fired)

    for i, hyp in enumerate(interp.hypotheses):
        for ref in hyp.evidence_refs:
            if ref < 0 or ref >= fired_evidence_count:
                errors.append(
                    f"hypothesis[{i}].evidence_refs contains invalid ref {ref} "
                    f"(valid range: 0..{fired_evidence_count - 1})"
                )

    if interp.prohibited_claims:
        errors.append("prohibited_claims must always be empty")

    if not interp.provider.strip():
        errors.append("provider must not be empty")

    if not interp.model.strip():
        errors.append("model must not be empty")

    if not interp.prompt_version.strip():
        errors.append("prompt_version must not be empty")

    if not interp.input_hash.strip():
        errors.append("input_hash must not be empty")

    return errors
