# Self-Evolving Multi-Agent Reviewer (SEMAR)

## Project Summary

SEMAR is a self-improving PR review system that uses multiple 
language-specific agents coordinated by a Judge Agent. The system 
continuously improves itself through:
- **Harness updates** (prompts, skills, rules)
- **Weight updates** (RL training)
- **Full trajectory analysis**

## Naming

| Context | Name |
|---------|------|
| Full Name | Self-Evolving Multi-Agent Reviewer |
| Package Name | `semar` |
| Import | `import semar` |
| CLI | `semar` |
| Repository | `github.com/sayedtenkanen/self-evolving-multi-agent-reviewer` |

## Goals

1. **Multi-agent PR review** with language-specific expertise
2. **Self-improvement** via harness + weight updates
3. **Full trajectory capture** and analysis
4. **Adaptive RL algorithm selection**
5. **Org-level learning** across repositories

## Based On

- Fork of [PR-Agent](https://github.com/sayedtenkanen/pr-agent)
- Architecture inspired by [SIA paper](https://arxiv.org/html/2605.27276v2)

## Timeline

10-12 weeks (solo developer)

## Key Features

### Language Support

- Python
- JavaScript
- TypeScript
- Go
- Java
- Rust
- C++

### Self-Improvement Mechanisms

- **Prompt Evolution**: Automatically improve review prompts
- **Skill Discovery**: Find new analysis patterns
- **Rule Evolution**: Optimize review criteria
- **Weight Training**: RL-based model adaptation

### Feedback Loops

- Outcome-based learning
- Human feedback integration
- Cross-agent learning
- Meta-learning (learning how to learn)

## Architecture Overview

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
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Review a PR
semar review --pr-url https://github.com/org/repo/pull/123

# List available agents
semar agents list

# View performance metrics
semar metrics
```

## License

Apache 2.0 (matching PR-Agent)
