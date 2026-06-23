"""Tests for JudgeAgent - orchestrator for language agents."""

from unittest.mock import AsyncMock

import pytest

from semar.agents.base_agent import AgentContext, AgentResult
from semar.agents.judge_agent import JudgeAgent


@pytest.fixture
def judge():
    return JudgeAgent()


@pytest.fixture
def mock_agent():
    agent = AsyncMock()
    agent.execute_cycle = AsyncMock(
        return_value=AgentResult(
            review="All good",
            suggestions=[],
            metrics={"accuracy": 0.9},
            trajectory={"steps": {}},
            agent_id="mock_agent",
            language="python",
            pr_url="https://github.com/org/repo/pull/1",
        )
    )
    return agent


@pytest.fixture
def sample_context():
    return AgentContext(
        pr_url="https://github.com/org/repo/pull/1",
        pr_diff="+def hello():\n    pass",
        pr_metadata={"files": ["main.py"]},
        language="python",
        files=["main.py"],
    )


def test_judge_initialization(judge):
    assert judge.agent_id == "judge"
    assert judge.language is None
    assert judge.language_agents == {}


def test_register_language_agent(judge, mock_agent):
    judge.register_language_agent("python", mock_agent)
    assert "python" in judge.language_agents
    assert judge.language_agents["python"] is mock_agent


def test_register_multiple_agents(judge, mock_agent):
    judge.register_language_agent("python", mock_agent)
    judge.register_language_agent("javascript", mock_agent)
    assert len(judge.language_agents) == 2


def test_detect_languages_from_diff(judge):
    diff = """
+import os
+def main():
+    pass
"""
    languages = judge._detect_languages(diff, {})
    assert "python" in languages


def test_detect_languages_mixed(judge):
    diff = """
+import os
+const x = 1;
+func main() {}
"""
    languages = judge._detect_languages(diff, {})
    assert len(languages) >= 2


def test_get_files_for_language(judge):
    diff = """
+--- a/main.py
+++ b/main.py
+import os
+--- a/app.js
+++ b/app.js
+const x = 1;
"""
    files = judge._get_files_for_language(diff, "python")
    assert isinstance(files, list)


@pytest.mark.asyncio
async def test_handle_pr_review_dispatches_to_agents(judge, mock_agent, sample_context):
    judge.register_language_agent("python", mock_agent)
    result = await judge.handle_pr_review(
        pr_url=sample_context.pr_url,
        pr_diff=sample_context.pr_diff,
        pr_metadata=sample_context.pr_metadata,
    )
    assert "review" in result or "results" in result


@pytest.mark.asyncio
async def test_handle_pr_review_no_agents_returns_empty(judge, sample_context):
    result = await judge.handle_pr_review(
        pr_url=sample_context.pr_url,
        pr_diff=sample_context.pr_diff,
        pr_metadata=sample_context.pr_metadata,
    )
    assert result is not None
