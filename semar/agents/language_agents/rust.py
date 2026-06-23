"""RustAgent - Rust-specific review agent."""

from typing import Any, Dict, List

from semar.agents.language_agents.base_language import BaseLanguageAgent


class RustAgent(BaseLanguageAgent):
    """Rust-specific review agent."""

    def __init__(self):
        super().__init__(language="rust")

    def _get_default_system_prompt(self) -> str:
        return (
            "You are an expert Rust code reviewer with deep knowledge of "
            "ownership, borrowing, lifetimes, unsafe code, "
            "performance, and Rust idioms."
        )

    def _get_default_skills(self) -> List[str]:
        return [
            "security_review",
            "ownership_review",
            "unsafe_code_review",
            "performance_analysis",
        ]

    def _get_default_rules(self) -> List[Dict[str, Any]]:
        return [
            {"name": "no_unsafe", "pattern": r"\bunsafe\s*\{", "severity": "medium"},
            {"name": "no_clone_abuse", "pattern": r"\.clone\(\)", "severity": "low"},
        ]
