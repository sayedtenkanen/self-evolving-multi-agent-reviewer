"""Tests for Engine - integration layer wiring JudgeAgent, language agents, harness, and weights."""

import pytest

# ============================================================
# Engine Tests
# ============================================================


class TestEngine:
    """Tests for the Engine integration class."""

    def test_import(self):
        from semar.engine import Engine

        assert Engine is not None

    def test_init_defaults(self):
        from semar.engine import Engine

        eng = Engine()
        assert eng is not None
        assert hasattr(eng, "review_pr")
        assert hasattr(eng, "get_metrics")

    def test_init_with_config(self):
        from semar.engine import Engine

        eng = Engine(
            harness_update_interval=5,
            weight_update_interval=20,
        )
        assert eng.harness_interval == 5
        assert eng.weight_interval == 20

    @pytest.mark.asyncio
    async def test_review_pr_returns_result(self, engine, github_pr):
        result = await engine.review_pr(**github_pr)
        assert "verdict" in result
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_review_pr_adds_engine_metrics(self, engine, github_pr):
        """Engine.review_pr should augment metrics with review_count and duration_ms."""
        result = await engine.review_pr(**github_pr)

        assert "metrics" in result
        metrics = result["metrics"]

        # Engine-level metrics
        assert metrics["review_count"] == 1
        assert "duration_ms" in metrics
        assert isinstance(metrics["duration_ms"], (int, float))
        assert metrics["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_review_pr_preserves_agent_metrics(self, engine, github_pr):
        """Agent metrics like accuracy should be preserved in per-language results."""
        result = await engine.review_pr(**github_pr)

        # Agent metrics are preserved in per-language results
        lang_results = result.get("results", [])
        assert len(lang_results) > 0
        assert lang_results[0]["metrics"]["accuracy"] == 0.9
        # Engine metrics are added at top level
        assert result["metrics"]["review_count"] == 1

    @pytest.mark.asyncio
    async def test_review_pr_stores_trajectory(self, engine, github_pr):
        await engine.review_pr(**github_pr)
        assert engine._review_count == 1

    @pytest.mark.asyncio
    async def test_review_pr_increments_count(self, engine, github_pr):
        await engine.review_pr(**github_pr)
        await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/2",
            pr_diff="+y = 2",
            pr_metadata={"files": ["b.py"]},
        )
        assert engine._review_count == 2

    @pytest.mark.asyncio
    async def test_review_pr_no_languages_returns_approve(self):
        from semar.engine import Engine

        eng = Engine()
        result = await eng.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="no code here",
            pr_metadata={"files": ["readme.md"]},
        )
        assert result["verdict"] == "approve"

    @pytest.mark.asyncio
    async def test_get_metrics(self, engine, github_pr):
        await engine.review_pr(**github_pr)
        metrics = engine.get_metrics()
        assert metrics["total_reviews"] == 1
        assert "harness_updates" in metrics
        assert "weight_updates" in metrics

    def test_get_status(self):
        from semar.engine import Engine

        eng = Engine()
        status = eng.get_status()
        assert "review_count" in status
        assert "registered_agents" in status


# ============================================================
# Engine with Custom Agents
# ============================================================


class TestEngineWithAgents:
    """Tests for Engine with registered language agents."""

    @pytest.mark.asyncio
    async def test_register_language_agent(self):
        from semar.engine import Engine

        eng = Engine()

        class _Agent:
            async def execute_cycle(self, ctx):
                from semar.agents.base_agent import AgentResult

                return AgentResult(
                    review="approve",
                    suggestions=[],
                    metrics={"accuracy": 0.9},
                    trajectory={},
                    agent_id="mock",
                    language="python",
                    pr_url=ctx.pr_url,
                )

        eng.register_agent("python", _Agent())
        assert "python" in eng.list_agents()

    @pytest.mark.asyncio
    async def test_review_dispatches_to_agents(self, engine, github_pr):
        result = await engine.review_pr(**github_pr)
        assert result["verdict"] in ("approve", "request_changes")


# ============================================================
# Engine Self-Improvement Integration
# ============================================================


class TestEngineSelfImprovement:
    """Tests for Engine self-improvement integration."""

    @pytest.mark.asyncio
    async def test_harness_evolution_updates_agents(self):
        from semar.engine import Engine

        eng = Engine(harness_update_interval=1)

        class _Agent:
            def __init__(self):
                self.scaffold = {"prompts": {"system": "base prompt"}}

            async def execute_cycle(self, ctx):
                from semar.agents.base_agent import AgentResult

                return AgentResult(
                    review="approve",
                    suggestions=[],
                    metrics={"accuracy": 0.5},
                    trajectory={
                        "steps": {"review": {"output": {"review": "missed SQL injection"}}},
                        "human_follow_up": [{"issue": "SQL injection found"}],
                    },
                    agent_id="mock",
                    language="python",
                    pr_url=ctx.pr_url,
                )

        agent = _Agent()
        eng.register_agent("python", agent)
        await eng.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["test.py"]},
        )
        assert eng._harness_update_count >= 1

    @pytest.mark.asyncio
    async def test_weight_training_triggered_on_stall(self):
        from semar.engine import Engine

        eng = Engine(weight_update_interval=1)

        class _Agent:
            async def execute_cycle(self, ctx):
                from semar.agents.base_agent import AgentResult

                return AgentResult(
                    review="approve",
                    suggestions=[],
                    metrics={"accuracy": 0.5, "improvement": 0.0},
                    trajectory={},
                    agent_id="mock",
                    language="python",
                    pr_url=ctx.pr_url,
                )

        eng.register_agent("python", _Agent())
        await eng.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["test.py"]},
        )
        assert eng._weight_update_count >= 1

    @pytest.mark.asyncio
    async def test_both_updates_on_same_cycle(self):
        from semar.engine import Engine

        eng = Engine(harness_update_interval=1, weight_update_interval=1)
        await eng.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+x = 1",
            pr_metadata={"files": ["a.py"]},
        )
        assert eng._harness_update_count >= 1
        assert eng._weight_update_count >= 1

    @pytest.mark.asyncio
    async def test_scaffold_none_does_not_crash(self):
        from semar.engine import Engine

        eng = Engine(harness_update_interval=1)

        class _AgentNoScaffold:
            async def execute_cycle(self, ctx):
                from semar.agents.base_agent import AgentResult

                return AgentResult(
                    review="approve",
                    suggestions=[],
                    metrics={},
                    trajectory={},
                    agent_id="mock",
                    language="python",
                    pr_url=ctx.pr_url,
                )

        eng.register_agent("python", _AgentNoScaffold())
        await eng.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["test.py"]},
        )

    @pytest.mark.asyncio
    async def test_harness_update_triggered_at_interval(self):
        from semar.engine import Engine

        eng = Engine(harness_update_interval=3)
        for i in range(3):
            await eng.review_pr(
                pr_url=f"https://github.com/test/repo/pull/{i}",
                pr_diff=f"+x = {i}",
                pr_metadata={"files": [f"f{i}.py"]},
            )
        assert eng._harness_update_count >= 1

    @pytest.mark.asyncio
    async def test_weight_update_triggered_at_interval(self):
        from semar.engine import Engine

        eng = Engine(weight_update_interval=2)
        for i in range(2):
            await eng.review_pr(
                pr_url=f"https://github.com/test/repo/pull/{i}",
                pr_diff=f"+x = {i}",
                pr_metadata={"files": [f"f{i}.py"]},
            )
        assert eng._weight_update_count >= 1
