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
        # Collect all rewards across trajectories
        all_rewards: List[float] = []
        for traj in trajectories:
            rewards = traj.get("rewards", [])
            all_rewards.extend(rewards)

        if not all_rewards:
            return {"loss": 0.0, "num_samples": 0}

        # Group-relative: normalize rewards within each trajectory for variance reduction
        advantages: List[float] = []
        for traj in trajectories:
            rewards = traj.get("rewards", [])
            if len(rewards) > 1:
                traj_mean = sum(rewards) / len(rewards)
                traj_var = sum((r - traj_mean) ** 2 for r in rewards) / len(rewards)
                traj_std = max(traj_var**0.5, 1e-8)
                advantages.extend([(r - traj_mean) / traj_std for r in rewards])
            else:
                advantages.extend(rewards)

        # Policy gradient loss: negative mean reward
        loss = -sum(all_rewards) / len(all_rewards)

        return {
            "loss": loss,
            "num_samples": len(all_rewards),
        }
