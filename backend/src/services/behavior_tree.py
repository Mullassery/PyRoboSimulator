"""Behavior tree system for agent control.

Implements hierarchical behavior trees with composite nodes (Sequence, Selector,
Parallel), decorator nodes (Inverter, Repeater, Limiter), and leaf nodes
(actions, conditions).
"""

import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class BehaviorStatus(Enum):
    """Status of behavior node execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BehaviorNode(ABC):
    """Base class for all behavior tree nodes."""

    def __init__(self, name: str, children: Optional[List["BehaviorNode"]] = None):
        """Initialize behavior node.

        Args:
            name: Node identifier
            children: Child nodes
        """
        self.name = name
        self.children = children or []
        self.parent: Optional["BehaviorNode"] = None
        self.status = BehaviorStatus.RUNNING
        self.execution_count = 0
        self.start_time: Optional[float] = None
        self.metadata: Dict[str, Any] = {}

        # Set parent references
        for child in self.children:
            child.parent = self

    @abstractmethod
    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Execute this node.

        Args:
            context: Blackboard (shared data) for the behavior tree

        Returns:
            Status of execution
        """
        pass

    def reset(self) -> None:
        """Reset node state."""
        self.status = BehaviorStatus.RUNNING
        self.start_time = None
        for child in self.children:
            child.reset()

    def get_execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if self.start_time is None:
            return None
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "status": self.status.value,
            "execution_count": self.execution_count,
            "children": [child.to_dict() for child in self.children],
        }


class Action(BehaviorNode):
    """Leaf node that executes an action."""

    def __init__(
        self,
        name: str,
        action_func: Callable[[Dict[str, Any]], BehaviorStatus],
    ):
        """Initialize action node.

        Args:
            name: Action identifier
            action_func: Function to execute returning BehaviorStatus
        """
        super().__init__(name)
        self.action_func = action_func

    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Execute action function."""
        self.execution_count += 1
        self.start_time = time.time()
        self.status = self.action_func(context)
        return self.status


class Condition(BehaviorNode):
    """Leaf node that checks a condition."""

    def __init__(
        self,
        name: str,
        condition_func: Callable[[Dict[str, Any]], bool],
    ):
        """Initialize condition node.

        Args:
            name: Condition identifier
            condition_func: Function returning True/False
        """
        super().__init__(name)
        self.condition_func = condition_func

    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Check condition."""
        self.execution_count += 1
        self.start_time = time.time()
        self.status = (
            BehaviorStatus.SUCCESS if self.condition_func(context) else BehaviorStatus.FAILURE
        )
        return self.status


class Sequence(BehaviorNode):
    """Composite node: executes children in sequence until one fails.

    Returns SUCCESS only if all children succeed.
    Returns FAILURE as soon as any child fails.
    Returns RUNNING if a child is still running.
    """

    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Execute sequence."""
        self.execution_count += 1
        self.start_time = time.time()

        for child in self.children:
            result = child.tick(context)

            if result == BehaviorStatus.FAILURE:
                self.status = BehaviorStatus.FAILURE
                return self.status

            if result == BehaviorStatus.RUNNING:
                self.status = BehaviorStatus.RUNNING
                return self.status

        self.status = BehaviorStatus.SUCCESS
        return self.status


class Selector(BehaviorNode):
    """Composite node: executes children until one succeeds.

    Returns SUCCESS as soon as any child succeeds.
    Returns FAILURE only if all children fail.
    Returns RUNNING if a child is still running and no child succeeded.
    """

    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Execute selector."""
        self.execution_count += 1
        self.start_time = time.time()

        for child in self.children:
            result = child.tick(context)

            if result == BehaviorStatus.SUCCESS:
                self.status = BehaviorStatus.SUCCESS
                return self.status

            if result == BehaviorStatus.RUNNING:
                self.status = BehaviorStatus.RUNNING
                return self.status

        self.status = BehaviorStatus.FAILURE
        return self.status


class Parallel(BehaviorNode):
    """Composite node: executes all children simultaneously.

    Returns SUCCESS if all children succeed.
    Returns FAILURE if any child fails.
    Returns RUNNING if any child is running.
    """

    def __init__(self, name: str, children: Optional[List[BehaviorNode]] = None,
                 success_policy: str = "all", failure_policy: str = "one"):
        """Initialize parallel node.

        Args:
            name: Node identifier
            children: Child nodes
            success_policy: "all" or "one"
            failure_policy: "all" or "one"
        """
        super().__init__(name, children)
        self.success_policy = success_policy  # "all" = all must succeed
        self.failure_policy = failure_policy  # "one" = one failure fails node

    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Execute parallel."""
        self.execution_count += 1
        self.start_time = time.time()

        statuses = [child.tick(context) for child in self.children]

        success_count = sum(1 for s in statuses if s == BehaviorStatus.SUCCESS)
        failure_count = sum(1 for s in statuses if s == BehaviorStatus.FAILURE)
        running_count = sum(1 for s in statuses if s == BehaviorStatus.RUNNING)

        # Check failure policy
        if self.failure_policy == "one" and failure_count > 0:
            self.status = BehaviorStatus.FAILURE
            return self.status

        # Check success policy
        if self.success_policy == "all":
            if success_count == len(self.children):
                self.status = BehaviorStatus.SUCCESS
                return self.status
        else:  # "one"
            if success_count > 0:
                self.status = BehaviorStatus.SUCCESS
                return self.status

        # If any running, return running
        if running_count > 0:
            self.status = BehaviorStatus.RUNNING
            return self.status

        # All failed
        self.status = BehaviorStatus.FAILURE
        return self.status


class Inverter(BehaviorNode):
    """Decorator: inverts the child's status (SUCCESS ↔ FAILURE)."""

    def __init__(self, name: str, child: BehaviorNode):
        """Initialize inverter.

        Args:
            name: Node identifier
            child: Child node to invert
        """
        super().__init__(name, [child])
        self.child = child

    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Execute and invert result."""
        self.execution_count += 1
        self.start_time = time.time()

        result = self.child.tick(context)

        if result == BehaviorStatus.SUCCESS:
            self.status = BehaviorStatus.FAILURE
        elif result == BehaviorStatus.FAILURE:
            self.status = BehaviorStatus.SUCCESS
        else:
            self.status = BehaviorStatus.RUNNING

        return self.status


class Repeater(BehaviorNode):
    """Decorator: repeats child execution N times."""

    def __init__(self, name: str, child: BehaviorNode, max_repetitions: int = 1):
        """Initialize repeater.

        Args:
            name: Node identifier
            child: Child node to repeat
            max_repetitions: Number of times to repeat
        """
        super().__init__(name, [child])
        self.child = child
        self.max_repetitions = max_repetitions
        self.repetition_count = 0

    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Execute child repeatedly."""
        self.execution_count += 1
        self.start_time = time.time()

        if self.repetition_count >= self.max_repetitions:
            self.repetition_count = 0
            self.status = BehaviorStatus.SUCCESS
            return self.status

        result = self.child.tick(context)

        if result == BehaviorStatus.SUCCESS:
            self.repetition_count += 1
            if self.repetition_count >= self.max_repetitions:
                self.status = BehaviorStatus.SUCCESS
            else:
                self.status = BehaviorStatus.RUNNING
        else:
            self.status = result

        return self.status

    def reset(self) -> None:
        """Reset repetition count."""
        super().reset()
        self.repetition_count = 0


class Limiter(BehaviorNode):
    """Decorator: limits execution to N times total."""

    def __init__(self, name: str, child: BehaviorNode, max_executions: int = 1):
        """Initialize limiter.

        Args:
            name: Node identifier
            child: Child node to limit
            max_executions: Maximum number of executions
        """
        super().__init__(name, [child])
        self.child = child
        self.max_executions = max_executions
        self.execution_counter = 0

    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Execute if under limit."""
        self.execution_count += 1
        self.start_time = time.time()

        if self.execution_counter >= self.max_executions:
            self.status = BehaviorStatus.SUCCESS
            return self.status

        result = self.child.tick(context)

        if result != BehaviorStatus.RUNNING:
            self.execution_counter += 1

        self.status = result
        return self.status

    def reset(self) -> None:
        """Reset execution counter."""
        super().reset()
        self.execution_counter = 0


class BehaviorTree:
    """Complete behavior tree with root node."""

    def __init__(self, root: BehaviorNode, name: str = "unnamed"):
        """Initialize behavior tree.

        Args:
            root: Root node of the tree
            name: Tree identifier
        """
        self.root = root
        self.name = name
        self.tick_count = 0
        self.execution_time_ms = 0.0

    def tick(self, context: Dict[str, Any]) -> BehaviorStatus:
        """Tick the behavior tree once.

        Args:
            context: Blackboard (shared data)

        Returns:
            Status of root node
        """
        self.tick_count += 1
        start = time.time()

        status = self.root.tick(context)

        self.execution_time_ms = (time.time() - start) * 1000
        return status

    def reset(self) -> None:
        """Reset tree state."""
        self.root.reset()
        self.tick_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "tick_count": self.tick_count,
            "execution_time_ms": self.execution_time_ms,
            "root": self.root.to_dict(),
        }

    @staticmethod
    def from_yaml(yaml_str: str, actions: Dict[str, Callable],
                  conditions: Dict[str, Callable]) -> "BehaviorTree":
        """Load behavior tree from YAML.

        Args:
            yaml_str: YAML configuration
            actions: Dictionary of available actions {name: function}
            conditions: Dictionary of available conditions {name: function}

        Returns:
            BehaviorTree instance
        """
        config = yaml.safe_load(yaml_str)

        def build_node(node_config: Dict[str, Any]) -> BehaviorNode:
            """Recursively build node tree."""
            node_type = node_config.get("type")
            name = node_config.get("name", "unnamed")

            if node_type == "action":
                action_name = node_config.get("action")
                if action_name not in actions:
                    raise ValueError(f"Unknown action: {action_name}")
                return Action(name, actions[action_name])

            elif node_type == "condition":
                condition_name = node_config.get("condition")
                if condition_name not in conditions:
                    raise ValueError(f"Unknown condition: {condition_name}")
                return Condition(name, conditions[condition_name])

            elif node_type == "sequence":
                children = [build_node(c) for c in node_config.get("children", [])]
                return Sequence(name, children)

            elif node_type == "selector":
                children = [build_node(c) for c in node_config.get("children", [])]
                return Selector(name, children)

            elif node_type == "parallel":
                children = [build_node(c) for c in node_config.get("children", [])]
                return Parallel(
                    name,
                    children,
                    success_policy=node_config.get("success_policy", "all"),
                    failure_policy=node_config.get("failure_policy", "one"),
                )

            elif node_type == "inverter":
                child = build_node(node_config.get("child", {}))
                return Inverter(name, child)

            elif node_type == "repeater":
                child = build_node(node_config.get("child", {}))
                return Repeater(
                    name,
                    child,
                    max_repetitions=node_config.get("max_repetitions", 1),
                )

            elif node_type == "limiter":
                child = build_node(node_config.get("child", {}))
                return Limiter(
                    name,
                    child,
                    max_executions=node_config.get("max_executions", 1),
                )

            else:
                raise ValueError(f"Unknown node type: {node_type}")

        root = build_node(config.get("root", {}))
        return BehaviorTree(root, name=config.get("name", "unnamed"))


class BehaviorTreeBuilder:
    """Builder for constructing behavior trees programmatically."""

    def __init__(self, name: str = "unnamed"):
        """Initialize builder.

        Args:
            name: Tree name
        """
        self.name = name
        self.root: Optional[BehaviorNode] = None

    def sequence(self, name: str, *children: BehaviorNode) -> "Sequence":
        """Create sequence node.

        Args:
            name: Node name
            *children: Child nodes

        Returns:
            Sequence node
        """
        return Sequence(name, list(children))

    def selector(self, name: str, *children: BehaviorNode) -> "Selector":
        """Create selector node.

        Args:
            name: Node name
            *children: Child nodes

        Returns:
            Selector node
        """
        return Selector(name, list(children))

    def parallel(self, name: str, *children: BehaviorNode,
                 success_policy: str = "all",
                 failure_policy: str = "one") -> "Parallel":
        """Create parallel node.

        Args:
            name: Node name
            *children: Child nodes
            success_policy: Success policy
            failure_policy: Failure policy

        Returns:
            Parallel node
        """
        return Parallel(name, list(children), success_policy, failure_policy)

    def action(self, name: str, action_func: Callable) -> "Action":
        """Create action node.

        Args:
            name: Node name
            action_func: Action function

        Returns:
            Action node
        """
        return Action(name, action_func)

    def condition(self, name: str, condition_func: Callable) -> "Condition":
        """Create condition node.

        Args:
            name: Node name
            condition_func: Condition function

        Returns:
            Condition node
        """
        return Condition(name, condition_func)

    def inverter(self, name: str, child: BehaviorNode) -> "Inverter":
        """Create inverter decorator.

        Args:
            name: Node name
            child: Child node

        Returns:
            Inverter node
        """
        return Inverter(name, child)

    def repeater(self, name: str, child: BehaviorNode,
                 max_repetitions: int = 1) -> "Repeater":
        """Create repeater decorator.

        Args:
            name: Node name
            child: Child node
            max_repetitions: Number of repetitions

        Returns:
            Repeater node
        """
        return Repeater(name, child, max_repetitions)

    def limiter(self, name: str, child: BehaviorNode,
                max_executions: int = 1) -> "Limiter":
        """Create limiter decorator.

        Args:
            name: Node name
            child: Child node
            max_executions: Maximum executions

        Returns:
            Limiter node
        """
        return Limiter(name, child, max_executions)

    def build(self, root: BehaviorNode) -> "BehaviorTree":
        """Build final tree.

        Args:
            root: Root node

        Returns:
            BehaviorTree instance
        """
        return BehaviorTree(root, name=self.name)
