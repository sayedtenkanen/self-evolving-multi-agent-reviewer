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


@pytest.mark.asyncio
async def test_detect_hallucination(analyzer):
    trajectory = {
        "steps": {
            "action": {"output": {"hallucinated": True, "file": "nonexistent.py"}},
        },
        "metrics": {},
    }
    result = await analyzer.analyze(trajectory)
    failures = result["failure_modes"]
    hallucinations = [f for f in failures if f.type == "hallucination"]
    assert len(hallucinations) == 1
    assert hallucinations[0].severity == "high"


@pytest.mark.asyncio
async def test_detect_overconfident(analyzer):
    trajectory = {
        "steps": {},
        "metrics": {"confidence": 0.95, "accuracy": 0.5},
    }
    result = await analyzer.analyze(trajectory)
    failures = result["failure_modes"]
    overconfident = [f for f in failures if f.type == "overconfident"]
    assert len(overconfident) == 1
    assert overconfident[0].severity == "medium"


@pytest.mark.asyncio
async def test_truncation_of_examples(analyzer):
    trajectory = {
        "steps": {},
        "metrics": {},
        "human_follow_up": [{"issue": f"missed {i}"} for i in range(10)],
        "rejected_suggestions": [{"suggestion": f"sugg {i}"} for i in range(10)],
    }
    result = await analyzer.analyze(trajectory)
    failures = result["failure_modes"]
    missed = [f for f in failures if f.type == "missed_issue"]
    false_pos = [f for f in failures if f.type == "false_positive"]
    assert len(missed) == 1
    assert missed[0].frequency == 10
    assert len(missed[0].examples) == 5
    assert len(false_pos) == 1
    assert false_pos[0].frequency == 10
    assert len(false_pos[0].examples) == 5
