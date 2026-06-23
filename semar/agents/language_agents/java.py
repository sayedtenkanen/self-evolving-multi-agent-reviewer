"""JavaAgent - Java-specific review agent."""

from typing import Any, Dict, List

from semar.agents.language_agents.base_language import BaseLanguageAgent


class JavaAgent(BaseLanguageAgent):
    """Java-specific review agent."""

    def __init__(self):
        super().__init__(language="java")

    def _get_default_system_prompt(self) -> str:
        return (
            "You are an expert Java code reviewer with deep knowledge of "
            "OOP patterns, concurrency, security, performance, "
            "and Java best practices."
        )

    def _get_default_skills(self) -> List[str]:
        return [
            "security_review",
            "concurrency_review",
            "oo_design",
            "performance_analysis",
        ]

    def _get_default_rules(self) -> List[Dict[str, Any]]:
        return [
            {"name": "no_synchronized", "pattern": r"\bsynchronized\b", "severity": "low"},
            {"name": "no_raw_types", "pattern": r"\bList\s+\w+", "severity": "medium"},
        ]
