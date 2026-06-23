"""PythonAgent - Python-specific review agent."""

from typing import Any, Dict, List

from semar.agents.language_agents.base_language import BaseLanguageAgent


class PythonAgent(BaseLanguageAgent):
    """Python-specific review agent with Python best practices."""

    def __init__(self):
        super().__init__(language="python")

    def _get_default_system_prompt(self) -> str:
        return (
            "You are an expert Python code reviewer with deep knowledge of "
            "PEP 8, type hints, async/await patterns, security vulnerabilities, "
            "performance optimization, and testing patterns."
        )

    def _get_default_skills(self) -> List[str]:
        return [
            "security_review",
            "performance_analysis",
            "type_hints_check",
            "pep8_compliance",
            "test_coverage",
        ]

    def _get_default_rules(self) -> List[Dict[str, Any]]:
        return [
            {"name": "no_eval", "pattern": r"\beval\s*\(", "severity": "high"},
            {"name": "no_exec", "pattern": r"\bexec\s*\(", "severity": "high"},
            {
                "name": "no_hardcoded_secrets",
                "pattern": r"(password|secret|key)\s*=\s*['\"]",
                "severity": "high",
            },
        ]
