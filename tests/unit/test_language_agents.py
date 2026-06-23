"""Tests for BaseLanguageAgent and language-specific agents.

Phase 3: Language Agents with evolvable scaffolds.
All tests written BEFORE implementation (TDD - RED phase).
"""

import pytest

from semar.agents.base_agent import AgentContext, AgentResult


class TestBaseLanguageAgent:
    """Tests for the BaseLanguageAgent base class."""

    def test_import(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        assert BaseLanguageAgent is not None

    def test_inherits_from_base_agent(self):
        from semar.agents.base_agent import BaseAgent
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        assert issubclass(BaseLanguageAgent, BaseAgent)

    def test_init_requires_language(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        agent = BaseLanguageAgent(language="python")
        assert agent.language == "python"
        assert agent.agent_id == "python_agent"

    def test_default_scaffold(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        agent = BaseLanguageAgent(language="python")
        scaffold = agent.get_scaffold()
        assert "system_prompt" in scaffold
        assert "skills" in scaffold
        assert "rules" in scaffold
        assert isinstance(scaffold["skills"], list)
        assert isinstance(scaffold["rules"], list)

    def test_default_system_prompt_mentions_language(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        agent = BaseLanguageAgent(language="python")
        scaffold = agent.get_scaffold()
        assert "python" in scaffold["system_prompt"].lower()

    @pytest.mark.asyncio
    async def test_health_ping(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        agent = BaseLanguageAgent(language="python")
        health = await agent.health_ping()
        assert health["status"] == "healthy"
        assert health["language"] == "python"

    @pytest.mark.asyncio
    async def test_execute_cycle_returns_agent_result(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        agent = BaseLanguageAgent(language="python")
        context = AgentContext(
            pr_url="https://github.com/org/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["main.py"]},
            language="python",
            files=["main.py"],
        )
        result = await agent.execute_cycle(context)
        assert isinstance(result, AgentResult)
        assert result.language == "python"
        assert result.agent_id == "python_agent"

    @pytest.mark.asyncio
    async def test_execute_cycle_captures_trajectory(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        agent = BaseLanguageAgent(language="python")
        context = AgentContext(
            pr_url="https://github.com/org/repo/pull/1",
            pr_diff="+import os",
            pr_metadata={"files": ["main.py"]},
            language="python",
            files=["main.py"],
        )
        result = await agent.execute_cycle(context)
        assert result.trajectory is not None
        assert "steps" in result.trajectory
        assert "plan" in result.trajectory["steps"]
        assert "action" in result.trajectory["steps"]
        assert "review" in result.trajectory["steps"]

    def test_update_scaffold_system_prompt(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        agent = BaseLanguageAgent(language="python")
        agent.update_scaffold(prompts={"system_prompt": "New prompt"})
        assert agent.get_scaffold()["system_prompt"] == "New prompt"

    def test_update_scaffold_skills(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        agent = BaseLanguageAgent(language="python")
        agent.update_scaffold(skills=["security_review", "type_hints"])
        assert agent.get_scaffold()["skills"] == ["security_review", "type_hints"]

    def test_update_scaffold_rules(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent

        agent = BaseLanguageAgent(language="python")
        new_rules = [{"name": "no_eval", "pattern": r"\beval\s*\(", "severity": "high"}]
        agent.update_scaffold(rules=new_rules)
        assert agent.get_scaffold()["rules"] == new_rules


class TestPythonAgent:
    """Tests for the Python-specific language agent."""

    def test_import(self):
        from semar.agents.language_agents.python import PythonAgent

        assert PythonAgent is not None

    def test_inherits_base_language(self):
        from semar.agents.language_agents.base_language import BaseLanguageAgent
        from semar.agents.language_agents.python import PythonAgent

        assert issubclass(PythonAgent, BaseLanguageAgent)

    def test_language_is_python(self):
        from semar.agents.language_agents.python import PythonAgent

        agent = PythonAgent()
        assert agent.language == "python"
        assert agent.agent_id == "python_agent"

    def test_default_skills(self):
        from semar.agents.language_agents.python import PythonAgent

        agent = PythonAgent()
        skills = agent.get_scaffold()["skills"]
        assert len(skills) > 0
        assert "security_review" in skills

    def test_default_rules(self):
        from semar.agents.language_agents.python import PythonAgent

        agent = PythonAgent()
        rules = agent.get_scaffold()["rules"]
        assert len(rules) > 0
        rule_names = [r["name"] for r in rules]
        assert "no_eval" in rule_names

    def test_system_prompt_mentions_python(self):
        from semar.agents.language_agents.python import PythonAgent

        agent = PythonAgent()
        prompt = agent.get_scaffold()["system_prompt"]
        assert "python" in prompt.lower()


class TestJavaScriptAgent:
    """Tests for the JavaScript-specific language agent."""

    def test_import(self):
        from semar.agents.language_agents.javascript import JavaScriptAgent

        assert JavaScriptAgent is not None

    def test_language_is_javascript(self):
        from semar.agents.language_agents.javascript import JavaScriptAgent

        agent = JavaScriptAgent()
        assert agent.language == "javascript"
        assert agent.agent_id == "javascript_agent"

    def test_default_skills(self):
        from semar.agents.language_agents.javascript import JavaScriptAgent

        agent = JavaScriptAgent()
        skills = agent.get_scaffold()["skills"]
        assert len(skills) > 0


class TestTypeScriptAgent:
    """Tests for the TypeScript-specific language agent."""

    def test_import(self):
        from semar.agents.language_agents.typescript import TypeScriptAgent

        assert TypeScriptAgent is not None

    def test_language_is_typescript(self):
        from semar.agents.language_agents.typescript import TypeScriptAgent

        agent = TypeScriptAgent()
        assert agent.language == "typescript"
        assert agent.agent_id == "typescript_agent"


class TestGoAgent:
    """Tests for the Go-specific language agent."""

    def test_import(self):
        from semar.agents.language_agents.go import GoAgent

        assert GoAgent is not None

    def test_language_is_go(self):
        from semar.agents.language_agents.go import GoAgent

        agent = GoAgent()
        assert agent.language == "go"
        assert agent.agent_id == "go_agent"


class TestJavaAgent:
    """Tests for the Java-specific language agent."""

    def test_import(self):
        from semar.agents.language_agents.java import JavaAgent

        assert JavaAgent is not None

    def test_language_is_java(self):
        from semar.agents.language_agents.java import JavaAgent

        agent = JavaAgent()
        assert agent.language == "java"
        assert agent.agent_id == "java_agent"


class TestRustAgent:
    """Tests for the Rust-specific language agent."""

    def test_import(self):
        from semar.agents.language_agents.rust import RustAgent

        assert RustAgent is not None

    def test_language_is_rust(self):
        from semar.agents.language_agents.rust import RustAgent

        agent = RustAgent()
        assert agent.language == "rust"
        assert agent.agent_id == "rust_agent"


class TestCppAgent:
    """Tests for the C++-specific language agent."""

    def test_import(self):
        from semar.agents.language_agents.cpp import CppAgent

        assert CppAgent is not None

    def test_language_is_cpp(self):
        from semar.agents.language_agents.cpp import CppAgent

        agent = CppAgent()
        assert agent.language == "cpp"
        assert agent.agent_id == "cpp_agent"


class TestAgentRegistry:
    """Tests for the AgentRegistry - agent discovery and management."""

    def test_import(self):
        from semar.agents.registry import AgentRegistry

        assert AgentRegistry is not None

    def test_init(self):
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        assert registry.agents == {}
        assert registry.health == {}

    def test_register_agent(self):
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        agent = PythonAgent()
        registry.register("python", agent)
        assert "python" in registry.agents
        assert registry.agents["python"] is agent

    def test_unregister_agent(self):
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        agent = PythonAgent()
        registry.register("python", agent)
        registry.unregister("python")
        assert "python" not in registry.agents

    def test_get_agent(self):
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        agent = PythonAgent()
        registry.register("python", agent)
        assert registry.get_agent("python") is agent
        assert registry.get_agent("nonexistent") is None

    def test_list_agents(self):
        from semar.agents.language_agents.javascript import JavaScriptAgent
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("python", PythonAgent())
        registry.register("javascript", JavaScriptAgent())
        agents = registry.list_agents()
        assert set(agents) == {"python", "javascript"}

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("python", PythonAgent())
        health = await registry.health_check()
        assert "python" in health
        assert health["python"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        import asyncio

        from semar.agents.base_agent import AgentResult, BaseAgent
        from semar.agents.registry import AgentRegistry

        class SlowAgent(BaseAgent):
            def __init__(self):
                super().__init__(agent_id="slow_agent", language="slow")

            async def health_ping(self):
                await asyncio.sleep(10)  # Will timeout
                return {"status": "healthy"}

            async def plan(self, context):
                return {}

            async def action(self, context, plan):
                return ""

            async def review(self, context, action_result):
                return AgentResult(
                    review="approve",
                    suggestions=[],
                    metrics={},
                    trajectory={},
                    agent_id="slow",
                    language="slow",
                    pr_url="",
                )

            async def update_instructions(self, context, review):
                pass

        registry = AgentRegistry()
        registry.register("slow", SlowAgent())
        health = await registry.health_check(timeout=0.1)
        assert health["slow"]["status"] == "degraded"

    def test_select_agents_for_language(self):
        from semar.agents.language_agents.javascript import JavaScriptAgent
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("python", PythonAgent())
        registry.register("javascript", JavaScriptAgent())
        selected = registry.select_agents(["python"])
        assert "python" in selected
        assert "javascript" not in selected

    def test_select_agents_multiple_languages(self):
        from semar.agents.language_agents.javascript import JavaScriptAgent
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("python", PythonAgent())
        registry.register("javascript", JavaScriptAgent())
        selected = registry.select_agents(["python", "javascript"])
        assert "python" in selected
        assert "javascript" in selected

    def test_select_agents_unhealthy_excluded(self):
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        agent = PythonAgent()
        registry.register("python", agent)
        # Manually mark as unhealthy
        registry.health["python"] = {"status": "unhealthy", "last_error": "test"}
        selected = registry.select_agents(["python"])
        assert "python" not in selected

    def test_record_success(self):
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("python", PythonAgent())
        registry.record_success("python", latency_ms=100.0)
        # Should not raise

    def test_record_failure(self):
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("python", PythonAgent())
        registry.record_failure("python", error="test error")
        # Should not raise

    def test_get_stats(self):
        from semar.agents.language_agents.python import PythonAgent
        from semar.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("python", PythonAgent())
        stats = registry.get_stats()
        assert "total_agents" in stats
        assert stats["total_agents"] == 1
