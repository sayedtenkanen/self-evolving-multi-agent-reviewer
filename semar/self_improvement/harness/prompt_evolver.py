"""PromptEvolver - Evolves agent prompts based on trajectory failure analysis."""

import time
from typing import Any, Dict, List

from semar.agents.trajectory_analyzer import FailureMode

# Keywords to inject based on failure type
_FAILURE_PROMPT_ADDITIONS = {
    "missed_issue": {
        "high": "\n\nIMPORTANT: Pay special attention to security vulnerabilities. "
        "Actively look for injection attacks (SQL, command, XSS), authentication bypasses, "
        "and data exposure. Do not skip any file without checking for these patterns.",
        "medium": "\n\nNote: Review for common issues that may have been missed previously.",
        "low": "",
    },
    "false_positive": {
        "high": "\n\nIMPORTANT: Be more precise in your suggestions. Only flag issues "
        "you are highly confident about. Avoid suggesting changes that are matters of "
        "preference rather than correctness. When uncertain, do not suggest a change.",
        "medium": "\n\nNote: Reduce false positives by verifying each suggestion against "
        "concrete evidence in the code.",
        "low": "",
    },
    "hallucination": {
        "high": "\n\nIMPORTANT: Only reference files and code that actually exist in the "
        "diff. Verify that every file you mention appears in the provided file list.",
        "medium": "",
        "low": "",
    },
    "overconfident": {
        "high": "\n\nIMPORTANT: Express appropriate uncertainty. If you are not sure about "
        "an issue, indicate your confidence level. Do not present tentative findings as "
        "definite bugs.",
        "medium": "",
        "low": "",
    },
}


class PromptEvolver:
    """Evolves agent prompts based on trajectory failure analysis.

    When failures are detected (missed issues, false positives, hallucinations,
    overconfident decisions), the PromptEvolver generates an improved prompt that
    addresses the specific weaknesses found.
    """

    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    async def evolve(
        self,
        current_prompt: str,
        failure_modes: List[FailureMode],
    ) -> str:
        """Evolve a prompt to address detected failure modes.

        Args:
            current_prompt: The current agent system prompt
            failure_modes: Failure modes detected by TrajectoryAnalyzer

        Returns:
            Improved prompt string
        """
        if not failure_modes:
            return current_prompt

        evolved = current_prompt

        # Group failures by type and pick highest severity
        by_type: Dict[str, str] = {}
        for fm in failure_modes:
            existing = by_type.get(fm.type)
            if existing is None or _severity_rank(fm.severity) > _severity_rank(existing):
                by_type[fm.type] = fm.severity

        # Append targeted guidance for each failure type
        for failure_type, severity in by_type.items():
            addition = _FAILURE_PROMPT_ADDITIONS.get(failure_type, {}).get(severity, "")
            if addition and addition not in evolved:
                evolved += addition

        # Record history
        self._history.append(
            {
                "original": current_prompt,
                "evolved": evolved,
                "failure_count": len(failure_modes),
                "failure_types": list(by_type.keys()),
                "timestamp": time.time(),
            }
        )

        return evolved

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the history of prompt evolutions.

        Returns:
            List of evolution records
        """
        return list(self._history)


def _severity_rank(severity: str) -> int:
    """Convert severity string to numeric rank for comparison."""
    return {"high": 3, "medium": 2, "low": 1}.get(severity, 0)
