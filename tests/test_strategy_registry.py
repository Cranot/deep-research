"""Tests for the strategy registry.

Regression cover for the collision where perspective_strategy() and
grounded_research_strategy() both delegated to recursive_research_strategy(),
which hardcoded name="recursive_research". Four registrations collapsed into
two keys, two advertised strategies became unreachable, and the surviving
"recursive_research" key silently resolved to the *grounded* variant -- which
runs a live web-search phase.
"""

from deep_research.core.strategy import (
    StrategyRegistry,
    grounded_research_strategy,
    perspective_strategy,
    recursive_research_strategy,
    register_builtin_strategies,
    socratic_strategy,
)

EXPECTED_BUILTINS = {
    "recursive_research",
    "socratic",
    "perspective_expander",
    "grounded_research",
}


def test_builtin_names_are_distinct():
    """Every builder must produce its own registry key."""
    names = [
        recursive_research_strategy().metadata.name,
        socratic_strategy().metadata.name,
        perspective_strategy().metadata.name,
        grounded_research_strategy().metadata.name,
    ]
    assert len(names) == len(set(names)), f"duplicate strategy names: {names}"
    assert set(names) == EXPECTED_BUILTINS


def test_all_builtins_are_addressable():
    """All four advertised strategies must resolve from the registry."""
    register_builtin_strategies()
    registry = StrategyRegistry.instance()
    available = set(registry.available())

    assert EXPECTED_BUILTINS <= available
    for name in EXPECTED_BUILTINS:
        assert registry.get(name) is not None, f"{name} is not addressable"
        assert registry.get(name).metadata.name == name


def test_recursive_research_does_not_run_web_search():
    """The plain strategy must not resolve to the grounded variant.

    This is the user-visible half of the collision: an unsuspecting caller
    asking for "recursive_research" got a live web-search phase.
    """
    register_builtin_strategies()
    strategy = StrategyRegistry.instance().get("recursive_research")

    phase_names = [p.name for p in strategy.phases]
    assert "ground_answers" not in phase_names
    assert "web-search" not in strategy.metadata.tags

    grounded = StrategyRegistry.instance().get("grounded_research")
    assert "ground_answers" in [p.name for p in grounded.phases]


def test_perspective_expander_has_perspective_phases():
    register_builtin_strategies()
    strategy = StrategyRegistry.instance().get("perspective_expander")

    phase_names = [p.name for p in strategy.phases]
    assert "expand_perspectives" in phase_names
    assert "detect_domain" in phase_names


def test_register_builtins_is_idempotent():
    """chef.MasterChef re-registers on every construction."""
    register_builtin_strategies()
    first = sorted(StrategyRegistry.instance().available())
    register_builtin_strategies()
    assert sorted(StrategyRegistry.instance().available()) == first


def test_variant_without_distinct_name_is_rejected():
    """The guard in register_builtin_strategies must catch a re-introduction."""
    import pytest

    from deep_research.core import strategy as strategy_module

    original = strategy_module.perspective_strategy
    try:
        # Simulate the old bug: a variant that forgets to pass name=.
        strategy_module.perspective_strategy = lambda: recursive_research_strategy(
            perspectives=True
        )
        with pytest.raises(ValueError, match="collision"):
            strategy_module.register_builtin_strategies()
    finally:
        strategy_module.perspective_strategy = original
        strategy_module.register_builtin_strategies()
