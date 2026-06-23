"""RuleEvolver - Optimizes review rules based on trajectory outcomes."""

import time
from typing import Any, Dict, List

from semar.agents.trajectory_analyzer import FailureMode

# Patterns to auto-generate rules for common issues
_AUTO_RULE_TEMPLATES = {
    "sql_injection": {
        "name": "no_sql_injection",
        "pattern": r"(execute|cursor\.execute|query)\s*\(.*(%s|f['\"]|\.format| \+)",
        "severity": "high",
        "description": "Detects potential SQL injection via string formatting",
    },
    "xss_vulnerability": {
        "name": "no_xss",
        "pattern": r"(innerHTML|dangerouslySetInnerHTML|document\.write)\s*\(",
        "severity": "high",
        "description": "Detects potential XSS via innerHTML/document.write",
    },
    "hardcoded_secret": {
        "name": "no_hardcoded_secrets",
        "pattern": r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
        "severity": "high",
        "description": "Detects hardcoded secrets and credentials",
    },
    "eval_usage": {
        "name": "no_eval",
        "pattern": r"\b(eval|exec)\s*\(",
        "severity": "high",
        "description": "Detects use of eval/exec which can execute arbitrary code",
    },
    "todo_fixme": {
        "name": "no_todo_in_prod",
        "pattern": r"\b(TODO|FIXME|HACK|XXX)\b",
        "severity": "low",
        "description": "Detects TODO/FIXME comments that should be resolved",
    },
    "raw_pointer": {
        "name": "no_unsafe_without_comment",
        "pattern": r"\bunsafe\s*\{",
        "severity": "medium",
        "description": "Detects unsafe code blocks that need justification",
    },
}

# Keywords in failure examples that map to rule templates
_EXAMPLE_KEYWORD_TO_RULE = {
    "sql": "sql_injection",
    "injection": "sql_injection",
    "xss": "xss_vulnerability",
    "cross-site": "xss_vulnerability",
    "secret": "hardcoded_secret",
    "password": "hardcoded_secret",
    "api_key": "hardcoded_secret",
    "eval": "eval_usage",
    "exec": "eval_usage",
    "todo": "todo_fixme",
    "fixme": "todo_fixme",
    "unsafe": "raw_pointer",
}


class RuleEvolver:
    """Evolves review rules based on trajectory analysis.

    - Adds rules for missed issues (high-frequency failure patterns)
    - Removes or downgrades rules that cause false positives
    - Preserves unrelated rules
    """

    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    async def evolve(
        self,
        current_rules: List[Dict[str, Any]],
        analysis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Evolve rules based on trajectory analysis.

        Args:
            current_rules: Current list of review rules
            analysis: Output from TrajectoryAnalyzer with failure_modes and metrics

        Returns:
            Updated list of rules
        """
        failure_modes = analysis.get("failure_modes", [])

        if not failure_modes:
            self._history.append(
                {
                    "original_count": len(current_rules),
                    "final_count": len(current_rules),
                    "failure_modes": [],
                    "timestamp": time.time(),
                }
            )
            return list(current_rules)

        result = list(current_rules)
        result_names = {r.get("name", "") for r in result}

        for fm in failure_modes:
            if fm.type == "missed_issue":
                result = self._add_rules_for_missed_issues(result, result_names, fm)
                result_names = {r.get("name", "") for r in result}

            elif fm.type == "false_positive":
                result = self._remove_false_positive_rules(result, fm)

        # Record history
        self._history.append(
            {
                "original_count": len(current_rules),
                "final_count": len(result),
                "failure_modes": [fm.type for fm in failure_modes],
                "timestamp": time.time(),
            }
        )

        return result

    def get_history(self) -> List[Dict[str, Any]]:
        """Get evolution history.

        Returns:
            List of evolution records
        """
        return list(self._history)

    def _add_rules_for_missed_issues(
        self,
        rules: List[Dict[str, Any]],
        existing_names: set,
        failure: FailureMode,
    ) -> List[Dict[str, Any]]:
        """Add rules based on missed issue examples."""
        result = list(rules)

        # Try to match examples to known rule templates
        templates_added = set()
        for example in failure.examples:
            example_str = str(example).lower()
            for keyword, template_key in _EXAMPLE_KEYWORD_TO_RULE.items():
                if keyword in example_str and template_key not in templates_added:
                    template = _AUTO_RULE_TEMPLATES[template_key]
                    if template["name"] not in existing_names:
                        result.append(dict(template))
                        existing_names.add(template["name"])
                        templates_added.add(template_key)

        # If no template matched, add a generic rule based on severity
        if not templates_added:
            generic_name = f"auto_rule_{failure.type}_{failure.severity}"
            if generic_name not in existing_names:
                result.append(
                    {
                        "name": generic_name,
                        "pattern": "(?!)",
                        "severity": failure.severity,
                        "description": f"Auto-generated rule for {failure.type} (frequency: {failure.frequency})",
                    }
                )

        return result

    def _remove_false_positive_rules(
        self,
        rules: List[Dict[str, Any]],
        failure: FailureMode,
    ) -> List[Dict[str, Any]]:
        """Remove or downgrade rules that cause false positives."""
        # Identify which rules are causing false positives
        false_positive_rules = set()
        for example in failure.examples:
            if not isinstance(example, dict):
                continue
            rule_name = example.get("rule", "")
            if rule_name:
                false_positive_rules.add(rule_name)

        result = []
        for rule in rules:
            name = rule.get("name", "")
            if name in false_positive_rules:
                # Remove the rule entirely if it causes many false positives
                if failure.frequency >= 5:
                    continue
                # Otherwise downgrade severity
                downgraded = dict(rule)
                downgraded["severity"] = "low"
                result.append(downgraded)
            else:
                result.append(rule)

        return result
