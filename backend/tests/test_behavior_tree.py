"""Tests for Phase 2.1: Behavior Tree System."""

import pytest
import yaml

from backend.src.services.behavior_tree import (
    Action,
    BehaviorNode,
    BehaviorStatus,
    BehaviorTree,
    BehaviorTreeBuilder,
    Condition,
    Inverter,
    Limiter,
    Parallel,
    Repeater,
    Selector,
    Sequence,
)


class TestBehaviorStatus:
    """Test behavior status."""

    def test_status_values(self):
        """Test status enum values."""
        assert BehaviorStatus.SUCCESS.value == "success"
        assert BehaviorStatus.FAILURE.value == "failure"
        assert BehaviorStatus.RUNNING.value == "running"


class TestAction:
    """Test action node."""

    def test_action_success(self):
        """Test action returning success."""

        def success_action(context):
            return BehaviorStatus.SUCCESS

        action = Action("test_action", success_action)
        context = {}

        status = action.tick(context)
        assert status == BehaviorStatus.SUCCESS
        assert action.status == BehaviorStatus.SUCCESS

    def test_action_failure(self):
        """Test action returning failure."""

        def fail_action(context):
            return BehaviorStatus.FAILURE

        action = Action("test_action", fail_action)
        context = {}

        status = action.tick(context)
        assert status == BehaviorStatus.FAILURE

    def test_action_running(self):
        """Test action returning running."""

        def running_action(context):
            return BehaviorStatus.RUNNING

        action = Action("test_action", running_action)
        context = {}

        status = action.tick(context)
        assert status == BehaviorStatus.RUNNING

    def test_action_with_context(self):
        """Test action modifying context."""

        def context_action(context):
            context["executed"] = True
            return BehaviorStatus.SUCCESS

        action = Action("test_action", context_action)
        context = {}

        action.tick(context)
        assert context["executed"]

    def test_action_execution_count(self):
        """Test execution count tracking."""

        def dummy_action(context):
            return BehaviorStatus.SUCCESS

        action = Action("test_action", dummy_action)
        context = {}

        assert action.execution_count == 0
        action.tick(context)
        assert action.execution_count == 1
        action.tick(context)
        assert action.execution_count == 2


class TestCondition:
    """Test condition node."""

    def test_condition_true(self):
        """Test condition returning true."""
        condition = Condition("test_cond", lambda c: True)
        status = condition.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_condition_false(self):
        """Test condition returning false."""
        condition = Condition("test_cond", lambda c: False)
        status = condition.tick({})
        assert status == BehaviorStatus.FAILURE

    def test_condition_with_context(self):
        """Test condition checking context."""
        condition = Condition("check_value", lambda c: c.get("value", 0) > 10)

        context1 = {"value": 20}
        assert condition.tick(context1) == BehaviorStatus.SUCCESS

        context2 = {"value": 5}
        assert condition.tick(context2) == BehaviorStatus.FAILURE


class TestSequence:
    """Test sequence composite."""

    def test_sequence_all_success(self):
        """Test sequence with all successful children."""
        children = [
            Action("act1", lambda c: BehaviorStatus.SUCCESS),
            Action("act2", lambda c: BehaviorStatus.SUCCESS),
            Action("act3", lambda c: BehaviorStatus.SUCCESS),
        ]
        sequence = Sequence("seq", children)

        status = sequence.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_sequence_one_fails(self):
        """Test sequence stops at first failure."""
        children = [
            Action("act1", lambda c: BehaviorStatus.SUCCESS),
            Action("act2", lambda c: BehaviorStatus.FAILURE),
            Action("act3", lambda c: BehaviorStatus.SUCCESS),
        ]
        sequence = Sequence("seq", children)

        status = sequence.tick({})
        assert status == BehaviorStatus.FAILURE

    def test_sequence_one_running(self):
        """Test sequence stops at running."""
        children = [
            Action("act1", lambda c: BehaviorStatus.SUCCESS),
            Action("act2", lambda c: BehaviorStatus.RUNNING),
            Action("act3", lambda c: BehaviorStatus.SUCCESS),
        ]
        sequence = Sequence("seq", children)

        status = sequence.tick({})
        assert status == BehaviorStatus.RUNNING

    def test_sequence_execution_order(self):
        """Test actions execute in order."""
        execution_order = []

        def action1(c):
            execution_order.append(1)
            return BehaviorStatus.SUCCESS

        def action2(c):
            execution_order.append(2)
            return BehaviorStatus.SUCCESS

        def action3(c):
            execution_order.append(3)
            return BehaviorStatus.SUCCESS

        children = [
            Action("act1", action1),
            Action("act2", action2),
            Action("act3", action3),
        ]
        sequence = Sequence("seq", children)

        sequence.tick({})
        assert execution_order == [1, 2, 3]


class TestSelector:
    """Test selector composite."""

    def test_selector_first_success(self):
        """Test selector succeeds at first success."""
        children = [
            Action("act1", lambda c: BehaviorStatus.SUCCESS),
            Action("act2", lambda c: BehaviorStatus.SUCCESS),
        ]
        selector = Selector("sel", children)

        status = selector.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_selector_all_fail(self):
        """Test selector fails if all fail."""
        children = [
            Action("act1", lambda c: BehaviorStatus.FAILURE),
            Action("act2", lambda c: BehaviorStatus.FAILURE),
        ]
        selector = Selector("sel", children)

        status = selector.tick({})
        assert status == BehaviorStatus.FAILURE

    def test_selector_stops_at_success(self):
        """Test selector doesn't execute after success."""
        execution = []

        def act1(c):
            execution.append(1)
            return BehaviorStatus.SUCCESS

        def act2(c):
            execution.append(2)
            return BehaviorStatus.SUCCESS

        children = [
            Action("act1", act1),
            Action("act2", act2),
        ]
        selector = Selector("sel", children)

        selector.tick({})
        assert execution == [1]  # act2 not executed


class TestParallel:
    """Test parallel composite."""

    def test_parallel_all_success(self):
        """Test parallel with all successful."""
        children = [
            Action("act1", lambda c: BehaviorStatus.SUCCESS),
            Action("act2", lambda c: BehaviorStatus.SUCCESS),
            Action("act3", lambda c: BehaviorStatus.SUCCESS),
        ]
        parallel = Parallel("par", children)

        status = parallel.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_parallel_one_failure_fails(self):
        """Test parallel fails if one child fails."""
        children = [
            Action("act1", lambda c: BehaviorStatus.SUCCESS),
            Action("act2", lambda c: BehaviorStatus.FAILURE),
        ]
        parallel = Parallel("par", children, failure_policy="one")

        status = parallel.tick({})
        assert status == BehaviorStatus.FAILURE

    def test_parallel_one_running(self):
        """Test parallel returns running if any running."""
        children = [
            Action("act1", lambda c: BehaviorStatus.SUCCESS),
            Action("act2", lambda c: BehaviorStatus.RUNNING),
        ]
        parallel = Parallel("par", children)

        status = parallel.tick({})
        assert status == BehaviorStatus.RUNNING

    def test_parallel_executes_all(self):
        """Test all children execute."""
        execution = []

        def act1(c):
            execution.append(1)
            return BehaviorStatus.SUCCESS

        def act2(c):
            execution.append(2)
            return BehaviorStatus.SUCCESS

        def act3(c):
            execution.append(3)
            return BehaviorStatus.SUCCESS

        children = [
            Action("act1", act1),
            Action("act2", act2),
            Action("act3", act3),
        ]
        parallel = Parallel("par", children)

        parallel.tick({})
        assert set(execution) == {1, 2, 3}


class TestInverter:
    """Test inverter decorator."""

    def test_invert_success_to_failure(self):
        """Test inverting success."""
        child = Action("act", lambda c: BehaviorStatus.SUCCESS)
        inverter = Inverter("inv", child)

        status = inverter.tick({})
        assert status == BehaviorStatus.FAILURE

    def test_invert_failure_to_success(self):
        """Test inverting failure."""
        child = Action("act", lambda c: BehaviorStatus.FAILURE)
        inverter = Inverter("inv", child)

        status = inverter.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_invert_running_stays_running(self):
        """Test running stays running."""
        child = Action("act", lambda c: BehaviorStatus.RUNNING)
        inverter = Inverter("inv", child)

        status = inverter.tick({})
        assert status == BehaviorStatus.RUNNING


class TestRepeater:
    """Test repeater decorator."""

    def test_repeat_once(self):
        """Test repeating once (normal execution)."""
        counter = {"value": 0}

        def count_action(c):
            counter["value"] += 1
            return BehaviorStatus.SUCCESS

        child = Action("act", count_action)
        repeater = Repeater("rep", child, max_repetitions=1)

        status = repeater.tick({})
        assert status == BehaviorStatus.SUCCESS
        assert counter["value"] == 1

    def test_repeat_multiple(self):
        """Test repeating multiple times."""
        counter = {"value": 0}

        def count_action(c):
            counter["value"] += 1
            return BehaviorStatus.SUCCESS

        child = Action("act", count_action)
        repeater = Repeater("rep", child, max_repetitions=3)

        repeater.tick({})
        repeater.tick({})
        repeater.tick({})

        status = repeater.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_repeat_reset(self):
        """Test repeater reset."""
        counter = {"value": 0}

        def count_action(c):
            counter["value"] += 1
            return BehaviorStatus.SUCCESS

        child = Action("act", count_action)
        repeater = Repeater("rep", child, max_repetitions=2)

        # Do 2 repetitions
        repeater.tick({})
        repeater.tick({})

        # Reset
        repeater.reset()
        repeater.tick({})

        assert repeater.repetition_count == 1


class TestLimiter:
    """Test limiter decorator."""

    def test_limiter_single_execution(self):
        """Test limiter with single execution."""
        counter = {"value": 0}

        def count_action(c):
            counter["value"] += 1
            return BehaviorStatus.SUCCESS

        child = Action("act", count_action)
        limiter = Limiter("lim", child, max_executions=1)

        status = limiter.tick({})
        assert status == BehaviorStatus.SUCCESS
        assert counter["value"] == 1

        # Second call should not execute child
        status = limiter.tick({})
        assert status == BehaviorStatus.SUCCESS
        assert counter["value"] == 1

    def test_limiter_multiple_executions(self):
        """Test limiter with multiple executions."""
        counter = {"value": 0}

        def count_action(c):
            counter["value"] += 1
            return BehaviorStatus.SUCCESS

        child = Action("act", count_action)
        limiter = Limiter("lim", child, max_executions=3)

        for _ in range(3):
            limiter.tick({})

        assert counter["value"] == 3


class TestBehaviorTree:
    """Test complete behavior tree."""

    def test_tree_creation(self):
        """Test creating tree."""
        root = Sequence("root", [])
        tree = BehaviorTree(root, name="test_tree")

        assert tree.name == "test_tree"
        assert tree.tick_count == 0

    def test_tree_tick(self):
        """Test ticking tree."""
        root = Action("root", lambda c: BehaviorStatus.SUCCESS)
        tree = BehaviorTree(root)

        status = tree.tick({})
        assert status == BehaviorStatus.SUCCESS
        assert tree.tick_count == 1

    def test_tree_complex(self):
        """Test complex tree structure."""
        # (condition AND action1) OR action2
        condition = Condition("cond", lambda c: c.get("condition", False))
        action1 = Action("act1", lambda c: BehaviorStatus.SUCCESS)
        seq = Sequence("seq", [condition, action1])

        action2 = Action("act2", lambda c: BehaviorStatus.SUCCESS)
        root = Selector("root", [seq, action2])

        tree = BehaviorTree(root)

        # Condition false, should execute action2
        status = tree.tick({"condition": False})
        assert status == BehaviorStatus.SUCCESS

    def test_tree_reset(self):
        """Test tree reset."""
        root = Action("root", lambda c: BehaviorStatus.SUCCESS)
        tree = BehaviorTree(root)

        tree.tick({})
        assert tree.tick_count == 1

        tree.reset()
        assert tree.tick_count == 0


class TestBehaviorTreeBuilder:
    """Test tree builder."""

    def test_builder_sequence(self):
        """Test builder creating sequence."""
        builder = BehaviorTreeBuilder("test")

        action1 = builder.action("act1", lambda c: BehaviorStatus.SUCCESS)
        action2 = builder.action("act2", lambda c: BehaviorStatus.SUCCESS)
        seq = builder.sequence("seq", action1, action2)

        tree = builder.build(seq)
        status = tree.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_builder_selector(self):
        """Test builder creating selector."""
        builder = BehaviorTreeBuilder("test")

        action1 = builder.action("act1", lambda c: BehaviorStatus.FAILURE)
        action2 = builder.action("act2", lambda c: BehaviorStatus.SUCCESS)
        sel = builder.selector("sel", action1, action2)

        tree = builder.build(sel)
        status = tree.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_builder_condition(self):
        """Test builder with condition."""
        builder = BehaviorTreeBuilder("test")

        cond = builder.condition("cond", lambda c: c.get("flag", False))
        action = builder.action("act", lambda c: BehaviorStatus.SUCCESS)
        seq = builder.sequence("seq", cond, action)

        tree = builder.build(seq)
        status = tree.tick({"flag": True})
        assert status == BehaviorStatus.SUCCESS

    def test_builder_decorators(self):
        """Test builder with decorators."""
        builder = BehaviorTreeBuilder("test")

        action = builder.action("act", lambda c: BehaviorStatus.SUCCESS)
        inverted = builder.inverter("inv", action)

        tree = builder.build(inverted)
        status = tree.tick({})
        assert status == BehaviorStatus.FAILURE


class TestBehaviorTreeYAML:
    """Test loading trees from YAML."""

    def test_load_simple_sequence(self):
        """Test loading simple sequence from YAML."""

        yaml_str = """
root:
  type: sequence
  name: root
  children:
    - type: action
      name: action1
      action: success_action
    - type: action
      name: action2
      action: success_action
"""

        def success_action(c):
            return BehaviorStatus.SUCCESS

        actions = {"success_action": success_action}
        conditions = {}

        tree = BehaviorTree.from_yaml(yaml_str, actions, conditions)
        status = tree.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_load_selector(self):
        """Test loading selector from YAML."""

        yaml_str = """
root:
  type: selector
  name: root
  children:
    - type: action
      name: action1
      action: fail_action
    - type: action
      name: action2
      action: success_action
"""

        def fail_action(c):
            return BehaviorStatus.FAILURE

        def success_action(c):
            return BehaviorStatus.SUCCESS

        actions = {"fail_action": fail_action, "success_action": success_action}
        conditions = {}

        tree = BehaviorTree.from_yaml(yaml_str, actions, conditions)
        status = tree.tick({})
        assert status == BehaviorStatus.SUCCESS

    def test_load_with_condition(self):
        """Test loading tree with condition."""

        yaml_str = """
root:
  type: sequence
  name: root
  children:
    - type: condition
      name: check_value
      condition: check_positive
    - type: action
      name: execute
      action: success_action
"""

        def check_positive(c):
            return c.get("value", 0) > 0

        def success_action(c):
            return BehaviorStatus.SUCCESS

        actions = {"success_action": success_action}
        conditions = {"check_positive": check_positive}

        tree = BehaviorTree.from_yaml(yaml_str, actions, conditions)
        status = tree.tick({"value": 10})
        assert status == BehaviorStatus.SUCCESS

    def test_tree_to_dict(self):
        """Test converting tree to dict."""
        root = Sequence("root", [
            Action("act1", lambda c: BehaviorStatus.SUCCESS),
            Action("act2", lambda c: BehaviorStatus.SUCCESS),
        ])
        tree = BehaviorTree(root, name="test")

        tree.tick({})
        d = tree.to_dict()

        assert d["name"] == "test"
        assert d["tick_count"] == 1
        assert "root" in d
