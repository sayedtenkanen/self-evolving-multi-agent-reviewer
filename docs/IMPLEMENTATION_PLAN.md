# SEMAR Implementation Plan

> **Status**: Phases 0-3 are **implemented**. Code examples below may differ from actual code.
> For accurate API reference, see the source files in `semar/semar/` and tests in `semar/tests/`.

## Phase 0: Repository Setup — Implemented

### Commands

```bash
# Create GitHub repo
gh repo create sayedtenkanen/self-evolving-multi-agent-reviewer --public

# Clone PR-Agent
git clone https://github.com/sayedtenkanen/pr-agent.git
cd pr-agent

# Rename remote
git remote rename origin upstream

# Add new repo as origin
git remote add origin https://github.com/sayedtenkanen/self-evolving-multi-agent-reviewer.git

# Push to new repo
git push -u origin main

# Create semar package
mkdir semar
```

### Files to Create

#### `semar/__init__.py`

```python
"""Self-Evolving Multi-Agent Reviewer (SEMAR)"""
__version__ = "0.1.0"
```

#### `pyproject.toml`

> **Note**: Actual file uses hatchling, Python >=3.12, ty (not mypy), and separates core vs ML deps.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "semar"
version = "0.1.0"
description = "Self-Evolving Multi-Agent Reviewer"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.12"
dependencies = [
    "litellm",
    "pydantic>=2.0",
    "dynaconf",
    "jinja2",
    "loguru",
    "tiktoken",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
    "ty>=0.0.1",
    "vulture",
    "radon",
]
ml = [
    "torch>=2.0",
    "transformers>=4.30",
    "peft>=0.4.0",
    "trl>=0.7",
    "datasets",
    "numpy",
]

[project.scripts]
semar = "semar.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["semar"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

#### `requirements.txt`

```
-e .
litellm
pydantic>=2.0
dynaconf
jinja2
loguru
tiktoken
```

#### `README.md`

```markdown
# Self-Evolving Multi-Agent Reviewer (SEMAR)

A self-improving PR review system with language-specific agents that 
continuously improve their review capabilities through harness updates 
and weight training.

## Features

- **Multi-Agent Architecture**: Judge Agent orchestrates language-specific agents
- **Self-Improvement**: Agents evolve via harness (prompts, skills, rules) and weight updates (RL)
- **Full Trajectory Analysis**: Captures complete execution logs for diagnosis
- **Adaptive RL**: Dynamically selects PPO, GRPO, Entropic Advantage, etc.
- **Language Support**: Python, JavaScript, TypeScript, Go, Java, Rust, C++
- **Org-Level Learning**: Learns from feedback across multiple repositories

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

Apache 2.0
```

---

## Phase 1: Foundation — Implemented

### BaseAgent Class

```python
# semar/agents/base_agent.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List
from enum import Enum

class AgentState(Enum):
    PLANNING = "planning"
    ACTION = "action"
    REVIEW = "review"
    UPDATE = "update"

@dataclass
class AgentContext:
    pr_url: str
    pr_diff: str
    pr_metadata: Dict[str, Any]
    language: str
    files: List[str]

@dataclass
class AgentResult:
    review: str
    suggestions: List[Dict[str, Any]]
    metrics: Dict[str, float]
    trajectory: Dict[str, Any]

class BaseAgent(ABC):
    def __init__(self, agent_id: str, language: str = None):
        self.agent_id = agent_id
        self.language = language
        self.state = AgentState.PLANNING
        self.trajectory_store = None  # Set externally
    
    async def execute_cycle(self, context: AgentContext) -> AgentResult:
        """Execute the 4-step self-improvement cycle"""
        # 1. Planning
        plan = await self.plan(context)
        
        # 2. Action
        action_result = await self.action(context, plan)
        
        # 3. Review (self-reflection)
        review = await self.review(context, action_result)
        
        # 4. Update instructions
        await self.update_instructions(context, review)
        
        return review
    
    @abstractmethod
    async def plan(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze PR and create execution plan"""
        pass
    
    @abstractmethod
    async def action(self, context: AgentContext, plan: Dict) -> Any:
        """Execute the review/improvement"""
        pass
    
    @abstractmethod
    async def review(self, context: AgentContext, action_result: Any) -> AgentResult:
        """Self-reflect on results"""
        pass
    
    @abstractmethod
    async def update_instructions(self, context: AgentContext, review: AgentResult) -> None:
        """Update instructions based on learnings"""
        pass
```

### TrajectoryStore

```python
# semar/agents/trajectory_store.py

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

class TrajectoryStore:
    """Stores full execution trajectories for analysis"""
    
    def __init__(self, db_path: str = "semar_trajectories.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trajectories (
                    id INTEGER PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    pr_url TEXT NOT NULL,
                    language TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    plan JSON,
                    action_result JSON,
                    review JSON,
                    metrics JSON,
                    full_trajectory JSON
                )
            """)
    
    async def store(self, agent_id: str, pr_url: str, language: str,
                    plan: Dict, action_result: Any, review: Dict, 
                    metrics: Dict, full_trajectory: Dict) -> int:
        """Store a complete execution trajectory"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO trajectories 
                (agent_id, pr_url, language, plan, action_result, review, metrics, full_trajectory)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (agent_id, pr_url, language, 
                  json.dumps(plan), json.dumps(action_result),
                  json.dumps(review), json.dumps(metrics),
                  json.dumps(full_trajectory)))
            return cursor.lastrowid
    
    async def get_trajectories(self, agent_id: Optional[str] = None,
                                pr_url: Optional[str] = None,
                                limit: int = 100) -> List[Dict]:
        """Retrieve trajectories with optional filters"""
        query = "SELECT * FROM trajectories WHERE 1=1"
        params = []
        
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        if pr_url:
            query += " AND pr_url = ?"
            params.append(pr_url)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
```

### Config System

```python
# semar/config/settings.py

from dynaconf import Dynaconf
from pathlib import Path

settings = Dynaconf(
    envvar_prefix="SEMAR",
    settings_files=[
        str(Path(__file__).parent / "default.toml"),
        ".semar.toml",
    ],
)

# Access settings
# settings.llm.model
# settings.agent.max_parallel
# settings.trajectory.db_path
```

```toml
# semar/config/default.toml

[app]
name = "SEMAR"
version = "0.1.0"
debug = false

[llm]
model = "gpt-4"
temperature = 0.7
max_tokens = 4096

[agent]
timeout = 300
max_concurrent_agents = 5
memory_size = 1000

[trajectory]
db_path = "semar_trajectories.db"
retention_days = 30

[self_improvement]
harness_update_interval = 10
weight_update_interval = 50
stall_detection_window = 5
stall_detection_threshold = 0.01

[learning]
decay_rate = 0.1
min_relevance = 0.1

[rollback]
threshold = 0.1

[conflict_resolution]
credibility_decay_rate = 0.01

[dispatch]
per_agent_timeout = 300
circuit_breaker_threshold = 3
circuit_breaker_recovery_timeout = 60
```

---

## Phase 2: Judge Agent — Implemented

### JudgeAgent

```python
# semar/agents/judge_agent.py

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentContext, AgentResult
from .trajectory_analyzer import TrajectoryAnalyzer
from .improvement_selector import ImprovementSelector
from .rl_algorithm_selector import RLAlgorithmSelector

class JudgeAgent(BaseAgent):
    """Orchestrates language agents and decides improvement strategy"""
    
    def __init__(self):
        super().__init__(agent_id="judge", language=None)
        self.analyzer = TrajectoryAnalyzer()
        self.selector = ImprovementSelector()
        self.rl_selector = RLAlgorithmSelector()
        self.language_agents = {}  # Registry of language agents
    
    def register_language_agent(self, language: str, agent: BaseAgent):
        """Register a language-specific agent"""
        self.language_agents[language] = agent
    
    async def handle_pr_review(self, pr_url: str, pr_diff: str, 
                                pr_metadata: Dict) -> Dict[str, Any]:
        """Main entry point for PR review"""
        # 1. Detect languages in PR
        languages = self._detect_languages(pr_diff, pr_metadata)
        
        # 2. Dispatch to language agents in parallel
        results = await self._dispatch_parallel(languages, pr_url, pr_diff, pr_metadata)
        
        # 3. Aggregate results
        final_review = self._aggregate_results(results)
        
        # 4. Analyze trajectories for improvement
        for language, result in results.items():
            trajectory = result.trajectory
            analysis = await self.analyzer.analyze(trajectory)
            
            # 5. Decide improvement strategy
            improvement_type = await self.selector.decide(analysis)
            
            if improvement_type == "harness":
                await self._improve_harness(language, analysis)
            elif improvement_type == "weight":
                algorithm = await self.rl_selector.select(analysis)
                await self._train_weights(language, algorithm, analysis)
        
        return final_review
    
    async def _dispatch_parallel(self, languages: List[str], pr_url: str,
                                  pr_diff: str, pr_metadata: Dict) -> Dict:
        """Dispatch to multiple language agents in parallel"""
        import asyncio
        tasks = []
        for lang in languages:
            if lang in self.language_agents:
                agent = self.language_agents[lang]
                context = AgentContext(
                    pr_url=pr_url,
                    pr_diff=pr_diff,
                    pr_metadata=pr_metadata,
                    language=lang,
                    files=self._get_files_for_language(pr_diff, lang)
                )
                tasks.append(agent.execute_cycle(context))
        
        results = await asyncio.gather(*tasks)
        return {lang: result for lang, result in zip(languages, results)}
```

### TrajectoryAnalyzer

```python
# semar/agents/trajectory_analyzer.py

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class FailureMode:
    type: str  # "missed_issue", "false_positive", "poor_suggestion"
    severity: str  # "high", "medium", "low"
    frequency: int
    examples: List[Dict]

class TrajectoryAnalyzer:
    """Analyzes execution trajectories to find failure patterns"""
    
    async def analyze(self, trajectory: Dict) -> Dict[str, Any]:
        """Full trajectory analysis"""
        return {
            "prompts": await self._analyze_prompts(trajectory.get("prompts", [])),
            "responses": await self._analyze_responses(trajectory.get("responses", [])),
            "tool_calls": await self._analyze_tool_calls(trajectory.get("tool_calls", [])),
            "metrics": await self._analyze_metrics(trajectory.get("metrics", {})),
            "failure_modes": await self._detect_failure_modes(trajectory),
        }
    
    async def _detect_failure_modes(self, trajectory: Dict) -> List[FailureMode]:
        """Identify specific failure patterns"""
        failures = []
        
        # Check for missed issues (human follow-up required)
        if trajectory.get("human_follow_up"):
            failures.append(FailureMode(
                type="missed_issue",
                severity="high",
                frequency=1,
                examples=trajectory["human_follow_up"]
            ))
        
        # Check for false positives (suggestions rejected)
        if trajectory.get("rejected_suggestions"):
            failures.append(FailureMode(
                type="false_positive",
                severity="medium",
                frequency=len(trajectory["rejected_suggestions"]),
                examples=trajectory["rejected_suggestions"]
            ))
        
        return failures
```

### ImprovementSelector

```python
# semar/agents/improvement_selector.py

from enum import Enum
from typing import Dict, Any

class ImprovementType(Enum):
    HARNESS = "harness"
    WEIGHT = "weight"
    NONE = "none"

class ImprovementSelector:
    """Decides whether to update harness or weights"""
    
    def __init__(self, stall_threshold: int = 3):
        self.stall_threshold = stall_threshold
        self.consecutive_no_improvement = 0
    
    async def decide(self, analysis: Dict[str, Any]) -> ImprovementType:
        """Decide improvement type based on trajectory analysis"""
        metrics = analysis.get("metrics", {})
        failure_modes = analysis.get("failure_modes", [])
        
        # Check for stall
        if self._is_stalled(metrics):
            self.consecutive_no_improvement += 1
        else:
            self.consecutive_no_improvement = 0
        
        # If stalled, try weight updates
        if self.consecutive_no_improvement >= self.stall_threshold:
            return ImprovementType.WEIGHT
        
        # If there are specific failure modes, try harness updates
        if failure_modes:
            return ImprovementType.HARNESS
        
        # Default: try harness first (cheaper)
        return ImprovementType.HARNESS
    
    def _is_stalled(self, metrics: Dict) -> bool:
        """Check if metrics have plateaued"""
        # Implement stall detection logic
        pass
```

### RLAlgorithmSelector

```python
# semar/agents/rl_algorithm_selector.py

from enum import Enum
from typing import Dict, Any

class RLAlgorithm(Enum):
    PPO_GAE = "ppo_gae"
    GRPO = "grpo"
    ENTROPIC_ADVANTAGE = "entropic_advantage"
    REINFORCE_KL = "reinforce_kl"
    BEST_OF_NN = "best_of_nn"
    DPO = "dpo"

class RLAlgorithmSelector:
    """Selects appropriate RL algorithm based on reward structure"""
    
    async def select(self, analysis: Dict[str, Any]) -> RLAlgorithm:
        """Select algorithm based on trajectory analysis"""
        reward_structure = analysis.get("metrics", {}).get("reward_structure", {})
        
        # Dense step-level rewards -> PPO with GAE
        if reward_structure.get("dense_step_level"):
            return RLAlgorithm.PPO_GAE
        
        # Cheap rollouts, episode-end verifier -> GRPO
        if reward_structure.get("cheap_rollouts") and reward_structure.get("episode_end_verifier"):
            return RLAlgorithm.GRPO
        
        # Right-skewed reward histogram -> Entropic Advantage
        if reward_structure.get("right_skewed"):
            return RLAlgorithm.ENTROPIC_ADVANTAGE
        
        # Dense rewards, risk of regression -> REINFORCE + KL
        if reward_structure.get("dense") and reward_structure.get("regression_risk"):
            return RLAlgorithm.REINFORCE_KL
        
        # Extremely sparse rewards -> Best-of-NN
        if reward_structure.get("extremely_sparse"):
            return RLAlgorithm.BEST_OF_NN
        
        # Verifier ranks but doesn't score -> DPO
        if reward_structure.get("ranking_only"):
            return RLAlgorithm.DPO
        
        # Default: GRPO (good balance)
        return RLAlgorithm.GRPO
```

---

## Phase 3: Language Agents — Implemented

### BaseLanguageAgent

```python
# semar/agents/language_agents/base_language_agent.py

from typing import Dict, Any, List
from ..base_agent import BaseAgent, AgentContext, AgentResult

class BaseLanguageAgent(BaseAgent):
    """Base class for language-specific agents"""
    
    def __init__(self, language: str):
        super().__init__(agent_id=f"{language}_agent", language=language)
        self.scaffold = {
            "system_prompt": self._get_default_system_prompt(),
            "skills": self._get_default_skills(),
            "rules": self._get_default_rules(),
        }
    
    def _get_default_system_prompt(self) -> str:
        """Override in subclass"""
        return f"You are an expert {self.language} code reviewer."
    
    def _get_default_skills(self) -> List[str]:
        """Override in subclass"""
        return ["security_review", "performance_analysis", "code_style"]
    
    def _get_default_rules(self) -> List[Dict]:
        """Override in subclass"""
        return []
    
    async def plan(self, context: AgentContext) -> Dict[str, Any]:
        """Create review plan based on language and files"""
        return {
            "language": self.language,
            "files": context.files,
            "skills_to_use": self.scaffold["skills"],
            "rules_to_apply": self.scaffold["rules"],
        }
    
    async def action(self, context: AgentContext, plan: Dict) -> Any:
        """Execute review using scaffold"""
        # Use LLM with current scaffold
        # Capture full trajectory
        pass
    
    async def review(self, context: AgentContext, action_result: Any) -> AgentResult:
        """Self-reflect on review quality"""
        # Analyze own performance
        # Identify issues
        pass
    
    async def update_instructions(self, context: AgentContext, review: AgentResult) -> None:
        """Update scaffold based on learnings"""
        # This is where harness evolution happens
        pass
```

### PythonAgent

```python
# semar/agents/language_agents/python_agent.py

from typing import Dict, Any, List
from .base_language_agent import BaseLanguageAgent

class PythonAgent(BaseLanguageAgent):
    """Python-specific review agent"""
    
    def __init__(self):
        super().__init__(language="python")
    
    def _get_default_system_prompt(self) -> str:
        return """You are an expert Python code reviewer with deep knowledge of:
- Python best practices (PEP 8, PEP 20)
- Type hints and mypy
- Async/await patterns
- Security vulnerabilities (SQL injection, XSS, etc.)
- Performance optimization
- Testing patterns (pytest, unittest)
- Package management (pip, poetry, conda)

Review the code thoroughly and provide actionable suggestions."""
    
    def _get_default_skills(self) -> List[str]:
        return [
            "security_review",
            "performance_analysis",
            "type_hints_check",
            "pep8_compliance",
            "test_coverage",
            "dependency_analysis",
        ]
    
    def _get_default_rules(self) -> List[Dict]:
        return [
            {"name": "no_eval", "pattern": r"\beval\s*\(", "severity": "high"},
            {"name": "no_exec", "pattern": r"\bexec\s*\(", "severity": "high"},
            {"name": "no_hardcoded_secrets", "pattern": r"(password|secret|key)\s*=\s*['\"]", "severity": "high"},
        ]
```

---

## Phase 4: Harness Evolution — Next

### PromptEvolver

```python
# semar/self_improvement/harness/prompt_evolver.py

from typing import Dict, Any, List

class PromptEvolver:
    """Evolves agent prompts based on trajectory analysis"""
    
    async def evolve(self, current_prompt: str, analysis: Dict[str, Any]) -> str:
        """Generate improved prompt based on failure analysis"""
        failure_modes = analysis.get("failure_modes", [])
        
        # Identify prompt weaknesses
        weaknesses = self._identify_weaknesses(current_prompt, failure_modes)
        
        # Generate improved prompt
        improved_prompt = await self._generate_improved_prompt(current_prompt, weaknesses)
        
        return improved_prompt
    
    def _identify_weaknesses(self, prompt: str, failures: List[Dict]) -> List[str]:
        """Identify what the prompt is missing"""
        weaknesses = []
        
        for failure in failures:
            if failure.type == "missed_issue":
                weaknesses.append(f"Missing guidance for: {failure.examples[0]}")
            elif failure.type == "false_positive":
                weaknesses.append(f"Overly broad rule: {failure.examples[0]}")
        
        return weaknesses
    
    async def _generate_improved_prompt(self, prompt: str, weaknesses: List[str]) -> str:
        """Use LLM to generate improved prompt"""
        # Call LLM to refine prompt
        pass
```

### SkillDiscovery

```python
# semar/self_improvement/harness/skill_discovery.py

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class DiscoveredSkill:
    name: str
    description: str
    trigger_pattern: str
    confidence: float

class SkillDiscovery:
    """Discovers new skills from code patterns"""
    
    async def discover(self, trajectories: List[Dict]) -> List[DiscoveredSkill]:
        """Analyze trajectories to find new skill opportunities"""
        patterns = self._extract_patterns(trajectories)
        skills = []
        
        for pattern in patterns:
            if self._is_actionable(pattern):
                skill = await self._create_skill(pattern)
                skills.append(skill)
        
        return skills
    
    def _extract_patterns(self, trajectories: List[Dict]) -> List[Dict]:
        """Extract common patterns from trajectories"""
        # Analyze tool calls, prompts, responses
        pass
    
    def _is_actionable(self, pattern: Dict) -> bool:
        """Determine if pattern is worth turning into a skill"""
        return pattern.get("frequency", 0) >= 3  # Appears 3+ times
```

---

## Phase 5: Weight Updates — Planned

### LoRATrainer

```python
# semar/self_improvement/weight_training/lora_trainer.py

from typing import Dict, Any, Optional
from pathlib import Path

class LoRATrainer:
    """Trains LoRA adapters for model weight updates"""
    
    def __init__(self, base_model: str = "meta-llama/Llama-3-70b", rank: int = 32):
        self.base_model = base_model
        self.rank = rank
        self.output_dir = Path("checkpoints")
        self.output_dir.mkdir(exist_ok=True)
    
    async def train(self, algorithm: str, training_data: Dict, 
                    hyperparams: Dict[str, Any]) -> Path:
        """Run training with specified algorithm"""
        # Initialize LoRA adapter
        # Run training loop
        # Save checkpoint
        pass
    
    async def load_adapter(self, checkpoint_path: Path) -> Any:
        """Load trained LoRA adapter"""
        pass
```

### PPO_GAE

```python
# semar/self_improvement/weight_training/algorithms/ppo_gae.py

from typing import Dict, Any, List
from .base_algorithm import BaseAlgorithm

class PPO_GAE(BaseAlgorithm):
    """PPO with Generalized Advantage Estimation"""
    
    async def train(self, trajectories: List[Dict], hyperparams: Dict) -> Dict:
        """Train using PPO with GAE"""
        # Compute advantages using value head
        # Clip surrogate objective
        # Update policy
        pass
    
    def _compute_gae(self, rewards: List[float], values: List[float], 
                     gamma: float = 0.99, lam: float = 0.95) -> List[float]:
        """Compute Generalized Advantage Estimation"""
        advantages = []
        gae = 0
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + gamma * values[t+1] - values[t]
            gae = delta + gamma * lam * gae
            advantages.insert(0, gae)
        return advantages
```

---

## Phase 6: Integration — Planned

### CLI

```python
# semar/cli.py

import argparse
import asyncio
from typing import List

def main():
    parser = argparse.ArgumentParser(description="SEMAR: Self-Evolving Multi-Agent Reviewer")
    subparsers = parser.add_subparsers(dest="command")
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review a PR")
    review_parser.add_argument("--pr-url", required=True, help="PR URL")
    review_parser.add_argument("--languages", help="Comma-separated languages")
    
    # Agents command
    agents_parser = subparsers.add_parser("agents", help="List agents")
    agents_parser.add_argument("action", choices=["list", "status"])
    
    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="View metrics")
    metrics_parser.add_argument("--agent", help="Filter by agent")
    
    args = parser.parse_args()
    
    if args.command == "review":
        asyncio.run(review_pr(args.pr_url, args.languages))
    elif args.command == "agents":
        list_agents(args.action)
    elif args.command == "metrics":
        view_metrics(args.agent)

async def review_pr(pr_url: str, languages: str = None):
    """Review a PR using SEMAR"""
    from semar.agents.judge_agent import JudgeAgent
    
    judge = JudgeAgent()
    # Register language agents
    # Run review
    result = await judge.handle_pr_review(pr_url, "", {})
    print(result)
```

### Server

```python
# semar/server.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio

app = FastAPI(title="SEMAR API", version="0.1.0")

class ReviewRequest(BaseModel):
    pr_url: str
    languages: Optional[List[str]] = None

class ReviewResponse(BaseModel):
    review: str
    suggestions: List[dict]
    metrics: dict

@app.post("/api/v1/review", response_model=ReviewResponse)
async def review_pr(request: ReviewRequest):
    """Review a PR"""
    from semar.agents.judge_agent import JudgeAgent
    
    judge = JudgeAgent()
    result = await judge.handle_pr_review(request.pr_url, "", {})
    return ReviewResponse(**result)

@app.get("/api/v1/agents")
async def list_agents():
    """List available agents"""
    return {"agents": ["python", "javascript", "typescript", "go", "java", "rust", "cpp"]}

@app.get("/api/v1/metrics")
async def get_metrics(agent: Optional[str] = None):
    """Get performance metrics"""
    return {"metrics": {}}
```

---

## Next Steps

1. **Phase 4**: Implement harness evolution (PromptEvolver, SkillDiscovery, RuleEvolver)
2. **Phase 5**: Implement weight training (LoRA, RL algorithms)
3. **Phase 6**: Implement CLI, GitHub bot, and monitoring
