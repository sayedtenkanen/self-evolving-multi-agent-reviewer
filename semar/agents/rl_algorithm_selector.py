"""RLAlgorithmSelector - Adaptive selection of reinforcement learning algorithms."""

from enum import Enum
from typing import Any, Dict


class RLAlgorithm(Enum):
    """Supported RL algorithms for self-improvement."""

    PPO_GAE = "ppo_gae"
    GRPO = "grpo"
    ENTROPIC_ADVANTAGE = "entropic_advantage"
    REINFORCE_KL = "reinforce_kl"
    BEST_OF_NN = "best_of_nn"
    DPO = "dpo"


class RLAlgorithmSelector:
    """Selects the most appropriate RL algorithm based on analysis.

    Decision factors:
    - PPO+GAE: Dense, step-level rewards (e.g., per-line feedback quality)
    - GRPO: Cheap rollouts, verifiable at episode end (default)
    - Entropic Advantage: Right-skewed reward distributions
    - REINFORCE+KL: Dense rewards with regression risk
    - Best-of-NN: Extremely sparse rewards
    - DPO: Ranking-only data (no absolute scores)
    """

    async def select(self, analysis: Dict[str, Any]) -> RLAlgorithm:
        """Select RL algorithm based on analysis.

        Args:
            analysis: Output from TrajectoryAnalyzer.analyze()

        Returns:
            Selected RLAlgorithm
        """
        reward = analysis.get("metrics", {}).get("reward_structure", {})

        if reward.get("dense_step_level"):
            return RLAlgorithm.PPO_GAE

        if reward.get("cheap_rollouts") and reward.get("episode_end_verifier"):
            return RLAlgorithm.GRPO

        if reward.get("right_skewed"):
            return RLAlgorithm.ENTROPIC_ADVANTAGE

        if reward.get("dense") and reward.get("regression_risk"):
            return RLAlgorithm.REINFORCE_KL

        if reward.get("extremely_sparse"):
            return RLAlgorithm.BEST_OF_NN

        if reward.get("ranking_only"):
            return RLAlgorithm.DPO

        return RLAlgorithm.GRPO
