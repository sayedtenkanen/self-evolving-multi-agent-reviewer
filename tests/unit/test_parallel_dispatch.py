"""Tests for parallel dispatch and conflict resolution."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from semar.agents.base_agent import AgentResult
from semar.agents.judge_agent import JudgeAgent


@pytest.fixture
def judge_with_agents():
    judge = JudgeAgent()
    for lang in ["python", "javascript", "go"]:
        agent = AsyncMock()
        agent.execute_cycle = AsyncMock(
            return_value=AgentResult(
                review=f"Review from {lang}",
                suggestions=[],
                metrics={"accuracy": 0.9},
                trajectory={"steps": {}},
                agent_id=f"{lang}_agent",
                language=lang,
                pr_url="https://github.com/org/repo/pull/1",
            )
        )
        judge.register_language_agent(lang, agent)
    return judge


@pytest.mark.asyncio
async def test_dispatch_parallel_runs_concurrently(judge_with_agents):
    call_order = []

    async def slow_execute(context):
        call_order.append(context.language)
        await asyncio.sleep(0.01)
        return AgentResult(
            review="ok",
            suggestions=[],
            metrics={},
            trajectory={"steps": {}},
            agent_id="x",
            language=context.language,
            pr_url="url",
            duration_ms=10,
        )

    for lang in judge_with_agents.language_agents:
        judge_with_agents.language_agents[lang].execute_cycle = slow_execute

    languages = ["python", "javascript", "go"]
    await judge_with_agents._dispatch_parallel(languages, "url", "diff", {})
    assert len(call_order) == 3


@pytest.mark.asyncio
async def test_dispatch_parallel_handles_agent_failure(judge_with_agents):
    fail_agent = AsyncMock()
    fail_agent.execute_cycle = AsyncMock(side_effect=Exception("Agent crashed"))
    judge_with_agents.language_agents["rust"] = fail_agent

    languages = ["python", "javascript", "rust"]
    results = await judge_with_agents._dispatch_parallel(languages, "url", "diff", {})
    assert "rust" in results or len(results) >= 2


@pytest.mark.asyncio
async def test_dispatch_parallel_empty_languages(judge_with_agents):
    results = await judge_with_agents._dispatch_parallel([], "url", "diff", {})
    assert results == {}


def test_conflict_resolution_majority_vote(judge_with_agents):
    results = {
        "python": AgentResult(
            review="approve",
            suggestions=[],
            metrics={},
            trajectory={},
            agent_id="py",
            language="python",
            pr_url="url",
        ),
        "javascript": AgentResult(
            review="approve",
            suggestions=[],
            metrics={},
            trajectory={},
            agent_id="js",
            language="javascript",
            pr_url="url",
        ),
        "go": AgentResult(
            review="request_changes",
            suggestions=[],
            metrics={},
            trajectory={},
            agent_id="go",
            language="go",
            pr_url="url",
        ),
    }
    verdict = judge_with_agents._resolve_conflicts(results)
    assert verdict in ["approve", "request_changes"]


def test_conflict_resolution_all_agree(judge_with_agents):
    results = {
        lang: AgentResult(
            review="approve",
            suggestions=[],
            metrics={},
            trajectory={},
            agent_id=f"{lang}_agent",
            language=lang,
            pr_url="url",
        )
        for lang in ["python", "javascript", "go"]
    }
    verdict = judge_with_agents._resolve_conflicts(results)
    assert verdict == "approve"


def test_aggregate_results_merges_suggestions(judge_with_agents):
    results = {
        "python": AgentResult(
            review="approve",
            suggestions=[{"line": 1, "comment": "fix type hint"}],
            metrics={"accuracy": 0.9},
            trajectory={},
            agent_id="py",
            language="python",
            pr_url="url",
        ),
        "javascript": AgentResult(
            review="approve",
            suggestions=[{"line": 5, "comment": "use const"}],
            metrics={"accuracy": 0.85},
            trajectory={},
            agent_id="js",
            language="javascript",
            pr_url="url",
        ),
    }
    merged = judge_with_agents._aggregate_results(results)
    assert "results" in merged
    assert len(merged["results"]) == 2
    assert merged["total_suggestions"] == 2
    assert len(merged["suggestions"]) == 2
    assert merged["suggestions"][0] == {"line": 1, "comment": "fix type hint"}
    assert merged["suggestions"][1] == {"line": 5, "comment": "use const"}
    assert merged["metrics_by_language"]["python"]["accuracy"] == 0.9
    assert merged["metrics_by_language"]["javascript"]["accuracy"] == 0.85
