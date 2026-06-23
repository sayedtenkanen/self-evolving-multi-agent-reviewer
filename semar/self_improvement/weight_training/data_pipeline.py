"""DataPipeline - Collects and processes training data from trajectories."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CollectedData:
    """Collected and processed training data."""

    data: List[Dict[str, Any]] = field(default_factory=list)
    count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataPipeline:
    """Collects training data from trajectories, processes and splits it.

    Handles:
    - Collecting trajectories into training format
    - Filtering invalid data points
    - Splitting into train/validation sets
    """

    def __init__(self):
        pass

    async def collect(self, trajectories: List[Dict[str, Any]]) -> CollectedData:
        """Collect trajectories into training data.

        Args:
            trajectories: List of trajectory dictionaries

        Returns:
            CollectedData with processed data
        """
        data = [dict(t) for t in trajectories]
        return CollectedData(data=data, count=len(data))

    async def process(self, data: List[Dict[str, Any]]) -> CollectedData:
        """Process and filter training data.

        Removes invalid entries (missing rewards, None values, etc.)

        Args:
            data: Raw training data

        Returns:
            CollectedData with valid entries only
        """
        valid = []
        for item in data:
            if self._is_valid(item):
                valid.append(item)
        return CollectedData(data=valid, count=len(valid))

    def split(
        self,
        data: List[Any],
        val_ratio: float = 0.2,
    ) -> tuple:
        """Split data into training and validation sets.

        Args:
            data: List of data points
            val_ratio: Fraction for validation (0.0-1.0)

        Returns:
            Tuple of (train_data, val_data)
        """
        split_idx = int(len(data) * (1 - val_ratio))
        return data[:split_idx], data[split_idx:]

    def _is_valid(self, item: Any) -> bool:
        """Check if a data item is valid."""
        if not isinstance(item, dict):
            return False
        # Check for None rewards
        if "reward" in item and item["reward"] is None:
            return False
        return True
