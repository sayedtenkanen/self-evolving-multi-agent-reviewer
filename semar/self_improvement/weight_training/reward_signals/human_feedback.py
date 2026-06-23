"""HumanFeedbackReward - Computes rewards from human feedback."""

from typing import Any, Dict


class HumanFeedbackReward:
    """Computes rewards based on human feedback signals.

    Uses acceptance/rejection counts from human reviewers.
    """

    def __init__(self):
        pass

    async def compute(self, trajectory: Dict[str, Any]) -> float:
        """Compute reward from human feedback.

        Args:
            trajectory: Trajectory dict with 'human_feedback' key
                       containing 'accepted' and 'rejected' counts

        Returns:
            Reward value between 0.0 and 1.0
        """
        feedback = trajectory.get("human_feedback", {})

        accepted = feedback.get("accepted", 0)
        rejected = feedback.get("rejected", 0)
        total = accepted + rejected

        if total == 0:
            return 0.5  # Neutral when no feedback

        reward = accepted / total
        return max(0.0, min(1.0, reward))
