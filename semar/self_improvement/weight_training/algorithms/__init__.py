"""RL algorithms for weight training."""

from typing import Dict, Type

from semar.self_improvement.weight_training.algorithms.base_algorithm import BaseAlgorithm
from semar.self_improvement.weight_training.algorithms.best_of_nn import BestOfNN
from semar.self_improvement.weight_training.algorithms.dpo import DPO
from semar.self_improvement.weight_training.algorithms.entropic_advantage import EntropicAdvantage
from semar.self_improvement.weight_training.algorithms.grpo import GRPO
from semar.self_improvement.weight_training.algorithms.ppo_gae import PPOGAE
from semar.self_improvement.weight_training.algorithms.reinforce_kl import REINFORCEKL

ALGORITHM_REGISTRY: Dict[str, Type[BaseAlgorithm]] = {
    "ppo_gae": PPOGAE,
    "grpo": GRPO,
    "entropic_advantage": EntropicAdvantage,
    "reinforce_kl": REINFORCEKL,
    "best_of_nn": BestOfNN,
    "dpo": DPO,
}


def get_algorithm(name: str) -> BaseAlgorithm:
    """Get an algorithm instance by name.

    Args:
        name: Algorithm name (e.g. 'ppo_gae', 'grpo')

    Returns:
        Algorithm instance

    Raises:
        ValueError: If algorithm name is not registered
    """
    cls = ALGORITHM_REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(ALGORITHM_REGISTRY.keys()))
        raise ValueError(f"Unknown algorithm '{name}'. Available: {available}")
    return cls()
