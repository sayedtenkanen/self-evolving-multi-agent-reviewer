"""Entropic Advantage - For right-skewed reward distributions."""

from typing import Any, Dict, List

from semar.self_improvement.weight_training.algorithms.base_algorithm import BaseAlgorithm


class EntropicAdvantage(BaseAlgorithm):
    """Entropic Advantage algorithm.

    Best for: Right-skewed reward histogram (rare successes)
    Uses entropy bonus to encourage exploration when successes are rare.
    """

    @property
    def name(self) -> str:
        return "entropic_advantage"

    async def train(
        self,
        trajectories: List[Dict[str, Any]],
        hyperparams: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run Entropic Advantage training step."""
        entropy_coeff = hyperparams.get("entropy_coeff", 0.01)

        all_rewards: List[float] = []
        for traj in trajectories:
            rewards = traj.get("rewards", [])
            all_rewards.extend(rewards)

        if not all_rewards:
            return {"loss": 0.0, "entropy": 0.0, "num_samples": 0}

        # Entropic advantage: weight rare successes more heavily
        successes = [r for r in all_rewards if r > 0.5]
        success_rate = len(successes) / len(all_rewards) if all_rewards else 0.0

        # Entropy estimate (simplified)
        p_success = max(success_rate, 1e-8)
        p_fail = max(1.0 - success_rate, 1e-8)
        entropy = -(p_success * __import__("math").log(p_success) + p_fail * __import__("math").log(p_fail))

        # Weighted advantage
        mean_advantage = sum(all_rewards) / len(all_rewards)
        loss = -(mean_advantage - entropy_coeff * entropy)

        return {
            "loss": loss,
            "entropy": entropy,
            "success_rate": success_rate,
            "num_samples": len(all_rewards),
        }
