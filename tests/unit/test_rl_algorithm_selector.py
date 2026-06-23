"""Tests for RLAlgorithmSelector - adaptive algorithm selection."""

import pytest

from semar.agents.rl_algorithm_selector import RLAlgorithm, RLAlgorithmSelector


@pytest.fixture
def selector():
    return RLAlgorithmSelector()


@pytest.mark.asyncio
async def test_select_ppo_for_dense_step_rewards(selector):
    analysis = {"metrics": {"reward_structure": {"dense_step_level": True}}}
    result = await selector.select(analysis)
    assert result == RLAlgorithm.PPO_GAE


@pytest.mark.asyncio
async def test_select_grpo_for_cheap_rollouts(selector):
    analysis = {
        "metrics": {
            "reward_structure": {
                "cheap_rollouts": True,
                "episode_end_verifier": True,
            }
        }
    }
    result = await selector.select(analysis)
    assert result == RLAlgorithm.GRPO


@pytest.mark.asyncio
async def test_select_entropic_for_right_skewed(selector):
    analysis = {"metrics": {"reward_structure": {"right_skewed": True}}}
    result = await selector.select(analysis)
    assert result == RLAlgorithm.ENTROPIC_ADVANTAGE


@pytest.mark.asyncio
async def test_select_reinforce_for_dense_with_regression_risk(selector):
    analysis = {"metrics": {"reward_structure": {"dense": True, "regression_risk": True}}}
    result = await selector.select(analysis)
    assert result == RLAlgorithm.REINFORCE_KL


@pytest.mark.asyncio
async def test_select_best_of_nn_for_sparse(selector):
    analysis = {"metrics": {"reward_structure": {"extremely_sparse": True}}}
    result = await selector.select(analysis)
    assert result == RLAlgorithm.BEST_OF_NN


@pytest.mark.asyncio
async def test_select_dpo_for_ranking_only(selector):
    analysis = {"metrics": {"reward_structure": {"ranking_only": True}}}
    result = await selector.select(analysis)
    assert result == RLAlgorithm.DPO


@pytest.mark.asyncio
async def test_select_default_grpo(selector):
    analysis = {"metrics": {"reward_structure": {}}}
    result = await selector.select(analysis)
    assert result == RLAlgorithm.GRPO


@pytest.mark.asyncio
async def test_select_with_empty_analysis(selector):
    result = await selector.select({})
    assert result == RLAlgorithm.GRPO


class TestRLAlgorithm:
    def test_all_algorithms(self):
        algorithms = [
            RLAlgorithm.PPO_GAE,
            RLAlgorithm.GRPO,
            RLAlgorithm.ENTROPIC_ADVANTAGE,
            RLAlgorithm.REINFORCE_KL,
            RLAlgorithm.BEST_OF_NN,
            RLAlgorithm.DPO,
        ]
        assert len(algorithms) == 6
        values = [a.value for a in algorithms]
        assert len(set(values)) == 6  # All unique
