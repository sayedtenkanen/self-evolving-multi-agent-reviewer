# SEMAR User Guide

SEMAR (Self-Evolving Multi-Agent Reviewer) v0.1.0

## What SEMAR Does

SEMAR is a self-improving code review system. It orchestrates multiple language-specific AI agents to review pull requests, detects its own failures, and learns from mistakes over time.

**Current capabilities (Phase 2):**
- Detects 13 programming languages from PR diffs
- Dispatches reviews to language agents in parallel
- Resolves conflicts between agents via majority voting
- Analyzes execution trajectories for failure modes
- Decides when to update prompts (harness) vs retrain (weights)
- Selects the best RL algorithm based on reward structure

## Installation

```bash
git clone https://github.com/sayedtenkanen/self-evolving-multi-agent-reviewer.git
cd self-evolving-multi-agent-reviewer/semar

# Core install (~100MB)
pip install -e ".[dev]"

# With ML deps for weight updates (~2GB, optional)
pip install -e ".[ml]"
```

Requires Python >= 3.12.

## Quick Start

### 1. Create a Language Agent

```python
import asyncio
from semar.agents.base_agent import BaseAgent, AgentContext, AgentResult

class PythonReviewer(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="python-reviewer", language="python")

    async def plan(self, context: AgentContext) -> dict:
        return {"files": context.files, "focus": "security"}

    async def action(self, context: AgentContext, plan: dict) -> str:
        return f"Reviewed {len(plan['files'])} Python files"

    async def review(self, context: AgentContext, action_result) -> AgentResult:
        return AgentResult(
            review="approve",
            suggestions=[{"line": 10, "comment": "Use f-string instead of .format()"}],
            metrics={"accuracy": 0.9},
            trajectory={},
            agent_id=self.agent_id,
            language=self.language,
            pr_url=context.pr_url,
        )

    async def update_instructions(self, context, review):
        pass
```

### 2. Register with Judge Agent

```python
from semar.agents.judge_agent import JudgeAgent

judge = JudgeAgent()
judge.register_language_agent("python", PythonReviewer())
# judge.register_language_agent("javascript", JSReviewer())
# judge.register_language_agent("go", GoReviewer())
```

### 3. Run a PR Review

```python
async def review_pr():
    result = await judge.handle_pr_review(
        pr_url="https://github.com/org/repo/pull/42",
        pr_diff="+import os\n+def main():\n+    pass",
        pr_metadata={"files": ["main.py"]},
    )
    print(result["verdict"])  # "approve" or "request_changes"
    print(result["total_suggestions"])

asyncio.run(review_pr())
```

## Components

### BaseAgent

Abstract base class. All agents implement the 4-step cycle:

| Step | Method | Purpose |
|------|--------|---------|
| 1 | `plan()` | Analyze PR, create execution plan |
| 2 | `action()` | Execute the review |
| 3 | `review()` | Self-reflect on results |
| 4 | `update_instructions()` | Learn from the experience |

### JudgeAgent

Orchestrator that:
- Detects languages in diffs using regex patterns and file extensions
- Dispatches to registered agents in parallel via `asyncio.gather`
- Aggregates results and merges suggestions
- Resolves conflicts via majority voting

```python
# Language detection works on diff content and file metadata
judge._detect_languages("+import os\n+const x = 1;", {"files": ["app.py", "utils.js"]})
# Returns: ["python", "javascript"]
```

### TrajectoryAnalyzer

Analyzes execution logs to detect failure modes:

| Failure Type | Severity | Detection Method |
|-------------|----------|-----------------|
| `missed_issue` | high | Human follow-up comments |
| `false_positive` | medium | Rejected suggestions |
| `hallucination` | high | Actions on non-existent files |
| `overconfident` | medium | High confidence + low accuracy |

```python
from semar.agents.trajectory_analyzer import TrajectoryAnalyzer

analyzer = TrajectoryAnalyzer()
result = await analyzer.analyze(trajectory)
# result["failure_modes"] -> List[FailureMode]
```

### ImprovementSelector

Decides what to update:

| Condition | Decision |
|-----------|----------|
| Failure modes detected | `HARNESS` (update prompts/skills) |
| Stalled (N iterations no improvement) | `WEIGHT` (retrain with RL) |
| Improving steadily | `NONE` (no action needed) |

```python
from semar.agents.improvement_selector import ImprovementSelector

selector = ImprovementSelector(stall_threshold=3)
decision = await selector.decide(analysis)
```

### RLAlgorithmSelector

Picks the right algorithm based on reward structure:

| Algorithm | When to Use |
|-----------|------------|
| PPO+GAE | Dense, step-level rewards |
| GRPO | Cheap rollouts, verifiable at episode end (default) |
| Entropic Advantage | Right-skewed rewards |
| REINFORCE+KL | Dense rewards with regression risk |
| Best-of-NN | Extremely sparse rewards |
| DPO | Ranking-only data |

```python
from semar.agents.rl_algorithm_selector import RLAlgorithmSelector

selector = RLAlgorithmSelector()
algo = await selector.select(analysis)
# Returns: RLAlgorithm.GRPO
```

### TrajectoryStore

SQLite storage for execution logs:

```python
from semar.agents.trajectory_store import TrajectoryStore

store = TrajectoryStore("my_trajectories.db")
await store.store(
    agent_id="python-reviewer",
    pr_url="https://github.com/org/repo/pull/42",
    language="python",
    plan={"files": ["main.py"]},
    action_result="Reviewed 1 file",
    review={"review": "approve", "suggestions": []},
    metrics={"accuracy": 0.9},
    full_trajectory={"steps": {}},
)

trajectories = await store.get_trajectories(agent_id="python-reviewer")
stats = await store.get_agent_stats("python-reviewer")
```

## Configuration

SEMAR uses dynaconf. Create a `settings.toml` in your working directory:

```toml
[default]
api_provider = "openai"
api_model = "gpt-4"
max_tokens = 4096
temperature = 0.1
stall_threshold = 3
trajectory_db_path = "semar_trajectories.db"
log_level = "INFO"
```

Or set environment variables:

```bash
export SEMAR_API_PROVIDER=openai
export SEMAR_API_KEY=sk-...
export SEMAR_API_MODEL=gpt-4
```

## Running Tests

```bash
# All tests (163)
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Security tests only
pytest tests/security/ -v

# With coverage
pytest tests/ --cov=semar --cov-report=term-missing

# Lint and format
ruff check . && ruff format .

# Type check
ty check
```

## Project Structure

```
semar/
├── semar/
│   ├── __init__.py
│   ├── agents/
│   │   ├── base_agent.py          # BaseAgent + AgentContext + AgentResult
│   │   ├── judge_agent.py         # JudgeAgent orchestrator
│   │   ├── trajectory_analyzer.py # Failure mode detection
│   │   ├── improvement_selector.py # Harness vs weight decisions
│   │   ├── rl_algorithm_selector.py # Adaptive RL selection
│   │   └── trajectory_store.py    # SQLite storage
│   ├── config/
│   │   ├── settings.py            # Dynaconf config
│   │   └── default.toml           # Default values
│   └── utils/
│       └── helpers.py             # Utilities
├── tests/
│   ├── unit/                      # 72 unit tests
│   ├── security/                  # 85 security tests
│   └── ...
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   └── USER_GUIDE.md              # This file
├── pyproject.toml
└── README.md
```

## Roadmap

| Phase | Status | What It Adds |
|-------|--------|-------------|
| 0 | Done | Package structure, config, tooling |
| 1 | Done | BaseAgent, TrajectoryStore, helpers |
| 2 | Done | Judge Agent, parallel dispatch, conflict resolution |
| 3 | Next | Self-improvement engine (harness + weight updates) |
| 4 | Planned | Org-level cross-repo learning |
| 5 | Planned | PR-Agent integration, GitHub bot |
| 6 | Planned | Dashboard, monitoring, production readiness |

## License

MIT License
