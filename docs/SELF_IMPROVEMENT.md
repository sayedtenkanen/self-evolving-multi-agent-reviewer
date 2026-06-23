# Self-Improvement Patterns from SIA Paper

> **Note**: This is a reference document describing patterns from the SIA paper.
> Code examples are aspirational designs. Implemented components are in `semar/semar/agents/`.
> See `docs/ARCHITECTURE.md` for implementation status.

## Overview

The SIA paper ("Self Improving AI with Harness & Weight Updates") proposes a system that improves both the scaffold (harness) and model weights of an AI agent. This document summarizes the key patterns and how they apply to SEMAR.

**Paper**: [arxiv.org/html/2605.27276v2](https://arxiv.org/html/2605.27276v2)

---

## Two Levers of Improvement

The paper identifies **two complementary levers** for agent improvement:

| Lever | What It Changes | When to Use |
|-------|-----------------|-------------|
| **Harness Updates** | External infrastructure: prompts, tools, retry logic, parsing | First, cheaper to implement |
| **Weight Updates** | Internal model knowledge via RL training | After stall detection |

### Key Insight

Neither lever alone saturates improvement. Combining both yields superior results:

| Benchmark | Harness Only | Harness + Weights | Improvement |
|-----------|--------------|-------------------|-------------|
| LawBench (191-class) | 50.0% | 70.1% | +20.1 pp |
| AlphaEvolve TriMul | 12,483 μs | 1,017 μs | 91.9% faster |
| MAGIC Denoising | 0.241 | 0.289 | +20.4% |

---

## Three-Phase Protocol

Each generation follows a three-phase protocol:

### 1. Execution

- Run the agent on the task
- Capture the full trajectory τg
- Record every prompt, response, tool call, and result

### 2. Analysis

- Feedback-Agent receives:
  - Agent source code (scaffold)
  - Full trajectory τg
  - Performance metrics ℰg
  - Task specification 𝒰
- Diagnose specific failure modes

### 3. Improvement

- Feedback-Agent emits:
  - Improvement report (prose analysis)
  - Next-generation agent (improved scaffold)
- OR triggers weight update via RL

---

## Full Trajectory Analysis

**Critical**: The Feedback-Agent receives the **complete execution log**, not just summary statistics.

### What's Captured

- Every prompt sent to the LLM
- Every response received
- Every tool call and result
- Every extracted answer
- Human follow-up actions

### Why It Matters

This enables diagnosis of **specific failure modes** rather than reacting to aggregate metrics.

### Example Failure Modes

- Missed issues (human follow-up required)
- False positives (suggestions rejected)
- Poor suggestions (low quality)
- Incomplete coverage (files not analyzed)

---

## Three-Component Architecture

### 1. Meta-Agent (ℳ)

- Generates initial scaffold from task specification
- One-time initialization
- Maps to: Judge Agent (initializes language agents)

### 2. Task-Specific Agent (Ag)

- Executes the task with current scaffold
- Produces trajectory τg
- Maps to: Language Agents (Python, JS, Go, etc.)

### 3. Feedback-Agent (ℱ)

- Analyzes full trajectory
- Decides between harness or weight update
- Generates improved scaffold or triggers RL training
- Maps to: Judge Agent (analyzes and decides)

---

## Adaptive RL Algorithm Selection

The Feedback-Agent dynamically selects the appropriate training algorithm:

### PPO with GAE

**When to use**: Dense step-level rewards, multi-step tasks

- Learned value head produces per-token advantage estimates
- Clipped surrogate objective prevents policy drift
- Dual actor-critic optimization (expensive but stable)

### GRPO (Group Relative Policy Optimization)

**When to use**: Cheap rollouts, episode-end verifier

- Advantages normalized within rollout group
- No value network needed
- Halves memory, enables large parallel batches

### Entropic Advantage Weighting

**When to use**: Right-skewed reward histogram (rare successes)

- Up-weights high-reward rollouts
- Discounts near-zero-reward noise
- Softmax redistribution with adaptive temperature

### REINFORCE + KL-to-base

**When to use**: Dense rewards, risk of capability regression

- Monte Carlo returns as advantages directly
- KL penalty against frozen reference policy
- No critic, no grouping, simplest loop

### Best-of-NN Behavioral Cloning

**When to use**: Extremely sparse rewards (cold start)

- Top-k rollouts by verifier score
- Distilled into model via cross-entropy loss
- Raises baseline for subsequent PPO/GRPO

### DPO (Direct Preference Optimization)

**When to use**: Verifier ranks but doesn't score absolutely

- Given winning and losing rollouts
- Minimizes objective directly without reward model

### Trajectory → RL Algorithm Mapping

The Judge Agent derives reward structure from trajectory analysis:

```python
def derive_reward_structure(trajectory: Dict) -> Dict[str, bool]:
    """Analyze trajectory to determine reward characteristics"""
    metrics = trajectory.get("metrics", {})
    
    return {
        # Dense step-level rewards: multiple reward signals per review step
        "dense_step_level": len(metrics.get("step_rewards", [])) > 3,
        
        # Cheap rollouts: can generate many reviews quickly
        "cheap_rollouts": metrics.get("avg_review_time", 10) < 5,  # < 5 seconds
        
        # Episode-end verifier: reward only at end
        "episode_end_verifier": len(metrics.get("step_rewards", [])) <= 1,
        
        # Right-skewed: most reviews fail, few succeed
        "right_skewed": metrics.get("success_rate", 0.5) < 0.2,
        
        # Dense overall: consistent reward signal
        "dense": metrics.get("reward_variance", 1.0) < 0.5,
        
        # Regression risk: high capability, small changes needed
        "regression_risk": metrics.get("base_model_score", 0) > 0.8,
        
        # Extremely sparse: almost no positive signal
        "extremely_sparse": metrics.get("success_rate", 0.5) < 0.05,
        
        # Ranking only: can rank outputs but not score absolutely
        "ranking_only": metrics.get("has_absolute_score", True) == False,
    }
```

**Mapping Logic**:
1. Trajectory analysis produces reward structure flags
2. Flags are matched to algorithm selection rules
3. Selected algorithm is used for weight training

---

## What Each Lever Changes

### Harness Updates (External)

Produce **externalised** changes:
- New tools and tighter parsers
- Smarter retry logic
- Better prompt structure
- Search procedures

**Example from paper**: On LawBench, harness iteration built a structured answer-extraction layer and an SVC re-ranker.

### Weight Updates (Internal)

Produce **internalised** knowledge:
- Domain-specific patterns in model parameters
- Task-specific intuition
- Patterns no prompt can encode

**Example from paper**: On MAGIC denoising, weight update introduced a `np.clip + np.rint` post-processing step (biological invariant) that harness never proposed.

---

## Mapping to SEMAR

### SIA Component → SEMAR Equivalent

| SIA Component | SEMAR Equivalent |
|---------------|------------------|
| Meta-Agent (ℳ) | Judge Agent (initialization) |
| Task-Specific Agent (Ag) | Language Agents |
| Feedback-Agent (ℱ) | Judge Agent (analysis + decision) |
| Scaffold | Prompts, skills, rules |
| Weights θ | LoRA adapters |
| Trajectory τg | Full execution logs |
| Metrics ℰg | Performance metrics |
| Verifier V | Review quality + human feedback |

### Implementation in SEMAR

#### Harness Evolution

```python
# PromptEvolver improves prompts based on failure analysis
improved_prompt = await prompt_evolver.evolve(
    current_prompt=agent.scaffold["system_prompt"],
    analysis=trajectory_analysis
)

# SkillDiscovery finds new patterns
new_skills = await skill_discovery.discover(trajectories)

# RuleEvolver optimizes criteria
evolved_rules = await rule_evolver.evolve(
    current_rules=agent.scaffold["rules"],
    analysis=trajectory_analysis
)
```

#### Weight Training

```python
# LoRA training with adaptive algorithm selection
algorithm = await rl_selector.select(trajectory_analysis)

if algorithm == RLAlgorithm.PPO_GAE:
    await lora_trainer.train_ppo_gae(trajectories, hyperparams)
elif algorithm == RLAlgorithm.GRPO:
    await lora_trainer.train_grpo(trajectories, hyperparams)
# ... etc
```

---

## Key Takeaways for Implementation

### 1. Capture Full Trajectories

Not just metrics, but complete execution logs. This is critical for diagnosing specific failure modes.

### 2. Judge Agent Decides Lever

The Judge Agent should detect stalls and decide between harness updates and weight updates.

### 3. Adaptive Algorithm Selection

Choose RL algorithm based on reward structure, not a fixed schedule.

### 4. Neither Lever Saturates

Always try both improvement paths. Harness updates make the model agentic; weight updates build domain intuition.

### 5. Domain Knowledge Emerges from Weight Updates

Weight updates can encode patterns no prompt can. This is how the system learns truly new capabilities.

---

## References

1. SIA: Self Improving AI with Harness & Weight Updates (arXiv:2605.27276v2)
2. Darwin Gödel Machine (Zhang et al., 2025)
3. Meta-Harness (Lee et al., 2026)
4. Hyperagents (Zhang et al., 2026)
5. TTRL (Zuo et al., 2025)
6. Self-Refine (Madaan et al., 2023)
7. Reflexion (Shinn et al., 2023)
8. STaR (Zelikman et al., 2022)
