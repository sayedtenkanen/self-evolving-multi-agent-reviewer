"""CppAgent - C++-specific review agent."""

from typing import Any, Dict, List

from semar.agents.language_agents.base_language import BaseLanguageAgent


class CppAgent(BaseLanguageAgent):
    """C++-specific review agent."""

    def __init__(self):
        super().__init__(language="cpp")

    def _get_default_system_prompt(self) -> str:
        return (
            "You are an expert C++ code reviewer with deep knowledge of "
            "memory management, RAII, templates, move semantics, "
            "performance, and modern C++ best practices."
        )

    def _get_default_skills(self) -> List[str]:
        return [
            "security_review",
            "memory_safety",
            "modern_cpp",
            "performance_analysis",
        ]

    def _get_default_rules(self) -> List[Dict[str, Any]]:
        return [
            {"name": "no_raw_new", "pattern": r"\bnew\s+\w+", "severity": "high"},
            {"name": "no_raw_delete", "pattern": r"\bdelete\s+", "severity": "high"},
            {"name": "no_sprintf", "pattern": r"\bsprintf\s*\(", "severity": "high"},
        ]
