# SEMAR Naming Conventions

## Project Names

| Context | Name |
|---------|------|
| Full Name | Self-Evolving Multi-Agent Reviewer |
| Package | `semar` |
| Import | `import semar` |
| CLI | `semar` |
| Repository | `self-evolving-multi-agent-reviewer` |
| GitHub URL | `github.com/sayedtenkanen/self-evolving-multi-agent-reviewer` |

---

## Code Naming

### Files

- **Convention**: snake_case
- **Examples**:
  - `base_agent.py`
  - `trajectory_store.py`
  - `judge_agent.py`
  - `prompt_evolver.py`

### Classes

- **Convention**: PascalCase
- **Examples**:
  - `BaseAgent`
  - `JudgeAgent`
  - `TrajectoryStore`
  - `PythonAgent`
  - `PromptEvolver`
  - `RLAlgorithmSelector`

### Functions

- **Convention**: snake_case
- **Examples**:
  - `execute_cycle()`
  - `analyze_trajectory()`
  - `decide_improvement()`
  - `select_algorithm()`

### Variables

- **Convention**: snake_case
- **Examples**:
  - `trajectories`
  - `failure_modes`
  - `improvement_type`
  - `algorithm_selector`

### Constants

- **Convention**: UPPER_SNAKE_CASE
- **Examples**:
  - `AGENT_STATE_PLANNING`
  - `DEFAULT_MODEL`
  - `MAX_TRAJECTORIES`

---

## Directory Structure

### Package Layout

```
semar/                          # Main package
├── agents/                     # Agent implementations
│   ├── language_agents/        # Language-specific agents
│   └── __init__.py
├── self_improvement/           # Self-improvement engine
│   ├── harness/                # Harness evolution
│   ├── weight_training/        # Weight updates
│   │   └── algorithms/         # RL algorithms
│   └── trajectory/             # Trajectory analysis
├── config/                     # Configuration
├── repo_management/            # Multi-repo support
├── monitoring/                 # Observability
└── utils/                      # Helper functions
```

### Test Layout

```
tests/
├── test_agents/                # Agent tests
│   ├── test_base_agent.py
│   ├── test_judge_agent.py
│   └── test_language_agents/
├── test_self_improvement/      # Self-improvement tests
│   ├── test_harness/
│   └── test_weight_training/
├── test_config/                # Config tests
└── conftest.py                 # Pytest fixtures
```

---

## Configuration Naming

### Environment Variables

- **Prefix**: `SEMAR_*`
- **Examples**:
  - `SEMAR_LLM_MODEL`
  - `SEMAR_AGENT_MAX_PARALLEL`
  - `SEMAR_TRAJECTORY_DB_PATH`
  - `SEMAR_WEIGHTS_BASE_MODEL`

### TOML Settings

```toml
[llm]
model = "gpt-4"
temperature = 0.2

[agent]
max_parallel = 5
stall_threshold = 3

[trajectory]
db_path = "semar_trajectories.db"

[weights]
base_model = "meta-llama/Llama-3-70b"  # or another open-source model
lora_rank = 32
```

---

## API Naming

### REST Endpoints

- **Convention**: kebab-case for URLs, camelCase for query params
- **Examples**:
  - `POST /api/v1/review`
  - `GET /api/v1/agents`
  - `GET /api/v1/metrics?agentId=python`

### Request/Response Models

- **Convention**: PascalCase for models, camelCase for fields
- **Examples**:
  - `ReviewRequest` with `prUrl`, `languages`
  - `ReviewResponse` with `review`, `suggestions`, `metrics`

---

## Git Naming

### Branch Names

- **Convention**: kebab-case with type prefix
- **Examples**:
  - `feature/add-python-agent`
  - `fix/trajectory-storage-bug`
  - `docs/update-roadmap`
  - `refactor/improve-judge-agent`

### Commit Messages

- **Convention**: Conventional Commits
- **Examples**:
  - `feat: add Python language agent`
  - `fix: resolve trajectory storage issue`
  - `docs: update implementation plan`
  - `refactor: improve Judge Agent logic`

### PR Titles

- **Convention**: Conventional Commits (same as commits)
- **Examples**:
  - `feat: add Python language agent`
  - `fix: resolve trajectory storage issue`

---

## Versioning

### Package Version

- **Convention**: Semantic Versioning (semver)
- **Format**: `MAJOR.MINOR.PATCH`
- **Examples**:
  - `0.1.0` - Initial development
  - `0.2.0` - Add language agents
  - `1.0.0` - First stable release

### API Version

- **Convention**: URL path versioning
- **Examples**:
  - `/api/v1/review`
  - `/api/v2/review` (breaking changes)

---

## Documentation Naming

### File Names

- **Convention**: UPPER_SNAKE_CASE for markdown
- **Examples**:
  - `PROJECT_OVERVIEW.md`
  - `ARCHITECTURE.md`
  - `ROADMAP.md`
  - `SELF_IMPROVEMENT.md`
  - `IMPLEMENTATION_PLAN.md`
  - `NAMING.md`

### Section Headers

- **Convention**: Title Case
- **Examples**:
  - `# Project Overview`
  - `## Architecture`
  - `### Components`

---

## Import Naming

### Standard Library Imports

```python
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
```

### Third-Party Imports

```python
from pydantic import BaseModel
from dynaconf import Dynaconf
from loguru import logger
```

### Local Imports

```python
from semar.agents.base_agent import BaseAgent
from semar.config.settings import settings
from semar.utils.helpers import analyze_trajectory
```

---

## Error Naming

### Exception Classes

- **Convention**: PascalCase with `Error` suffix
- **Examples**:
  - `TrajectoryStorageError`
  - `AgentNotFoundError`
  - `ImprovementSelectionError`
  - `RLAlgorithmError`

### Error Messages

- **Convention**: snake_case for error codes, human-readable for messages
- **Examples**:
  - Error code: `trajectory_storage_failed`
  - Message: "Failed to store trajectory in database"

---

## Database Naming

### Table Names

- **Convention**: snake_case, plural
- **Examples**:
  - `trajectories`
  - `agents`
  - `improvements`
  - `metrics`

### Column Names

- **Convention**: snake_case
- **Examples**:
  - `id`
  - `agent_id`
  - `pr_url`
  - `created_at`
  - `full_trajectory`

---

## Summary

| Context | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `base_agent.py` |
| Classes | PascalCase | `BaseAgent` |
| Functions | snake_case | `execute_cycle()` |
| Variables | snake_case | `trajectories` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_MODEL` |
| Directories | snake_case | `language_agents/` |
| Environment | UPPER_SNAKE_CASE | `SEMAR_LLM_MODEL` |
| Git branches | kebab-case | `feature/add-agent` |
| Commits | Conventional | `feat: add agent` |
| API URLs | kebab-case | `/api/v1/review` |
| DB tables | snake_case | `trajectories` |
| Docs | UPPER_SNAKE_CASE | `ROADMAP.md` |
