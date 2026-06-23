"""BaseAlgorithm - Abstract base class for RL algorithms."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAlgorithm(ABC):
    """Abstract base class for all RL algorithms.

    Each algorithm must implement:
    - name: Algorithm identifier
    - train(): Execute one training step
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Algorithm name identifier."""
        pass

    @abstractmethod
    async def train(
        self,
        trajectories: List[Dict[str, Any]],
        hyperparams: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run one training step.

        Args:
            trajectories: List of trajectory data
            hyperparams: Algorithm-specific hyperparameters

        Returns:
            Dictionary with at least 'loss' key
        """
        pass
