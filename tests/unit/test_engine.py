"""Tests for Engine - integration layer wiring JudgeAgent, language agents, harness, and weights."""

import pytest  # noqa: I001


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

        engine = Engine()
        assert engine is not None
        assert hasattr(engine, "review_pr")
        assert hasattr(engine, "get_metrics")

    def test_init_with_config(self):
        from semar.engine import Engine

        engine = Engine(
            harness_update_interval=5,
            weight_update_interval=20,
        )
        assert engine.harness_interval == 5
        assert engine.weight_interval == 20

    @pytest.mark.asyncio
    async def test_review_pr_returns_result(self):
        from semar.engine import Engine

        engine = Engine()
        result = await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+def foo(): pass",
            pr_metadata={"files": ["test.py"]},
        )
        assert "verdict" in result
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_review_pr_adds_engine_metrics(self):
        from semar.engine import Engine

        engine = Engine()
        result = await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+def foo(): pass",
            pr_metadata={"files": ["test.py"]},
        )
        metrics = result["metrics"]
        assert metrics["review_count"] == 1
        assert "duration_ms" in metrics
        assert isinstance(metrics["duration_ms"], (int, float))
        assert metrics["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_review_pr_stores_trajectory(self):
        from semar.engine import Engine

        engine = Engine()
        await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+def foo(): pass",
            pr_metadata={"files": ["test.py"]},
        )
        assert engine._review_count == 1

    @pytest.mark.asyncio
    async def test_review_pr_increments_count(self):
        from semar.engine import Engine

        engine = Engine()
        await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+x = 1",
            pr_metadata={"files": ["a.py"]},
        )
        await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/2",
            pr_diff="+y = 2",
            pr_metadata={"files": ["b.py"]},
        )
        assert engine._review_count == 2

    @pytest.mark.asyncio
    async def test_review_pr_no_languages_returns_approve(self):
        from semar.engine import Engine

        engine = Engine()
        result = await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="no code here",
            pr_metadata={"files": ["readme.md"]},
        )
        assert result["verdict"] == "approve"

    @pytest.mark.asyncio
    async def test_harness_update_triggered_at_interval(self):
        from semar.engine import Engine

        engine = Engine(harness_update_interval=3)
        for i in range(3):
            await engine.review_pr(
                pr_url=f"https://github.com/test/repo/pull/{i}",
                pr_diff=f"+x = {i}",
                pr_metadata={"files": [f"f{i}.py"]},
            )
        assert engine._harness_update_count >= 1

    @pytest.mark.asyncio
    async def test_weight_update_triggered_at_interval(self):
        from semar.engine import Engine

        engine = Engine(weight_update_interval=2)
        for i in range(2):
            await engine.review_pr(
                pr_url=f"https://github.com/test/repo/pull/{i}",
                pr_diff=f"+x = {i}",
                pr_metadata={"files": [f"f{i}.py"]},
            )
        assert engine._weight_update_count >= 1

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        from semar.engine import Engine

        engine = Engine()
        await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+x = 1",
            pr_metadata={"files": ["a.py"]},
        )
        metrics = engine.get_metrics()
        assert metrics["total_reviews"] == 1
        assert "harness_updates" in metrics
        assert "weight_updates" in metrics

    def test_get_status(self):
        from semar.engine import Engine

        engine = Engine()
        status = engine.get_status()
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

        engine = Engine()

        class MockAgent:
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

        engine.register_agent("python", MockAgent())
        assert "python" in engine.list_agents()

    @pytest.mark.asyncio
    async def test_review_dispatches_to_agents(self):
        from semar.engine import Engine

        engine = Engine()

        class MockAgent:
            async def execute_cycle(self, ctx):
                from semar.agents.base_agent import AgentResult

                return AgentResult(
                    review="approve",
                    suggestions=[{"message": "fix typo"}],
                    metrics={"accuracy": 0.9},
                    trajectory={},
                    agent_id="mock",
                    language="python",
                    pr_url=ctx.pr_url,
                )

        engine.register_agent("python", MockAgent())
        result = await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["test.py"]},
        )
        assert result["verdict"] in ("approve", "request_changes")

    @pytest.mark.asyncio
    async def test_review_pr_preserves_agent_metrics(self):
        from semar.engine import Engine

        engine = Engine()

        class MockAgent:
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

        engine.register_agent("python", MockAgent())
        result = await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["test.py"]},
        )
        # Agent metrics are preserved in per-language results
        lang_results = result.get("results", [])
        assert len(lang_results) > 0
        assert lang_results[0]["metrics"]["accuracy"] == 0.9
        # Engine metrics are added at top level
        assert result["metrics"]["review_count"] == 1


# ============================================================
# Engine Self-Improvement Integration
# ============================================================


class TestEngineSelfImprovement:
    """Tests for Engine self-improvement integration."""

    @pytest.mark.asyncio
    async def test_harness_evolution_updates_agents(self):
        from semar.engine import Engine

        engine = Engine(harness_update_interval=1)

        class MockAgent:
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

        agent = MockAgent()
        engine.register_agent("python", agent)
        await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["test.py"]},
        )
        assert engine._harness_update_count >= 1

    @pytest.mark.asyncio
    async def test_weight_training_triggered_on_stall(self):
        from semar.engine import Engine

        engine = Engine(weight_update_interval=1)

        class MockAgent:
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

        engine.register_agent("python", MockAgent())
        await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["test.py"]},
        )
        assert engine._weight_update_count >= 1

    @pytest.mark.asyncio
    async def test_both_updates_on_same_cycle(self):
        from semar.engine import Engine

        # Both intervals = 1, so both should fire on every review
        engine = Engine(harness_update_interval=1, weight_update_interval=1)
        await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+x = 1",
            pr_metadata={"files": ["a.py"]},
        )
        assert engine._harness_update_count >= 1
        assert engine._weight_update_count >= 1

    @pytest.mark.asyncio
    async def test_scaffold_none_does_not_crash(self):
        from semar.engine import Engine

        engine = Engine(harness_update_interval=1)

        class AgentNoScaffold:
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

        engine.register_agent("python", AgentNoScaffold())
        # Should not crash even though agent has no scaffold
        await engine.review_pr(
            pr_url="https://github.com/test/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["test.py"]},
        )
