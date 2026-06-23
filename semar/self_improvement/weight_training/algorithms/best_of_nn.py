"""Best-of-N - Selection-based algorithm for sparse rewards."""

from typing import Any, Dict, List

from semar.self_improvement.weight_training.algorithms.base_algorithm import BaseAlgorithm


class BestOfNN(BaseAlgorithm):
    """Best-of-N algorithm.

    Best for: Extremely sparse rewards (cold start).
    Generates N candidates and trains on the best one.
    """

    @property
    def name(self) -> str:
        return "best_of_nn"

    def select_best(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best candidate from a list.

        Args:
            candidates: List of candidate dicts with 'reward' key

        Returns:
            Best candidate dict
        """
        if not candidates:
            return {"reward": 0.0, "output": ""}
        return max(candidates, key=lambda c: c.get("reward", 0.0))

    async def train(
        self,
        trajectories: List[Dict[str, Any]],
        hyperparams: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run Best-of-N training step.

        For each trajectory, select the best candidate and use it for training.
        """
        all_best_rewards: List[float] = []

        for traj in trajectories:
            candidates = traj.get("candidates", [])
            if candidates:
                best = self.select_best(candidates)
                all_best_rewards.append(best.get("reward", 0.0))

        if not all_best_rewards:
            return {"loss": 0.0, "num_samples": 0}

        # Train on best candidates
        mean_reward = sum(all_best_rewards) / len(all_best_rewards)
        loss = -mean_reward

        return {
            "loss": loss,
            "mean_best_reward": mean_reward,
            "num_samples": len(all_best_rewards),
        }
