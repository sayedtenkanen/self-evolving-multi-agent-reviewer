"""DPO - Direct Preference Optimization."""

import math
from typing import Any, Dict, List

from semar.self_improvement.weight_training.algorithms.base_algorithm import BaseAlgorithm


class DPO(BaseAlgorithm):
    """Direct Preference Optimization.

    Best for: Verifier ranks but doesn't score absolutely.
    Learns from pairwise preferences (preferred vs rejected).
    """

    @property
    def name(self) -> str:
        return "dpo"

    async def train(
        self,
        trajectories: List[Dict[str, Any]],
        hyperparams: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run DPO training step.

        Computes loss from preferred/rejected pairs.
        """
        beta = hyperparams.get("beta", 0.1)

        losses: List[float] = []
        for traj in trajectories:
            preferred = traj.get("preferred", {})
            rejected = traj.get("rejected", {})

            pref_reward = preferred.get("reward", 0.0)
            rej_reward = rejected.get("reward", 0.0)

            # DPO loss: -log(sigmoid(beta * (log pref - log rej)))
            # Simplified: directly use reward difference
            log_ratio = beta * (pref_reward - rej_reward)
            # Numerically stable: log(1 + exp(-x)) = max(0, -x) + log1p(exp(-|x|))
            loss = max(0.0, -log_ratio) + math.log1p(math.exp(-abs(log_ratio)))
            losses.append(loss)

        if not losses:
            return {"loss": 0.0, "num_pairs": 0}

        mean_loss = sum(losses) / len(losses)

        return {
            "loss": mean_loss,
            "num_pairs": len(losses),
            "beta": beta,
        }
