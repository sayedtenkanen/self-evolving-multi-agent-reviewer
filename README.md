# SEMAR - Self-Evolving Multi-Agent Reviewer

A self-improving PR review system with language-specific agents, Judge Agent orchestration, and continuous learning capabilities.

## Overview

SEMAR is a multi-agent code review system that learns and improves over time. It uses:

- **Language-specific agents** for Python, JavaScript, TypeScript, Go, Java, Rust, C++, Ruby, PHP, Shell, SQL, Swift, and Kotlin
- **Judge Agent** for orchestrating reviews and making improvement decisions
- **Self-improvement** through harness evolution (prompts, skills, rules) and weight updates (RL training)
- **Cross-agent learning** for knowledge transfer between languages
- **Org-level learning** for cross-repository knowledge sharing

## Installation

```bash
git clone https://github.com/sayedtenkanen/self-evolving-multi-agent-reviewer.git
cd self-evolving-multi-agent-reviewer/semar
pip install -e ".[dev]"
```

## Getting Started

```python
from semar.agents.judge_agent import JudgeAgent

judge = JudgeAgent()
# Register a language agent, then call:
# result = await judge.handle_pr_review(pr_url, pr_diff, pr_metadata)
```

See the [User Guide](docs/USER_GUIDE.md#quick-start) for a complete walkthrough.

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Quick start, API examples, component reference |
| [Architecture](docs/ARCHITECTURE.md) | System design, component status, code examples |
| [Roadmap](docs/ROADMAP.md) | Implementation timeline and milestones |
| [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) | Phase-by-phase plan with code examples |
| [Self-Improvement](docs/SELF_IMPROVEMENT.md) | SIA paper patterns and SEMAR mapping |
| [Naming Conventions](docs/NAMING.md) | Code style, directory layout, API conventions |

## Project Status

- **Phase 0**: Package structure, config, tooling ✅
- **Phase 1**: BaseAgent, TrajectoryStore, Config, helpers ✅
- **Phase 2**: Judge Agent, parallel dispatch, conflict resolution ✅
- **Phase 3**: Language Agents, AgentRegistry ✅
- **Phase 4**: Harness Evolution (next)
- **Phase 5**: Weight Updates (planned)
- **Phase 6**: Integration & Polish (planned)

## License

MIT License
