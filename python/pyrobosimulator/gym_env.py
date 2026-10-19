"""Optional Gymnasium/PettingZoo environment adapters.

The simulation backend already owns physics and step semantics. These adapters
put a standard RL interface around an existing engine instance so users can use
Stable-Baselines3, RLlib, CleanRL, etc. without changing the simulator.

Install::

    pip install "pyrobosimulator[rl]"
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np


class RLUnavailable(RuntimeError):
    """Raised when gymnasium/pettingzoo is not installed."""


def _require_gym():
    try:
        import gymnasium as gym
        from gymnasium import spaces
    except ImportError as exc:
        raise RLUnavailable(
            'Gymnasium is required. Install with `pip install "pyrobosimulator[rl]"`.'
        ) from exc
    return gym, spaces


def _require_pettingzoo():
    try:
        from pettingzoo import ParallelEnv
    except ImportError as exc:
        raise RLUnavailable(
            'PettingZoo is required. Install with `pip install "pyrobosimulator[rl]"`.'
        ) from exc
    return ParallelEnv


def _agent_state(agent: Any) -> np.ndarray:
    return np.array(
        [
            agent.position.x,
            agent.position.y,
            agent.velocity.x,
            agent.velocity.y,
            agent.goal.x if agent.goal is not None else agent.position.x,
            agent.goal.y if agent.goal is not None else agent.position.y,
        ],
        dtype=np.float32,
    )


class RobotGymEnv:
    """Single-agent Gymnasium environment over a SimulationEngine.

    Action: absolute 2D goal target ``[x, y]`` for the selected agent.
    Observation: ``[x, y, vx, vy, goal_x, goal_y]`` plus other-agent positions.
    """

    metadata: ClassVar[dict] = {"render_modes": []}

    def __init__(self, engine: Any, agent_id: int = 0, goal_tolerance: float = 1.0):
        gym, spaces = _require_gym()
        self.engine = engine
        self.agent_id = agent_id
        self.goal_tolerance = goal_tolerance
        self._gym = gym
        count = max(1, len(getattr(engine, "agents", {})))
        obs_size = 6 + max(0, count - 1) * 2
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_size,), dtype=np.float32
        )
        self.action_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32
        )

    def _agent(self):
        return self.engine.agents[self.agent_id]

    def _obs(self) -> np.ndarray:
        agent = self._agent()
        values = list(_agent_state(agent))
        for other_id, other in self.engine.agents.items():
            if other_id != self.agent_id:
                values.extend([other.position.x, other.position.y])
        return np.asarray(values, dtype=np.float32)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        if seed is not None:
            np.random.seed(seed)
            if hasattr(self.engine, "reset"):
                self.engine.reset(seed=seed)
        elif hasattr(self.engine, "reset"):
            self.engine.reset()
        return self._obs(), {}

    def step(self, action):
        agent = self._agent()
        previous_distance = (
            float(
                np.linalg.norm(
                    [agent.goal.x - agent.position.x, agent.goal.y - agent.position.y]
                )
            )
            if agent.goal is not None
            else 0.0
        )
        agent.goal = (
            type(agent.goal)(float(action[0]), float(action[1]), 0.0)
            if agent.goal is not None
            else agent.goal
        )
        events = self.engine.step()
        new_distance = (
            float(
                np.linalg.norm(
                    [agent.goal.x - agent.position.x, agent.goal.y - agent.position.y]
                )
            )
            if agent.goal is not None
            else 0.0
        )
        reward = previous_distance - new_distance
        terminated = bool(agent.reached_goal)
        if terminated:
            reward += 10.0
        collided = any(
            getattr(event, "event_type", "") == "collision" for event in events
        )
        if collided:
            reward -= 5.0
        truncated = bool(
            getattr(self.engine, "current_time", 0.0)
            >= getattr(self.engine, "duration", float("inf"))
        )
        return (
            self._obs(),
            float(reward),
            terminated,
            truncated,
            {"collisions": getattr(self.engine, "total_collisions", 0)},
        )

    def render(self):
        return None


class RobotParallelEnv:
    """PettingZoo ParallelEnv over all agents in a SimulationEngine.

    Actions are ``{agent_id: [goal_x, goal_y]}``; observations are per-agent
    6-dimensional state vectors.
    """

    metadata: ClassVar[dict] = {"name": "pyrobosimulator_v0", "is_parallelizable": True}

    def __init__(self, engine: Any, goal_tolerance: float = 1.0):
        _require_pettingzoo()
        self.engine = engine
        self.goal_tolerance = goal_tolerance
        self.possible_agents = [str(agent_id) for agent_id in sorted(engine.agents)]
        self.agents = list(self.possible_agents)
        self.observation_spaces = {
            agent: self._space(6) for agent in self.possible_agents
        }
        self.action_spaces = {agent: self._space(2) for agent in self.possible_agents}

    @staticmethod
    def _space(size: int):
        _gym, spaces = _require_gym()
        return spaces.Box(low=-np.inf, high=np.inf, shape=(size,), dtype=np.float32)

    def observation_space(self, agent: str):
        return self.observation_spaces[agent]

    def action_space(self, agent: str):
        return self.action_spaces[agent]

    def _obs_for(self, agent_id: str) -> np.ndarray:
        return _agent_state(self.engine.agents[int(agent_id)])

    def reset(self, seed: int | None = None, options: dict | None = None):
        if seed is not None:
            np.random.seed(seed)
            if hasattr(self.engine, "reset"):
                self.engine.reset(seed=seed)
        elif hasattr(self.engine, "reset"):
            self.engine.reset()
        self.agents = list(self.possible_agents)
        return {agent: self._obs_for(agent) for agent in self.agents}, {}

    def step(self, actions: dict[str, Any]):
        rewards = {agent: 0.0 for agent in self.agents}
        for agent_id, action in actions.items():
            agent = self.engine.agents[int(agent_id)]
            if agent.goal is None:
                continue
            previous = float(
                np.linalg.norm(
                    [agent.goal.x - agent.position.x, agent.goal.y - agent.position.y]
                )
            )
            agent.goal = type(agent.goal)(float(action[0]), float(action[1]), 0.0)
            rewards[agent_id] = previous
        events = self.engine.step()
        terminations: dict[str, bool] = {}
        truncations: dict[str, bool] = {}
        for agent_id in self.agents:
            agent = self.engine.agents[int(agent_id)]
            new_distance = (
                float(
                    np.linalg.norm(
                        [
                            agent.goal.x - agent.position.x,
                            agent.goal.y - agent.position.y,
                        ]
                    )
                )
                if agent.goal is not None
                else 0.0
            )
            rewards[agent_id] = rewards.get(agent_id, 0.0) - new_distance
            terminations[agent_id] = bool(agent.reached_goal)
            truncations[agent_id] = bool(
                getattr(self.engine, "current_time", 0.0)
                >= getattr(self.engine, "duration", float("inf"))
            )
        collided = any(
            getattr(event, "event_type", "") == "collision" for event in events
        )
        if collided:
            for agent_id in list(rewards):
                rewards[agent_id] -= 5.0
        observations = {agent: self._obs_for(agent) for agent in self.agents}
        infos = {agent: {} for agent in self.agents}
        self.agents = [
            a for a in self.agents if not (terminations[a] or truncations[a])
        ]
        return observations, rewards, terminations, truncations, infos


__all__ = ["RLUnavailable", "RobotGymEnv", "RobotParallelEnv"]
