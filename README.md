# SEMAR - Self-Evolving Multi-Agent Reviewer

A self-improving PR review system with language-specific agents, Judge Agent orchestration, and continuous learning capabilities.

## Overview

SEMAR is a multi-agent code review system that learns and improves over time. It uses:

- **Language-specific agents** for Python, JavaScript, TypeScript, Go, Java, Rust, and C++
- **Judge Agent** for orchestrating reviews and making improvement decisions
- **Self-improvement** through harness evolution (prompts, skills, rules) and weight updates (RL training)
- **Cross-agent learning** for knowledge transfer between languages
- **Org-level learning** for cross-repository knowledge sharing

## Features

- Multi-language support with specialized agents
- Parallel agent dispatch with timeout enforcement
- Conflict resolution with credibility tracking
- Continuous learning with decay and rollback
- Adaptive RL algorithm selection
- Full trajectory capture and analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/sayedtenkanen/self-evolving-multi-agent-reviewer.git
cd self-evolving-multi-agent-reviewer/semar

# Install in development mode
pip install -e ".[dev]"
```

## Quick Start

```python
from semar.agents.base_agent import BaseAgent

# Create a custom agent
class MyAgent(BaseAgent):
    async def plan(self, context):
        return {"action": "review", "files": context.changed_files}

    async def act(self, context, plan):
        return {"review": "Looks good!"}

    async def review(self, context, action_result):
        return {"approved": True, "feedback": action_result}

    async def update(self, context, action_result, review_result):
        pass  # Store trajectory for learning

# Use the agent
agent = MyAgent(agent_id="python-reviewer", language="python")
```

## Development

```bash
# Run all tests (108 tests)
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run security tests only
pytest tests/security/ -v

# Run with coverage
pytest tests/ --cov=semar --cov-report=term-missing

# Lint
ruff check .

# Format
ruff format .

# Type check
ty check
```

## CI/CD

The project includes comprehensive GitHub Actions workflows:

- **CI**: Lint, type check, unit tests (Python 3.12/3.13), security tests, build
- **Security Scan**: Secret detection, dependency audit, Bandit SAST
- **Code Quality**: Ruff lint/format, ty type check, complexity analysis, dead code detection
- **Release**: Tag-triggered PyPI publishing

## Project Status

- **Phase 0**: Package structure, config, tooling ✅
- **Phase 1**: BaseAgent, TrajectoryStore, Config, helpers ✅
- **Phase 2**: Judge Agent, parallel dispatch, conflict resolution (in progress)
- **Phase 3**: Self-improvement engine (planned)
- **Phase 4**: Org-level learning (planned)
- **Phase 5**: Integration with PR-Agent (planned)

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for implementation roadmap and milestones.

## License

MIT License
