# SEMAR Architecture

> **Status**: This is a **design document**. Code examples are aspirational/reference designs.
> Components marked as "Implemented" have production code and tests in `semar/semar/` and `semar/tests/`.
> Components marked as "Planned" are design-only and will be implemented in future phases.

## Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Judge Agent (orchestrator) | **Implemented** | `semar/semar/agents/judge_agent.py` |
| BaseAgent (4-step cycle) | **Implemented** | `semar/semar/agents/base_agent.py` |
| Language Detection | **Implemented** | `semar/semar/agents/judge_agent.py:_detect_languages()` |
| Parallel Dispatch | **Implemented** | `semar/semar/agents/judge_agent.py:_dispatch_parallel()` |
| Result Aggregation | **Implemented** | `semar/semar/agents/judge_agent.py:_aggregate_results()` |
| Conflict Resolution (majority vote) | **Implemented** | `semar/semar/agents/judge_agent.py:_resolve_conflicts()` |
| TrajectoryAnalyzer | **Implemented** | `semar/semar/agents/trajectory_analyzer.py` |
| ImprovementSelector | **Implemented** | `semar/semar/agents/improvement_selector.py` |
| RLAlgorithmSelector | **Implemented** | `semar/semar/agents/rl_algorithm_selector.py` |
| TrajectoryStore (SQLite) | **Implemented** | `semar/semar/agents/trajectory_store.py` |
| Config (dynaconf) | **Implemented** | `semar/semar/config/settings.py` |
| BaseLanguageAgent | **Implemented** | `semar/semar/agents/language_agents/base_language.py` |
| PythonAgent | **Implemented** | `semar/semar/agents/language_agents/python.py` |
| JavaScriptAgent | **Implemented** | `semar/semar/agents/language_agents/javascript.py` |
| TypeScriptAgent | **Implemented** | `semar/semar/agents/language_agents/typescript.py` |
| GoAgent | **Implemented** | `semar/semar/agents/language_agents/go.py` |
| JavaAgent | **Implemented** | `semar/semar/agents/language_agents/java.py` |
| RustAgent | **Implemented** | `semar/semar/agents/language_agents/rust.py` |
| CppAgent | **Implemented** | `semar/semar/agents/language_agents/cpp.py` |
| AgentRegistry | **Implemented** | `semar/semar/agents/registry.py` |
| Inter-Agent Communication | **Planned** | `semar/semar/agents/` (Phase 4) |
| Cross-Agent Learning | **Planned** | `semar/semar/self_improvement/` (Phase 4) |
| Harness Evolution | **Implemented** | `semar/semar/self_improvement/harness/` |
| Weight Training (LoRA) | **Implemented** | `semar/semar/self_improvement/weight_training/` |

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Judge Agent (Feedback-Agent)                    │
│  - Analyzes full review trajectories                        │
│  - Decides: harness update OR weight update                 │
│  - Selects appropriate RL algorithm                         │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│              Language Agent Pool                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│  │ Python  │ │   JS    │ │   Go    │ │  Java   │ ...     │
│  │ Agent   │ │  Agent  │ │  Agent  │ │  Agent  │         │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│              Self-Improvement Infrastructure                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Trajectory   │  │ Harness      │  │ Weight       │     │
│  │ Store        │  │ Evolution    │  │ Training     │     │
│  │ (SQLite)     │  │ (Prompts,    │  │ (RL with     │     │
│  │              │  │  Skills,     │  │  adaptive    │     │
│  │              │  │  Rules)      │  │  algorithm)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Judge Agent (Dual-Role Orchestrator) — Implemented

The Judge Agent is a **single class** that handles two distinct roles from the SIA paper:

**Role 1: Orchestrator (Meta-Agent ℳ)**
- Receives PR review requests
- Detects languages in the PR
- Dispatches to language agents in parallel
- Aggregates results
- Handles error recovery and timeouts

**Role 2: Feedback-Agent (ℱ)**
- Analyzes full trajectories (not just metrics)
- Identifies specific failure modes
- Decides between harness updates and weight updates
- Selects appropriate RL algorithm
- Triggers self-improvement actions

**Why Single Class**: The Judge Agent maintains context across both roles. The orchestrator role needs trajectory data that the feedback role analyzes. Separating them would require duplicating state management.

**Key Methods**:
- `handle_pr_review()` - Main entry point (orchestrator role)
- `_dispatch_parallel()` - Parallel agent execution with error handling
- `_aggregate_results()` - Combine agent outputs
- `analyze_trajectories()` - Analyze execution logs (feedback role)
- `decide_improvement()` - Select H vs W update (feedback role)
- `_improve_harness()` - Trigger scaffold evolution
- `_train_weights()` - Trigger RL training

### Language Agents — Planned (Phase 3)

Each language agent is specialized for a specific programming language:
- Python, JavaScript, TypeScript, Go, Java, Rust, C++

**Base Class**: `BaseLanguageAgent`
- Inherits from `BaseAgent`
- Has evolvable scaffold (prompts, skills, rules)
- Captures full execution trajectories
- Implements 4-step cycle
- **Must implement `health_ping()`**: Returns health status for agent registry

**Agent Registry**: Discovers, manages, and health-checks language agents:

```python
import asyncio
import time
import importlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from pathlib import Path

@dataclass
class AgentCapabilities:
    languages: List[str]
    frameworks: List[str] = field(default_factory=list)  # e.g., ["django", "flask", "fastapi"]
    min_files: int = 1
    max_files: int = 10000
    supports_broadcast: bool = True
    supports_request_response: bool = True

@dataclass
class AgentHealth:
    status: Literal["healthy", "degraded", "unhealthy", "unknown"]
    last_heartbeat: float
    success_rate: float  # rolling 30-day
    avg_latency_ms: float
    error_count: int
    last_error: Optional[str] = None

import logging

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Discovers, manages, and health-checks language agents"""

    def __init__(self):
        self.agents: Dict[str, BaseLanguageAgent] = {}
        self.health: Dict[str, AgentHealth] = {}
        self.capabilities: Dict[str, AgentCapabilities] = {}
        self._failure_counts: Dict[str, int] = {}

    async def discover(self, agents_dir: str = "semar/agents/language_agents"):
        """Auto-discover agents from directory structure"""
        agent_files = Path(agents_dir).glob("*_agent.py")
        for agent_file in agent_files:
            if agent_file.name.startswith("base_"):
                continue
            module_name = agent_file.stem
            try:
                module = importlib.import_module(f"semar.agents.language_agents.{module_name}")
                agent_class = getattr(module, module_name.replace("_agent", "Agent").title() + "Agent")
                agent = agent_class()
                await self.register(
                    agent_id=f"{module_name.replace('_agent', '')}_agent",
                    agent=agent,
                    capabilities=agent.get_capabilities()
                )
            except (ImportError, AttributeError) as e:
                logger.warning(f"Failed to load agent {module_name}: {e}")

    async def register(self, agent_id: str, agent: BaseLanguageAgent,
                       capabilities: AgentCapabilities):
        """Register a language agent"""
        self.agents[agent_id] = agent
        self.capabilities[agent_id] = capabilities
        self.health[agent_id] = AgentHealth(
            status="unknown",
            last_heartbeat=0,
            success_rate=1.0,
            avg_latency_ms=0,
            error_count=0
        )
        logger.info(f"Registered agent: {agent_id} for languages: {capabilities.languages}")

    async def unregister(self, agent_id: str):
        """Remove an agent from registry"""
        self.agents.pop(agent_id, None)
        self.health.pop(agent_id, None)
        self.capabilities.pop(agent_id, None)
        self._failure_counts.pop(agent_id, None)

    async def health_check(self) -> Dict[str, AgentHealth]:
        """Periodic health check of all registered agents"""
        # Snapshot agent IDs to avoid RuntimeError during iteration
        agent_ids = list(self.agents.keys())
        for agent_id in agent_ids:
            agent = self.agents.get(agent_id)
            if not agent:
                continue
            try:
                start = time.time()
                await asyncio.wait_for(agent.health_ping(), timeout=5.0)
                latency = (time.time() - start) * 1000
                self.health[agent_id] = AgentHealth(
                    status="healthy",
                    last_heartbeat=time.time(),
                    success_rate=self._calc_success_rate(agent_id),
                    avg_latency_ms=latency,
                    error_count=0
                )
            except asyncio.TimeoutError:
                self.health[agent_id].status = "degraded"
                self.health[agent_id].last_error = "Health check timeout"
            except Exception as e:
                self.health[agent_id].status = "unhealthy"
                self.health[agent_id].last_error = str(e)
                self._failure_counts[agent_id] = self._failure_counts.get(agent_id, 0) + 1

        return self.health

    def _calc_success_rate(self, agent_id: str) -> float:
        """Calculate rolling success rate for an agent"""
        failures = self._failure_counts.get(agent_id, 0)
        return max(0.0, 1.0 - (failures * 0.1))  # Allow 0.0 for completely dead agents

    def select_agents(self, languages: List[str],
                      file_counts: Dict[str, int]) -> List[str]:
        """Select best agents for given languages based on capabilities and health"""
        selected = []
        for lang in languages:
            candidates = [
                aid for aid, caps in self.capabilities.items()
                if lang in caps.languages
                and self.health.get(aid, AgentHealth("unknown", 0, 0, 0, 0)).status != "unhealthy"
                and file_counts.get(lang, 0) >= caps.min_files
                and file_counts.get(lang, 0) <= caps.max_files
            ]
            # Pick best by weighted score (success_rate * inverse_latency)
            if candidates:
                best = max(candidates, key=lambda a: (
                    self.health[a].success_rate * (1.0 / max(self.health[a].avg_latency_ms, 1))
                ))
                selected.append(best)
        return selected

    async def record_success(self, agent_id: str, latency_ms: float):
        """Record successful agent execution"""
        if agent_id in self.health:
            h = self.health[agent_id]
            h.success_rate = min(1.0, h.success_rate * 0.95 + 0.05)
            h.avg_latency_ms = h.avg_latency_ms * 0.9 + latency_ms * 0.1
            self._failure_counts[agent_id] = max(0, self._failure_counts.get(agent_id, 0) - 1)

    async def record_failure(self, agent_id: str, error: str):
        """Record failed agent execution"""
        if agent_id in self.health:
            h = self.health[agent_id]
            h.success_rate = max(0.0, h.success_rate * 0.9)
            h.error_count += 1
            h.last_error = error
            self._failure_counts[agent_id] = self._failure_counts.get(agent_id, 0) + 1
```

**Key Features**:
- **Dynamic Registration**: Agents auto-discovered from directory structure
- **Health Checking**: Periodic pings with timeout, status tracking
- **Capability Declaration**: Languages, frameworks, file count limits
- **Smart Selection**: Best agent chosen by success rate and latency
- **Failure Tracking**: Rolling success rate, error counts, automatic recovery

### Language Detection Mechanism — Implemented (simplified in JudgeAgent)

The Judge Agent detects languages in a PR using multiple strategies with confidence scoring:

**Strategy 1: File Extension Mapping**
```python
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

LANGUAGE_EXTENSIONS = {
    "python": [".py", ".pyw", ".pyi"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "typescript": [".ts", ".tsx"],
    "go": [".go"],
    "java": [".java"],
    "rust": [".rs"],
    "cpp": [".cpp", ".cc", ".cxx", ".c++", ".hpp"],
    "c": [".c", ".h"],  # Separate from C++
    "swift": [".swift"],
    "kotlin": [".kt", ".kts"],
    "ruby": [".rb", ".rake", ".gemspec"],
    "php": [".php"],
    "shell": [".sh", ".bash", ".zsh"],
    "sql": [".sql"],
}

EXCLUDED_PATTERNS = [
    r".*\.min\.(js|css)$",           # Minified files
    r".*\.pyc$",                       # Compiled Python
    r".*__pycache__.*",                # Python cache
    r".*node_modules.*",               # Node dependencies
    r".*\.lock$",                      # Lock files
    r".*\.sum$",                       # Sum files
    r".*vendor/.*",                    # Go/PHP vendor
    r".*dist/.*",                      # Build output
    r".*build/.*",                     # Build output
    r".*\.o$",                         # Object files
    r".*\.so$",                        # Shared objects
    r".*\.dylib$",                     # macOS libraries
    r".*\.exe$",                       # Windows executables
    r".*\.jar$",                       # Java archives
    r".*\.pyc$",                       # Python bytecode
]

@dataclass
class LanguageDetectionResult:
    languages: Dict[str, int]  # language -> file count
    confidence: Dict[str, float]  # language -> detection confidence
    method: str  # "extensions", "metadata", "content", "mixed"
    ambiguous_files: List[str] = field(default_factory=list)  # Could be multiple languages
    excluded_files: List[str] = field(default_factory=list)  # Filtered out

def detect_languages_from_extensions(files: List[str]) -> Tuple[Dict[str, int], List[str], List[str]]:
    """Count files by language extension, filter exclusions, track ambiguous"""
    counts = {}
    excluded = []
    ambiguous = []

    for file in files:
        # Check exclusion patterns
        if any(re.match(pattern, file) for pattern in EXCLUDED_PATTERNS):
            excluded.append(file)
            continue

        # Check extensions
        matched_langs = []
        for lang, extensions in LANGUAGE_EXTENSIONS.items():
            if any(file.endswith(ext) for ext in extensions):
                matched_langs.append(lang)

        if len(matched_langs) > 1:
            ambiguous.append(file)
            # Use primary extension to pick one
            counts[matched_langs[0]] = counts.get(matched_langs[0], 0) + 1
        elif len(matched_langs) == 1:
            counts[matched_langs[0]] = counts.get(matched_langs[0], 0) + 1

    return counts, ambiguous, excluded

def detect_languages_from_metadata(pr_metadata: Optional[Dict]) -> Dict[str, float]:
    """Detect from PR metadata (GitHub API language stats)"""
    if not pr_metadata or "languages" not in pr_metadata:
        return {}
    # Convert byte counts to percentages
    total = sum(pr_metadata["languages"].values()) or 1  # Prevent division by zero
    return {lang: bytes_count / total for lang, bytes_count in pr_metadata["languages"].items()}

def detect_languages_from_content(files: List[str], sample_size: int = 3) -> Dict[str, float]:
    """Content-based detection with heuristics"""
    import random
    from pathlib import Path

    heuristics = {
        "python": [r"\bdef\s+\w+\s*\(", r"\bimport\s+\w+", r"\bclass\s+\w+\s*:"],
        "javascript": [r"\bfunction\s+\w+\s*\(", r"\bconst\s+\w+\s*=", r"\blet\s+\w+\s*="],
        "typescript": [r"\binterface\s+\w+", r":\s*(string|number|boolean)", r"import\s*\{.*\}\s*from"],
        "go": [r"\bfunc\s+\w+\s*\(", r"\bpackage\s+\w+", r"\bimport\s*\("],
        "java": [r"\bpublic\s+class\s+\w+", r"\bimport\s+java\.", r"\bpublic\s+static\s+void"],
        "rust": [r"\bfn\s+\w+\s*\(", r"\blet\s+mut\s+\w+", r"\bimpl\s+\w+"],
        "cpp": [r"\bstd::\w+", r"\b#include\s*<", r"\btemplate\s*<"],
        "swift": [r"\bfunc\s+\w+\s*\(", r"\bvar\s+\w+\s*=", r"\blet\s+\w+\s*=", r"\bguard\s+"],
        "kotlin": [r"\bfun\s+\w+\s*\(", r"\bval\s+\w+\s*=", r"\bvar\s+\w+\s*=", r"\bclass\s+\w+\s*\("],
        "ruby": [r"\bdef\s+\w+\s*\(", r"\bclass\s+\w+\s*<", r"\bend\b", r"\bputs\s+"],
        "php": [r"\bfunction\s+\w+\s*\(", r"\$\w+\s*=", r"<\?php", r"\becho\s+"],
        "shell": [r"\bif\s+\[", r"\bfi\b", r"\besac\b", r"\bdone\b", r"\becho\s+"],
        "sql": [r"\bSELECT\s+", r"\bFROM\s+", r"\bWHERE\s+", r"\bINSERT\s+INTO", r"\bCREATE\s+TABLE"],
    }

    scores = {}
    # Random sampling to avoid alphabetical bias
    sampled = random.sample(files, min(sample_size, len(files)))

    for file in sampled:
        try:
            # Use absolute path to handle relative working directories
            file_path = Path(file).resolve()
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read(1000)  # Read first 1000 chars
                for lang, patterns in heuristics.items():
                    matches = sum(1 for p in patterns if re.search(p, content))
                    if matches > 0:
                        scores[lang] = scores.get(lang, 0) + matches / len(patterns)
        except (IOError, OSError):
            continue

    # Normalize scores
    total = sum(scores.values()) or 1
    return {lang: score / total for lang, score in scores.items()}

def detect_languages(pr_files: List[str], pr_metadata: Optional[Dict] = None) -> LanguageDetectionResult:
    """Multi-strategy language detection with confidence scoring"""
    # Strategy 1: Extension-based (highest confidence)
    ext_counts, ambiguous, excluded = detect_languages_from_extensions(pr_files)
    total_files = sum(ext_counts.values()) or 1

    # Calculate confidence based on file count distribution
    ext_confidence = {}
    for lang, count in ext_counts.items():
        ratio = count / total_files
        if ratio >= 0.5:
            ext_confidence[lang] = 0.95  # Dominant language
        elif ratio >= 0.2:
            ext_confidence[lang] = 0.85  # Significant presence
        elif ratio >= 0.05:
            ext_confidence[lang] = 0.7   # Minor presence
        else:
            ext_confidence[lang] = 0.5   # Very few files

    # Strategy 2: Metadata-based (if available)
    metadata_confidence = detect_languages_from_metadata(pr_metadata)

    # Strategy 3: Content-based (fallback)
    content_confidence = detect_languages_from_content(pr_files)

    # Merge with weighted averaging (use full weight sum for normalization)
    final_confidence = {}
    all_langs = set(list(ext_confidence.keys()) + list(metadata_confidence.keys()) + list(content_confidence.keys()))
    total_weight = 0.6 + 0.3 + 0.1  # Always use full weight sum = 1.0

    for lang in all_langs:
        scores = [
            (ext_confidence.get(lang, 0), 0.6),      # Extensions: 60% weight
            (metadata_confidence.get(lang, 0), 0.3),  # Metadata: 30% weight
            (content_confidence.get(lang, 0), 0.1),   # Content: 10% weight
        ]
        weighted_sum = sum(score * weight for score, weight in scores)
        final_confidence[lang] = weighted_sum / total_weight

    # Determine method used
    if metadata_confidence:
        method = "mixed"
    elif content_confidence:
        method = "mixed"
    else:
        method = "extensions"

    return LanguageDetectionResult(
        languages=ext_counts,
        confidence=final_confidence,
        method=method,
        ambiguous_files=ambiguous,
        excluded_files=excluded
    )


class LanguageDetector:
    """Wrapper class for language detection with caching and eviction"""

    def __init__(self, max_cache_size: int = 100):
        from collections import OrderedDict
        self._cache: OrderedDict = OrderedDict()
        self._max_cache_size = max_cache_size

    def detect_languages(self, pr_files: List[str],
                         pr_metadata: Optional[Dict] = None) -> LanguageDetectionResult:
        """Detect languages with caching for repeated calls"""
        cache_key = str(sorted(pr_files))
        if cache_key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        result = detect_languages(pr_files, pr_metadata)
        self._cache[cache_key] = result

        # Evict oldest entry if cache is full
        if len(self._cache) > self._max_cache_size:
            self._cache.popitem(last=False)

        return result

    def clear_cache(self):
        """Clear detection cache"""
        self._cache.clear()
```

**Dispatch Rules**:
- Only dispatch to agents for languages present in the PR
- If no language detected, dispatch to all agents (conservative)
- **Confidence-based dispatch**: Low-confidence detections (< 0.5) trigger content analysis
- **Ambiguous file handling**: Files matching multiple languages are flagged for review
- **Excluded files**: Binary, compiled, and generated files are filtered out

### Inter-Agent Communication Protocol — Planned (Phase 3)

Agents communicate during review to share findings, request context, and resolve conflicts:

**Message Types**:
```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from uuid import uuid4
import time

class MessageType(Enum):
    FINDING = "finding"           # Shared code issue/pattern
    REQUEST = "request"           # Request for cross-language context
    RESPONSE = "response"         # Response to request
    CONFLICT = "conflict"         # Contradictory suggestion detected
    LEARNING = "learning"         # Shared learning/pattern
    HEARTBEAT = "heartbeat"       # Health check between agents
    CANCEL = "cancel"             # Abort an in-progress review
    STATUS = "status"             # Agent reporting current state
    DELEGATE = "delegate"         # Judge reassigning work

@dataclass
class Finding:
    file: str
    line: int
    issue: str
    severity: str                 # "high", "medium", "low"
    language: str
    suggestion: Optional[str] = None

@dataclass
class RequestPayload:
    question: str
    context_files: List[str] = field(default_factory=list)
    urgency: str = "normal"       # "high", "normal", "low"

@dataclass
class ResponsePayload:
    answer: str
    confidence: float
    related_files: List[str] = field(default_factory=list)

@dataclass
class ConflictPayload:
    conflicts_with: str           # Agent ID
    file: str                     # File where conflict occurs
    line: int                     # Line number
    issue: str
    original_suggestion: str
    conflicting_suggestion: str

@dataclass
class LearningPayload:
    learning_type: str            # "pattern", "rule", "skill", "anti_pattern"
    content: Dict[str, Any]
    source_files: List[str] = field(default_factory=list)

@dataclass
class CancelPayload:
    reason: str

@dataclass
class StatusPayload:
    status: str                   # "idle", "busy", "failed", "completed"
    current_task: Optional[str] = None

@dataclass
class AgentMessage:
    message_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None  # Links request-response
    sender: str = ""
    receiver: str = ""            # Agent ID or "broadcast"
    message_type: MessageType = MessageType.FINDING
    version: int = 1              # Protocol version for compatibility
    payload: Union[Finding, RequestPayload, ResponsePayload,
                   ConflictPayload, LearningPayload, CancelPayload,
                   StatusPayload, Dict[str, Any]] = None
    confidence: float = 0.0
    pr_url: str = ""
    timestamp: float = field(default_factory=time.time)
    ttl_seconds: Optional[float] = None
    expires_at: Optional[float] = None

    def __post_init__(self):
        """Reconcile TTL and expires_at"""
        if self.ttl_seconds and not self.expires_at:
            self.expires_at = self.timestamp + self.ttl_seconds

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage/transmission"""
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "version": self.version,
            "payload": self._serialize_payload(),
            "confidence": self.confidence,
            "pr_url": self.pr_url,
            "timestamp": self.timestamp,
            "ttl_seconds": self.ttl_seconds,
            "expires_at": self.expires_at,
        }

    def _serialize_payload(self) -> Any:
        if hasattr(self.payload, '__dataclass_fields__'):
            return {k: v for k, v in self.payload.__dict__.items()}
        return self.payload
```

**Communication Patterns**:

1. **Broadcast Pattern**: Agent shares findings with all other agents
```python
# Python agent finds security issue in shared config
await agent.broadcast(AgentMessage(
    sender="python_agent",
    receiver="broadcast",
    message_type=MessageType.FINDING,
    payload=Finding(
        file="config.py",
        line=42,
        issue="hardcoded_secret",
        severity="high",
        language="python",
        suggestion="Use environment variables"
    ),
    confidence=0.9
))
```

2. **Request-Response**: Agent requests context from another agent
```python
# Go agent finds API call, asks Python agent about validation
request = AgentMessage(
    message_id=str(uuid4()),
    sender="go_agent",
    receiver="python_agent",
    message_type=MessageType.REQUEST,
    payload=RequestPayload(
        question="Is there input validation for this API?",
        context_files=["api/handler.go", "models/user.py"]
    ),
    confidence=0.85
)
response = await agent.request(request)
```

3. **Conflict Detection**: Agents flag contradictory suggestions
```python
# JavaScript agent disagrees with Python agent's suggestion
await agent.send(AgentMessage(
    sender="javascript_agent",
    receiver="judge",
    message_type=MessageType.CONFLICT,
    payload=ConflictPayload(
        conflicts_with="python_agent",
        file="api/handler.py",
        line=42,
        issue="Different error handling approaches",
        original_suggestion="Use try-except",
        conflicting_suggestion="Use Promise.catch"
    ),
    confidence=0.8
))
```

4. **Heartbeat**: Health check between agents
```python
# Periodic health check
await agent.send(AgentMessage(
    sender="python_agent",
    receiver="broadcast",
    message_type=MessageType.HEARTBEAT,
    payload={"status": "healthy", "current_task": None}
))
```

5. **Cancellation**: Abort in-progress review
```python
# Judge cancels review due to timeout
await agent.send(AgentMessage(
    sender="judge",
    receiver="rust_agent",
    message_type=MessageType.CANCEL,
    payload={"reason": "PR review timeout exceeded"}
))
```

### Conflict Resolution — Implemented (simplified majority vote)

When agents provide contradictory suggestions, the Judge Agent resolves conflicts using continuous weighting, deduplication, and cycle detection:

**Conflict Types**:
- **Approach Conflict**: Different ways to solve the same problem
- **Severity Conflict**: Different severity assessments
- **Priority Conflict**: Different priorities for fixes
- **Contradictory Code Suggestions**: Agent A says "add null check", Agent B says "null check is unnecessary"
- **Overlapping Findings**: Two agents report the same issue differently

**Resolution Strategy**:
```python
import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

class ConflictResolver:
    def __init__(self, credibility_decay_rate: float = 0.01):
        self.agent_credibility: Dict[str, float] = {}
        self.credibility_decay_rate = credibility_decay_rate
        self.conflict_history: List[Dict] = []
        self.last_credibility_update: Dict[str, float] = {}

    def _decay_credibility(self, agent_id: str, days_since_last_update: float):
        """Apply temporal decay to credibility"""
        current = self.agent_credibility.get(agent_id, 0.5)
        decayed = current * math.exp(-self.credibility_decay_rate * days_since_last_update)
        self.agent_credibility[agent_id] = max(0.1, decayed)

    def _update_credibility(self, agent_id: str, accepted: bool):
        """Update agent credibility based on outcome"""
        current = self.agent_credibility.get(agent_id, 0.5)
        if accepted:
            self.agent_credibility[agent_id] = min(1.0, current + 0.05)
        else:
            self.agent_credibility[agent_id] = max(0.1, current - 0.1)
        self.last_credibility_update[agent_id] = time.time()

    def _resolve_continuous(self, cred_a: float, cred_b: float,
                            conf_a: float, conf_b: float) -> Tuple[str, float]:
        """Continuous credibility+confidence weighting"""
        score_a = cred_a * conf_a
        score_b = cred_b * conf_b
        total = score_a + score_b
        if total == 0:
            return "tie", 0.0  # Equal scores
        winner = "agent_a" if score_a > score_b else "agent_b"
        margin = abs(score_a - score_b) / total
        return winner, margin

    def _deduplicate_conflicts(self, conflicts: List[AgentMessage]) -> List[AgentMessage]:
        """Remove duplicate conflicts (same underlying issue)"""
        seen = {}
        unique = []
        for conflict in conflicts:
            key = self._conflict_fingerprint(conflict)
            if key not in seen:
                seen[key] = conflict
                unique.append(conflict)
            else:
                # Keep the one with higher confidence
                if conflict.confidence > seen[key].confidence:
                    unique.remove(seen[key])
                    unique.append(conflict)
                    seen[key] = conflict
        return unique

    def _conflict_fingerprint(self, conflict: AgentMessage) -> str:
        """Generate fingerprint for deduplication"""
        payload = conflict.payload
        return f"{payload.conflicts_with}:{payload.file}:{payload.line}"

    def _is_language_specific(self, conflict: AgentMessage) -> bool:
        """Check if conflict is about language-specific advice"""
        # A conflict is language-specific if exactly one agent is a language expert
        # and the other is the judge (not two language agents disagreeing)
        agent_a = conflict.sender
        agent_b = conflict.payload.conflicts_with
        a_is_lang = agent_a.endswith("_agent") and not agent_a.startswith("judge")
        b_is_lang = agent_b.endswith("_agent") and not agent_b.startswith("judge")
        a_is_judge = agent_a.startswith("judge")
        b_is_judge = agent_b.startswith("judge")
        # One is language agent, other is judge
        return (a_is_lang and b_is_judge) or (b_is_lang and a_is_judge)

    def _get_language_agent(self, conflict: AgentMessage) -> str:
        """Get the language-specific agent from a conflict"""
        agent_a = conflict.sender
        agent_b = conflict.payload.conflicts_with
        # Prefer the language-specific agent (not the judge)
        if agent_a.endswith("_agent") and not agent_a.startswith("judge"):
            return agent_a
        if agent_b.endswith("_agent") and not agent_b.startswith("judge"):
            return agent_b
        return agent_a  # Default to sender

    def _detect_cycle(self, conflicts: List[AgentMessage]) -> Optional[List[str]]:
        """Detect circular conflict chains (A→B→C→A)"""
        graph = defaultdict(list)
        for c in conflicts:
            sender = c.sender
            target = c.payload.conflicts_with
            graph[sender].append(target)

        # DFS with parent tracking for cycle path reconstruction
        visited = set()
        parent = {}

        def dfs(node, par):
            visited.add(node)
            parent[node] = par
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor, node):
                        return True
                elif neighbor != par and neighbor in visited:
                    # Cycle found, reconstruct path
                    cycle = [neighbor, node]
                    current = node
                    while parent.get(current) != neighbor and parent.get(current) is not None:
                        current = parent[current]
                        cycle.append(current)
                    cycle.reverse()
                    return cycle
            return False

        for node in graph:
            if node not in visited:
                result = dfs(node, None)
                if result and isinstance(result, list):
                    return result
        return None

    async def resolve(self, conflicts: List[AgentMessage]) -> List[Dict]:
        """Resolve conflicts between agents"""
        # Deduplicate first
        conflicts = self._deduplicate_conflicts(conflicts)

        # Check for cycles
        cycle = self._detect_cycle(conflicts)
        if cycle:
            return [{
                "conflicts": conflicts,
                "resolution": "cycle_detected",
                "cycle": cycle,
                "winner": None,
                "reason": f"Circular conflict detected: {' → '.join(cycle)}"
            }]

        resolutions = []
        for conflict in conflicts:
            agent_a = conflict.sender
            agent_b = conflict.payload.conflicts_with

            # Apply temporal decay to credibility
            for agent_id in [agent_a, agent_b]:
                last_update = self.last_credibility_update.get(agent_id, time.time())
                days_since = (time.time() - last_update) / 86400
                if days_since > 1:
                    self._decay_credibility(agent_id, days_since)

            cred_a = self.agent_credibility.get(agent_a, 0.5)
            cred_b = self.agent_credibility.get(agent_b, 0.5)

            # Strategy 1: Continuous credibility+confidence weighting
            winner, margin = self._resolve_continuous(
                cred_a, cred_b,
                conflict.confidence, 0.8  # Default confidence for agent_b
            )

            if margin > 0.3:
                # Clear winner
                winner_id = agent_a if winner == "agent_a" else agent_b
                resolutions.append({
                    "conflict": conflict,
                    "resolution": "credibility",
                    "winner": winner_id,
                    "confidence_margin": margin,
                    "reason": f"Higher credibility×confidence ({max(cred_a*conflict.confidence, cred_b*0.8):.2f})"
                })

            # Strategy 2: Language-specific priority
            elif self._is_language_specific(conflict):
                resolutions.append({
                    "conflict": conflict,
                    "resolution": "language_expertise",
                    "winner": self._get_language_agent(conflict),
                    "reason": "Language-specific expertise"
                })

            # Strategy 3: Confidence-weighted voting (multiple agents)
            else:
                resolutions.append({
                    "conflict": conflict,
                    "resolution": "needs_review",
                    "winner": None,
                    "reason": f"Low confidence margin ({margin:.2f}), needs human judgment"
                })

        return resolutions
```

**Credibility Tracking**:
- Agent credibility increases when suggestions are accepted
- Agent credibility decreases when suggestions are rejected
- **Temporal decay**: Credibility degrades over time if agent hasn't been tested
- **Continuous weighting**: No arbitrary thresholds, smooth scoring function
- **Conflict deduplication**: Same issue flagged by multiple agents is counted once
- **Cycle detection**: Detects circular conflicts (A disagrees with B, B with C, C with A)

### Parallel Dispatch Error Handling — Implemented (simplified)

When dispatching to multiple language agents in parallel, the system handles failures with timeout enforcement, circuit breakers, and resource limiting:

**Failure Modes**:
- Agent crash (exception during execution)
- Timeout (agent takes too long)
- Partial failure (some agents succeed, some fail)
- Rate limiting (LLM API limits)
- Resource exhaustion (too many concurrent agents)

**Strategy with Timeout Enforcement and Circuit Breaker**:
```python
import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class AgentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, don't dispatch
    HALF_OPEN = "half_open" # Testing recovery

@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout: float = 60.0  # seconds
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN: allow one attempt

@dataclass
class DispatchResult:
    successful: Dict[str, Any] = field(default_factory=dict)
    failed: Dict[str, Exception] = field(default_factory=dict)
    timed_out: List[str] = field(default_factory=list)
    partial: bool = False

class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and agent cannot execute"""
    pass

class AllAgentsFailedError(Exception):
    """Raised when all dispatched agents fail"""
    def __init__(self, failures: Dict[str, Exception]):
        self.failures = failures
        super().__init__(f"All agents failed: {failures}")

class ParallelDispatcher:
    def __init__(self, max_concurrent: int = 5, per_agent_timeout: float = 300.0):
        self.max_concurrent = max_concurrent
        self.per_agent_timeout = per_agent_timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    async def _run_with_timeout(self, lang: str, agent, pr_context):
        """Run agent with enforced timeout and circuit breaker"""
        # Check circuit breaker
        if lang not in self.circuit_breakers:
            self.circuit_breakers[lang] = CircuitBreaker()
        breaker = self.circuit_breakers[lang]

        if not breaker.can_execute():
            raise CircuitOpenError(f"Circuit open for {lang}, skipping")

        async with self.semaphore:
            try:
                # Use asyncio.wait_for for timeout enforcement
                result = await asyncio.wait_for(
                    agent.review(pr_context),
                    timeout=self.per_agent_timeout
                )
                breaker.record_success()
                return lang, result, None
            except asyncio.TimeoutError:
                breaker.record_failure()
                return lang, None, TimeoutError(
                    f"Agent {lang} timed out after {self.per_agent_timeout}s"
                )
            except CircuitOpenError:
                raise
            except Exception as e:
                breaker.record_failure()
                return lang, None, e

    async def dispatch(self, agents: Dict[str, Any],
                       pr_context: Any) -> DispatchResult:
        """Dispatch to agents with parallel execution and error handling"""
        tasks = [
            self._run_with_timeout(lang, agent, pr_context)
            for lang, agent in agents.items()
        ]

        results = DispatchResult()
        completed = 0
        total = len(tasks)

        # Process results as they complete
        for coro in asyncio.as_completed(tasks):
            lang, result, error = await coro
            completed += 1

            if error:
                if isinstance(error, TimeoutError):
                    results.timed_out.append(lang)
                results.failed[lang] = error
                logger.warning(f"Agent {lang} failed: {error}")
            else:
                results.successful[lang] = result

            # Report progress
            logger.info(f"Dispatch progress: {completed}/{total} completed")

        results.partial = bool(results.failed)

        if not results.successful:
            raise AllAgentsFailedError(results.failed)

        return results
```

**Retry Policy**:
- **Transient failures** (network timeouts, rate limits): Retry up to 2 times with exponential backoff
- **Idempotent failures** (logic errors): No retry, log and continue
- **Circuit breaker**: After 3 consecutive failures, stop dispatching to that agent for 60 seconds

**Timeout Handling**:
- Each agent has a configurable timeout (default: 5 minutes)
- Uses `asyncio.wait_for` for strict timeout enforcement
- Partial results from timed-out agents are **kept** (not discarded) with a warning
- Timeout triggers circuit breaker to prevent repeated failures

**Resource Limiting**:
- Semaphore limits concurrent agent execution (default: 5)
- Prevents resource exhaustion when reviewing large PRs
- Configurable based on system capacity

### Self-Improvement Engine — Partially Implemented

#### Harness Evolution — Planned (Phase 4)

- **PromptEvolver**: Improves agent prompts based on failure analysis
- **SkillDiscovery**: Finds new analysis patterns from trajectories
- **RuleEvolver**: Optimizes review criteria based on outcomes

#### Weight Training — Implemented

- **LoRA Training**: Low-rank adaptation for model weights
- **Algorithm Selection**: Adaptive choice based on reward structure (RLAlgorithmSelector is implemented)
- **Data Pipeline**: Collects training data from trajectories (TrajectoryStore is implemented)
- **Reward Signals**: Outcome-based, human feedback, cross-agent

#### Cross-Agent Learning — Planned (Phase 4)

Agents share knowledge across languages using a full similarity matrix, semantic adaptation, and transfer validation:

```python
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

@dataclass
class TransferRecord:
    source: str
    target: str
    similarity: float
    strength: float
    learning_type: str
    timestamp: float
    success: Optional[bool] = None  # Validated later

class CrossAgentLearner:
    """Enables knowledge transfer between language agents"""

    def __init__(self, agent_registry=None):
        self.similarity_matrix = self._build_similarity_matrix()
        self.transfer_log: List[TransferRecord] = []
        self.transfer_validation: Dict[str, bool] = {}
        self._agent_registry = agent_registry

    def _build_similarity_matrix(self) -> Dict[Tuple[str, str], float]:
        """Compute pairwise similarity between all language agents"""
        languages = ["python", "javascript", "typescript", "go",
                     "java", "rust", "cpp", "c", "ruby", "kotlin", "swift",
                     "php", "shell", "sql"]

        matrix = {}
        for i, lang_a in enumerate(languages):
            for lang_b in languages[i+1:]:
                sim = self._compute_similarity(lang_a, lang_b)
                matrix[(lang_a, lang_b)] = sim
                matrix[(lang_b, lang_a)] = sim
        return matrix

    def _compute_similarity(self, lang_a: str, lang_b: str) -> float:
        """Compute language similarity based on multiple factors"""
        factors = {
            "paradigm": self._paradigm_similarity(lang_a, lang_b),
            "type_system": self._type_similarity(lang_a, lang_b),
            "memory_model": self._memory_similarity(lang_a, lang_b),
            "ecosystem": self._ecosystem_similarity(lang_a, lang_b),
        }
        weights = {"paradigm": 0.3, "type_system": 0.2,
                   "memory_model": 0.25, "ecosystem": 0.25}
        return sum(factors[k] * weights[k] for k in factors)

    def _paradigm_similarity(self, lang_a: str, lang_b: str) -> float:
        """Similarity based on programming paradigm"""
        oop = {"python", "java", "kotlin", "swift", "ruby", "javascript", "typescript", "php"}
        scripting = {"python", "ruby", "javascript", "typescript", "php", "shell", "sql"}
        systems = {"go", "rust", "cpp", "c"}

        groups = [oop, systems, scripting]
        for group in groups:
            if lang_a in group and lang_b in group:
                return 0.9
        return 0.3  # Different paradigms

    def _type_similarity(self, lang_a: str, lang_b: str) -> float:
        """Similarity based on type system"""
        static = {"go", "java", "rust", "cpp", "c", "kotlin", "swift", "typescript"}
        dynamic = {"python", "ruby", "javascript", "php", "shell", "sql"}

        if lang_a in static and lang_b in static:
            return 0.9
        if lang_a in dynamic and lang_b in dynamic:
            return 0.9
        return 0.4  # Mixed type systems

    def _memory_similarity(self, lang_a: str, lang_b: str) -> float:
        """Similarity based on memory model"""
        gc = {"python", "java", "go", "javascript", "typescript", "ruby", "kotlin", "swift", "php", "shell", "sql"}
        ownership = {"rust"}
        manual = {"cpp", "c"}

        groups = [gc, ownership, manual]
        for group in groups:
            if lang_a in group and lang_b in group:
                return 0.9
        return 0.3  # Different memory models

    def _ecosystem_similarity(self, lang_a: str, lang_b: str) -> float:
        """Similarity based on ecosystem overlap"""
        web = {"javascript", "typescript", "python", "ruby", "php"}
        systems = {"go", "rust", "cpp", "c"}
        enterprise = {"java", "kotlin"}
        data = {"python", "sql", "shell"}

        groups = [web, systems, enterprise, data]
        for group in groups:
            if lang_a in group and lang_b in group:
                return 0.8
        return 0.4  # Different ecosystems

    def _transfer_function(self, similarity: float) -> float:
        """Continuous transfer strength curve (sigmoid-like)"""
        if similarity < 0.3:
            return 0.0
        return 1 / (1 + math.exp(-10 * (similarity - 0.6)))

    def _get_language(self, agent_id: str) -> str:
        """Extract language from agent ID"""
        return agent_id.replace("_agent", "")

    def _get_agent(self, lang: str):
        """Get agent by language"""
        if self._agent_registry:
            return self._agent_registry.agents.get(f"{lang}_agent")
        return None

    async def share_learning(self, source_agent: str, learning: Dict[str, Any]):
        """Share learning with similarity-weighted transfer"""
        source_lang = self._get_language(source_agent)

        # Deduplicate: only process each target language once
        seen_targets = set()
        for (lang_a, lang_b), similarity in self.similarity_matrix.items():
            if source_lang in (lang_a, lang_b):
                target_lang = lang_b if source_lang == lang_a else lang_a

                # Skip if already processed this target
                if target_lang in seen_targets:
                    continue
                seen_targets.add(target_lang)

                # Skip back-transfer to source
                if target_lang == source_lang:
                    continue

                # Continuous transfer strength based on similarity
                transfer_strength = self._transfer_function(similarity)
                if transfer_strength < 0.1:
                    continue

                # Validate BEFORE adaptation
                if not await self._validate_transfer(learning, target_lang):
                    continue

                target_agent = self._get_agent(target_lang)
                if not target_agent:
                    continue

                adapted = await self._adapt_learning(learning, target_lang, transfer_strength)
                await target_agent.receive_learning(adapted)

                self.transfer_log.append(TransferRecord(
                    source=source_lang,
                    target=target_lang,
                    similarity=similarity,
                    strength=transfer_strength,
                    learning_type=learning.get("type", "unknown"),
                    timestamp=time.time(),
                    success=True  # Mark as successful after validation
                ))

    async def _adapt_learning(self, learning: Dict[str, Any],
                               target_lang: str, strength: float) -> Dict[str, Any]:
        """Adapt a learning for a different language"""
        adapted = learning.copy()

        # Adjust syntax examples
        if "syntax_example" in adapted:
            adapted["syntax_example"] = self._translate_syntax(
                adapted["syntax_example"],
                learning.get("language", ""),
                target_lang
            )

        # Adjust confidence based on transfer strength
        base_confidence = adapted.get("confidence", 0.5)
        adapted["confidence"] = base_confidence * strength
        adapted["transferred"] = True
        adapted["original_language"] = learning.get("language")
        adapted["target_language"] = target_lang

        # Keep language-agnostic parts, transform language-specific parts
        if "language_specific" in adapted:
            del adapted["language_specific"]

        return adapted

    def _translate_syntax(self, code: str, source_lang: str, target_lang: str) -> str:
        """Translate code syntax between languages"""
        translations = {
            ("python", "javascript"): {
                "def ": "function ", "True": "true", "False": "false", "None": "null",
            },
            ("python", "go"): {
                "def ": "func ", "True": "true", "False": "false", "None": "nil",
            },
            ("python", "ruby"): {
                "def ": "def ", "True": "true", "False": "false", "None": "nil",
            },
            ("python", "java"): {
                "def ": "public void ", "True": "true", "False": "false", "None": "null",
            },
            ("javascript", "typescript"): {
                "var ": "let ", "function ": "function ",
            },
            ("go", "rust"): {
                "func ": "fn ", "package ": "pub ", "import(": "use ",
            },
            ("java", "kotlin"): {
                "public ": "", "private ": "private ",
            },
        }

        key = (source_lang, target_lang)
        if key in translations:
            result = code
            for old, new in translations[key].items():
                result = result.replace(old, new)
            return result
        return code  # No translation available

    async def _validate_transfer(self, learning: Dict[str, Any],
                                  target_lang: str) -> bool:
        """Validate that a transferred learning makes sense in target language"""
        # Check 1: Referenced libraries exist in target ecosystem
        if "required_libraries" in learning:
            ecosystem_compatibility = {
                "python": ["requests", "flask", "django", "fastapi", "pytest"],
                "javascript": ["express", "react", "vue", "lodash", "axios"],
                "typescript": ["express", "react", "vue", "axios"],
                "go": ["gin", "echo", "fiber", "gorilla"],
                "java": ["spring", "junit", "maven", "gradle"],
                "rust": ["tokio", "serde", "clap", "reqwest"],
                "cpp": ["boost", "gtest", "cmake"],
                "ruby": ["rails", "sinatra", "rspec", "bundler"],
                "kotlin": ["ktor", "spring", "junit", "gradle"],
                "swift": ["vapor", "alamofire", "swiftlint"],
                "php": ["laravel", "symfony", "phpunit", "composer"],
                "shell": ["bash", "zsh", "curl", "jq"],
                "sql": ["postgresql", "mysql", "sqlite"],
            }
            target_ecosystem = ecosystem_compatibility.get(target_lang, [])
            for lib in learning["required_libraries"]:
                if lib not in target_ecosystem:
                    return False

        # Check 2: Syntax is valid in target
        if "syntax_example" in learning:
            syntax_rules = {
                "python": lambda s: "def " in s,
                "javascript": lambda s: "function " in s or "const " in s,
                "typescript": lambda s: "function " in s or "const " in s,
                "go": lambda s: "func " in s or "package " in s,
                "rust": lambda s: "fn " in s or "let " in s,
                "java": lambda s: "public " in s or "class " in s,
                "cpp": lambda s: "std::" in s or "#include" in s,
                "c": lambda s: "#include" in s or "printf" in s,
                "ruby": lambda s: "def " in s or "end" in s,
                "kotlin": lambda s: "fun " in s or "val " in s,
                "swift": lambda s: "func " in s or "var " in s,
                "php": lambda s: "function " in s or "$" in s,
                "shell": lambda s: "if [" in s or "fi" in s,
                "sql": lambda s: "SELECT " in s or "FROM " in s,
            }
            if target_lang in syntax_rules:
                if not syntax_rules[target_lang](learning["syntax_example"]):
                    return False

        # Check 3: No language-specific contradictions
        if learning.get("original_language") == target_lang:
            return False

        # Check 4: Learning type compatibility
        incompatible_types = {
            "python": ["memory_management", "pointers"],
            "go": ["exception_handling", "try_catch"],
            "rust": ["garbage_collection", "null_checks"],
            "c": ["garbage_collection", "null_checks"],
            "cpp": ["garbage_collection"],
        }
        if target_lang in incompatible_types:
            if learning.get("type") in incompatible_types[target_lang]:
                return False

        return True

    def record_transfer_result(self, source: str, target: str, success: bool):
        """Record the result of a transfer for stats tracking"""
        for record in self.transfer_log:
            if record.source == source and record.target == target and record.success is None:
                record.success = success
                break

    def get_transfer_stats(self) -> Dict[str, Any]:
        """Get statistics about cross-agent transfers"""
        if not self.transfer_log:
            return {"total_transfers": 0}

        successful = sum(1 for t in self.transfer_log if t.success is True)
        failed = sum(1 for t in self.transfer_log if t.success is False)
        pending = sum(1 for t in self.transfer_log if t.success is None)
        return {
            "total_transfers": len(self.transfer_log),
            "successful": successful,
            "failed": failed,
            "pending": pending,
            "success_rate": successful / len(self.transfer_log) if self.transfer_log else 0,
            "avg_similarity": sum(t.similarity for t in self.transfer_log) / len(self.transfer_log),
            "avg_strength": sum(t.strength for t in self.transfer_log) / len(self.transfer_log),
        }
```

**Similarity Matrix (Full Pairwise)**:
- 0.9+: Direct transfer (JS ↔ TS, C ↔ C++)
- 0.7-0.9: Adapt transfer (Python ↔ Ruby, Java ↔ Kotlin)
- 0.5-0.7: Pattern transfer (Go ↔ Rust, Python ↔ Go)
- 0.3-0.5: Weak transfer (Python ↔ C++)
- <0.3: No transfer

**What Gets Shared**:
- Security patterns (language-agnostic)
- Performance anti-patterns
- Testing strategies
- Code organization principles

**What Doesn't Get Shared**:
- Syntax-specific rules (translated, not shared)
- Language-specific idioms (adapted with low confidence)
- Library-specific patterns (validated against target ecosystem)

**Transfer Validation**:
- Check syntax validity in target language
- Check library availability in target ecosystem
- Track transfer success rates for future decisions

#### Trajectory Store

- SQLite database for execution logs
- Stores complete trajectories (prompts, responses, tool calls)
- Analyzes failure patterns
- Supports querying by agent, PR, language

### Stall Detection Algorithm

Stall detection determines when to switch from harness updates to weight updates.

**Algorithm: Moving Average Plateau Detection**

```python
class StallDetector:
    def __init__(self, window_size: int = 5, threshold: float = 0.01):
        self.window_size = window_size
        self.threshold = threshold
        self.history = []
    
    def is_stalled(self, metric_value: float) -> bool:
        """Check if metrics have plateaued"""
        self.history.append(metric_value)
        
        # Need at least window_size data points
        if len(self.history) < self.window_size:
            return False
        
        # Get last window_size values
        recent = self.history[-self.window_size:]
        
        # Calculate moving average
        moving_avg = sum(recent) / len(recent)
        
        # Calculate improvement rate
        if len(self.history) >= 2:
            improvement = abs(self.history[-1] - self.history[-2]) / abs(self.history[-2] + 1e-10)
            return improvement < self.threshold
        
        return False
```

**Configuration**:
- `window_size`: Number of recent values to consider (default: 5)
- `threshold`: Minimum improvement rate to avoid stall (default: 1%)
- `consecutive_stalls`: Number of consecutive stalls before switching (default: 3)

**Metrics Tracked**:
- Review quality score (human feedback)
- Suggestion acceptance rate
- False positive rate
- Issue detection rate

### Org-Level Learning

SEMAR learns across multiple repositories in an organization:

**Knowledge Store**:
```python
class OrgMemory:
    """Stores learnings across repositories"""
    
    def __init__(self, org_id: str):
        self.org_id = org_id
        self.store = MemoryStore()
    
    async def store_learning(self, learning: Dict):
        """Store a learning from a PR review"""
        await self.store.save(self.org_id, learning)
    
    async def get_relevant_learnings(self, context: Dict) -> List[Dict]:
        """Retrieve relevant past learnings"""
        return await self.store.query(self.org_id, context)
```

**Learning Types**:
- **Pattern Learnings**: Common issues found in specific languages/frameworks
- **Rule Learnings**: Effective review rules discovered
- **Skill Learnings**: New analysis patterns that worked well
- **Anti-Patterns**: False positives to avoid

**Cross-Repository Transfer**:
1. Agent learns from PR in Repo A
2. Learning is stored in org memory
3. When reviewing PR in Repo B, relevant learnings are retrieved
4. Agent applies learned knowledge to new context

**Configuration**:
```toml
[org_learning]
enabled = true
org_id = "my-org"
max_learnings = 1000
relevance_threshold = 0.7

# Learning decay parameters
[org_learning.decay]
decay_rate = 0.1           # 10% per day
min_relevance = 0.1        # Retire below this
usage_boost_factor = 0.3   # Weight for usage frequency
success_boost_factor = 0.3 # Weight for success rate
```

### Learning Decay Mechanism

Learnings lose relevance over time and usage:

```python
class LearningDecay:
    """Manages learning relevance decay"""
    
    def __init__(self, decay_rate: float = 0.1, min_relevance: float = 0.1):
        self.decay_rate = decay_rate
        self.min_relevance = min_relevance
    
    def calculate_relevance(self, learning: Dict) -> float:
        """Calculate current relevance of a learning"""
        age = time.time() - learning["created_at"]
        usage_count = learning.get("usage_count", 0)
        success_rate = learning.get("success_rate", 0.5)
        
        # Time decay: relevance decreases with age
        time_factor = math.exp(-self.decay_rate * age / (24 * 3600))  # Days
        
        # Usage boost: frequently used learnings stay relevant
        usage_factor = min(1.0, usage_count / 100)
        
        # Success boost: learnings with high success rate stay relevant
        success_factor = success_rate
        
        # Combined relevance
        relevance = (time_factor * 0.4 + usage_factor * 0.3 + success_factor * 0.3)
        
        return max(relevance, self.min_relevance)
    
    def should_retire(self, learning: Dict) -> bool:
        """Check if learning should be retired"""
        return self.calculate_relevance(learning) < self.min_relevance
```

**Decay Factors**:
- **Time Decay**: 10% per day (configurable)
- **Usage Boost**: Learnings used frequently stay relevant
- **Success Boost**: High-success learnings stay relevant

**Retirement Policy**:
- Learnings with relevance < 0.1 are retired
- Retired learnings are archived, not deleted
- Can be revived if referenced again

### Rollback Manager

Reverts poor improvements when metrics degrade:

```python
class RollbackManager:
    """Manages rollback of improvements"""
    
    def __init__(self, rollback_threshold: float = 0.1):
        self.rollback_threshold = rollback_threshold  # 10% degradation
        self.improvement_history = []
    
    async def should_rollback(self, improvement_id: str, current_metrics: Dict) -> bool:
        """Check if improvement should be rolled back"""
        # Find the improvement
        improvement = self._find_improvement(improvement_id)
        if not improvement:
            return False
        
        # Compare current metrics to baseline
        baseline = improvement["baseline_metrics"]
        degradation = self._calculate_degradation(baseline, current_metrics)
        
        return degradation > self.rollback_threshold
    
    async def rollback(self, improvement_id: str):
        """Rollback an improvement"""
        improvement = self._find_improvement(improvement_id)
        
        # Restore previous scaffold version
        await self._restore_scaffold(improvement["previous_scaffold"])
        
        # Restore previous weights (if weight update)
        if improvement["type"] == "weight":
            await self._restore_weights(improvement["previous_checkpoint"])
        
        # Mark as rolled back
        improvement["status"] = "rolled_back"
        
        # Log for learning
        await self._log_rollback(improvement)
    
    def _calculate_degradation(self, baseline: Dict, current: Dict) -> float:
        """Calculate performance degradation"""
        degradations = []
        for metric in baseline:
            if metric in current:
                baseline_val = baseline[metric]
                current_val = current[metric]
                if baseline_val > 0:
                    degradation = (baseline_val - current_val) / baseline_val
                    degradations.append(max(0, degradation))
        
        return sum(degradations) / len(degradations) if degradations else 0
```

**Rollback Triggers**:
- Metric degradation > 10% (configurable)
- Multiple consecutive failures
- Human feedback indicates regression

**What Gets Rolled Back**:
- Prompt changes (restore previous prompt)
- Rule changes (restore previous rules)
- Weight updates (restore previous checkpoint)
- Skill additions (remove added skills)

### Learning Metrics

Track the effectiveness of continuous learning:

```python
class LearningMetrics:
    """Tracks learning effectiveness"""
    
    def __init__(self):
        self.metrics = {
            "learning_velocity": [],      # How fast we learn
            "learning_retention": [],     # How well we retain
            "cross_agent_transfer": [],   # How well knowledge transfers
            "improvement_impact": [],     # Impact of improvements
        }
    
    async def record_learning(self, learning: Dict, outcome: Dict):
        """Record a learning event"""
        self.metrics["learning_velocity"].append({
            "timestamp": time.time(),
            "learning_type": learning["type"],
            "time_to_learn": outcome.get("time_to_learn", 0),
        })
    
    async def calculate_velocity(self) -> float:
        """Calculate learning velocity (learnings per PR)"""
        recent = self._get_recent(limit=100)
        if not recent:
            return 0.0
        return len(recent) / 100  # Learnings per PR
    
    async def calculate_retention(self) -> float:
        """Calculate learning retention (success rate of applied learnings)"""
        applied = self._get_applied(limit=100)
        if not applied:
            return 0.0
        successful = sum(1 for a in applied if a["success"])
        return successful / len(applied)
    
    async def calculate_transfer_rate(self) -> float:
        """Calculate cross-agent transfer success rate"""
        transfers = self._get_transfers(limit=100)
        if not transfers:
            return 0.0
        successful = sum(1 for t in transfers if t["success"])
        return successful / len(transfers)
    
    async def get_dashboard(self) -> Dict:
        """Get metrics dashboard"""
        return {
            "learning_velocity": await self.calculate_velocity(),
            "learning_retention": await self.calculate_retention(),
            "transfer_rate": await self.calculate_transfer_rate(),
            "total_learnings": self._count_total(),
            "active_learnings": self._count_active(),
            "retired_learnings": self._count_retired(),
        }
```

**Key Metrics**:
- **Learning Velocity**: Learnings per PR (higher = faster learning)
- **Learning Retention**: Success rate of applied learnings (higher = better)
- **Transfer Rate**: Cross-agent transfer success (higher = better knowledge sharing)

**Dashboard**:
```
SEMAR Learning Dashboard
├── Learning Velocity: 0.5 learnings/PR
├── Learning Retention: 85%
├── Transfer Rate: 70%
├── Total Learnings: 1,234
├── Active Learnings: 892
└── Retired Learnings: 342
```

## 4-Step Self-Improvement Cycle

```
┌─────────────────────────────────────────────────────────────┐
│                    1. PLANNING                               │
│  - Analyze PR context                                       │
│  - Identify files and languages                             │
│  - Select skills and rules to apply                         │
│  - Create execution plan                                    │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    2. ACTION                                 │
│  - Execute review using current scaffold                    │
│  - Apply skills and rules                                   │
│  - Generate suggestions                                     │
│  - Capture full trajectory                                  │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    3. REVIEW                                 │
│  - Self-reflect on results                                  │
│  - Identify issues and missed opportunities                 │
│  - Evaluate suggestion quality                              │
│  - Compute performance metrics                              │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. UPDATE                                 │
│  - Evolve scaffold (prompts, skills, rules)                 │
│  - OR trigger weight training (RL)                          │
│  - Store learnings in trajectory store                      │
│  - Update instructions for future reviews                   │
└─────────────────────────────────────────────────────────────┘
```

### Update Step Timing

Self-improvement happens at different cadences:

**Per-PR Updates (Always)**:
- Store trajectory in trajectory store
- Update performance metrics
- Check for stall detection

**Harness Updates (Batched)**:
- Frequency: After every N PRs (default: 10)
- Trigger: When metrics improve significantly
- Scope: Prompt evolution, skill discovery, rule evolution
- Validation: A/B test before applying

**Weight Updates (Scheduled)**:
- Frequency: After every M PRs (default: 50)
- Trigger: When harness updates stall
- Scope: LoRA training with selected algorithm
- Validation: Hold-out test set evaluation

**Configuration**:
```toml
[update_timing]
# Per-PR updates
store_trajectory = true
check_stall = true

# Harness updates (batched)
harness_update_interval = 10  # PRs
harness_update_threshold = 0.05  # 5% improvement

# Weight updates (scheduled)
weight_update_interval = 50  # PRs
weight_update_min_samples = 100  # minimum trajectories needed
```

**Why Different Cadences**:
- Per-PR: Trajectory storage is cheap, must capture immediately
- Harness: Prompt/skill changes are cheap, can apply frequently
- Weight: RL training is expensive, needs many samples, apply rarely

## Data Flow

```
PR Request
    │
    ▼
Judge Agent
    │
    ├─► Language Agent 1 ─► Trajectory 1 ─┐
    ├─► Language Agent 2 ─► Trajectory 2 ─┤
    ├─► Language Agent 3 ─► Trajectory 3 ─┤
    └─► ...                               │
                                          │
                                          ▼
                                   Trajectory Store
                                          │
                                          ▼
                                   Analysis Engine
                                          │
                                          ▼
                                   Improvement Selector
                                          │
                        ┌─────────────────┴─────────────────┐
                        │                                   │
                        ▼                                   ▼
                 Harness Evolution                  Weight Training
                        │                                   │
                        └─────────────────┬─────────────────┘
                                          │
                                          ▼
                                   Updated Agent
```

## Key Patterns from SIA Paper

### Two Levers of Improvement

| Lever | What It Changes | When to Use |
|-------|-----------------|-------------|
| **Harness Updates** | External infrastructure (prompts, tools, rules) | First, cheaper |
| **Weight Updates** | Internal model knowledge (RL training) | After stall detection |

### Full Trajectory Analysis

The system captures and analyzes:
- Every prompt sent to the LLM
- Every response received
- Every tool call and result
- Every extracted answer
- Human follow-up actions

This enables diagnosis of specific failure modes rather than reacting to summary statistics.

### Adaptive RL Algorithm Selection

| Algorithm | When to Use |
|-----------|-------------|
| **PPO with GAE** | Dense step-level rewards, multi-step tasks |
| **GRPO** | Cheap rollouts, episode-end verifier |
| **Entropic Advantage** | Right-skewed reward histogram (rare successes) |
| **REINFORCE + KL** | Dense rewards, risk of capability regression |
| **Best-of-NN** | Extremely sparse rewards (cold start) |
| **DPO** | Verifier ranks but doesn't score absolutely |

## Directory Structure

```
semar/
├── __init__.py
├── cli.py                    # CLI entry point
├── server.py                 # FastAPI server
├── agents/
│   ├── __init__.py
│   ├── base_agent.py         # Abstract base class
│   ├── judge_agent.py        # Orchestrator (dual-role)
│   ├── trajectory_store.py   # Execution log storage
│   ├── communication.py      # AgentMessage protocol with typed payloads
│   ├── conflict_resolver.py  # Deduplication, continuous weighting, cycle detection
│   ├── parallel_dispatcher.py # Timeout enforcement, circuit breaker, resource limiting
│   ├── language_detection.py  # Multi-strategy detection with confidence scoring
│   └── language_agents/
│       ├── __init__.py
│       ├── base_language_agent.py
│       ├── python_agent.py
│       ├── javascript_agent.py
│       ├── typescript_agent.py
│       ├── go_agent.py
│       ├── java_agent.py
│       ├── rust_agent.py
│       ├── cpp_agent.py
│       └── registry.py        # Health checks, capabilities, dynamic registration
├── self_improvement/
│   ├── __init__.py
│   ├── harness/
│   │   ├── __init__.py
│   │   ├── prompt_evolver.py
│   │   ├── skill_discovery.py
│   │   └── rule_evolver.py
│   ├── weight_training/
│   │   ├── __init__.py
│   │   ├── lora_trainer.py
│   │   ├── algorithms/
│   │   │   ├── __init__.py
│   │   │   ├── base_algorithm.py
│   │   │   ├── ppo_gae.py
│   │   │   ├── grpo.py
│   │   │   ├── entropic_advantage.py
│   │   │   ├── reinforce_kl.py
│   │   │   ├── best_of_nn.py
│   │   │   └── dpo.py
│   │   ├── data_pipeline.py
│   │   └── reward_signals/
│   │       ├── __init__.py
│   │       ├── outcome_based.py
│   │       ├── human_feedback.py
│   │       └── cross_agent_learning.py
│   ├── trajectory/
│   │   ├── __init__.py
│   │   └── analyzer.py
│   ├── cross_agent_learner.py   # Full similarity matrix, adaptation, validation
│   ├── learning_decay.py        # Learning relevance decay
│   ├── rollback_manager.py      # Revert poor improvements
│   └── learning_metrics.py      # Track improvement effectiveness
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── default.toml
├── repo_management/
│   ├── __init__.py
│   ├── org_config.py
│   └── repo_registry.py
├── monitoring/
│   ├── __init__.py
│   ├── dashboards.py
│   └── alerts.py
└── utils/
    ├── __init__.py
    ├── helpers.py
    └── types.py
```

## Component Integration

### Judge Agent Initialization

```python
class JudgeAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="judge", language=None)

        # Orchestrator components
        self.agent_registry = AgentRegistry()
        self.conflict_resolver = ConflictResolver(credibility_decay_rate=0.01)
        self.parallel_dispatcher = ParallelDispatcher(max_concurrent=5, per_agent_timeout=300.0)
        self.language_detector = LanguageDetector()

        # Feedback-Agent components
        self.trajectory_analyzer = TrajectoryAnalyzer()
        self.improvement_selector = ImprovementSelector()
        self.rl_algorithm_selector = RLAlgorithmSelector()

        # Self-improvement components
        self.cross_agent_learner = CrossAgentLearner()
        self.learning_decay = LearningDecay(decay_rate=0.1, min_relevance=0.1)
        self.rollback_manager = RollbackManager(rollback_threshold=0.1)
        self.learning_metrics = LearningMetrics()

        # Language agents
        self.language_agents = {}
```

### Integration in 4-Step Cycle

```python
async def execute_cycle(self, context: AgentContext) -> AgentResult:
    """Execute the 4-step self-improvement cycle"""

    # 1. Planning - detect languages, select agents
    plan = await self.plan(context)
    detection_result = self.language_detector.detect_languages(
        context.pr_files, context.pr_metadata
    )
    selected_agents = self.agent_registry.select_agents(
        list(detection_result.languages.keys()),
        detection_result.languages
    )

    # 2. Action - parallel dispatch with timeout enforcement and circuit breaker
    dispatch_result = await self.parallel_dispatcher.dispatch(
        {lang: self.language_agents[lang] for lang in selected_agents},
        context
    )

    # Handle inter-agent communication (broadcasts, requests, conflicts)
    conflicts = await self._collect_conflicts(dispatch_result)
    if conflicts:
        resolutions = await self.conflict_resolver.resolve(conflicts)
        await self._apply_resolutions(dispatch_result, resolutions)

    # 3. Review - aggregate results, analyze trajectories
    aggregated = self._aggregate_results(dispatch_result)
    review = await self.review(context, aggregated)

    # 4. Update - with rollback protection
    await self.update_instructions(context, review)

    # Track metrics
    await self.learning_metrics.record_learning(review)

    return review
```

### Agent Lifecycle Example

```python
async def handle_pr_review(self, pr_url: str):
    """Full PR review lifecycle with all orchestration components"""
    # 1. Health check all agents
    health = await self.agent_registry.health_check()

    # 2. Detect languages in PR
    pr_files = await self._get_pr_files(pr_url)
    detection = self.language_detector.detect_languages(pr_files)

    # 3. Select best agents based on health and capabilities
    selected = self.agent_registry.select_agents(
        list(detection.languages.keys()),
        detection.languages
    )

    # 4. Dispatch with parallel execution, timeout, circuit breaker
    result = await self.parallel_dispatcher.dispatch(
        {lang: self.language_agents[lang] for lang in selected},
        pr_url
    )

    # 5. Handle conflicts via credibility-weighted resolution
    if result.conflicts:
        resolutions = await self.conflict_resolver.resolve(result.conflicts)

    # 6. Share learnings with similar language agents
    for learning in result.learnings:
        await self.cross_agent_learner.share_learning(
            learning.source_agent, learning
        )

    return result
```

## Integration with PR-Agent

SEMAR builds on top of PR-Agent by:
- Reusing the git provider abstraction layer
- Reusing the LLM integration (LiteLLM)
- Reusing the configuration system (Dynaconf)
- Adding multi-agent orchestration
- Adding self-improvement capabilities
- Adding trajectory capture and analysis

## Configuration

SEMAR uses Dynaconf for configuration:
- `semar/config/default.toml` - Default settings
- Environment variables with `SEMAR_*` prefix
- `.semar.toml` in repository root for repo-specific settings

## Testing Strategy

- **Unit Tests**: Individual components in isolation
- **Integration Tests**: Components working together
- **E2E Tests**: Full self-improvement cycle
- **Performance Tests**: Concurrent reviews, storage limits
- **A/B Tests**: Validate improvements are real
