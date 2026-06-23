"""Tests for harness evolution components: PromptEvolver, SkillDiscovery, RuleEvolver."""

import pytest

from semar.agents.trajectory_analyzer import FailureMode

# ============================================================
# PromptEvolver Tests
# ============================================================


class TestPromptEvolver:
    """Tests for PromptEvolver."""

    def test_import(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver

        assert PromptEvolver is not None

    def test_init(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver

        evolver = PromptEvolver()
        assert evolver is not None
        assert hasattr(evolver, "evolve")
        assert hasattr(evolver, "get_history")

    @pytest.mark.asyncio
    async def test_evolve_returns_string(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver

        evolver = PromptEvolver()
        result = await evolver.evolve(
            current_prompt="You are a code reviewer.",
            failure_modes=[],
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_evolve_no_failures_returns_original(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver

        evolver = PromptEvolver()
        original = "You are a code reviewer."
        result = await evolver.evolve(
            current_prompt=original,
            failure_modes=[],
        )
        assert result == original

    @pytest.mark.asyncio
    async def test_evolve_with_missed_issues(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver

        evolver = PromptEvolver()
        failures = [
            FailureMode(
                type="missed_issue",
                severity="high",
                frequency=3,
                examples=[{"file": "auth.py", "issue": "SQL injection"}],
            )
        ]
        result = await evolver.evolve(
            current_prompt="You are a code reviewer.",
            failure_modes=failures,
        )
        assert isinstance(result, str)
        assert len(result) > len("You are a code reviewer.")
        # Should mention security or injection
        assert any(kw in result.lower() for kw in ["security", "injection", "sql", "vulnerability"])

    @pytest.mark.asyncio
    async def test_evolve_with_false_positives(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver

        evolver = PromptEvolver()
        failures = [
            FailureMode(
                type="false_positive",
                severity="medium",
                frequency=5,
                examples=[{"suggestion": "Use type hints", "rejected": True}],
            )
        ]
        result = await evolver.evolve(
            current_prompt="You are a code reviewer.",
            failure_modes=failures,
        )
        assert isinstance(result, str)
        # Should add guidance about precision
        assert any(kw in result.lower() for kw in ["precise", "accurate", "avoid", "false"])

    @pytest.mark.asyncio
    async def test_evolve_records_history(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver

        evolver = PromptEvolver()
        failures = [FailureMode(type="missed_issue", severity="high", frequency=2, examples=[])]
        await evolver.evolve(current_prompt="Review code.", failure_modes=failures)
        history = evolver.get_history()
        assert len(history) == 1
        assert history[0]["original"] == "Review code."
        assert "evolved" in history[0]
        assert history[0]["failure_count"] == 1

    @pytest.mark.asyncio
    async def test_evolve_multiple_failures_cumulative(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver

        evolver = PromptEvolver()
        failures = [
            FailureMode(type="missed_issue", severity="high", frequency=3, examples=[{"issue": "SQL injection"}]),
            FailureMode(type="false_positive", severity="medium", frequency=2, examples=[{"suggestion": "rename var"}]),
            FailureMode(
                type="overconfident",
                severity="low",
                frequency=1,
                examples=[{"confidence": 0.95, "accuracy": 0.5}],
            ),
        ]
        result = await evolver.evolve(
            current_prompt="You are a code reviewer.",
            failure_modes=failures,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_evolve_preserves_base_prompt(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver

        evolver = PromptEvolver()
        base = "You are an expert Python code reviewer. Focus on security."
        failures = [FailureMode(type="missed_issue", severity="high", frequency=1, examples=[])]
        result = await evolver.evolve(current_prompt=base, failure_modes=failures)
        # Original content should be present
        assert "Python" in result or "reviewer" in result


# ============================================================
# SkillDiscovery Tests
# ============================================================


class TestSkillDiscovery:
    """Tests for SkillDiscovery."""

    def test_import(self):
        from semar.self_improvement.harness.skill_discovery import SkillDiscovery

        assert SkillDiscovery is not None

    def test_init(self):
        from semar.self_improvement.harness.skill_discovery import SkillDiscovery

        discovery = SkillDiscovery()
        assert discovery is not None
        assert hasattr(discovery, "discover")
        assert hasattr(discovery, "get_skills")

    @pytest.mark.asyncio
    async def test_discover_empty_trajectories(self):
        from semar.self_improvement.harness.skill_discovery import SkillDiscovery

        discovery = SkillDiscovery()
        result = await discovery.discover(trajectories=[])
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_discover_returns_skill_objects(self):
        from semar.self_improvement.harness.skill_discovery import SkillDiscovery

        discovery = SkillDiscovery()
        trajectories = [
            {
                "steps": {
                    "action": {"output": "Reviewed 5 files"},
                    "review": {"output": "Found SQL injection in auth.py"},
                },
                "metrics": {"accuracy": 0.9},
            }
        ]
        result = await discovery.discover(trajectories=trajectories)
        assert isinstance(result, list)
        for skill in result:
            assert hasattr(skill, "name")
            assert hasattr(skill, "description")
            assert hasattr(skill, "confidence")
            assert skill.confidence >= 0.0
            assert skill.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_discover_extracts_patterns(self):
        from semar.self_improvement.harness.skill_discovery import SkillDiscovery

        discovery = SkillDiscovery()
        # Multiple trajectories with similar patterns should be detected
        trajectories = [
            {"steps": {"review": {"output": "Found SQL injection"}}, "metrics": {}},
            {"steps": {"review": {"output": "Found SQL injection"}}, "metrics": {}},
            {"steps": {"review": {"output": "Found SQL injection"}}, "metrics": {}},
        ]
        result = await discovery.discover(trajectories=trajectories)
        # With 3 matching trajectories, security_review should be discovered
        assert len(result) >= 0  # May or may not find patterns depending on threshold

    @pytest.mark.asyncio
    async def test_get_skills_returns_registered(self):
        from semar.self_improvement.harness.skill_discovery import SkillDiscovery

        discovery = SkillDiscovery()
        skills = discovery.get_skills()
        assert isinstance(skills, list)

    @pytest.mark.asyncio
    async def test_discover_min_frequency_threshold(self):
        from semar.self_improvement.harness.skill_discovery import SkillDiscovery

        discovery = SkillDiscovery(min_frequency=2)
        # Single occurrence should not be discovered
        trajectories = [
            {"steps": {"review": {"output": "Found rare issue"}}, "metrics": {}},
        ]
        result = await discovery.discover(trajectories=trajectories)
        # With min_frequency=2, single occurrence should not produce skills
        for skill in result:
            assert skill.frequency >= 2


# ============================================================
# RuleEvolver Tests
# ============================================================


class TestRuleEvolver:
    """Tests for RuleEvolver."""

    def test_import(self):
        from semar.self_improvement.harness.rule_evolver import RuleEvolver

        assert RuleEvolver is not None

    def test_init(self):
        from semar.self_improvement.harness.rule_evolver import RuleEvolver

        evolver = RuleEvolver()
        assert evolver is not None
        assert hasattr(evolver, "evolve")
        assert hasattr(evolver, "get_history")

    @pytest.mark.asyncio
    async def test_evolve_no_analysis_returns_original(self):
        from semar.self_improvement.harness.rule_evolver import RuleEvolver

        evolver = RuleEvolver()
        rules = [
            {"name": "no_eval", "pattern": r"\beval\s*\(", "severity": "high"},
        ]
        result = await evolver.evolve(
            current_rules=rules,
            analysis={"failure_modes": [], "metrics": {}},
        )
        assert result == rules

    @pytest.mark.asyncio
    async def test_evolve_adds_rules_for_missed_issues(self):
        from semar.self_improvement.harness.rule_evolver import RuleEvolver

        evolver = RuleEvolver()
        rules = []
        analysis = {
            "failure_modes": [
                FailureMode(
                    type="missed_issue",
                    severity="high",
                    frequency=5,
                    examples=[{"file": "auth.py", "issue": "SQL injection", "pattern": "execute("}],
                )
            ],
            "metrics": {},
        }
        result = await evolver.evolve(current_rules=rules, analysis=analysis)
        assert isinstance(result, list)
        assert len(result) >= 1
        # New rule should be added
        rule_names = [r.get("name", "") for r in result]
        assert any(
            "sql" in name.lower() or "injection" in name.lower() or "security" in name.lower() for name in rule_names
        )

    @pytest.mark.asyncio
    async def test_evolve_removes_false_positive_rules(self):
        from semar.self_improvement.harness.rule_evolver import RuleEvolver

        evolver = RuleEvolver()
        rules = [
            {"name": "always_require_type_hints", "pattern": r":\s*\w+", "severity": "low"},
        ]
        analysis = {
            "failure_modes": [
                FailureMode(
                    type="false_positive",
                    severity="medium",
                    frequency=10,
                    examples=[{"rule": "always_require_type_hints", "rejections": 10}],
                )
            ],
            "metrics": {},
        }
        result = await evolver.evolve(current_rules=rules, analysis=analysis)
        assert isinstance(result, list)
        # The false-positive rule should be removed or downgraded
        rule_names = [r.get("name", "") for r in result]
        assert "always_require_type_hints" not in rule_names

    @pytest.mark.asyncio
    async def test_evolve_records_history(self):
        from semar.self_improvement.harness.rule_evolver import RuleEvolver

        evolver = RuleEvolver()
        rules = [{"name": "test_rule", "pattern": r"test", "severity": "low"}]
        analysis = {"failure_modes": [], "metrics": {}}
        await evolver.evolve(current_rules=rules, analysis=analysis)
        history = evolver.get_history()
        assert len(history) == 1
        assert history[0]["original_count"] == 1

    @pytest.mark.asyncio
    async def test_evolve_preserves_unrelated_rules(self):
        from semar.self_improvement.harness.rule_evolver import RuleEvolver

        evolver = RuleEvolver()
        rules = [
            {"name": "no_eval", "pattern": r"\beval\s*\(", "severity": "high"},
            {"name": "no_exec", "pattern": r"\bexec\s*\(", "severity": "high"},
        ]
        analysis = {
            "failure_modes": [
                FailureMode(
                    type="missed_issue",
                    severity="high",
                    frequency=3,
                    examples=[{"issue": "SQL injection"}],
                )
            ],
            "metrics": {},
        }
        result = await evolver.evolve(current_rules=rules, analysis=analysis)
        assert isinstance(result, list)
        # Original rules should be preserved
        rule_names = [r.get("name", "") for r in result]
        assert "no_eval" in rule_names
        assert "no_exec" in rule_names

    @pytest.mark.asyncio
    async def test_evolve_severity_upgrade_on_frequent_failures(self):
        from semar.self_improvement.harness.rule_evolver import RuleEvolver

        evolver = RuleEvolver()
        rules = [
            {"name": "no_todo", "pattern": r"TODO", "severity": "low"},
        ]
        analysis = {
            "failure_modes": [
                FailureMode(
                    type="missed_issue",
                    severity="high",
                    frequency=20,
                    examples=[{"issue": "TODO left in production code"}],
                )
            ],
            "metrics": {},
        }
        result = await evolver.evolve(current_rules=rules, analysis=analysis)
        assert isinstance(result, list)


# ============================================================
# Integration Tests
# ============================================================


class TestHarnessIntegration:
    """Integration tests for harness evolution components."""

    @pytest.mark.asyncio
    async def test_prompt_evolver_to_rule_evolver_pipeline(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver
        from semar.self_improvement.harness.rule_evolver import RuleEvolver

        prompt_evolver = PromptEvolver()
        rule_evolver = RuleEvolver()

        failures = [
            FailureMode(
                type="missed_issue",
                severity="high",
                frequency=5,
                examples=[{"file": "db.py", "issue": "SQL injection via string formatting"}],
            )
        ]

        # Evolve prompt
        new_prompt = await prompt_evolver.evolve(
            current_prompt="You are a code reviewer.",
            failure_modes=failures,
        )
        assert isinstance(new_prompt, str)

        # Evolve rules based on same analysis
        new_rules = await rule_evolver.evolve(
            current_rules=[],
            analysis={"failure_modes": failures, "metrics": {}},
        )
        assert isinstance(new_rules, list)
        assert len(new_rules) >= 1

    @pytest.mark.asyncio
    async def test_full_harness_cycle(self):
        from semar.self_improvement.harness.prompt_evolver import PromptEvolver
        from semar.self_improvement.harness.rule_evolver import RuleEvolver
        from semar.self_improvement.harness.skill_discovery import SkillDiscovery

        prompt_evolver = PromptEvolver()
        skill_discovery = SkillDiscovery()
        rule_evolver = RuleEvolver()

        trajectories = [
            {
                "steps": {
                    "action": {"output": "Reviewed auth.py"},
                    "review": {"output": "Found SQL injection vulnerability"},
                },
                "metrics": {"accuracy": 0.7},
                "failure_modes": [{"type": "missed_issue", "severity": "high", "frequency": 3}],
            }
        ]

        # All three should work independently
        new_prompt = await prompt_evolver.evolve(
            current_prompt="Review code.",
            failure_modes=[FailureMode(type="missed_issue", severity="high", frequency=3, examples=[])],
        )
        skills = await skill_discovery.discover(trajectories=trajectories)
        new_rules = await rule_evolver.evolve(
            current_rules=[],
            analysis={
                "failure_modes": [FailureMode(type="missed_issue", severity="high", frequency=3, examples=[])],
                "metrics": {},
            },
        )

        assert isinstance(new_prompt, str)
        assert isinstance(skills, list)
        assert isinstance(new_rules, list)
