"""Helper utilities for SEMAR."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique ID string
    """
    import uuid

    id_str = str(uuid.uuid4())[:8]
    return f"{prefix}_{id_str}" if prefix else id_str


def hash_content(content: str) -> str:
    """Generate a hash of content.

    Args:
        content: String to hash

    Returns:
        SHA256 hash of content
    """
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def parse_pr_url(pr_url: str) -> Dict[str, Optional[str]]:
    """Parse a PR URL to extract components.

    Args:
        pr_url: PR URL (e.g., https://github.com/org/repo/pull/123)

    Returns:
        Dictionary with owner, repo, pr_number
    """
    patterns = [
        r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<pr_number>\d+)",
        r"https?://gitlab\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/-/merge_requests/(?P<pr_number>\d+)",
    ]

    for pattern in patterns:
        match = re.match(pattern, pr_url)
        if match:
            return match.groupdict()

    return {"owner": None, "repo": None, "pr_number": None}


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def safe_json_dumps(obj: Any) -> str:
    """Safely serialize object to JSON.

    Args:
        obj: Object to serialize

    Returns:
        JSON string
    """

    def default_serializer(o):
        if hasattr(o, "__dict__"):
            return o.__dict__
        return str(o)

    return json.dumps(obj, default=default_serializer, ensure_ascii=False)


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_extension(filename: str) -> str:
    """Get file extension.

    Args:
        filename: Filename

    Returns:
        File extension (without dot)
    """
    return Path(filename).suffix.lstrip(".")


def is_binary_file(filepath: str) -> bool:
    """Check if file is binary.

    Args:
        filepath: Path to file

    Returns:
        True if binary, False otherwise
    """
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
            return b"\0" in chunk
    except (IOError, OSError):
        return False


def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregate metrics from results.

    Args:
        results: List of result dictionaries

    Returns:
        Aggregated metrics
    """
    if not results:
        return {}

    metrics = {
        "total_reviews": len(results),
        "successful_reviews": sum(1 for r in results if r.get("success", True)),
        "failed_reviews": sum(1 for r in results if not r.get("success", True)),
    }

    # Calculate averages
    durations = [r.get("duration_ms", 0) for r in results]
    metrics["avg_duration_ms"] = sum(durations) / len(durations) if durations else 0

    # Calculate language distribution
    languages = [r.get("language", "unknown") for r in results]
    language_counts = {}
    for lang in languages:
        language_counts[lang] = language_counts.get(lang, 0) + 1
    metrics["language_distribution"] = language_counts

    return metrics


class Logger:
    """Simple logger for SEMAR."""

    def __init__(self, name: str = "semar", level: str = "INFO"):
        """Initialize logger.

        Args:
            name: Logger name
            level: Log level
        """
        self.name = name
        self.level = level
        self._log_file = None

    def _format_message(self, level: str, message: str) -> str:
        """Format log message.

        Args:
            level: Log level
            message: Log message

        Returns:
            Formatted message
        """
        timestamp = datetime.now().isoformat()
        return f"[{timestamp}] [{level}] [{self.name}] {message}"

    def info(self, message: str) -> None:
        """Log info message."""
        print(self._format_message("INFO", message))

    def warning(self, message: str) -> None:
        """Log warning message."""
        print(self._format_message("WARNING", message))

    def error(self, message: str) -> None:
        """Log error message."""
        print(self._format_message("ERROR", message))

    def debug(self, message: str) -> None:
        """Log debug message."""
        if self.level == "DEBUG":
            print(self._format_message("DEBUG", message))


# Global logger instance
logger = Logger()
