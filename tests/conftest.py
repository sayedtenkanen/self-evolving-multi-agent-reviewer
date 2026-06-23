"""Shared fixtures for SEMAR tests."""

import pytest


class _MockAgent:
    """Lightweight mock agent for unit tests."""

    def __init__(self, metrics=None):
        self.scaffold = {"prompts": {"system": "base prompt"}, "rules": []}
        self._metrics = metrics or {"accuracy": 0.9}

    async def execute_cycle(self, ctx):
        from semar.agents.base_agent import AgentResult

        return AgentResult(
            review="approve",
            suggestions=[],
            metrics=dict(self._metrics),
            trajectory={},
            agent_id="mock",
            language="python",
            pr_url=ctx.pr_url,
        )


@pytest.fixture
def github_pr():
    """Minimal PR payload for engine.review_pr()."""
    return {
        "pr_url": "https://github.com/test/repo/pull/1",
        "pr_diff": "+import os",
        "pr_metadata": {"files": ["test.py"]},
    }


@pytest.fixture
def engine():
    """Engine with a single Python mock agent registered."""
    from semar.engine import Engine

    eng = Engine(harness_update_interval=100, weight_update_interval=100)
    eng.register_agent("python", _MockAgent())
    return eng
