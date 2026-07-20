from solgreen.diagnostics.rule_catalog import SEED_RULES, RuleCatalog


class TestRuleCatalog:
    def test_default_has_seed_rules(self) -> None:
        catalog = RuleCatalog()
        rules = catalog.list_rules()
        assert len(rules) == 5

    def test_get_existing_rule(self) -> None:
        catalog = RuleCatalog()
        rule = catalog.get("DATA-001")
        assert rule is not None
        assert rule.name == "Intervalo ausente"
        assert rule.category == "data"

    def test_get_nonexistent_returns_none(self) -> None:
        catalog = RuleCatalog()
        assert catalog.get("NONEXISTENT") is None

    def test_list_by_category(self) -> None:
        catalog = RuleCatalog()
        data_rules = catalog.list_by_category("data")
        assert len(data_rules) == 1
        assert data_rules[0].rule_id == "DATA-001"

    def test_list_by_category_empty(self) -> None:
        catalog = RuleCatalog()
        assert catalog.list_by_category("nonexistent") == []

    def test_custom_rules(self) -> None:
        from solgreen.diagnostics.rule import Rule

        custom = Rule(
            rule_id="CUSTOM-001",
            name="Custom",
            category="data",
            question="Test?",
            signals_required=("x",),
            base_severity="info",
        )
        catalog = RuleCatalog(rules=[custom])
        assert len(catalog.list_rules()) == 1
        assert catalog.get("CUSTOM-001") is custom

    def test_seed_rules_have_required_fields(self) -> None:
        for rule in SEED_RULES:
            assert rule.rule_id
            assert rule.name
            assert rule.question
            assert rule.signals_required
            assert rule.base_severity
