"""Narrative Converter - NL to Simulation Scenario.

Transforms natural language descriptions into executable narrative structures
using Claude AI for semantic understanding.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic

from src.narratives.narrative_definitions import (
    Narrative,
    NarrativeType,
    NarrativeEntity,
    NarrativeGoal,
    NarrativeSequence,
    NarrativeEvent,
    NarrativeEventType,
    NarrativeConstraint,
    AgentRole,
)

logger = logging.getLogger(__name__)


class NarrativeConverter:
    """Converts natural language descriptions to narrative structures.

    Uses Claude AI to understand story descriptions and extract:
    - Entities (robots, obstacles, etc.)
    - Goals (objectives to achieve)
    - Events (timeline of actions)
    - Constraints (rules and safety requirements)
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize converter.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY if not provided)
        """
        self._client = Anthropic(api_key=api_key)
        self._model = "claude-3-5-sonnet-20241022"

    def parse_narrative(self, narrative_text: str) -> Narrative:
        """Parse NL narrative description into Narrative object.

        Args:
            narrative_text: Natural language narrative description

        Returns:
            Parsed Narrative object
        """
        logger.info(f"Parsing narrative ({len(narrative_text)} chars)...")

        # Step 1: Extract narrative metadata
        metadata = self._extract_metadata(narrative_text)

        # Step 2: Extract entities (robots, obstacles, etc.)
        entities = self._extract_entities(narrative_text, metadata)

        # Step 3: Extract goals
        goals = self._extract_goals(narrative_text, metadata)

        # Step 4: Extract event sequence
        sequences = self._extract_sequences(narrative_text, entities, metadata)

        # Step 5: Extract constraints
        constraints = self._extract_constraints(narrative_text, metadata)

        # Assemble narrative
        narrative = Narrative(
            narrative_id=metadata.get("narrative_id", "narrative_0"),
            title=metadata.get("title", "Untitled Narrative"),
            description=metadata.get("description", narrative_text[:200]),
            narrative_type=NarrativeType(metadata.get("type", "custom")),
            environment_type=metadata.get("environment", "urban"),
            time_of_day=metadata.get("time_of_day", "noon"),
            difficulty_level=metadata.get("difficulty", 0.5),
        )

        for entity in entities:
            narrative.add_entity(entity)

        for goal in goals:
            narrative.add_goal(goal)

        for sequence in sequences:
            narrative.add_sequence(sequence)

        for constraint in constraints:
            narrative.add_constraint(constraint)

        logger.info(f"Parsed narrative: {narrative.title} " +
                   f"({len(entities)} entities, {len(goals)} goals, " +
                   f"{len(sequences)} sequences)")

        return narrative

    def _extract_metadata(self, narrative_text: str) -> Dict[str, Any]:
        """Extract high-level narrative metadata."""
        prompt = f"""Analyze this narrative and extract metadata:

NARRATIVE:
{narrative_text}

Extract and return JSON with:
- title: Brief title (max 50 chars)
- description: One-sentence summary
- type: One of [rescue_operation, delivery_mission, exploration, inspection, multi_agent_coordination, adversarial_scenario, training_curriculum, custom]
- environment: One of [urban, industrial, outdoor, indoor]
- time_of_day: One of [dawn, morning, noon, afternoon, dusk, night]
- difficulty: Float 0-1 (0=trivial, 1=extremely hard)
- estimated_duration_sec: Estimated duration in seconds

Return only valid JSON."""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            return json.loads(response.content[0].text)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse metadata: {e}")
            return {
                "title": "Parsed Narrative",
                "description": narrative_text[:100],
                "type": "custom",
                "environment": "urban",
                "time_of_day": "noon",
                "difficulty": 0.5,
                "estimated_duration_sec": 300.0,
            }

    def _extract_entities(self, narrative_text: str, metadata: Dict) -> List[NarrativeEntity]:
        """Extract entities from narrative."""
        prompt = f"""From this narrative, extract all entities (robots, obstacles, people, etc.):

NARRATIVE:
{narrative_text}

For each entity, return JSON array with:
- entity_id: Unique ID (e.g., "robot_0", "obstacle_1")
- entity_type: "robot" | "human" | "obstacle" | "landmark" | "object"
- name: Human-readable name
- role: "protagonist" | "assistant" | "antagonist" | "obstacle" | "observer"
- initial_position: [x, y, z] coordinates
- initial_orientation: [x, y, z, w] quaternion (0,0,0,1 if not specified)
- description: Brief description
- sensor_suite: Sensor config name if robot (e.g., "mobile", "aerial")

Return only valid JSON array."""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            data = json.loads(response.content[0].text)
            entities = []

            for item in data:
                entity = NarrativeEntity(
                    entity_id=item.get("entity_id", f"entity_{len(entities)}"),
                    entity_type=item.get("entity_type", "object"),
                    name=item.get("name", "Unknown"),
                    role=AgentRole(item.get("role", "observer")),
                    initial_position=tuple(item.get("initial_position", [0, 0, 0])),
                    initial_orientation=tuple(item.get("initial_orientation", [0, 0, 0, 1])),
                    description=item.get("description", ""),
                    sensor_suite=item.get("sensor_suite"),
                )
                entities.append(entity)

            return entities
        except Exception as e:
            logger.warning(f"Failed to extract entities: {e}")
            return []

    def _extract_goals(self, narrative_text: str, metadata: Dict) -> List[NarrativeGoal]:
        """Extract goals/objectives from narrative."""
        prompt = f"""From this narrative, extract all goals or objectives:

NARRATIVE:
{narrative_text}

For each goal, return JSON array with:
- goal_id: Unique ID (e.g., "goal_0")
- description: What needs to be achieved
- goal_type: "reach_location" | "pick_object" | "avoid_obstacle" | "follow_path" | "inspect_area" | "coordinate_agents" | etc.
- target: Object (target location, object properties, area to inspect, etc.)
- priority: 0-1 (1 = highest priority)
- time_limit_sec: Time limit or null if none
- success_criteria: Object describing success (e.g., {{"distance": 0.1}})

Return only valid JSON array."""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            data = json.loads(response.content[0].text)
            goals = []

            for item in data:
                goal = NarrativeGoal(
                    goal_id=item.get("goal_id", f"goal_{len(goals)}"),
                    description=item.get("description", ""),
                    goal_type=item.get("goal_type", "custom"),
                    target=item.get("target"),
                    priority=item.get("priority", 1.0),
                    time_limit_sec=item.get("time_limit_sec"),
                    success_criteria=item.get("success_criteria", {}),
                )
                goals.append(goal)

            return goals
        except Exception as e:
            logger.warning(f"Failed to extract goals: {e}")
            return []

    def _extract_sequences(
        self,
        narrative_text: str,
        entities: List[NarrativeEntity],
        metadata: Dict,
    ) -> List[NarrativeSequence]:
        """Extract event sequences from narrative."""
        entity_names = ", ".join([f"{e.name} ({e.entity_id})" for e in entities])

        prompt = f"""From this narrative, extract the timeline of events:

ENTITIES: {entity_names}
NARRATIVE:
{narrative_text}

Create one or more sequences with events. For each event, return:
- event_id: Unique ID
- event_type: "agent_action" | "environment_change" | "sensor_event" | "goal_milestone" | "constraint_violation" | "decision_point" | "outcome"
- timestamp_sec: When it occurs (relative to start)
- description: What happens
- triggering_entity: Which entity triggers this (entity_id)
- affected_entities: List of entity_ids affected
- parameters: Specific details (actions, values, etc.)

Return JSON object:
{{
  "sequences": [
    {{
      "sequence_id": "seq_0",
      "name": "Sequence name",
      "description": "Description",
      "events": [<events>],
      "duration_sec": <total duration>
    }}
  ]
}}"""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            data = json.loads(response.content[0].text)
            sequences = []

            for seq_data in data.get("sequences", []):
                sequence = NarrativeSequence(
                    sequence_id=seq_data.get("sequence_id", f"seq_{len(sequences)}"),
                    name=seq_data.get("name", "Sequence"),
                    description=seq_data.get("description", ""),
                    duration_sec=seq_data.get("duration_sec", 0.0),
                )

                for evt_data in seq_data.get("events", []):
                    event = NarrativeEvent(
                        event_id=evt_data.get("event_id", f"evt_{len(sequence.events)}"),
                        event_type=NarrativeEventType(evt_data.get("event_type", "agent_action")),
                        timestamp_sec=evt_data.get("timestamp_sec", 0.0),
                        description=evt_data.get("description", ""),
                        triggering_entity=evt_data.get("triggering_entity"),
                        affected_entities=evt_data.get("affected_entities", []),
                        parameters=evt_data.get("parameters", {}),
                        confidence=evt_data.get("confidence", 0.8),
                    )
                    sequence.add_event(event)

                sequences.append(sequence)

            return sequences
        except Exception as e:
            logger.warning(f"Failed to extract sequences: {e}")
            return []

    def _extract_constraints(self, narrative_text: str, metadata: Dict) -> List[NarrativeConstraint]:
        """Extract constraints from narrative."""
        prompt = f"""From this narrative, extract all constraints, rules, or safety requirements:

NARRATIVE:
{narrative_text}

For each constraint, return JSON array with:
- constraint_id: Unique ID
- description: What the constraint is
- constraint_type: "safety" | "efficiency" | "realism" | "challenge"
- rule: NL description of the rule
- violation_penalty: Penalty for violation (-1 to 0, where -1 is severe)

Return only valid JSON array."""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            data = json.loads(response.content[0].text)
            constraints = []

            for item in data:
                constraint = NarrativeConstraint(
                    constraint_id=item.get("constraint_id", f"const_{len(constraints)}"),
                    description=item.get("description", ""),
                    constraint_type=item.get("constraint_type", "realism"),
                    rule=item.get("rule", ""),
                    violation_penalty=item.get("violation_penalty", -0.5),
                )
                constraints.append(constraint)

            return constraints
        except Exception as e:
            logger.warning(f"Failed to extract constraints: {e}")
            return []
