"""ImprovementSelector - Decides between harness and weight updates."""

from enum import Enum
from typing import Any, Dict


class ImprovementType(Enum):
    """Type of improvement to apply."""

    HARNESS = "harness"
    WEIGHT = "weight"
    NONE = "none"


class ImprovementSelector:
    """Decides whether to apply harness update or weight update.

    Decision logic:
    - Harness update: When failure modes are detected (needs prompt/skill changes)
    - Weight update: When agent is stalled (needs algorithmic improvement)
    - None: When performance is improving steadily

    Uses stall detection: tracks consecutive iterations without improvement.
    """

    def __init__(self, stall_threshold: int = 3):
        """Initialize the selector.

        Args:
            stall_threshold: Number of consecutive no-improvement iterations before weight update
        """
        self.stall_threshold = stall_threshold
        self.consecutive_no_improvement = 0

    async def decide(self, analysis: Dict[str, Any]) -> ImprovementType:
        """Decide improvement type based on analysis.

        Args:
            analysis: Output from TrajectoryAnalyzer.analyze()

        Returns:
            ImprovementType to apply
        """
        failure_modes = analysis.get("failure_modes", [])
        metrics = analysis.get("metrics", {})
        improvement = metrics.get("improvement", 0.0)

        # Always harness update if there are failures to fix
        if failure_modes:
            return ImprovementType.HARNESS

        # Track improvement
        if improvement <= 0.0:
            self.consecutive_no_improvement += 1
        else:
            self.consecutive_no_improvement = 0

        # Weight update if stalled
        if self.consecutive_no_improvement >= self.stall_threshold:
            return ImprovementType.WEIGHT

        return ImprovementType.HARNESS
