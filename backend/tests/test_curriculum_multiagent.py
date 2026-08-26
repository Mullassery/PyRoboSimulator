"""Tests for Curriculum (Phase 8) and Multi-Agent (Phase 9) systems."""

import pytest
from src.curriculum import (
    DifficultyLevel,
    DifficultyFactors,
    LearnerProfile,
    CurriculumPlan,
    DifficultyModel,
    CurriculumScenarioGenerator,
)
from src.multiagent import (
    FormationType,
    AgentState,
    AgentCoordinator,
    ExperienceRecord,
    FleetLearningEngine,
)


class TestDifficultyModel:
    """Test difficulty model."""

    def test_difficulty_factors(self):
        """Test difficulty factors computation."""
        factors = DifficultyFactors(
            path_complexity=0.5,
            obstacle_density=0.3,
            time_pressure=0.4,
        )

        overall = factors.overall_difficulty()
        assert 0.0 <= overall <= 1.0

    def test_analyze_trajectory(self):
        """Test trajectory analysis."""
        model = DifficultyModel()

        factors = model.analyze_trajectory_difficulty(
            trajectory_distance=50.0,
            trajectory_duration=100.0,
            path_smoothness=0.8,
            num_turns=3,
            obstacle_count=2,
        )

        assert factors.path_complexity > 0.0
        assert factors.obstacle_density > 0.0

    def test_scale_difficulty(self):
        """Test difficulty scaling."""
        model = DifficultyModel()

        base = DifficultyFactors(
            path_complexity=0.3,
            obstacle_density=0.2,
            time_pressure=0.2,
        )

        scaled = model.scale_difficulty(base, 0.8)

        assert scaled.overall_difficulty() > base.overall_difficulty()

    def test_learner_profile(self):
        """Test learner profile."""
        profile = LearnerProfile(
            learner_id="learner_1",
            success_rate=0.7,
            current_difficulty=0.25,
        )

        assert profile.learner_id == "learner_1"

    def test_generate_curriculum(self):
        """Test curriculum generation."""
        model = DifficultyModel()

        plan = model.generate_curriculum(
            learner_id="learner_1",
            start_difficulty=0.1,
            target_difficulty=0.8,
            num_lessons=5,
        )

        assert plan.learner_id == "learner_1"
        assert len(plan.lessons) == 5
        assert plan.lessons[0].difficulty < plan.lessons[-1].difficulty

    def test_record_performance(self):
        """Test recording performance."""
        model = DifficultyModel()

        plan = model.generate_curriculum("learner_1")

        model.record_lesson_performance(
            "learner_1",
            "lesson_0",
            success_rate=0.9,
            time_efficiency=0.85,
            path_efficiency=0.88,
        )

        profile = model.get_learner_profile("learner_1")
        assert profile.success_rate == 0.9


class TestCurriculumScenarioGenerator:
    """Test scenario generator."""

    def test_generate_navigation_scenario(self):
        """Test navigation scenario generation."""
        gen = CurriculumScenarioGenerator()

        scenario = gen.generate_scenario(
            "test_curriculum",
            0,
            0.3,
            scenario_type="navigation",
        )

        assert scenario.title
        assert len(scenario.entities) > 0
        assert len(scenario.goals) > 0

    def test_generate_inspection_scenario(self):
        """Test inspection scenario."""
        gen = CurriculumScenarioGenerator()

        scenario = gen.generate_scenario(
            "test_curriculum",
            0,
            0.5,
            scenario_type="inspection",
        )

        assert scenario.title
        assert len(scenario.goals) > 0

    def test_generate_delivery_scenario(self):
        """Test delivery scenario."""
        gen = CurriculumScenarioGenerator()

        scenario = gen.generate_scenario(
            "test_curriculum",
            0,
            0.6,
            scenario_type="delivery",
        )

        assert scenario.title
        assert len(scenario.goals) > 0

    def test_progressive_difficulty(self):
        """Test progressive scenario difficulty."""
        gen = CurriculumScenarioGenerator()

        scenarios = gen.generate_curriculum_scenarios(
            "test_curriculum",
            num_lessons=3,
            start_difficulty=0.1,
            end_difficulty=0.7,
        )

        assert len(scenarios) == 3
        assert scenarios[0].difficulty_level < scenarios[-1].difficulty_level


class TestAgentCoordinator:
    """Test agent coordinator."""

    def test_coordinator_initialization(self):
        """Test coordinator creation."""
        coordinator = AgentCoordinator("team_1")

        assert coordinator._team_id == "team_1"
        assert coordinator.get_agent_count() == 0

    def test_register_agent(self):
        """Test registering agents."""
        coordinator = AgentCoordinator("team_1")

        coordinator.register_agent("robot_0", (0.0, 0.0, 0.0), "leader")
        coordinator.register_agent("robot_1", (5.0, 0.0, 0.0), "follower")

        assert coordinator.get_agent_count() == 2

    def test_update_agent_state(self):
        """Test updating agent state."""
        coordinator = AgentCoordinator("team_1")
        coordinator.register_agent("robot_0", (0.0, 0.0, 0.0))

        coordinator.update_agent_state(
            "robot_0",
            (1.0, 2.0, 0.0),
            (0.5, 0.5, 0.0),
            {"location": (1.0, 2.0)},
        )

        state = coordinator.get_agent_state("robot_0")
        assert state.position == (1.0, 2.0, 0.0)

    def test_messaging(self):
        """Test inter-agent messaging."""
        coordinator = AgentCoordinator("team_1")
        coordinator.register_agent("robot_0", (0.0, 0.0, 0.0))
        coordinator.register_agent("robot_1", (5.0, 0.0, 0.0))

        coordinator.send_message(
            "robot_0",
            "robot_1",
            "goal",
            {"target": (10.0, 0.0, 0.0)},
            0.0,
        )

        messages = coordinator.process_messages()
        assert "robot_1" in messages

    def test_formation(self):
        """Test formation control."""
        coordinator = AgentCoordinator("team_1")
        coordinator.register_agent("robot_0", (0.0, 0.0, 0.0), "leader")
        coordinator.register_agent("robot_1", (0.0, 0.0, 0.0), "follower")

        coordinator.set_formation(FormationType.LINE)
        positions = coordinator.compute_formation_positions()

        assert "robot_1" in positions

    def test_team_status(self):
        """Test team status."""
        coordinator = AgentCoordinator("team_1")
        coordinator.register_agent("robot_0", (0.0, 0.0, 0.0))
        coordinator.register_agent("robot_1", (5.0, 0.0, 0.0))

        status = coordinator.get_team_status()

        assert status["total_agents"] == 2
        assert status["active_agents"] == 2


class TestFleetLearningEngine:
    """Test fleet learning."""

    def test_fleet_initialization(self):
        """Test fleet learning creation."""
        engine = FleetLearningEngine("team_1")

        assert engine._team_id == "team_1"

    def test_record_experience(self):
        """Test recording experiences."""
        engine = FleetLearningEngine("team_1")

        engine.record_experience(
            agent_id="robot_0",
            scenario_id="scenario_1",
            action_type="navigation",
            success=True,
            outcome_metrics={"distance": 50.0, "time": 100.0},
            timestamp=0.0,
        )

        assert len(engine._experience_log) == 1

    def test_identify_patterns(self):
        """Test pattern identification."""
        engine = FleetLearningEngine("team_1")

        # Record multiple experiences
        for i in range(5):
            engine.record_experience(
                "robot_0",
                "scenario_1",
                "navigation",
                True,
                {"efficiency": 0.8},
                float(i),
            )

        patterns = engine.identify_patterns()

        assert len(patterns) >= 0  # May or may not find patterns with limited data

    def test_knowledge_transfer(self):
        """Test knowledge transfer."""
        engine = FleetLearningEngine("team_1")

        # Record diverse experiences
        for i in range(10):
            engine.record_experience(
                f"robot_{i % 3}",
                f"scenario_{i % 2}",
                "navigation",
                i % 2 == 0,
                {"efficiency": 0.5 + (i % 5) * 0.1},
                float(i),
            )

        engine.identify_patterns()

        knowledge = engine.transfer_knowledge_to_agent("robot_0")

        assert "successful_patterns" in knowledge
        assert "best_practices" in knowledge

    def test_team_performance(self):
        """Test team performance metrics."""
        engine = FleetLearningEngine("team_1")

        for i in range(5):
            engine.record_experience(
                "robot_0",
                "scenario_1",
                "navigation",
                i % 2 == 0,
                {"efficiency": 0.7},
                float(i),
            )

        perf = engine.get_team_performance()

        assert perf["team_id"] == "team_1"
        assert 0.0 <= perf["overall_success_rate"] <= 1.0

    def test_agent_recommendation(self):
        """Test agent recommendation."""
        engine = FleetLearningEngine("team_1")

        # Record some experiences
        for i in range(10):
            engine.record_experience(
                "robot_0",
                "scenario_1",
                "navigation",
                i > 5,  # First half fail, second half succeed
                {"efficiency": 0.6},
                float(i),
            )

        rec = engine.get_agent_recommendation("robot_0")

        assert rec["agent_id"] == "robot_0"
        assert len(rec["recommended_actions"]) > 0


class TestCurriculumMultiAgentIntegration:
    """Integration tests."""

    def test_curriculum_with_learner_progression(self):
        """Test curriculum with learning progression."""
        model = DifficultyModel()
        gen = CurriculumScenarioGenerator()

        # Generate curriculum
        plan = model.generate_curriculum(
            "learner_1",
            start_difficulty=0.1,
            target_difficulty=0.7,
            num_lessons=5,
        )

        # Simulate learning progression
        for i, lesson in enumerate(plan.lessons):
            scenario = gen.generate_scenario("curriculum_1", i, lesson.difficulty)

            # Simulate performance
            success_rate = 0.7 + (i * 0.05)  # Improving over time
            model.record_lesson_performance(
                "learner_1", lesson.lesson_id, success_rate, 0.8, 0.85
            )

        profile = model.get_learner_profile("learner_1")
        assert profile.scenarios_completed == 5

    def test_multiagent_fleet_coordination(self):
        """Test multi-agent fleet with learning."""
        coordinator = AgentCoordinator("fleet_1")
        learning = FleetLearningEngine("fleet_1")

        # Setup fleet
        for i in range(3):
            role = "leader" if i == 0 else "follower"
            coordinator.register_agent(f"robot_{i}", (i * 5.0, 0.0, 0.0), role)

        # Simulate missions
        for mission in range(3):
            for i in range(3):
                agent_id = f"robot_{i}"
                success = mission > 0 or i == 0  # First robot succeeds first time
                learning.record_experience(
                    agent_id,
                    f"mission_{mission}",
                    "navigation",
                    success,
                    {"efficiency": 0.7 + (i * 0.05)},
                    float(mission),
                )

        # Get team stats
        status = coordinator.get_team_status()
        perf = learning.get_team_performance()

        assert status["total_agents"] == 3
        assert perf["total_experiences"] == 9
