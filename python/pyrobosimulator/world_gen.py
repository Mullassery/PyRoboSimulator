"""World generation using Claude Sonnet 5 with extended thinking."""

import json
import logging
from typing import Optional
from anthropic import Anthropic, APIError

from .schemas import WorldSpec

logger = logging.getLogger(__name__)


class WorldGenerator:
    """Generates world specifications from natural language using Claude."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        budget_tokens: int = 10000,
    ):
        """Initialize world generator.

        Args:
            api_key: Anthropic API key (uses env var if not provided)
            model: Claude model ID to use
            budget_tokens: Extended thinking budget tokens
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.budget_tokens = budget_tokens

    def generate(
        self,
        prompt: str,
        reference_spec: Optional[WorldSpec] = None,
    ) -> WorldSpec:
        """Generate world spec from natural language prompt.

        Args:
            prompt: Natural language description of desired world
            reference_spec: Optional reference spec to use as baseline

        Returns:
            Validated WorldSpec

        Raises:
            ValueError: If world generation fails or spec is invalid
        """
        system_prompt = self._build_system_prompt(reference_spec)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                thinking={
                    "type": "enabled",
                    "budget_tokens": self.budget_tokens,
                },
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            json_output = self._extract_json_from_response(response)
            spec_dict = json.loads(json_output)
            spec = WorldSpec(**spec_dict)
            logger.info(f"Generated world spec: {spec.metadata.get('name', 'unnamed')}")
            return spec

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in world spec: {e}")
        except APIError as e:
            raise ValueError(f"Claude API error: {e}")

    def _build_system_prompt(self, reference_spec: Optional[WorldSpec] = None) -> str:
        """Build system prompt for world generation."""
        prompt = """You are an expert world designer for robotics simulation environments.
Your task is to generate a complete world specification (JSON) based on the user's description.

The output MUST be valid JSON following the WorldSpec schema exactly.

Key constraints:
- Materials must be from the predefined set: asphalt, wet_asphalt, concrete, grass, bark, leaves, water, metal, glass, brick, wood
- All numeric values must be within specified ranges
- Positions should be within scene bounds (default: -250 to 250 XY, 0 to 100 Z)
- For robots/vehicles, ensure sufficient clearance (min 2m height recommended)
- Lighting should be realistic for the time of day specified
- Weather effects should be consistent with the season

The WorldSpec JSON structure must include:
{
  "metadata": {"name": "...", "description": "..."},
  "scene_bounds_min": [...],
  "scene_bounds_max": [...],
  "materials": {...},
  "objects": [...],
  "lighting": {...},
  "weather": {...},
  "time_of_day": {...},
  "rendering": {...},
  "sensors": {...},
  "camera": {...} (optional)
}

Generate a complete, self-contained world spec that is immediately ready for use."""

        if reference_spec:
            prompt += f"\n\nBase configuration to extend:\n{json.dumps(reference_spec.model_dump(), indent=2)}"

        return prompt

    def _extract_json_from_response(self, response) -> str:
        """Extract JSON from Claude response, handling thinking blocks."""
        json_content = None

        for block in response.content:
            if block.type == "text":
                text = block.text.strip()
                if text.startswith("{"):
                    json_content = text
                    break
                try:
                    start_idx = text.find("{")
                    end_idx = text.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_content = text[start_idx:end_idx]
                        break
                except (ValueError, IndexError):
                    continue

        if not json_content:
            raise ValueError("No JSON found in Claude response")

        return json_content
