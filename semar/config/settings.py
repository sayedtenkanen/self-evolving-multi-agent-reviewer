"""Settings - Dynaconf-based configuration system.

Provides centralized configuration management for SEMAR.
"""

from dynaconf import Dynaconf
from pathlib import Path
from typing import Any, Dict, Optional


# Default settings
DEFAULT_SETTINGS = {
    # General
    "app_name": "SEMAR",
    "version": "0.1.0",
    "debug": False,
    
    # LLM Configuration
    "llm_model": "gpt-4",
    "llm_temperature": 0.7,
    "llm_max_tokens": 4096,
    "llm_api_key": None,  # Set via environment variable SEMAR_LLM_API_KEY
    
    # Agent Configuration
    "agent_timeout": 300,  # seconds
    "max_concurrent_agents": 5,
    "agent_memory_size": 1000,
    
    # Trajectory Store
    "trajectory_db_path": "semar_trajectories.db",
    "trajectory_retention_days": 30,
    
    # Self-Improvement
    "harness_update_interval": 10,  # PRs
    "weight_update_interval": 50,  # PRs
    "stall_detection_window": 5,
    "stall_detection_threshold": 0.01,
    
    # Learning Decay
    "learning_decay_rate": 0.1,
    "learning_min_relevance": 0.1,
    
    # Rollback
    "rollback_threshold": 0.1,
    
    # Conflict Resolution
    "credibility_decay_rate": 0.01,
    
    # Parallel Dispatch
    "per_agent_timeout": 300,
    "circuit_breaker_threshold": 3,
    "circuit_breaker_recovery_timeout": 60,
    
    # Language Detection
    "min_files_for_dispatch": 1,
    "max_cache_size": 100,
    
    # Organization
    "org_id": "default",
    "org_max_learnings": 1000,
    "org_relevance_threshold": 0.7,
    
    # Logging
    "log_level": "INFO",
    "log_file": "semar.log",
}


def create_settings(
    envvar_prefix: str = "SEMAR",
    settings_files: Optional[list] = None,
    environments: bool = False,
    env_switcher: str = "SEMAR_ENV",
    base_path: Optional[Path] = None,
) -> Dynaconf:
    """Create a Dynaconf settings instance.
    
    Args:
        envvar_prefix: Prefix for environment variables
        settings_files: List of settings files to load
        environments: Whether to support environment-based settings
        env_switcher: Environment variable to switch environments
        base_path: Base path for settings files
        
    Returns:
        Dynaconf settings instance
    """
    if base_path is None:
        base_path = Path(__file__).parent
    
    if settings_files is None:
        settings_files = [
            str(base_path / "default.toml"),
            ".semar.toml",
        ]
    
    settings = Dynaconf(
        envvar_prefix=envvar_prefix,
        settings_files=settings_files,
        environments=environments,
        env_switcher=env_switcher,
        core_loaders=["TOML"],
    )
    
    # Set default values
    for key, value in DEFAULT_SETTINGS.items():
        if not settings.exists(key):
            settings.set(key, value)
    
    return settings


# Global settings instance
settings = create_settings()


class Config:
    """Configuration manager for SEMAR.
    
    Provides a unified interface to access settings with type safety.
    """

    def __init__(self):
        self._settings = settings

    @property
    def llm(self) -> Dict[str, Any]:
        """LLM configuration."""
        return {
            "model": self._settings.get("llm_model", "gpt-4"),
            "temperature": self._settings.get("llm_temperature", 0.7),
            "max_tokens": self._settings.get("llm_max_tokens", 4096),
            "api_key": self._settings.get("llm_api_key"),
        }

    @property
    def agent(self) -> Dict[str, Any]:
        """Agent configuration."""
        return {
            "timeout": self._settings.get("agent_timeout", 300),
            "max_concurrent": self._settings.get("max_concurrent_agents", 5),
            "memory_size": self._settings.get("agent_memory_size", 1000),
        }

    @property
    def trajectory(self) -> Dict[str, Any]:
        """Trajectory store configuration."""
        return {
            "db_path": self._settings.get("trajectory_db_path", "semar_trajectories.db"),
            "retention_days": self._settings.get("trajectory_retention_days", 30),
        }

    @property
    def self_improvement(self) -> Dict[str, Any]:
        """Self-improvement configuration."""
        return {
            "harness_update_interval": self._settings.get("harness_update_interval", 10),
            "weight_update_interval": self._settings.get("weight_update_interval", 50),
            "stall_detection_window": self._settings.get("stall_detection_window", 5),
            "stall_detection_threshold": self._settings.get("stall_detection_threshold", 0.01),
        }

    @property
    def learning(self) -> Dict[str, Any]:
        """Learning configuration."""
        return {
            "decay_rate": self._settings.get("learning_decay_rate", 0.1),
            "min_relevance": self._settings.get("learning_min_relevance", 0.1),
        }

    @property
    def rollback(self) -> Dict[str, Any]:
        """Rollback configuration."""
        return {
            "threshold": self._settings.get("rollback_threshold", 0.1),
        }

    @property
    def conflict_resolution(self) -> Dict[str, Any]:
        """Conflict resolution configuration."""
        return {
            "credibility_decay_rate": self._settings.get("credibility_decay_rate", 0.01),
        }

    @property
    def dispatch(self) -> Dict[str, Any]:
        """Dispatch configuration."""
        return {
            "per_agent_timeout": self._settings.get("per_agent_timeout", 300),
            "circuit_breaker_threshold": self._settings.get("circuit_breaker_threshold", 3),
            "circuit_breaker_recovery_timeout": self._settings.get("circuit_breaker_recovery_timeout", 60),
        }

    @property
    def language_detection(self) -> Dict[str, Any]:
        """Language detection configuration."""
        return {
            "min_files_for_dispatch": self._settings.get("min_files_for_dispatch", 1),
            "max_cache_size": self._settings.get("max_cache_size", 100),
        }

    @property
    def organization(self) -> Dict[str, Any]:
        """Organization configuration."""
        return {
            "org_id": self._settings.get("org_id", "default"),
            "max_learnings": self._settings.get("org_max_learnings", 1000),
            "relevance_threshold": self._settings.get("org_relevance_threshold", 0.7),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self._settings.set(key, value)

    def as_dict(self) -> Dict[str, Any]:
        """Get all settings as a dictionary.
        
        Returns:
            Dictionary of all settings
        """
        return dict(self._settings)


# Global config instance
config = Config()
