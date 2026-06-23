"""Tests for ImprovementSelector - decides harness vs weight update."""

import pytest

from semar.agents.improvement_selector import ImprovementSelector, ImprovementType


@pytest.fixture
def selector():
    return ImprovementSelector(stall_threshold=3)


@pytest.fixture
def analysis_with_failures():
    return {
        "metrics": {"accuracy": 0.7},
        "failure_modes": [{"type": "missed_issue", "severity": "high", "frequency": 1, "examples": []}],
    }


@pytest.fixture
def analysis_healthy():
    return {
        "metrics": {"accuracy": 0.95, "improvement": 0.05},
        "failure_modes": [],
    }


@pytest.mark.asyncio
async def test_decide_returns_harness_when_failures_present(selector, analysis_with_failures):
    result = await selector.decide(analysis_with_failures)
    assert result == ImprovementType.HARNESS


@pytest.mark.asyncio
async def test_decide_returns_none_when_healthy(selector, analysis_healthy):
    result = await selector.decide(analysis_healthy)
    assert result == ImprovementType.NONE


@pytest.mark.asyncio
async def test_decide_returns_weight_when_stalled(selector):
    selector.consecutive_no_improvement = 3
    analysis = {
        "metrics": {"accuracy": 0.5, "improvement": 0.0},
        "failure_modes": [],
    }
    result = await selector.decide(analysis)
    assert result == ImprovementType.WEIGHT


@pytest.mark.asyncio
async def test_stall_counter_increments(selector):
    stalled_analysis = {
        "metrics": {"accuracy": 0.5, "improvement": 0.0},
        "failure_modes": [],
    }
    await selector.decide(stalled_analysis)
    await selector.decide(stalled_analysis)
    assert selector.consecutive_no_improvement == 2


@pytest.mark.asyncio
async def test_decide_returns_none_when_not_stalled(selector):
    analysis = {
        "metrics": {"accuracy": 0.8, "improvement": 0.0},
        "failure_modes": [],
    }
    result = await selector.decide(analysis)
    assert result == ImprovementType.NONE
    assert selector.consecutive_no_improvement == 1


@pytest.mark.asyncio
async def test_stall_counter_resets_on_improvement(selector):
    stalled = {"metrics": {"accuracy": 0.5, "improvement": 0.0}, "failure_modes": []}
    improved = {"metrics": {"accuracy": 0.6, "improvement": 0.1}, "failure_modes": []}
    await selector.decide(stalled)
    await selector.decide(stalled)
    await selector.decide(improved)
    assert selector.consecutive_no_improvement == 0


@pytest.mark.asyncio
async def test_stall_threshold_triggers_weight(selector):
    stalled = {"metrics": {"accuracy": 0.5, "improvement": 0.0}, "failure_modes": []}
    for _ in range(3):
        await selector.decide(stalled)
    result = await selector.decide(stalled)
    assert result == ImprovementType.WEIGHT


class TestImprovementType:
    def test_enum_values(self):
        assert ImprovementType.HARNESS.value == "harness"
        assert ImprovementType.WEIGHT.value == "weight"
        assert ImprovementType.NONE.value == "none"
