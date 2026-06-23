"""JudgeAgent - Orchestrator for language-specific review agents.

The Judge Agent:
1. Detects languages in a PR diff
2. Dispatches to language agents in parallel
3. Aggregates results and resolves conflicts
4. Makes final review decision
"""

import re
from typing import Any, Dict, List

from semar.agents.base_agent import AgentContext, AgentResult, BaseAgent
from semar.agents.improvement_selector import ImprovementSelector
from semar.agents.rl_algorithm_selector import RLAlgorithmSelector
from semar.agents.trajectory_analyzer import TrajectoryAnalyzer

# Language detection patterns
LANGUAGE_PATTERNS = {
    "python": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:import |from |def |class |if __name__)", re.MULTILINE),
    "javascript": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:const |let |var |function |=>|require\()", re.MULTILINE),
    "typescript": re.compile(
        r"(?:^|\n)\s*[+-]?\s*(?:interface \w+|type \w+|enum \w+"
        r"|\w+[\w\s]*:\s*(?:string|number|boolean|void|any|never)\b)",
        re.MULTILINE,
    ),
    "go": re.compile(r'(?:^|\n)\s*[+-]?\s*(?:package |import "|"func )', re.MULTILINE),
    "java": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:public |private |protected |class |interface )", re.MULTILINE),
    "rust": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:fn |let mut |use |struct |impl |pub )", re.MULTILINE),
    "cpp": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:#include|std::|using namespace|int main)", re.MULTILINE),
    "ruby": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:def |class |module |require |puts )", re.MULTILINE),
    "php": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:\<\?php|\$\w+\s*=)", re.MULTILINE),
    "shell": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:#!/bin/(?:ba)?sh|echo |if \[|for |while )", re.MULTILINE),
    "sql": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:SELECT |INSERT |UPDATE |DELETE |CREATE TABLE)", re.MULTILINE),
    "swift": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:import |func |let |var |class |struct )", re.MULTILINE),
    "kotlin": re.compile(r"(?:^|\n)\s*[+-]?\s*(?:fun |val |var |class |object |import )", re.MULTILINE),
}

# File extension to language mapping
EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".sh": "shell",
    ".bash": "shell",
    ".sql": "sql",
    ".swift": "swift",
    ".kt": "kotlin",
}


class JudgeAgent(BaseAgent):
    """Orchestrator agent that dispatches to language-specific agents.

    Responsibilities:
    - Detect languages in PR diffs
    - Route to appropriate language agents
    - Execute agents in parallel
    - Resolve conflicts between agent reviews
    - Aggregate results into final verdict
    """

    def __init__(self):
        super().__init__(agent_id="judge", language=None)
        self.language_agents: Dict[str, Any] = {}
        self.trajectory_analyzer = TrajectoryAnalyzer()
        self.improvement_selector = ImprovementSelector()
        self.rl_selector = RLAlgorithmSelector()

    def register_language_agent(self, language: str, agent: Any) -> None:
        """Register a language-specific agent.

        Args:
            language: Language key (e.g., 'python', 'javascript')
            agent: Agent instance with execute_cycle method
        """
        self.language_agents[language] = agent

    def _detect_languages(self, diff: str, metadata: Dict[str, Any]) -> List[str]:
        """Detect programming languages in a PR diff.

        Args:
            diff: The PR diff content
            metadata: PR metadata with file list

        Returns:
            List of detected language keys
        """
        detected = set()

        # Check diff content against language patterns
        for lang, pattern in LANGUAGE_PATTERNS.items():
            if pattern.search(diff):
                detected.add(lang)

        # Check file extensions from metadata
        files = metadata.get("files", [])
        for file_path in files:
            for ext, lang in EXTENSION_MAP.items():
                if file_path.endswith(ext):
                    detected.add(lang)

        return list(detected)

    def _get_files_for_language(self, diff: str, language: str) -> List[str]:
        """Extract file paths from diff for a specific language.

        Args:
            diff: The PR diff content
            language: Language to filter files for

        Returns:
            List of file paths
        """
        files = []
        for ext, lang in EXTENSION_MAP.items():
            if lang == language:
                # Find files with this extension in diff
                pattern = re.compile(r"diff --git a/.*" + re.escape(ext) + r".*")
                matches = pattern.findall(diff)
                files.extend(matches)
        return files

    def _check_stall(self, metrics: Dict[str, Any]) -> bool:
        """Check if agent performance is stalled.

        Args:
            metrics: Current performance metrics

        Returns:
            True if stalled
        """
        improvement = metrics.get("improvement", 0.0)
        accuracy = metrics.get("accuracy", 0.0)
        return improvement <= 0.0 and accuracy < 0.7

    async def _dispatch_parallel(
        self,
        languages: List[str],
        pr_url: str,
        pr_diff: str,
        pr_metadata: Dict[str, Any],
    ) -> Dict[str, AgentResult]:
        """Dispatch review to multiple language agents in parallel.

        Args:
            languages: List of languages to dispatch to
            pr_url: PR URL
            pr_diff: PR diff content
            pr_metadata: PR metadata

        Returns:
            Dict mapping language to AgentResult
        """
        import asyncio

        results: Dict[str, AgentResult] = {}
        tasks = []

        for lang in languages:
            agent = self.language_agents.get(lang)
            if agent is None:
                continue

            context = AgentContext(
                pr_url=pr_url,
                pr_diff=pr_diff,
                pr_metadata=pr_metadata,
                language=lang,
                files=self._get_files_for_language(pr_diff, lang),
            )

            async def run_agent(a=agent, c=context, lang_name=lang):
                try:
                    return lang_name, await a.execute_cycle(c)
                except Exception:
                    return lang_name, None

            tasks.append(run_agent())

        if tasks:
            gathered = await asyncio.gather(*tasks, return_exceptions=True)
            for result in gathered:
                if isinstance(result, tuple) and len(result) == 2:
                    lang, agent_result = result
                    if agent_result is not None:
                        results[lang] = agent_result

        return results

    def _resolve_conflicts(self, results: Dict[str, AgentResult]) -> str:
        """Resolve conflicts between language agent reviews.

        Uses majority voting. Returns 'approve' or 'request_changes'.

        Args:
            results: Dict mapping language to AgentResult

        Returns:
            Final verdict string
        """
        if not results:
            return "approve"

        votes = {}
        for _lang, result in results.items():
            review = result.review.lower() if result.review else "approve"
            if "approve" in review:
                votes["approve"] = votes.get("approve", 0) + 1
            else:
                votes["request_changes"] = votes.get("request_changes", 0) + 1

        if votes.get("request_changes", 0) > votes.get("approve", 0):
            return "request_changes"
        return "approve"

    def _aggregate_results(self, results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """Aggregate results from multiple language agents.

        Args:
            results: Dict mapping language to AgentResult

        Returns:
            Aggregated results dict
        """
        all_suggestions = []
        all_metrics = {}

        for lang, result in results.items():
            all_suggestions.extend(result.suggestions)
            all_metrics[lang] = result.metrics

        return {
            "results": [
                {
                    "language": lang,
                    "review": result.review,
                    "suggestions": result.suggestions,
                    "metrics": result.metrics,
                }
                for lang, result in results.items()
            ],
            "total_suggestions": len(all_suggestions),
            "suggestions": all_suggestions,
            "metrics_by_language": all_metrics,
        }

    async def handle_pr_review(
        self,
        pr_url: str,
        pr_diff: str,
        pr_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle a full PR review by dispatching to language agents.

        Args:
            pr_url: PR URL
            pr_diff: PR diff content
            pr_metadata: PR metadata

        Returns:
            Aggregated review results
        """
        languages = self._detect_languages(pr_diff, pr_metadata)
        if not languages:
            return {"review": "no code changes detected", "results": [], "verdict": "approve"}

        results = await self._dispatch_parallel(languages, pr_url, pr_diff, pr_metadata)
        if not results:
            return {"review": "no agents available", "results": [], "verdict": "approve"}

        aggregated = self._aggregate_results(results)
        verdict = self._resolve_conflicts(results)
        aggregated["verdict"] = verdict

        return aggregated

    async def plan(self, context: AgentContext) -> Dict[str, Any]:
        return {"languages": self._detect_languages(context.pr_diff, context.pr_metadata)}

    async def action(self, context: AgentContext, plan: Dict[str, Any]) -> Any:
        return await self._dispatch_parallel(
            plan.get("languages", []), context.pr_url, context.pr_diff, context.pr_metadata
        )

    async def review(self, context: AgentContext, action_result: Any) -> AgentResult:
        verdict = self._resolve_conflicts(action_result) if action_result else "approve"
        return AgentResult(
            review=verdict,
            suggestions=[],
            metrics={"verdict": 1 if verdict == "approve" else 0},
            trajectory={},
            agent_id=self.agent_id,
            language="mixed",
            pr_url=context.pr_url,
        )

    async def update_instructions(self, context: AgentContext, review: AgentResult) -> None:
        pass
