from solgreen.diagnostics.llm_output import Hypothesis, LLMInterpretation


class TestHypothesis:
    def test_creation(self) -> None:
        h = Hypothesis(
            description="MPPT failure",
            support_level="strong",
            evidence_refs=(0, 1),
        )
        assert h.description == "MPPT failure"
        assert h.support_level == "strong"
        assert h.evidence_refs == (0, 1)


class TestLLMInterpretation:
    def test_creation(self) -> None:
        interp = LLMInterpretation(
            summary="PV dropout detected.",
            hypotheses=(
                Hypothesis(description="MPPT fault", support_level="moderate", evidence_refs=(0,)),
            ),
            alternatives=("Cloud cover.",),
            missing_info=("Inverter log.",),
            suggested_actions=("Check MPPT.",),
            warnings=("Do not reset inverter remotely.",),
            provider="openai",
            model="gpt-4",
            prompt_version="1.0.0",
            input_hash="abc123",
        )
        assert interp.summary == "PV dropout detected."
        assert len(interp.hypotheses) == 1
        assert interp.hypotheses[0].support_level == "moderate"
        assert interp.prohibited_claims == ()
        assert interp.provider == "openai"

    def test_defaults(self) -> None:
        interp = LLMInterpretation(
            summary="Test.",
            provider="test",
            model="test",
            prompt_version="1.0",
            input_hash="x",
        )
        assert interp.hypotheses == ()
        assert interp.alternatives == ()
        assert interp.warnings == ()
