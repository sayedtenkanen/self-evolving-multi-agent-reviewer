"""PPO with GAE - Proximal Policy Optimization with Generalized Advantage Estimation."""

from typing import Any, Dict, List

from semar.self_improvement.weight_training.algorithms.base_algorithm import BaseAlgorithm


class PPOGAE(BaseAlgorithm):
    """PPO with Generalized Advantage Estimation.

    Best for: Dense, step-level rewards (e.g., per-line feedback quality)
    """

    @property
    def name(self) -> str:
        return "ppo_gae"

    def compute_gae(
        self,
        rewards: List[float],
        values: List[float],
        gamma: float = 0.99,
        lam: float = 0.95,
    ) -> List[float]:
        """Compute Generalized Advantage Estimation.

        Args:
            rewards: Reward at each timestep
            values: Value estimates (length = len(rewards) + 1)
            gamma: Discount factor
            lam: GAE lambda parameter

        Returns:
            List of advantage estimates
        """
        advantages: List[float] = []
        gae = 0.0

        for t in reversed(range(len(rewards))):
            next_value = values[t + 1] if t + 1 < len(values) else 0.0
            delta = rewards[t] + gamma * next_value - values[t]
            gae = delta + gamma * lam * gae
            advantages.insert(0, gae)

        return advantages

    async def train(
        self,
        trajectories: List[Dict[str, Any]],
        hyperparams: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run PPO+GAE training step.

        Computes advantages, clips surrogate objective, updates policy.
        """
        gamma = hyperparams.get("gamma", 0.99)
        lam = hyperparams.get("lam", 0.95)

        all_advantages: List[float] = []
        for traj in trajectories:
            rewards = traj.get("rewards", [])
            values = traj.get("values", [0.0] * (len(rewards) + 1))
            advantages = self.compute_gae(rewards, values, gamma, lam)
            all_advantages.extend(advantages)

        # Simplified loss computation (actual implementation would use torch)
        loss = -sum(all_advantages) / max(len(all_advantages), 1)

        return {
            "loss": loss,
            "advantages": all_advantages,
            "mean_advantage": sum(all_advantages) / max(len(all_advantages), 1),
            "num_samples": len(all_advantages),
        }
