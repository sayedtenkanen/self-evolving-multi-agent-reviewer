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
cd self-evolving-multi-agent-reviewer

# Install in development mode
pip install -e ".[dev]"
```

## Quick Start

```python
from semar.agents.judge_agent import JudgeAgent

# Initialize the Judge Agent
judge = JudgeAgent()

# Review a PR
result = await judge.handle_pr_review("https://github.com/org/repo/pull/123")
print(result)
```

## CLI Usage

```bash
# Review a PR
semar review --pr-url https://github.com/org/repo/pull/123

# Describe a PR
semar describe --pr-url https://github.com/org/repo/pull/123

# Improve a PR
semar improve --pr-url https://github.com/org/repo/pull/123
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for implementation roadmap and milestones.

## Development

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=semar

# Lint
ruff check semar/

# Format
ruff format semar/
```

## License

MIT License
