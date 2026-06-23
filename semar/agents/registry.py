"""AgentRegistry - Agent discovery, registration, and health management.

Manages language-specific agents with health checks, smart selection,
and performance tracking.
"""

import time
from typing import Any, Dict, List, Optional

from semar.agents.base_agent import BaseAgent


class AgentRegistry:
    """Discovers, manages, and health-checks language agents."""

    MAX_LATENCY_SAMPLES = 100

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.health: Dict[str, Dict[str, Any]] = {}
        self._failure_counts: Dict[str, int] = {}
        self._success_counts: Dict[str, int] = {}
        self._latencies: Dict[str, List[float]] = {}
        self._latency_sums: Dict[str, float] = {}
        self._latency_mins: Dict[str, float] = {}
        self._latency_maxs: Dict[str, float] = {}

    def register(self, language: str, agent: BaseAgent) -> None:
        """Register a language agent.

        Args:
            language: Language key (e.g., 'python')
            agent: Agent instance
        """
        self.agents[language] = agent
        self.health[language] = {
            "status": "unknown",
            "last_heartbeat": 0.0,
            "last_error": None,
        }
        self._failure_counts[language] = 0
        self._success_counts[language] = 0
        self._latencies[language] = []
        self._latency_sums[language] = 0.0
        self._latency_mins[language] = float("inf")
        self._latency_maxs[language] = 0.0

    def unregister(self, language: str) -> None:
        """Remove an agent from registry.

        Args:
            language: Language key to remove
        """
        self.agents.pop(language, None)
        self.health.pop(language, None)
        self._failure_counts.pop(language, None)
        self._success_counts.pop(language, None)
        self._latencies.pop(language, None)
        self._latency_sums.pop(language, None)
        self._latency_mins.pop(language, None)
        self._latency_maxs.pop(language, None)

    def get_agent(self, language: str) -> Optional[BaseAgent]:
        """Get agent by language.

        Args:
            language: Language key

        Returns:
            Agent instance or None
        """
        return self.agents.get(language)

    def list_agents(self) -> List[str]:
        """List all registered language keys.

        Returns:
            List of language keys
        """
        return list(self.agents.keys())

    async def health_check(self, timeout: float = 5.0) -> Dict[str, Dict[str, Any]]:
        """Run health check on all registered agents.

        Args:
            timeout: Max seconds to wait per agent

        Returns:
            Dict mapping language to health status
        """
        import asyncio

        for language, agent in self.agents.items():
            try:
                start = time.time()
                await asyncio.wait_for(agent.health_ping(), timeout=timeout)
                latency_ms = (time.time() - start) * 1000
                self.health[language] = {
                    "status": "healthy",
                    "last_heartbeat": time.time(),
                    "last_error": None,
                    "latency_ms": latency_ms,
                }
            except asyncio.TimeoutError:
                self.health[language] = {
                    "status": "degraded",
                    "last_heartbeat": self.health.get(language, {}).get("last_heartbeat", 0),
                    "last_error": "Health check timeout",
                }
                self._failure_counts[language] = self._failure_counts.get(language, 0) + 1
            except Exception as e:
                self.health[language] = {
                    "status": "unhealthy",
                    "last_heartbeat": self.health.get(language, {}).get("last_heartbeat", 0),
                    "last_error": str(e),
                }
                self._failure_counts[language] = self._failure_counts.get(language, 0) + 1

        return self.health

    def select_agents(self, languages: List[str]) -> List[str]:
        """Select best agents for given languages.

        Excludes unhealthy agents.

        Args:
            languages: List of languages to select agents for

        Returns:
            List of selected language keys
        """
        selected = []
        for lang in languages:
            if lang not in self.agents:
                continue
            status = self.health.get(lang, {}).get("status", "unknown")
            if status == "unhealthy":
                continue
            selected.append(lang)
        return selected

    def record_success(self, language: str, latency_ms: float = 0.0) -> None:
        """Record successful agent execution.

        Args:
            language: Language key
            latency_ms: Execution latency in milliseconds
        """
        if language in self.agents:
            self._success_counts[language] = self._success_counts.get(language, 0) + 1
            # Track aggregates
            self._latency_sums[language] = self._latency_sums.get(language, 0.0) + latency_ms
            self._latency_mins[language] = min(self._latency_mins.get(language, float("inf")), latency_ms)
            self._latency_maxs[language] = max(self._latency_maxs.get(language, 0.0), latency_ms)
            # Keep bounded sample window for avg
            samples = self._latencies.setdefault(language, [])
            samples.append(latency_ms)
            if len(samples) > self.MAX_LATENCY_SAMPLES:
                samples.pop(0)

    def record_failure(self, language: str, error: str = "") -> None:
        """Record failed agent execution.

        Args:
            language: Language key
            error: Error message
        """
        if language in self.agents:
            self._failure_counts[language] = self._failure_counts.get(language, 0) + 1
            self.health[language]["last_error"] = error

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics.

        Returns:
            Stats dictionary
        """
        total = len(self.agents)
        healthy = sum(1 for h in self.health.values() if h.get("status") == "healthy")
        total_successes = sum(self._success_counts.values())
        total_failures = sum(self._failure_counts.values())

        avg_latency = 0.0
        min_latency = 0.0
        max_latency = 0.0
        all_latencies = []
        for latencies in self._latencies.values():
            all_latencies.extend(latencies)
        if all_latencies:
            avg_latency = sum(all_latencies) / len(all_latencies)
        if self._latency_mins:
            valid_mins = [v for v in self._latency_mins.values() if v != float("inf")]
            min_latency = min(valid_mins) if valid_mins else 0.0
        if self._latency_maxs:
            max_latency = max(self._latency_maxs.values()) if self._latency_maxs else 0.0

        return {
            "total_agents": total,
            "healthy_agents": healthy,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "avg_latency_ms": avg_latency,
            "min_latency_ms": min_latency,
            "max_latency_ms": max_latency,
        }
