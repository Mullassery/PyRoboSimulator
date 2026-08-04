"""Agent Behavior Interpreter - NL to Robot Behavior.

Interprets narrative descriptions as executable agent behaviors and motion plans.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AgentBehaviorType:
    """Enumeration of agent behavior types."""
    NAVIGATE = "navigate"
    PICK = "pick_object"
    PLACE = "place_object"
    INSPECT = "inspect"
    WAIT = "wait"
    FOLLOW = "follow_entity"
    AVOID = "avoid_entity"
    TRACK = "track_entity"
    COLLABORATE = "collaborate"


class BehaviorPrimitive:
    """Atomic behavior that can be executed."""

    def __init__(
        self,
        behavior_id: str,
        behavior_type: str,
        description: str,
        parameters: Dict[str, Any],
        duration_sec: Optional[float] = None,
        success_criteria: Optional[Dict[str, Any]] = None,
    ):
        """Initialize behavior primitive.

        Args:
            behavior_id: Unique identifier
            behavior_type: Type of behavior
            description: Human-readable description
            parameters: Execution parameters
            duration_sec: Expected duration
            success_criteria: Conditions for success
        """
        self.behavior_id = behavior_id
        self.behavior_type = behavior_type
        self.description = description
        self.parameters = parameters
        self.duration_sec = duration_sec
        self.success_criteria = success_criteria or {}
        self.status = "pending"  # pending, running, completed, failed

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "behavior_id": self.behavior_id,
            "behavior_type": self.behavior_type,
            "description": self.description,
            "parameters": self.parameters,
            "duration_sec": self.duration_sec,
            "success_criteria": self.success_criteria,
            "status": self.status,
        }


class BehaviorPlan:
    """Sequence of behavior primitives for an agent."""

    def __init__(self, agent_id: str, plan_id: str):
        """Initialize behavior plan.

        Args:
            agent_id: Agent executing the plan
            plan_id: Unique plan identifier
        """
        self.agent_id = agent_id
        self.plan_id = plan_id
        self.primitives: List[BehaviorPrimitive] = []
        self.current_primitive_idx = 0

    def add_primitive(self, primitive: BehaviorPrimitive) -> None:
        """Add behavior primitive to plan."""
        self.primitives.append(primitive)

    def get_current_primitive(self) -> Optional[BehaviorPrimitive]:
        """Get currently executing primitive."""
        if self.current_primitive_idx < len(self.primitives):
            return self.primitives[self.current_primitive_idx]
        return None

    def advance(self) -> bool:
        """Move to next primitive.

        Returns:
            True if more primitives, False if plan complete
        """
        self.current_primitive_idx += 1
        return self.current_primitive_idx < len(self.primitives)

    def is_complete(self) -> bool:
        """Check if plan is complete."""
        return self.current_primitive_idx >= len(self.primitives)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "agent_id": self.agent_id,
            "plan_id": self.plan_id,
            "primitive_count": len(self.primitives),
            "current_index": self.current_primitive_idx,
            "primitives": [p.to_dict() for p in self.primitives],
        }


class AgentBehaviorInterpreter:
    """Interprets narrative descriptions as agent behaviors.

    Converts high-level narrative actions into sequences of executable
    behavior primitives that robots can execute.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize interpreter.

        Args:
            api_key: Anthropic API key
        """
        self._client = Anthropic(api_key=api_key)
        self._model = "claude-3-5-sonnet-20241022"

    def interpret_action(
        self,
        agent_id: str,
        action_description: str,
        agent_type: str = "mobile",
        context: Optional[Dict[str, Any]] = None,
    ) -> BehaviorPlan:
        """Interpret narrative action as behavior plan.

        Args:
            agent_id: Agent identifier
            action_description: NL description of action
            agent_type: "mobile" | "aerial" | "humanoid" | "manipulator"
            context: Additional context (environment, constraints, etc.)

        Returns:
            Behavior plan with primitives
        """
        logger.info(f"Interpreting action for {agent_id}: {action_description}")

        # Step 1: Classify action type
        action_type = self._classify_action(action_description, agent_type)

        # Step 2: Extract parameters
        parameters = self._extract_parameters(action_description, action_type, agent_type, context)

        # Step 3: Decompose into primitives
        primitives = self._decompose_to_primitives(
            action_type, parameters, agent_type, context
        )

        # Step 4: Assemble plan
        plan = BehaviorPlan(agent_id, f"plan_{agent_id}_{id(action_description)}")
        for primitive in primitives:
            plan.add_primitive(primitive)

        logger.info(f"Created plan with {len(primitives)} primitives")

        return plan

    def _classify_action(self, description: str, agent_type: str) -> str:
        """Classify action type."""
        prompt = f"""Classify this action into one category:

ACTION: {description}
AGENT TYPE: {agent_type}

Respond with ONE of:
- navigate (move to location)
- pick (grab object)
- place (put down object)
- inspect (examine area/object)
- wait (pause/hold)
- follow (track another agent)
- avoid (move away from)
- track (monitor)
- collaborate (work with others)

Respond with only the category."""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )

        classification = response.content[0].text.strip().lower()
        valid_types = [
            "navigate", "pick", "place", "inspect", "wait",
            "follow", "avoid", "track", "collaborate"
        ]

        return classification if classification in valid_types else "navigate"

    def _extract_parameters(
        self,
        description: str,
        action_type: str,
        agent_type: str,
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract action parameters."""
        context_str = json.dumps(context or {})

        prompt = f"""Extract parameters from this action description:

ACTION: {description}
ACTION TYPE: {action_type}
AGENT TYPE: {agent_type}
CONTEXT: {context_str}

Return JSON with relevant parameters for {action_type}:
- For navigate: target_position [x,y,z], max_speed, path_type
- For pick: object_id, gripper_type, approach_angle
- For place: target_position, surface_type, orientation
- For inspect: target_location, inspection_type, precision
- For follow: target_entity_id, maintain_distance, offset
- For avoid: obstacle_id, min_distance, detour_distance

Return only valid JSON."""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {"description": description}

    def _decompose_to_primitives(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        agent_type: str,
        context: Optional[Dict[str, Any]],
    ) -> List[BehaviorPrimitive]:
        """Decompose action into behavior primitives."""
        primitives = []
        primitive_id = 0

        if action_type == "navigate":
            # Navigation: move to position
            target = parameters.get("target_position", [0, 0, 0])
            primitives.append(BehaviorPrimitive(
                behavior_id=f"nav_{primitive_id}",
                behavior_type=AgentBehaviorType.NAVIGATE,
                description=f"Navigate to {target}",
                parameters={
                    "target_position": target,
                    "max_speed": parameters.get("max_speed", 1.0),
                    "path_type": parameters.get("path_type", "optimal"),
                },
                duration_sec=parameters.get("duration_sec"),
                success_criteria={"distance_to_goal": 0.5},
            ))

        elif action_type == "pick":
            # Pick: approach + grasp + retract
            object_id = parameters.get("object_id", "object_0")
            primitives.append(BehaviorPrimitive(
                behavior_id=f"approach_{primitive_id}",
                behavior_type="approach",
                description=f"Approach {object_id}",
                parameters={
                    "target_object": object_id,
                    "approach_distance": 0.3,
                },
                duration_sec=2.0,
            ))
            primitive_id += 1
            primitives.append(BehaviorPrimitive(
                behavior_id=f"grasp_{primitive_id}",
                behavior_type="grasp",
                description=f"Grasp {object_id}",
                parameters={
                    "target_object": object_id,
                    "gripper_type": parameters.get("gripper_type", "parallel"),
                    "grasp_force": 50.0,
                },
                duration_sec=1.0,
                success_criteria={"object_grasped": True},
            ))
            primitive_id += 1
            primitives.append(BehaviorPrimitive(
                behavior_id=f"retract_{primitive_id}",
                behavior_type="retract",
                description=f"Retract with {object_id}",
                parameters={"retract_distance": 0.2},
                duration_sec=1.0,
            ))

        elif action_type == "inspect":
            # Inspect: move to position + scan + analyze
            target = parameters.get("target_location", [0, 0, 0])
            primitives.append(BehaviorPrimitive(
                behavior_id=f"move_to_inspect_{primitive_id}",
                behavior_type="navigate",
                description=f"Move to inspection point {target}",
                parameters={
                    "target_position": target,
                    "precision_required": True,
                },
                duration_sec=3.0,
            ))
            primitive_id += 1
            primitives.append(BehaviorPrimitive(
                behavior_id=f"scan_{primitive_id}",
                behavior_type="scan",
                description=f"Scan area at {target}",
                parameters={
                    "scan_type": parameters.get("inspection_type", "visual"),
                    "scan_duration_sec": 5.0,
                },
                duration_sec=5.0,
            ))

        elif action_type == "wait":
            # Wait: pause for duration
            duration = parameters.get("duration_sec", 5.0)
            primitives.append(BehaviorPrimitive(
                behavior_id=f"wait_{primitive_id}",
                behavior_type=AgentBehaviorType.WAIT,
                description=f"Wait for {duration} seconds",
                parameters={"duration_sec": duration},
                duration_sec=duration,
            ))

        elif action_type == "follow":
            # Follow: track entity
            target_entity = parameters.get("target_entity_id", "entity_0")
            primitives.append(BehaviorPrimitive(
                behavior_id=f"follow_{primitive_id}",
                behavior_type=AgentBehaviorType.FOLLOW,
                description=f"Follow {target_entity}",
                parameters={
                    "target_entity": target_entity,
                    "maintain_distance": parameters.get("maintain_distance", 2.0),
                    "max_speed": 1.0,
                },
                success_criteria={"distance_maintained": True},
            ))

        else:
            # Generic action
            primitives.append(BehaviorPrimitive(
                behavior_id=f"action_{primitive_id}",
                behavior_type=action_type,
                description=parameters.get("description", description),
                parameters=parameters,
            ))

        return primitives
