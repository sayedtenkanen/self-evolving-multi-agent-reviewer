"""Engine - Integration layer wiring JudgeAgent, language agents, harness, and weights.

The Engine is the main entry point for SEMAR. It orchestrates:
1. Language agent registration and dispatch
2. PR review via JudgeAgent
3. Trajectory storage and analysis
4. Self-improvement cycles (harness evolution + weight training)
"""

import time
from typing import Any, Dict, List

from semar.agents.improvement_selector import ImprovementSelector, ImprovementType
from semar.agents.judge_agent import JudgeAgent
from semar.agents.trajectory_analyzer import TrajectoryAnalyzer
from semar.agents.trajectory_store import TrajectoryStore
from semar.self_improvement.harness.prompt_evolver import PromptEvolver
from semar.self_improvement.harness.rule_evolver import RuleEvolver
from semar.self_improvement.harness.skill_discovery import SkillDiscovery
from semar.self_improvement.weight_training.data_pipeline import DataPipeline
from semar.self_improvement.weight_training.lora_trainer import LoRATrainer


class Engine:
    """Main integration layer for SEMAR.

    Wires together JudgeAgent, language agents, trajectory storage,
    harness evolution, and weight training into a cohesive review system.
    """

    def __init__(
        self,
        harness_update_interval: int = 10,
        weight_update_interval: int = 50,
        db_path: str = "semar_engine.db",
    ):
        self.harness_interval = harness_update_interval
        self.weight_interval = weight_update_interval

        # Core components
        self.judge = JudgeAgent()
        self.trajectory_store = TrajectoryStore(db_path=db_path)
        self.trajectory_analyzer = TrajectoryAnalyzer()
        self.improvement_selector = ImprovementSelector()

        # Harness evolution
        self.prompt_evolver = PromptEvolver()
        self.skill_discovery = SkillDiscovery()
        self.rule_evolver = RuleEvolver()

        # Weight training
        self.data_pipeline = DataPipeline()
        self.lora_trainer = LoRATrainer()

        # Counters
        self._review_count = 0
        self._harness_update_count = 0
        self._weight_update_count = 0
        self._improvement_history: List[Dict[str, Any]] = []

    def register_agent(self, language: str, agent: Any) -> None:
        """Register a language-specific agent.

        Args:
            language: Language key (e.g. 'python')
            agent: Agent instance with execute_cycle method
        """
        self.judge.register_language_agent(language, agent)

    def list_agents(self) -> List[str]:
        """List all registered language agent keys.

        Returns:
            List of registered language keys
        """
        return list(self.judge.language_agents.keys())

    async def review_pr(
        self,
        pr_url: str,
        pr_diff: str,
        pr_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a full PR review with self-improvement cycle.

        Args:
            pr_url: PR URL
            pr_diff: PR diff content
            pr_metadata: PR metadata (files, etc.)

        Returns:
            Review result with verdict, suggestions, and metrics
        """
        start = time.perf_counter()

        # Run review via JudgeAgent
        result = await self.judge.handle_pr_review(pr_url, pr_diff, pr_metadata)

        # Store trajectory
        await self.trajectory_store.store(
            agent_id="judge",
            pr_url=pr_url,
            language="mixed",
            plan={"diff": pr_diff[:500]},
            action_result=result,
            review={"verdict": result.get("verdict", "approve")},
            metrics=result.get("metrics", {}),
            full_trajectory=result,
        )

        self._review_count += 1

        # Analyze trajectory for failure modes
        analysis = await self.trajectory_analyzer.analyze(
            {
                "steps": {"review": {"output": result}},
                "metrics": result.get("metrics", {}),
            }
        )

        # Decide improvement type
        improvement = await self.improvement_selector.decide(analysis)

        # Apply analysis-based improvement if needed
        if improvement != ImprovementType.NONE:
            await self._apply_improvement(improvement, analysis)

        # Apply schedule-based updates (independent — both can run on same cycle)
        if self._should_run_harness_update():
            await self._apply_harness_update(analysis)
        if self._should_run_weight_update():
            await self._apply_weight_update(analysis)

        duration_ms = (time.perf_counter() - start) * 1000
        result["metrics"] = {
            **result.get("metrics", {}),
            "duration_ms": duration_ms,
            "review_count": self._review_count,
        }

        return result

    async def _apply_improvement(
        self,
        improvement: ImprovementType,
        analysis: Dict[str, Any],
    ) -> None:
        """Apply the selected improvement.

        Args:
            improvement: Type of improvement to apply
            analysis: Trajectory analysis result
        """
        if improvement == ImprovementType.HARNESS:
            await self._apply_harness_update(analysis)
        elif improvement == ImprovementType.WEIGHT:
            await self._apply_weight_update(analysis)

    async def _apply_harness_update(self, analysis: Dict[str, Any]) -> None:
        """Apply harness evolution update.

        Args:
            analysis: Trajectory analysis with failure modes
        """
        failure_modes = analysis.get("failure_modes", [])

        # Normalize failure modes: handle both FailureMode objects and plain dicts
        normalized_modes = []
        for fm in failure_modes:
            if isinstance(fm, dict):
                from semar.agents.trajectory_analyzer import FailureMode

                normalized_modes.append(
                    FailureMode(
                        type=fm.get("type", "unknown"),
                        severity=fm.get("severity", "medium"),
                        frequency=fm.get("frequency", 1),
                        examples=fm.get("examples", []),
                    )
                )
            else:
                normalized_modes.append(fm)

        # Evolve prompts for each registered agent
        for _lang, agent in self.judge.language_agents.items():
            scaffold = getattr(agent, "scaffold", None)
            if isinstance(scaffold, dict):
                current_prompt = scaffold.get("prompts", {}).get("system", "")
            else:
                current_prompt = ""

            if current_prompt and normalized_modes:
                evolved = await self.prompt_evolver.evolve(current_prompt, normalized_modes)
                if evolved != current_prompt and isinstance(scaffold, dict):
                    scaffold.setdefault("prompts", {})["system"] = evolved

        # Discover skills from recent trajectories
        recent = await self.trajectory_store.get_recent_trajectories(limit=10)
        if recent:
            await self.skill_discovery.discover(recent)

        # Evolve rules
        current_rules: List[Dict[str, Any]] = []
        for _lang, agent in self.judge.language_agents.items():
            scaffold = getattr(agent, "scaffold", None)
            if isinstance(scaffold, dict):
                agent_rules = scaffold.get("rules", [])
                if isinstance(agent_rules, list):
                    current_rules.extend(agent_rules)

        if current_rules:
            await self.rule_evolver.evolve(current_rules, analysis)

        self._harness_update_count += 1
        self._improvement_history.append(
            {
                "type": "harness",
                "timestamp": time.time(),
                "failure_modes": [fm.type for fm in normalized_modes],
            }
        )

    async def _apply_weight_update(self, analysis: Dict[str, Any]) -> None:
        """Apply weight training update.

        Args:
            analysis: Trajectory analysis
        """
        # Collect training data from recent trajectories
        recent = await self.trajectory_store.get_recent_trajectories(limit=50)
        if not recent:
            return

        collected = await self.data_pipeline.collect(trajectories=recent)
        if collected.count == 0:
            return

        # Train with GRPO (default algorithm)
        try:
            train_result = await self.lora_trainer.train(
                algorithm="grpo",
                training_data={
                    "trajectories": collected.data,
                    "rewards": [1.0] * collected.count,
                },
                hyperparams={"lr": 1e-4},
            )
        except Exception:
            train_result = None

        self._weight_update_count += 1
        self._improvement_history.append(
            {
                "type": "weight",
                "timestamp": time.time(),
                "algorithm": "grpo",
                "success": train_result is not None,
            }
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get engine performance metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "total_reviews": self._review_count,
            "harness_updates": self._harness_update_count,
            "weight_updates": self._weight_update_count,
            "harness_rate": (self._harness_update_count / self._review_count if self._review_count > 0 else 0.0),
            "weight_rate": (self._weight_update_count / self._review_count if self._review_count > 0 else 0.0),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get engine status.

        Returns:
            Status dictionary
        """
        return {
            "review_count": self._review_count,
            "registered_agents": self.list_agents(),
            "harness_update_count": self._harness_update_count,
            "weight_update_count": self._weight_update_count,
            "improvement_history": list(self._improvement_history),
        }

    def _should_run_harness_update(self) -> bool:
        """Check if a harness update should run based on schedule.

        Returns:
            True if it's time for a harness update
        """
        return self._review_count > 0 and self._review_count % self.harness_interval == 0

    def _should_run_weight_update(self) -> bool:
        """Check if a weight update should run based on schedule.

        Returns:
            True if it's time for a weight update
        """
        return self._review_count > 0 and self._review_count % self.weight_interval == 0
