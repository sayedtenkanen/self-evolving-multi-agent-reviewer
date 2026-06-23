"""Tests for TrajectoryAnalyzer - failure mode detection and trajectory analysis."""

import pytest

from semar.agents.trajectory_analyzer import FailureMode, TrajectoryAnalyzer


@pytest.fixture
def analyzer():
    return TrajectoryAnalyzer()


@pytest.fixture
def healthy_trajectory():
    return {
        "steps": {
            "plan": {"output": {"files": ["main.py"]}},
            "action": {"output": {"review": "Looks good"}},
            "review": {"output": "approved", "metrics": {"accuracy": 0.95}},
        },
        "metrics": {"accuracy": 0.95, "duration_ms": 150},
    }


@pytest.fixture
def failed_trajectory():
    return {
        "steps": {
            "plan": {"output": {"files": ["main.py"]}},
            "action": {"output": {"review": "No issues found"}},
            "review": {"output": "approved", "metrics": {"accuracy": 0.5}},
        },
        "metrics": {"accuracy": 0.5, "duration_ms": 200},
        "human_follow_up": [{"issue": "missed SQL injection", "file": "db.py"}],
        "rejected_suggestions": [{"suggestion": "unused import", "reason": "false positive"}],
    }


@pytest.mark.asyncio
async def test_analyze_returns_all_sections(analyzer, healthy_trajectory):
    result = await analyzer.analyze(healthy_trajectory)
    assert "prompts" in result
    assert "responses" in result
    assert "tool_calls" in result
    assert "metrics" in result
    assert "failure_modes" in result


@pytest.mark.asyncio
async def test_analyze_healthy_trajectory_no_failures(analyzer, healthy_trajectory):
    result = await analyzer.analyze(healthy_trajectory)
    assert len(result["failure_modes"]) == 0


@pytest.mark.asyncio
async def test_detect_missed_issue(analyzer, failed_trajectory):
    result = await analyzer.analyze(failed_trajectory)
    failures = result["failure_modes"]
    missed = [f for f in failures if f.type == "missed_issue"]
    assert len(missed) == 1
    assert missed[0].severity == "high"
    assert missed[0].frequency == 1


@pytest.mark.asyncio
async def test_detect_false_positive(analyzer, failed_trajectory):
    result = await analyzer.analyze(failed_trajectory)
    failures = result["failure_modes"]
    false_pos = [f for f in failures if f.type == "false_positive"]
    assert len(false_pos) == 1
    assert false_pos[0].severity == "medium"
    assert false_pos[0].frequency == 1


@pytest.mark.asyncio
async def test_analyze_empty_trajectory(analyzer):
    result = await analyzer.analyze({})
    assert "failure_modes" in result
    assert len(result["failure_modes"]) == 0


@pytest.mark.asyncio
async def test_analyze_metrics(analyzer, healthy_trajectory):
    result = await analyzer.analyze(healthy_trajectory)
    assert "accuracy" in result["metrics"]
    assert result["metrics"]["accuracy"] == 0.95


class TestFailureMode:
    def test_failure_mode_creation(self):
        fm = FailureMode(
            type="missed_issue",
            severity="high",
            frequency=1,
            examples=[{"issue": "test"}],
        )
        assert fm.type == "missed_issue"
        assert fm.severity == "high"
        assert fm.frequency == 1
