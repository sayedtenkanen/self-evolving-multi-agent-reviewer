"""GoAgent - Go-specific review agent."""

from typing import Any, Dict, List

from semar.agents.language_agents.base_language import BaseLanguageAgent


class GoAgent(BaseLanguageAgent):
    """Go-specific review agent."""

    def __init__(self):
        super().__init__(language="go")

    def _get_default_system_prompt(self) -> str:
        return (
            "You are an expert Go code reviewer with deep knowledge of "
            "concurrency patterns, goroutines, error handling, "
            "performance, and Go idioms."
        )

    def _get_default_skills(self) -> List[str]:
        return [
            "security_review",
            "concurrency_review",
            "error_handling",
            "performance_analysis",
        ]

    def _get_default_rules(self) -> List[Dict[str, Any]]:
        return [
            {"name": "no_unchecked_errors", "pattern": r"_\s*=\s*\w+\(", "severity": "medium"},
            {"name": "no_raw_goroutine", "pattern": r"\bgo\s+\w+\(", "severity": "low"},
        ]
