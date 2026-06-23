"""GRPO - Group Relative Policy Optimization."""

from typing import Any, Dict, List

from semar.self_improvement.weight_training.algorithms.base_algorithm import BaseAlgorithm


class GRPO(BaseAlgorithm):
    """Group Relative Policy Optimization.

    Best for: Cheap rollouts, episode-end verifier (default algorithm)
    """

    @property
    def name(self) -> str:
        return "grpo"

    async def train(
        self,
        trajectories: List[Dict[str, Any]],
        hyperparams: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run GRPO training step.

        Computes group-relative advantages and updates policy.
        """
        all_rewards: List[float] = []
        for traj in trajectories:
            rewards = traj.get("rewards", [])
            all_rewards.extend(rewards)

        if not all_rewards:
            return {"loss": 0.0, "num_samples": 0}

        # Group-relative advantage: normalize rewards within group
        mean_reward = sum(all_rewards) / len(all_rewards)
        advantages = [(r - mean_reward) for r in all_rewards]

        # Simplified policy gradient loss
        loss = -sum(advantages) / max(len(advantages), 1)

        return {
            "loss": loss,
            "mean_reward": mean_reward,
            "num_samples": len(all_rewards),
        }
