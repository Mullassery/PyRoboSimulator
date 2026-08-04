"""Tests for Narrative Simulation Engine - Phase 6."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.src.narratives import (
    Narrative,
    NarrativeType,
    NarrativeEntity,
    NarrativeGoal,
    NarrativeEvent,
    NarrativeEventType,
    NarrativeSequence,
    NarrativeConstraint,
    NarrativeExecutionContext,
    AgentRole,
    NarrativeBranch,
    NarrativeConverter,
    NarrativeExecutor,
    AgentBehaviorInterpreter,
    BehaviorPrimitive,
    BehaviorPlan,
    StoryBranchingEngine,
    BranchCondition,
    BranchPath,
    NarrativeValidator,
)


class TestNarrativeDefinitions:
    """Test narrative data structures."""

    def test_narrative_entity_creation(self):
        """Test creating narrative entity."""
        entity = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Delivery Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
            sensor_suite="mobile",
        )

        assert entity.entity_id == "robot_0"
        assert entity.name == "Delivery Robot"
        assert entity.role == AgentRole.PROTAGONIST

    def test_narrative_goal_creation(self):
        """Test creating narrative goal."""
        goal = NarrativeGoal(
            goal_id="goal_0",
            description="Deliver package to location",
            goal_type="reach_location",
            target={"position": [10.0, 5.0, 0.0], "tolerance": 0.5},
            priority=1.0,
            time_limit_sec=300.0,
        )

        assert goal.goal_id == "goal_0"
        assert goal.goal_type == "reach_location"
        assert goal.time_limit_sec == 300.0

    def test_narrative_event_creation(self):
        """Test creating narrative event."""
        event = NarrativeEvent(
            event_id="evt_0",
            event_type=NarrativeEventType.AGENT_ACTION,
            timestamp_sec=10.0,
            description="Robot starts navigation",
            triggering_entity="robot_0",
            affected_entities=["robot_0"],
            confidence=0.95,
        )

        assert event.event_id == "evt_0"
        assert event.event_type == NarrativeEventType.AGENT_ACTION
        assert event.confidence == 0.95

    def test_narrative_sequence_creation(self):
        """Test creating narrative sequence."""
        sequence = NarrativeSequence(
            sequence_id="seq_0",
            name="Navigation Phase",
            description="Robot navigates to destination",
        )

        event = NarrativeEvent(
            event_id="evt_0",
            event_type=NarrativeEventType.AGENT_ACTION,
            timestamp_sec=0.0,
            description="Start navigation",
        )

        sequence.add_event(event)

        assert sequence.get_sensor_count() if hasattr(sequence, 'get_sensor_count') else len(sequence.events) == 1
        assert sequence.duration_sec >= 0.0

    def test_narrative_constraint_creation(self):
        """Test creating narrative constraint."""
        constraint = NarrativeConstraint(
            constraint_id="const_0",
            description="Maintain safe distance from obstacles",
            constraint_type="safety",
            rule="min_distance >= 1.0",
            violation_penalty=-0.8,
        )

        assert constraint.constraint_id == "const_0"
        assert constraint.constraint_type == "safety"
        assert -1.0 <= constraint.violation_penalty <= 0.0

    def test_narrative_creation(self):
        """Test creating complete narrative."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Delivery Mission",
            description="Robot delivers package safely",
            narrative_type=NarrativeType.DELIVERY_MISSION,
        )

        entity = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
        )

        goal = NarrativeGoal(
            goal_id="goal_0",
            description="Reach destination",
            goal_type="reach_location",
        )

        narrative.add_entity(entity)
        narrative.add_goal(goal)

        assert len(narrative.entities) == 1
        assert len(narrative.goals) == 1

    def test_execution_context_creation(self):
        """Test execution context."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Test",
            description="Test",
            narrative_type=NarrativeType.CUSTOM,
        )

        context = NarrativeExecutionContext(narrative=narrative)

        assert context.elapsed_time_sec == 0.0
        assert len(context.entity_states) == 0

        context.update_entity_state("robot_0", {"position": (1.0, 2.0, 3.0)})
        assert "robot_0" in context.entity_states

        context.update_goal_progress("goal_0", 0.5)
        assert context.goal_progress["goal_0"] == 0.5


class TestNarrativeConverter:
    """Test narrative converter."""

    @pytest.mark.skip(reason="Requires API key and live Claude API")
    def test_parse_narrative_real_api(self):
        """Test parsing narrative with real API."""
        converter = NarrativeConverter()

        narrative_text = """
        A delivery robot starts at the warehouse.
        It must navigate to the customer location 50 meters away.
        The robot has a camera and LiDAR for sensing.
        Safety constraint: maintain 2 meters distance from obstacles.
        """

        narrative = converter.parse_narrative(narrative_text)

        assert narrative.narrative_id
        assert len(narrative.entities) > 0

    def test_extract_metadata_parsing(self):
        """Test metadata extraction error handling."""
        converter = NarrativeConverter()

        # Mock the API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"title": "Test", "type": "delivery_mission", "difficulty": 0.5}'

        with patch.object(converter._client.messages, 'create', return_value=mock_response):
            metadata = converter._extract_metadata("test narrative")

            assert metadata["title"] == "Test"
            assert metadata["type"] == "delivery_mission"

    def test_extract_metadata_fallback(self):
        """Test metadata extraction fallback."""
        converter = NarrativeConverter()

        # Mock API to return invalid JSON
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "invalid json"

        with patch.object(converter._client.messages, 'create', return_value=mock_response):
            metadata = converter._extract_metadata("test narrative")

            assert "title" in metadata
            assert "type" in metadata


class TestNarrativeExecutor:
    """Test narrative executor."""

    def test_executor_initialization(self):
        """Test executor creation."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Test",
            description="Test",
            narrative_type=NarrativeType.CUSTOM,
        )

        executor = NarrativeExecutor(narrative)

        assert executor._narrative == narrative
        assert executor._context is not None

    def test_start_execution(self):
        """Test starting execution."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Test",
            description="Test",
            narrative_type=NarrativeType.CUSTOM,
        )

        entity = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
        )

        narrative.add_entity(entity)

        executor = NarrativeExecutor(narrative)
        context = executor.start_execution()

        assert context.execution_state == "running"
        assert "robot_0" in context.entity_states

    def test_pause_resume_execution(self):
        """Test pausing and resuming execution."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Test",
            description="Test",
            narrative_type=NarrativeType.CUSTOM,
        )

        executor = NarrativeExecutor(narrative)
        executor.start_execution()

        executor.pause_execution()
        assert executor._context.execution_state == "paused"

        executor.resume_execution()
        assert executor._context.execution_state == "running"

    def test_finish_execution(self):
        """Test finishing execution."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Test",
            description="Test",
            narrative_type=NarrativeType.CUSTOM,
        )

        goal = NarrativeGoal(
            goal_id="goal_0",
            description="Reach location",
            goal_type="reach_location",
        )

        narrative.add_goal(goal)

        executor = NarrativeExecutor(narrative)
        executor.start_execution()

        summary = executor.finish_execution("completed")

        assert summary["outcome"] == "completed"
        assert summary["goals_total"] == 1


class TestAgentBehaviorInterpreter:
    """Test agent behavior interpreter."""

    def test_interpreter_initialization(self):
        """Test interpreter creation."""
        interpreter = AgentBehaviorInterpreter()

        assert interpreter._model is not None

    def test_behavior_primitive_creation(self):
        """Test creating behavior primitive."""
        primitive = BehaviorPrimitive(
            behavior_id="nav_0",
            behavior_type="navigate",
            description="Navigate to location",
            parameters={"target_position": [10.0, 5.0, 0.0]},
            duration_sec=15.0,
        )

        assert primitive.behavior_id == "nav_0"
        assert primitive.status == "pending"
        assert primitive.duration_sec == 15.0

    def test_behavior_plan_creation(self):
        """Test creating behavior plan."""
        plan = BehaviorPlan("robot_0", "plan_0")

        primitive = BehaviorPrimitive(
            behavior_id="nav_0",
            behavior_type="navigate",
            description="Navigate",
            parameters={},
        )

        plan.add_primitive(primitive)

        assert len(plan.primitives) == 1
        assert plan.get_current_primitive() == primitive

    def test_behavior_plan_progression(self):
        """Test plan progression."""
        plan = BehaviorPlan("robot_0", "plan_0")

        for i in range(3):
            plan.add_primitive(BehaviorPrimitive(
                behavior_id=f"action_{i}",
                behavior_type="action",
                description=f"Action {i}",
                parameters={},
            ))

        assert not plan.is_complete()

        # Advance through first 2 primitives (should return True)
        assert plan.advance()
        assert plan.advance()

        # Advance past the end (should return False)
        assert not plan.advance()

        assert plan.is_complete()

    @pytest.mark.skip(reason="Requires API key")
    def test_interpret_action_real_api(self):
        """Test action interpretation with real API."""
        interpreter = AgentBehaviorInterpreter()

        plan = interpreter.interpret_action(
            "robot_0",
            "Navigate to the customer's house at coordinates (50, 30, 0)",
            agent_type="mobile",
        )

        assert len(plan.primitives) > 0


class TestStoryBranchingEngine:
    """Test story branching engine."""

    def test_engine_initialization(self):
        """Test engine creation."""
        engine = StoryBranchingEngine()

        assert len(engine._conditions) == 0
        assert len(engine._branch_points) == 0

    def test_register_condition(self):
        """Test registering condition."""
        engine = StoryBranchingEngine()

        condition = BranchCondition(
            condition_id="success",
            description="Mission succeeded",
            evaluator=lambda ctx: ctx.get("success", False),
        )

        engine.register_condition(condition)

        assert "success" in engine._conditions

    def test_condition_evaluation(self):
        """Test condition evaluation."""
        condition = BranchCondition(
            condition_id="test",
            description="Test condition",
            evaluator=lambda ctx: ctx.get("value", 0) > 5,
        )

        assert condition.evaluate({"value": 10}) is True
        assert condition.evaluate({"value": 3}) is False

    def test_branch_path_creation(self):
        """Test creating branch path."""
        sequence = NarrativeSequence(
            sequence_id="seq_0",
            name="Success path",
            description="Executed when successful",
        )

        path = BranchPath(
            path_id="path_success",
            description="Success branch",
            sequence=sequence,
            probability=0.7,
        )

        assert path.path_id == "path_success"
        assert path.probability == 0.7
        assert path.taken_count == 0

    def test_probabilistic_branch_selection(self):
        """Test probabilistic branch selection."""
        engine = StoryBranchingEngine()

        seq1 = NarrativeSequence("seq_1", "Path 1", "")
        seq2 = NarrativeSequence("seq_2", "Path 2", "")

        paths = [
            BranchPath("path_1", "Path 1", seq1, 0.8),
            BranchPath("path_2", "Path 2", seq2, 0.2),
        ]

        # Select multiple times to test probability
        counts = {"path_1": 0, "path_2": 0}

        for _ in range(100):
            selected = engine._evaluate_probabilistic_branch(paths)
            counts[selected.path_id] += 1

        # Rough check that distribution is reasonable
        assert counts["path_1"] > counts["path_2"]

    def test_decision_history(self):
        """Test tracking decision history."""
        engine = StoryBranchingEngine()

        seq = NarrativeSequence("seq_0", "Test", "")
        paths = [BranchPath("path_0", "Path 0", seq)]

        engine.add_branch_point("narr_0", Mock(branch_id="branch_0", branch_type=NarrativeBranch.LINEAR), paths)
        engine.evaluate_branch("narr_0", "branch_0", {}, 0.0)

        history = engine.get_decision_history()

        assert len(history) == 1
        assert history[0]["branch_id"] == "branch_0"

    def test_branch_statistics(self):
        """Test branch statistics."""
        engine = StoryBranchingEngine()

        seq = NarrativeSequence("seq_0", "Test", "")
        paths = [BranchPath("path_0", "Path 0", seq)]

        engine.add_branch_point("narr_0", Mock(branch_id="b1", branch_type=NarrativeBranch.LINEAR), paths)
        engine.add_branch_point("narr_0", Mock(branch_id="b2", branch_type=NarrativeBranch.LINEAR), paths)

        engine.evaluate_branch("narr_0", "b1", {}, 0.0)
        engine.evaluate_branch("narr_0", "b2", {}, 1.0)

        stats = engine.get_branch_statistics()

        assert stats["total_branch_points"] == 2
        assert stats["total_decisions"] == 2


class TestNarrativeValidator:
    """Test narrative validator."""

    def test_validator_initialization(self):
        """Test validator creation."""
        validator = NarrativeValidator()

        assert len(validator._validation_rules) > 0

    def test_validate_empty_narrative(self):
        """Test validating empty narrative."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Empty",
            description="Empty narrative",
            narrative_type=NarrativeType.CUSTOM,
        )

        validator = NarrativeValidator()
        result = validator.validate(narrative)

        assert len(result.errors) > 0  # Should have at least one error (no entities)
        assert not result.is_valid

    def test_validate_valid_narrative(self):
        """Test validating valid narrative."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Valid",
            description="Valid narrative",
            narrative_type=NarrativeType.CUSTOM,
        )

        entity = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
            sensor_suite="mobile",
        )

        goal = NarrativeGoal(
            goal_id="goal_0",
            description="Reach location",
            goal_type="reach_location",
            success_criteria={"distance": 0.5},
        )

        narrative.add_entity(entity)
        narrative.add_goal(goal)

        validator = NarrativeValidator()
        result = validator.validate(narrative)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_feasibility_scoring(self):
        """Test feasibility score computation."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Test",
            description="Test",
            narrative_type=NarrativeType.CUSTOM,
        )

        entity = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
        )

        narrative.add_entity(entity)

        validator = NarrativeValidator()
        result = validator.validate(narrative)

        assert 0.0 <= result.feasibility_score <= 1.0

    def test_sensor_coverage_scoring(self):
        """Test sensor coverage score."""
        narrative = Narrative(
            narrative_id="narr_0",
            title="Test",
            description="Test",
            narrative_type=NarrativeType.CUSTOM,
        )

        # Robot with sensor suite
        entity1 = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Equipped Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
            sensor_suite="mobile",
        )

        # Robot without sensor suite
        entity2 = NarrativeEntity(
            entity_id="robot_1",
            entity_type="robot",
            name="Bare Robot",
            role=AgentRole.ASSISTANT,
            initial_position=(5.0, 5.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
        )

        narrative.add_entity(entity1)
        narrative.add_entity(entity2)

        validator = NarrativeValidator()
        result = validator.validate(narrative)

        assert 0.0 <= result.sensor_coverage_score <= 1.0
        assert result.sensor_coverage_score == 0.5  # 1 out of 2


class TestNarrativeIntegration:
    """Integration tests for narrative engine."""

    def test_complete_narrative_workflow(self):
        """Test complete narrative workflow."""
        # Create narrative
        narrative = Narrative(
            narrative_id="narr_0",
            title="Delivery Mission",
            description="Safe delivery scenario",
            narrative_type=NarrativeType.DELIVERY_MISSION,
            environment_type="urban",
            time_of_day="afternoon",
            difficulty_level=0.6,
        )

        # Add entities
        robot = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Delivery Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
            sensor_suite="mobile",
        )

        obstacle = NarrativeEntity(
            entity_id="obs_0",
            entity_type="obstacle",
            name="Building",
            role=AgentRole.OBSTACLE,
            initial_position=(20.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
        )

        narrative.add_entity(robot)
        narrative.add_entity(obstacle)

        # Add goal
        goal = NarrativeGoal(
            goal_id="goal_0",
            description="Deliver to customer",
            goal_type="reach_location",
            target={"position": [50.0, 0.0, 0.0], "tolerance": 1.0},
            priority=1.0,
            time_limit_sec=300.0,
        )

        narrative.add_goal(goal)

        # Add constraint
        constraint = NarrativeConstraint(
            constraint_id="const_0",
            description="Safety distance",
            constraint_type="safety",
            rule="min_distance >= 1.0",
        )

        narrative.add_constraint(constraint)

        # Validate
        validator = NarrativeValidator()
        result = validator.validate(narrative)

        assert result.is_valid
        assert len(result.errors) == 0

        # Execute
        executor = NarrativeExecutor(narrative)
        context = executor.start_execution()

        assert context.execution_state == "running"

        # Update and finish
        summary = executor.finish_execution("completed")

        assert summary["narrative_id"] == "narr_0"
        assert summary["outcome"] == "completed"
