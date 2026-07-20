from solgreen.diagnostics.severity import SEVERITY_ORDER, severity_gte


class TestSeverityLevel:
    def test_all_levels_present(self) -> None:
        expected = {"info", "low", "medium", "high", "critical"}
        assert set(SEVERITY_ORDER.keys()) == expected

    def test_ordering(self) -> None:
        assert SEVERITY_ORDER["info"] < SEVERITY_ORDER["low"]
        assert SEVERITY_ORDER["low"] < SEVERITY_ORDER["medium"]
        assert SEVERITY_ORDER["medium"] < SEVERITY_ORDER["high"]
        assert SEVERITY_ORDER["high"] < SEVERITY_ORDER["critical"]


class TestSeverityGte:
    def test_equal_returns_true(self) -> None:
        assert severity_gte("medium", "medium") is True

    def test_greater_returns_true(self) -> None:
        assert severity_gte("high", "low") is True

    def test_less_returns_false(self) -> None:
        assert severity_gte("info", "critical") is False
