"""BaseAgent - Abstract base class for SEMAR agents.

Implements the 4-step self-improvement cycle:
1. Planning - Analyze PR and create execution plan
2. Action - Execute the review/improvement
3. Review - Self-reflect on results
4. Update - Update instructions based on learnings
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentState(Enum):
    """Agent execution states"""

    PLANNING = "planning"
    ACTION = "action"
    REVIEW = "review"
    UPDATE = "update"
    IDLE = "idle"
    ERROR = "error"


@dataclass
class AgentContext:
    """Context for agent execution"""

    pr_url: str
    pr_diff: str
    pr_metadata: Dict[str, Any]
    language: str
    files: List[str]
    repo_url: Optional[str] = None
    pr_number: Optional[int] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    base_branch: Optional[str] = None
    head_branch: Optional[str] = None


@dataclass
class AgentResult:
    """Result from agent execution"""

    review: str
    suggestions: List[Dict[str, Any]]
    metrics: Dict[str, float]
    trajectory: Dict[str, Any]
    agent_id: str
    language: str
    pr_url: str
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    """Abstract base class for SEMAR agents.

    All agents must implement the 4-step cycle:
    - plan(): Analyze context and create execution plan
    - action(): Execute the review/improvement
    - review(): Self-reflect on results
    - update_instructions(): Update instructions based on learnings
    """

    def __init__(self, agent_id: str, language: Optional[str] = None):
        """Initialize the agent.

        Args:
            agent_id: Unique identifier for this agent
            language: Programming language this agent handles (None for Judge)
        """
        self.agent_id = agent_id
        self.language = language
        self.state = AgentState.IDLE
        self.trajectory_store = None  # Set externally
        self._scaffold = {
            "prompts": {},
            "skills": [],
            "rules": [],
        }
        self._metrics = {
            "total_reviews": 0,
            "successful_reviews": 0,
            "failed_reviews": 0,
            "avg_duration_ms": 0.0,
        }

    async def execute_cycle(self, context: AgentContext) -> AgentResult:
        """Execute the 4-step self-improvement cycle.

        Args:
            context: The context for this execution cycle

        Returns:
            AgentResult with review, suggestions, metrics, and trajectory
        """
        start_time = time.time()
        trajectory = {
            "agent_id": self.agent_id,
            "language": self.language,
            "pr_url": context.pr_url,
            "steps": {},
        }

        try:
            # 1. Planning
            self.state = AgentState.PLANNING
            plan = await self.plan(context)
            trajectory["steps"]["plan"] = {
                "input": {"pr_url": context.pr_url, "language": context.language},
                "output": plan,
                "timestamp": time.time(),
            }

            # 2. Action
            self.state = AgentState.ACTION
            action_result = await self.action(context, plan)
            trajectory["steps"]["action"] = {
                "input": {"plan": plan},
                "output": action_result,
                "timestamp": time.time(),
            }

            # 3. Review (self-reflection)
            self.state = AgentState.REVIEW
            review = await self.review(context, action_result)
            trajectory["steps"]["review"] = {
                "input": {"action_result": action_result},
                "output": review.review,
                "metrics": review.metrics,
                "timestamp": time.time(),
            }

            # 4. Update instructions
            self.state = AgentState.UPDATE
            await self.update_instructions(context, review)
            trajectory["steps"]["update"] = {
                "input": {"review": review.review},
                "output": "instructions updated",
                "timestamp": time.time(),
            }

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            review.duration_ms = duration_ms
            review.trajectory = trajectory

            # Update metrics
            self._metrics["total_reviews"] += 1
            self._metrics["successful_reviews"] += 1
            self._metrics["avg_duration_ms"] = (
                self._metrics["avg_duration_ms"] * (self._metrics["total_reviews"] - 1) + duration_ms
            ) / self._metrics["total_reviews"]

            # Store trajectory if available
            if self.trajectory_store:
                await self.trajectory_store.store(
                    agent_id=self.agent_id,
                    pr_url=context.pr_url,
                    language=context.language,
                    plan=plan,
                    action_result=action_result,
                    review={"review": review.review, "suggestions": review.suggestions},
                    metrics=review.metrics,
                    full_trajectory=trajectory,
                )

            self.state = AgentState.IDLE
            return review

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._metrics["total_reviews"] += 1
            self._metrics["failed_reviews"] += 1

            error_result = AgentResult(
                review=f"Error: {str(e)}",
                suggestions=[],
                metrics={"error": 1.0, "duration_ms": duration_ms},
                trajectory=trajectory,
                agent_id=self.agent_id,
                language=self.language or "unknown",
                pr_url=context.pr_url,
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )

            self.state = AgentState.ERROR
            return error_result

    @abstractmethod
    async def plan(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze PR and create execution plan.

        Args:
            context: The context for this execution

        Returns:
            Execution plan as a dictionary
        """
        pass

    @abstractmethod
    async def action(self, context: AgentContext, plan: Dict[str, Any]) -> Any:
        """Execute the review/improvement.

        Args:
            context: The context for this execution
            plan: The execution plan from plan()

        Returns:
            Action result (type depends on agent implementation)
        """
        pass

    @abstractmethod
    async def review(self, context: AgentContext, action_result: Any) -> AgentResult:
        """Self-reflect on results.

        Args:
            context: The context for this execution
            action_result: The result from action()

        Returns:
            AgentResult with review, suggestions, and metrics
        """
        pass

    @abstractmethod
    async def update_instructions(self, context: AgentContext, review: AgentResult) -> None:
        """Update instructions based on learnings.

        Args:
            context: The context for this execution
            review: The review result from review()
        """
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities.

        Returns:
            Dictionary of agent capabilities
        """
        return {
            "agent_id": self.agent_id,
            "language": self.language,
            "state": self.state.value,
            "metrics": self._metrics.copy(),
            "scaffold": {
                "prompt_count": len(self._scaffold["prompts"]),
                "skill_count": len(self._scaffold["skills"]),
                "rule_count": len(self._scaffold["rules"]),
            },
        }

    async def health_ping(self) -> Dict[str, Any]:
        """Health check for agent registry.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "language": self.language,
            "state": self.state.value,
            "timestamp": time.time(),
        }

    def update_scaffold(
        self,
        prompts: Optional[Dict[str, str]] = None,
        skills: Optional[List[str]] = None,
        rules: Optional[List[Any]] = None,
    ) -> None:
        """Update agent scaffold (evolvable components).

        Args:
            prompts: Updated prompts
            skills: Updated skills list
            rules: Updated rules list
        """
        if prompts:
            current = self._scaffold.get("prompts", {})
            if isinstance(current, dict):
                current.update(prompts)
                self._scaffold["prompts"] = current
        if skills:
            self._scaffold["skills"] = skills
        if rules:
            self._scaffold["rules"] = rules

    def get_scaffold(self) -> Dict[str, Any]:
        """Get current scaffold.

        Returns:
            Current scaffold dictionary
        """
        return self._scaffold.copy()
