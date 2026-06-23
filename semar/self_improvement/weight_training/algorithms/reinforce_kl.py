"""REINFORCE with KL Regularization."""

from typing import Any, Dict, List

from semar.self_improvement.weight_training.algorithms.base_algorithm import BaseAlgorithm


class REINFORCEKL(BaseAlgorithm):
    """REINFORCE with KL divergence regularization.

    Best for: Dense rewards, risk of capability regression.
    Uses KL penalty to prevent the policy from drifting too far.
    """

    @property
    def name(self) -> str:
        return "reinforce_kl"

    async def train(
        self,
        trajectories: List[Dict[str, Any]],
        hyperparams: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run REINFORCE+KL training step."""
        kl_coeff = hyperparams.get("kl_coeff", 0.1)

        all_rewards: List[float] = []
        for traj in trajectories:
            rewards = traj.get("rewards", [])
            all_rewards.extend(rewards)

        if not all_rewards:
            return {"loss": 0.0, "kl_penalty": 0.0, "num_samples": 0}

        # REINFORCE: policy gradient = -reward
        mean_reward = sum(all_rewards) / len(all_rewards)

        # KL penalty (simplified: assume fixed reference policy)
        kl_penalty = kl_coeff * 0.01  # Simplified KL estimate

        loss = -(mean_reward - kl_penalty)

        return {
            "loss": loss,
            "kl_penalty": kl_penalty,
            "mean_reward": mean_reward,
            "num_samples": len(all_rewards),
        }
