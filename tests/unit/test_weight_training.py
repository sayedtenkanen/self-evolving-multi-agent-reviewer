"""Tests for weight training components: LoRATrainer, RL algorithms, DataPipeline, RewardSignals."""

import pytest

# ============================================================
# LoRATrainer Tests
# ============================================================


class TestLoRATrainer:
    """Tests for LoRATrainer."""

    def test_import(self):
        from semar.self_improvement.weight_training.lora_trainer import LoRATrainer

        assert LoRATrainer is not None

    def test_init_defaults(self):
        from semar.self_improvement.weight_training.lora_trainer import LoRATrainer

        trainer = LoRATrainer()
        assert trainer.rank == 32
        assert trainer.base_model == "meta-llama/Llama-3-70b"

    def test_init_custom(self):
        from semar.self_improvement.weight_training.lora_trainer import LoRATrainer

        trainer = LoRATrainer(base_model="custom/model", rank=16, output_dir="/tmp/ckpts")
        assert trainer.base_model == "custom/model"
        assert trainer.rank == 16
        assert str(trainer.output_dir) == "/tmp/ckpts"

    @pytest.mark.asyncio
    async def test_train_returns_checkpoint_path(self):
        from semar.self_improvement.weight_training.lora_trainer import LoRATrainer

        trainer = LoRATrainer()
        result = await trainer.train(
            algorithm="ppo_gae",
            training_data={"trajectories": [], "rewards": []},
            hyperparams={"lr": 1e-4, "epochs": 1},
        )
        assert result is not None
        assert hasattr(result, "algorithm")
        assert result.algorithm == "ppo_gae"

    @pytest.mark.asyncio
    async def test_train_stores_history(self):
        from semar.self_improvement.weight_training.lora_trainer import LoRATrainer

        trainer = LoRATrainer()
        await trainer.train(
            algorithm="grpo",
            training_data={"trajectories": [], "rewards": []},
            hyperparams={},
        )
        history = trainer.get_history()
        assert len(history) == 1
        assert history[0]["algorithm"] == "grpo"

    @pytest.mark.asyncio
    async def test_validate_data_empty(self):
        from semar.self_improvement.weight_training.lora_trainer import LoRATrainer

        trainer = LoRATrainer()
        result = await trainer.validate_data({"trajectories": [], "rewards": []})
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_data_valid(self):
        from semar.self_improvement.weight_training.lora_trainer import LoRATrainer

        trainer = LoRATrainer()
        data = {
            "trajectories": [{"steps": {}, "metrics": {}}],
            "rewards": [1.0],
        }
        result = await trainer.validate_data(data)
        assert result.is_valid is True


# ============================================================
# BaseAlgorithm Tests
# ============================================================


class TestBaseAlgorithm:
    """Tests for BaseAlgorithm interface."""

    def test_import(self):
        from semar.self_improvement.weight_training.algorithms.base_algorithm import BaseAlgorithm

        assert BaseAlgorithm is not None

    def test_is_abstract(self):
        from semar.self_improvement.weight_training.algorithms.base_algorithm import BaseAlgorithm

        with pytest.raises(TypeError):
            BaseAlgorithm()


# ============================================================
# PPO_GAE Tests
# ============================================================


class TestPPOGAE:
    """Tests for PPO with GAE algorithm."""

    def test_import(self):
        from semar.self_improvement.weight_training.algorithms.ppo_gae import PPOGAE

        assert PPOGAE is not None

    def test_init(self):
        from semar.self_improvement.weight_training.algorithms.ppo_gae import PPOGAE

        algo = PPOGAE()
        assert algo.name == "ppo_gae"

    @pytest.mark.asyncio
    async def test_compute_gae(self):
        from semar.self_improvement.weight_training.algorithms.ppo_gae import PPOGAE

        algo = PPOGAE()
        rewards = [1.0, 0.5, 0.8]
        values = [0.9, 0.6, 0.7, 0.0]
        advantages = algo.compute_gae(rewards, values)
        assert len(advantages) == 3
        assert all(isinstance(a, float) for a in advantages)

    @pytest.mark.asyncio
    async def test_train_returns_metrics(self):
        from semar.self_improvement.weight_training.algorithms.ppo_gae import PPOGAE

        algo = PPOGAE()
        result = await algo.train(
            trajectories=[{"rewards": [1.0, 0.5], "values": [0.9, 0.6, 0.0]}],
            hyperparams={"lr": 1e-4, "clip_epsilon": 0.2, "gamma": 0.99, "lam": 0.95},
        )
        assert "loss" in result
        assert "advantages" in result


# ============================================================
# GRPO Tests
# ============================================================


class TestGRPO:
    """Tests for GRPO algorithm."""

    def test_import(self):
        from semar.self_improvement.weight_training.algorithms.grpo import GRPO

        assert GRPO is not None

    def test_init(self):
        from semar.self_improvement.weight_training.algorithms.grpo import GRPO

        algo = GRPO()
        assert algo.name == "grpo"

    @pytest.mark.asyncio
    async def test_train_returns_metrics(self):
        from semar.self_improvement.weight_training.algorithms.grpo import GRPO

        algo = GRPO()
        result = await algo.train(
            trajectories=[{"rewards": [1.0, 0.5]}],
            hyperparams={"lr": 1e-4, "kl_coeff": 0.1},
        )
        assert "loss" in result


# ============================================================
# EntropicAdvantage Tests
# ============================================================


class TestEntropicAdvantage:
    """Tests for Entropic Advantage algorithm."""

    def test_import(self):
        from semar.self_improvement.weight_training.algorithms.entropic_advantage import EntropicAdvantage

        assert EntropicAdvantage is not None

    def test_init(self):
        from semar.self_improvement.weight_training.algorithms.entropic_advantage import EntropicAdvantage

        algo = EntropicAdvantage()
        assert algo.name == "entropic_advantage"

    @pytest.mark.asyncio
    async def test_train_returns_metrics(self):
        from semar.self_improvement.weight_training.algorithms.entropic_advantage import EntropicAdvantage

        algo = EntropicAdvantage()
        result = await algo.train(
            trajectories=[{"rewards": [0.0, 0.0, 1.0]}],
            hyperparams={"lr": 1e-4, "entropy_coeff": 0.01},
        )
        assert "loss" in result


# ============================================================
# REINFORCE_KL Tests
# ============================================================


class TestREINFORCEKL:
    """Tests for REINFORCE + KL algorithm."""

    def test_import(self):
        from semar.self_improvement.weight_training.algorithms.reinforce_kl import REINFORCEKL

        assert REINFORCEKL is not None

    def test_init(self):
        from semar.self_improvement.weight_training.algorithms.reinforce_kl import REINFORCEKL

        algo = REINFORCEKL()
        assert algo.name == "reinforce_kl"

    @pytest.mark.asyncio
    async def test_train_returns_metrics(self):
        from semar.self_improvement.weight_training.algorithms.reinforce_kl import REINFORCEKL

        algo = REINFORCEKL()
        result = await algo.train(
            trajectories=[{"rewards": [1.0, 0.5]}],
            hyperparams={"lr": 1e-4, "kl_coeff": 0.1},
        )
        assert "loss" in result


# ============================================================
# BestOfNN Tests
# ============================================================


class TestBestOfNN:
    """Tests for Best-of-N algorithm."""

    def test_import(self):
        from semar.self_improvement.weight_training.algorithms.best_of_nn import BestOfNN

        assert BestOfNN is not None

    def test_init(self):
        from semar.self_improvement.weight_training.algorithms.best_of_nn import BestOfNN

        algo = BestOfNN()
        assert algo.name == "best_of_nn"

    @pytest.mark.asyncio
    async def test_select_best(self):
        from semar.self_improvement.weight_training.algorithms.best_of_nn import BestOfNN

        algo = BestOfNN()
        candidates = [
            {"reward": 0.5, "output": "a"},
            {"reward": 0.9, "output": "b"},
            {"reward": 0.3, "output": "c"},
        ]
        result = algo.select_best(candidates)
        assert result["output"] == "b"
        assert result["reward"] == 0.9

    @pytest.mark.asyncio
    async def test_train_returns_metrics(self):
        from semar.self_improvement.weight_training.algorithms.best_of_nn import BestOfNN

        algo = BestOfNN()
        result = await algo.train(
            trajectories=[
                {"candidates": [{"reward": 0.5}, {"reward": 0.9}], "best_idx": 1},
            ],
            hyperparams={"n_candidates": 4},
        )
        assert "loss" in result


# ============================================================
# DPO Tests
# ============================================================


class TestDPO:
    """Tests for DPO algorithm."""

    def test_import(self):
        from semar.self_improvement.weight_training.algorithms.dpo import DPO

        assert DPO is not None

    def test_init(self):
        from semar.self_improvement.weight_training.algorithms.dpo import DPO

        algo = DPO()
        assert algo.name == "dpo"

    @pytest.mark.asyncio
    async def test_train_returns_metrics(self):
        from semar.self_improvement.weight_training.algorithms.dpo import DPO

        algo = DPO()
        result = await algo.train(
            trajectories=[
                {
                    "preferred": {"output": "good", "reward": 1.0},
                    "rejected": {"output": "bad", "reward": 0.0},
                }
            ],
            hyperparams={"lr": 1e-4, "beta": 0.1},
        )
        assert "loss" in result


# ============================================================
# DataPipeline Tests
# ============================================================


class TestDataPipeline:
    """Tests for DataPipeline."""

    def test_import(self):
        from semar.self_improvement.weight_training.data_pipeline import DataPipeline

        assert DataPipeline is not None

    def test_init(self):
        from semar.self_improvement.weight_training.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        assert pipeline is not None
        assert hasattr(pipeline, "collect")
        assert hasattr(pipeline, "process")

    @pytest.mark.asyncio
    async def test_collect_empty(self):
        from semar.self_improvement.weight_training.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        result = await pipeline.collect(trajectories=[])
        assert result.count == 0

    @pytest.mark.asyncio
    async def test_collect_with_trajectories(self):
        from semar.self_improvement.weight_training.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        trajectories = [
            {"steps": {"action": {"output": "reviewed"}}, "metrics": {"reward": 0.8}},
            {"steps": {"action": {"output": "reviewed"}}, "metrics": {"reward": 0.6}},
        ]
        result = await pipeline.collect(trajectories=trajectories)
        assert result.count == 2
        assert len(result.data) == 2

    @pytest.mark.asyncio
    async def test_process_filters_invalid(self):
        from semar.self_improvement.weight_training.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        data = [
            {"valid": True, "reward": 0.8},
            {"valid": False, "reward": None},
            {"valid": True, "reward": 0.6},
        ]
        result = await pipeline.process(data)
        assert result.count == 2

    @pytest.mark.asyncio
    async def test_split_train_validation(self):
        from semar.self_improvement.weight_training.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        data = list(range(100))
        train, val = pipeline.split(data, val_ratio=0.2)
        assert len(train) == 80
        assert len(val) == 20


# ============================================================
# RewardSignals Tests
# ============================================================


class TestRewardSignals:
    """Tests for RewardSignals."""

    def test_import(self):
        from semar.self_improvement.weight_training.reward_signals.human_feedback import HumanFeedbackReward
        from semar.self_improvement.weight_training.reward_signals.outcome_based import OutcomeBasedReward

        assert OutcomeBasedReward is not None
        assert HumanFeedbackReward is not None

    def test_outcome_based_init(self):
        from semar.self_improvement.weight_training.reward_signals.outcome_based import OutcomeBasedReward

        reward = OutcomeBasedReward()
        assert reward is not None

    @pytest.mark.asyncio
    async def test_outcome_based_compute(self):
        from semar.self_improvement.weight_training.reward_signals.outcome_based import OutcomeBasedReward

        reward = OutcomeBasedReward()
        result = await reward.compute(
            trajectory={"metrics": {"accuracy": 0.9, "false_positives": 1}},
        )
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_human_feedback_init(self):
        from semar.self_improvement.weight_training.reward_signals.human_feedback import HumanFeedbackReward

        reward = HumanFeedbackReward()
        assert reward is not None

    @pytest.mark.asyncio
    async def test_human_feedback_compute(self):
        from semar.self_improvement.weight_training.reward_signals.human_feedback import HumanFeedbackReward

        reward = HumanFeedbackReward()
        result = await reward.compute(
            trajectory={"human_feedback": {"accepted": 5, "rejected": 1}},
        )
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


# ============================================================
# Integration Tests
# ============================================================


class TestWeightTrainingIntegration:
    """Integration tests for weight training components."""

    @pytest.mark.asyncio
    async def test_algorithm_selection_to_training_pipeline(self):
        from semar.self_improvement.weight_training.algorithms.grpo import GRPO
        from semar.self_improvement.weight_training.lora_trainer import LoRATrainer

        trainer = LoRATrainer()
        algo = GRPO()

        # Simulate training
        train_result = await algo.train(
            trajectories=[{"rewards": [1.0, 0.5]}],
            hyperparams={"lr": 1e-4},
        )
        assert "loss" in train_result

        # Full pipeline
        result = await trainer.train(
            algorithm="grpo",
            training_data={"trajectories": [], "rewards": []},
            hyperparams={},
        )
        assert result.algorithm == "grpo"

    @pytest.mark.asyncio
    async def test_data_pipeline_to_training(self):
        from semar.self_improvement.weight_training.algorithms.ppo_gae import PPOGAE
        from semar.self_improvement.weight_training.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        algo = PPOGAE()

        trajectories = [
            {"steps": {"action": {"output": "review"}}, "metrics": {"reward": 0.8}},
        ]
        collected = await pipeline.collect(trajectories=trajectories)
        assert collected.count == 1

        train_result = await algo.train(
            trajectories=collected.data,
            hyperparams={"lr": 1e-4, "gamma": 0.99, "lam": 0.95},
        )
        assert "loss" in train_result

    @pytest.mark.asyncio
    async def test_reward_signal_to_data_pipeline(self):
        from semar.self_improvement.weight_training.data_pipeline import DataPipeline
        from semar.self_improvement.weight_training.reward_signals.outcome_based import OutcomeBasedReward

        reward_signal = OutcomeBasedReward()
        pipeline = DataPipeline()

        trajectory = {"metrics": {"accuracy": 0.9, "false_positives": 1}}
        reward = await reward_signal.compute(trajectory=trajectory)
        assert 0.0 <= reward <= 1.0

        enriched = {**trajectory, "computed_reward": reward}
        collected = await pipeline.collect(trajectories=[enriched])
        assert collected.count == 1
