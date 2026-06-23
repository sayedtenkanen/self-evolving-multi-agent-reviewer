"""Unit tests for BaseAgent."""

import pytest
import asyncio
from semar.agents.base_agent import BaseAgent, AgentState, AgentContext, AgentResult


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, agent_id: str = "test_agent", language: str = "python"):
        super().__init__(agent_id, language)
        self.plan_called = False
        self.action_called = False
        self.review_called = False
        self.update_called = False
        self.should_fail = False
    
    async def plan(self, context: AgentContext) -> dict:
        self.plan_called = True
        return {"files_to_review": context.files, "language": context.language}
    
    async def action(self, context: AgentContext, plan: dict) -> dict:
        self.action_called = True
        if self.should_fail:
            raise ValueError("Mock failure")
        return {"findings": ["test finding"], "suggestions": []}
    
    async def review(self, context: AgentContext, action_result: dict) -> AgentResult:
        self.review_called = True
        return AgentResult(
            review="Test review",
            suggestions=[{"file": "test.py", "line": 1, "suggestion": "test"}],
            metrics={"quality": 0.8},
            trajectory={},
            agent_id=self.agent_id,
            language=self.language or "unknown",
            pr_url=context.pr_url,
        )
    
    async def update_instructions(self, context: AgentContext, review: AgentResult) -> None:
        self.update_called = True


@pytest.fixture
def agent():
    """Create a mock agent for testing."""
    return MockAgent()


@pytest.fixture
def context():
    """Create a test context."""
    return AgentContext(
        pr_url="https://github.com/test/repo/pull/1",
        pr_diff="test diff",
        pr_metadata={"author": "test"},
        language="python",
        files=["test.py", "main.py"],
    )


class TestAgentState:
    """Tests for AgentState enum."""
    
    def test_agent_states(self):
        """Test all agent states exist."""
        assert AgentState.PLANNING.value == "planning"
        assert AgentState.ACTION.value == "action"
        assert AgentState.REVIEW.value == "review"
        assert AgentState.UPDATE.value == "update"
        assert AgentState.IDLE.value == "idle"
        assert AgentState.ERROR.value == "error"


class TestAgentContext:
    """Tests for AgentContext dataclass."""
    
    def test_context_creation(self, context):
        """Test context creation with required fields."""
        assert context.pr_url == "https://github.com/test/repo/pull/1"
        assert context.language == "python"
        assert len(context.files) == 2
    
    def test_context_optional_fields(self):
        """Test context creation with optional fields."""
        context = AgentContext(
            pr_url="test",
            pr_diff="diff",
            pr_metadata={},
            language="python",
            files=[],
            repo_url="https://github.com/test/repo",
            pr_number=1,
        )
        assert context.repo_url == "https://github.com/test/repo"
        assert context.pr_number == 1


class TestAgentResult:
    """Tests for AgentResult dataclass."""
    
    def test_result_creation(self):
        """Test result creation."""
        result = AgentResult(
            review="test review",
            suggestions=[],
            metrics={},
            trajectory={},
            agent_id="test",
            language="python",
            pr_url="test",
        )
        assert result.review == "test review"
        assert result.success is True
        assert result.error is None
    
    def test_result_with_error(self):
        """Test result creation with error."""
        result = AgentResult(
            review="error",
            suggestions=[],
            metrics={},
            trajectory={},
            agent_id="test",
            language="python",
            pr_url="test",
            success=False,
            error="Test error",
        )
        assert result.success is False
        assert result.error == "Test error"


class TestBaseAgent:
    """Tests for BaseAgent class."""
    
    @pytest.mark.asyncio
    async def test_execute_cycle(self, agent, context):
        """Test complete 4-step cycle."""
        result = await agent.execute_cycle(context)
        
        assert agent.plan_called
        assert agent.action_called
        assert agent.review_called
        assert agent.update_called
        assert result.review == "Test review"
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_execute_cycle_error_handling(self, agent, context):
        """Test error handling in execute cycle."""
        agent.should_fail = True
        result = await agent.execute_cycle(context)
        
        assert not result.success
        assert "Mock failure" in result.error
        assert agent.state == AgentState.ERROR
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.agent_id == "test_agent"
        assert agent.language == "python"
        assert agent.state == AgentState.IDLE
    
    def test_get_capabilities(self, agent):
        """Test get_capabilities method."""
        caps = agent.get_capabilities()
        assert caps["agent_id"] == "test_agent"
        assert caps["language"] == "python"
        assert "metrics" in caps
    
    @pytest.mark.asyncio
    async def test_health_ping(self, agent):
        """Test health ping method."""
        health = await agent.health_ping()
        assert health["status"] == "healthy"
        assert health["agent_id"] == "test_agent"
    
    def test_update_scaffold(self, agent):
        """Test scaffold update."""
        agent.update_scaffold(
            prompts={"review": "Review this code"},
            skills=["security"],
            rules=["no hardcoded secrets"],
        )
        scaffold = agent.get_scaffold()
        assert "review" in scaffold["prompts"]
        assert "security" in scaffold["skills"]
        assert "no hardcoded secrets" in scaffold["rules"]


class TestTrajectoryStore:
    """Tests for TrajectoryStore class."""
    
    @pytest.fixture
    def store(self, tmp_path):
        """Create a temporary trajectory store."""
        from semar.agents.trajectory_store import TrajectoryStore
        db_path = tmp_path / "test.db"
        return TrajectoryStore(str(db_path))
    
    @pytest.mark.asyncio
    async def test_store_trajectory(self, store):
        """Test storing a trajectory."""
        trajectory_id = await store.store(
            agent_id="test_agent",
            pr_url="https://github.com/test/repo/pull/1",
            language="python",
            plan={"files": ["test.py"]},
            action_result={"findings": []},
            review={"review": "test"},
            metrics={"quality": 0.8},
            full_trajectory={"steps": []},
        )
        assert trajectory_id is not None
        assert trajectory_id > 0
    
    @pytest.mark.asyncio
    async def test_get_trajectories(self, store):
        """Test retrieving trajectories."""
        await store.store(
            agent_id="test_agent",
            pr_url="https://github.com/test/repo/pull/1",
            language="python",
            plan={},
            action_result={},
            review={},
            metrics={},
            full_trajectory={},
        )
        
        trajectories = await store.get_trajectories(agent_id="test_agent")
        assert len(trajectories) == 1
        assert trajectories[0]["agent_id"] == "test_agent"
    
    @pytest.mark.asyncio
    async def test_get_trajectory_by_id(self, store):
        """Test getting trajectory by ID."""
        trajectory_id = await store.store(
            agent_id="test_agent",
            pr_url="https://github.com/test/repo/pull/1",
            language="python",
            plan={},
            action_result={},
            review={},
            metrics={},
            full_trajectory={},
        )
        
        trajectory = await store.get_trajectory_by_id(trajectory_id)
        assert trajectory is not None
        assert trajectory["agent_id"] == "test_agent"
    
    @pytest.mark.asyncio
    async def test_delete_trajectory(self, store):
        """Test deleting a trajectory."""
        trajectory_id = await store.store(
            agent_id="test_agent",
            pr_url="https://github.com/test/repo/pull/1",
            language="python",
            plan={},
            action_result={},
            review={},
            metrics={},
            full_trajectory={},
        )
        
        deleted = await store.delete_trajectory(trajectory_id)
        assert deleted is True
        
        trajectory = await store.get_trajectory_by_id(trajectory_id)
        assert trajectory is None


class TestConfig:
    """Tests for Config class."""
    
    def test_config_creation(self):
        """Test config creation."""
        from semar.config.settings import Config
        config = Config()
        assert config is not None
    
    def test_config_properties(self):
        """Test config properties."""
        from semar.config.settings import Config
        config = Config()
        
        assert "model" in config.llm
        assert "timeout" in config.agent
        assert "db_path" in config.trajectory
        assert "harness_update_interval" in config.self_improvement
    
    def test_config_get_set(self):
        """Test config get/set methods."""
        from semar.config.settings import Config
        config = Config()
        
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"
        assert config.get("nonexistent", "default") == "default"


class TestHelpers:
    """Tests for helper utilities."""
    
    def test_generate_id(self):
        """Test ID generation."""
        from semar.utils.helpers import generate_id
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2
        
        prefixed = generate_id("agent")
        assert prefixed.startswith("agent_")
    
    def test_hash_content(self):
        """Test content hashing."""
        from semar.utils.helpers import hash_content
        hash1 = hash_content("test")
        hash2 = hash_content("test")
        hash3 = hash_content("different")
        
        assert hash1 == hash2
        assert hash1 != hash3
    
    def test_truncate_text(self):
        """Test text truncation."""
        from semar.utils.helpers import truncate_text
        short = "hello"
        long = "a" * 100
        
        assert truncate_text(short, 10) == "hello"
        assert len(truncate_text(long, 10)) == 10
        assert truncate_text(long, 10).endswith("...")
    
    def test_parse_pr_url(self):
        """Test PR URL parsing."""
        from semar.utils.helpers import parse_pr_url
        
        result = parse_pr_url("https://github.com/org/repo/pull/123")
        assert result["owner"] == "org"
        assert result["repo"] == "repo"
        assert result["pr_number"] == "123"
    
    def test_format_duration(self):
        """Test duration formatting."""
        from semar.utils.helpers import format_duration
        
        assert format_duration(30) == "30.0s"
        assert format_duration(90) == "1.5m"
        assert format_duration(3600) == "1.0h"
