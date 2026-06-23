"""JavaScriptAgent - JavaScript-specific review agent."""

from typing import Any, Dict, List

from semar.agents.language_agents.base_language import BaseLanguageAgent


class JavaScriptAgent(BaseLanguageAgent):
    """JavaScript-specific review agent."""

    def __init__(self):
        super().__init__(language="javascript")

    def _get_default_system_prompt(self) -> str:
        return (
            "You are an expert JavaScript code reviewer with deep knowledge of "
            "ES6+ features, async/await, security (XSS, prototype pollution), "
            "performance, and Node.js/browser best practices."
        )

    def _get_default_skills(self) -> List[str]:
        return [
            "security_review",
            "performance_analysis",
            "es6_best_practices",
            "async_patterns",
        ]

    def _get_default_rules(self) -> List[Dict[str, Any]]:
        return [
            {"name": "no_eval", "pattern": r"\beval\s*\(", "severity": "high"},
            {"name": "no_innerhtml", "pattern": r"\.innerHTML\s*=", "severity": "high"},
            {
                "name": "no_document_write",
                "pattern": r"\bdocument\.write\s*\(",
                "severity": "medium",
            },
        ]
