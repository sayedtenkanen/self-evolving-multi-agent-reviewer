"""TypeScriptAgent - TypeScript-specific review agent."""

from typing import Any, Dict, List

from semar.agents.language_agents.base_language import BaseLanguageAgent


class TypeScriptAgent(BaseLanguageAgent):
    """TypeScript-specific review agent."""

    def __init__(self):
        super().__init__(language="typescript")

    def _get_default_system_prompt(self) -> str:
        return (
            "You are an expert TypeScript code reviewer with deep knowledge of "
            "type system design, generics, utility types, strict mode, "
            "and TypeScript-specific best practices."
        )

    def _get_default_skills(self) -> List[str]:
        return [
            "security_review",
            "type_safety",
            "generics_review",
            "strict_mode_check",
        ]

    def _get_default_rules(self) -> List[Dict[str, Any]]:
        return [
            {"name": "no_any", "pattern": r":\s*any\b", "severity": "medium"},
            {"name": "no_explicit_null", "pattern": r":\s*null\b", "severity": "low"},
        ]
