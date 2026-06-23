"""TrajectoryAnalyzer - Analyzes execution trajectories for failure modes."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class FailureMode:
    """Detected failure mode in agent execution."""

    type: str
    severity: str
    frequency: int
    examples: List[Dict[str, Any]] = field(default_factory=list)


class TrajectoryAnalyzer:
    """Analyzes execution trajectories to detect failure modes.

    Failure modes detected:
    - missed_issue: Issues found by humans that agents missed
    - false_positive: Suggestions rejected as incorrect
    - hallucination: Actions taken on non-existent code
    - overconfident: High confidence on wrong decisions
    """

    async def analyze(self, trajectory: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a trajectory and return failure modes.

        Args:
            trajectory: Full execution trajectory dict

        Returns:
            Analysis with prompts, responses, tool_calls, metrics, failure_modes
        """
        steps = trajectory.get("steps", {})
        metrics = trajectory.get("metrics", {})
        failure_modes: List[FailureMode] = []

        # Extract trajectory sections
        prompts = []
        responses = []
        tool_calls = []

        for step_name, step_data in steps.items():
            output = step_data.get("output", {})
            if isinstance(output, dict):
                if "review" in output:
                    responses.append(output["review"])
                if "plan" in output:
                    prompts.append(output.get("plan"))
                tool_calls.append({"step": step_name, "output": output})
            elif isinstance(output, str):
                responses.append(output)

        # Detect missed issues (from human follow-up)
        human_follow_up = trajectory.get("human_follow_up", [])
        if human_follow_up:
            failure_modes.append(
                FailureMode(
                    type="missed_issue",
                    severity="high",
                    frequency=len(human_follow_up),
                    examples=human_follow_up[:5],
                )
            )

        # Detect false positives (from rejected suggestions)
        rejected = trajectory.get("rejected_suggestions", [])
        if rejected:
            failure_modes.append(
                FailureMode(
                    type="false_positive",
                    severity="medium",
                    frequency=len(rejected),
                    examples=rejected[:5],
                )
            )

        # Detect hallucination (actions on non-existent files)
        action_files = steps.get("action", {}).get("output", {})
        if isinstance(action_files, dict) and action_files.get("hallucinated"):
            failure_modes.append(
                FailureMode(
                    type="hallucination",
                    severity="high",
                    frequency=1,
                    examples=[action_files],
                )
            )

        # Detect overconfident decisions
        confidence = metrics.get("confidence", 0.0)
        accuracy = metrics.get("accuracy", 1.0)
        if confidence > 0.9 and accuracy < 0.7:
            failure_modes.append(
                FailureMode(
                    type="overconfident",
                    severity="medium",
                    frequency=1,
                    examples=[{"confidence": confidence, "accuracy": accuracy}],
                )
            )

        return {
            "prompts": prompts,
            "responses": responses,
            "tool_calls": tool_calls,
            "metrics": metrics,
            "failure_modes": failure_modes,
        }
