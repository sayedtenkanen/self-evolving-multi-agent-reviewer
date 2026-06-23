"""OutcomeBasedReward - Computes rewards from trajectory outcomes."""

from typing import Any, Dict


class OutcomeBasedReward:
    """Computes rewards based on review outcomes.

    Uses accuracy, false positive rate, and suggestion quality
    to compute a scalar reward signal.
    """

    def __init__(self):
        pass

    async def compute(self, trajectory: Dict[str, Any]) -> float:
        """Compute reward from trajectory metrics.

        Args:
            trajectory: Trajectory dict with 'metrics' key

        Returns:
            Reward value between 0.0 and 1.0
        """
        metrics = trajectory.get("metrics", {})

        accuracy = metrics.get("accuracy", 0.5)
        false_positives = metrics.get("false_positives", 0)

        # Penalize false positives
        fp_penalty = min(false_positives * 0.1, 0.5)

        reward = max(0.0, min(1.0, accuracy - fp_penalty))
        return reward
