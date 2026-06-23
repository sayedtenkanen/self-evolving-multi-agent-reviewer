"""BaseLanguageAgent - Language-specific base class with evolvable scaffold.

Extends BaseAgent with:
- Language-specific default prompts, skills, and rules
- Scaffold management for harness evolution
"""

from typing import Any, Dict, List, Optional, cast

from semar.agents.base_agent import AgentContext, AgentResult, BaseAgent


class BaseLanguageAgent(BaseAgent):
    """Base class for language-specific review agents.

    Provides default scaffold (system prompt, skills, rules) that can be
    evolved via harness updates. Subclasses override defaults for their
    specific language.
    """

    def __init__(self, language: str):
        """Initialize language agent.

        Args:
            language: Programming language this agent handles
        """
        super().__init__(agent_id=f"{language}_agent", language=language)
        scaffold: Dict[str, Any] = {
            "system_prompt": self._get_default_system_prompt(),
            "skills": self._get_default_skills(),
            "rules": self._get_default_rules(),
        }
        self._scaffold = scaffold

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt. Override in subclass."""
        return f"You are an expert {self.language} code reviewer."

    def _get_default_skills(self) -> List[str]:
        """Get default skills. Override in subclass."""
        return ["security_review"]

    def _get_default_rules(self) -> List[Any]:
        """Get default rules. Override in subclass."""
        return []

    def update_scaffold(
        self,
        prompts: Optional[Dict[str, str]] = None,
        skills: Optional[List[str]] = None,
        rules: Optional[List[Any]] = None,
    ) -> None:
        """Update agent scaffold.

        Args:
            prompts: Updated prompts (any key stored in scaffold["prompts"])
            skills: Updated skills list
            rules: Updated rules list
        """
        scaffold = cast(Dict[str, Any], self._scaffold)
        if prompts:
            scaffold.setdefault("prompts", {}).update(prompts)
            # Also set system_prompt if provided for backward compatibility
            if "system_prompt" in prompts:
                scaffold["system_prompt"] = prompts["system_prompt"]
        if skills is not None:
            scaffold["skills"] = skills
        if rules is not None:
            scaffold["rules"] = rules

    def get_scaffold(self) -> Dict[str, Any]:
        """Get current scaffold.

        Returns:
            Copy of current scaffold dictionary
        """
        return {
            "system_prompt": self._scaffold["system_prompt"],
            "skills": list(self._scaffold["skills"]),
            "rules": list(self._scaffold["rules"]),
        }

    async def plan(self, context: AgentContext) -> Dict[str, Any]:
        """Create review plan based on language and files."""
        return {
            "language": self.language,
            "files": context.files,
            "skills_to_use": self._scaffold["skills"],
            "rules_to_apply": self._scaffold["rules"],
        }

    async def action(self, context: AgentContext, plan: Dict[str, Any]) -> str:
        """Execute review. Returns review text."""
        files = plan.get("files", [])
        return f"Reviewed {len(files)} {self.language} files"

    async def review(self, context: AgentContext, action_result: str) -> AgentResult:
        """Self-reflect on review quality."""
        return AgentResult(
            review="approve",
            suggestions=[],
            metrics={"accuracy": 0.8},
            trajectory={},
            agent_id=self.agent_id,
            language=self.language or "unknown",
            pr_url=context.pr_url,
        )

    async def update_instructions(self, context: AgentContext, review: AgentResult) -> None:
        """Update scaffold based on learnings. Override for custom behavior."""
        pass
