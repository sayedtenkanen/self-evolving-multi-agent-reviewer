"""SkillDiscovery - Discovers new analysis patterns from trajectories."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DiscoveredSkill:
    """A skill discovered from trajectory patterns."""

    name: str
    description: str
    confidence: float
    frequency: int = 1
    examples: List[Dict[str, Any]] = field(default_factory=list)
    discovered_at: float = field(default_factory=time.time)


# Common patterns to detect in review outputs
_PATTERN_DETECTORS = [
    {
        "name": "security_review",
        "keywords": ["injection", "xss", "csrf", "vulnerability", "security", "auth", "sanitize"],
        "description": "Security vulnerability detection",
    },
    {
        "name": "performance_analysis",
        "keywords": ["performance", "slow", "optimize", "cache", "latency", "memory", "cpu"],
        "description": "Performance issue detection",
    },
    {
        "name": "error_handling",
        "keywords": ["error handling", "exception", "try catch", "unwrap", "panic", "raise"],
        "description": "Error handling pattern review",
    },
    {
        "name": "type_safety",
        "keywords": ["type hint", "type check", "any type", "type mismatch", "casting"],
        "description": "Type safety and type hint review",
    },
    {
        "name": "code_style",
        "keywords": ["naming", "formatting", "lint", "style", "convention", "pep8"],
        "description": "Code style and convention review",
    },
    {
        "name": "test_coverage",
        "keywords": ["test", "coverage", "mock", "assert", "unittest", "pytest"],
        "description": "Test coverage and quality review",
    },
    {
        "name": "dependency_analysis",
        "keywords": ["dependency", "import", "package", "version", "vulnerability", "supply chain"],
        "description": "Dependency and supply chain review",
    },
    {
        "name": "concurrency_review",
        "keywords": ["race condition", "deadlock", "thread", "async", "goroutine", "mutex"],
        "description": "Concurrency and thread safety review",
    },
]


class SkillDiscovery:
    """Discovers new analysis skills from trajectory patterns.

    Analyzes trajectories to find recurring patterns in agent reviews,
    then registers them as reusable skills.
    """

    def __init__(self, min_frequency: int = 1):
        """Initialize skill discovery.

        Args:
            min_frequency: Minimum occurrence count to register a skill
        """
        self.min_frequency = min_frequency
        self._skills: List[DiscoveredSkill] = []

    async def discover(self, trajectories: List[Dict[str, Any]]) -> List[DiscoveredSkill]:
        """Discover skills from trajectory data.

        Args:
            trajectories: List of execution trajectories

        Returns:
            List of newly discovered skills
        """
        if not trajectories:
            return []

        # Extract review outputs from trajectories
        review_texts = self._extract_review_texts(trajectories)

        # Count pattern occurrences
        pattern_counts: Dict[str, int] = {}
        pattern_examples: Dict[str, List[Dict[str, Any]]] = {}

        for text in review_texts:
            text_lower = text.lower()
            for detector in _PATTERN_DETECTORS:
                matches = sum(1 for kw in detector["keywords"] if kw in text_lower)
                if matches > 0:
                    det_name = str(detector["name"])
                    pattern_counts[det_name] = pattern_counts.get(det_name, 0) + 1
                    if det_name not in pattern_examples:
                        pattern_examples[det_name] = []
                    pattern_examples[det_name].append({"text": text[:200], "matches": matches})

        # Register skills that meet frequency threshold
        new_skills: List[DiscoveredSkill] = []
        for pat_name, count in pattern_counts.items():
            if count >= self.min_frequency:
                # Check if already discovered
                existing = next((s for s in self._skills if s.name == pat_name), None)
                if existing is None:
                    detector = next(d for d in _PATTERN_DETECTORS if d["name"] == pat_name)
                    det_desc = str(detector["description"])
                    confidence = min(1.0, count / max(len(trajectories), 1))
                    skill = DiscoveredSkill(
                        name=pat_name,
                        description=det_desc,
                        confidence=confidence,
                        frequency=count,
                        examples=pattern_examples.get(pat_name, [])[:3],
                    )
                    self._skills.append(skill)
                    new_skills.append(skill)
                else:
                    # Update frequency
                    existing.frequency = max(existing.frequency, count)
                    existing.confidence = min(1.0, count / max(len(trajectories), 1))

        return new_skills

    def get_skills(self) -> List[DiscoveredSkill]:
        """Get all discovered skills.

        Returns:
            List of discovered skills
        """
        return list(self._skills)

    def _extract_review_texts(self, trajectories: List[Dict[str, Any]]) -> List[str]:
        """Extract review text content from trajectories."""
        texts: List[str] = []
        for traj in trajectories:
            steps = traj.get("steps", {})
            for step_data in steps.values():
                output = step_data.get("output", "")
                if isinstance(output, str):
                    texts.append(output)
                elif isinstance(output, dict):
                    review = output.get("review", "")
                    if review:
                        texts.append(str(review))
        return texts
