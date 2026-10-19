"""Gymnasium/PettingZoo adapter tests with a fake engine."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

pytest.importorskip("gymnasium")
pytest.importorskip("pettingzoo")

from pyrobosimulator.gym_env import RobotGymEnv, RobotParallelEnv


@dataclass
class _Vec:
    x: float
    y: float
    z: float = 0.0


@dataclass
class _Agent:
    position: _Vec
    velocity: _Vec
    goal: _Vec
    reached_goal: bool = False


class _Event:
    event_type = "step_complete"


class _Engine:
    def __init__(self):
        self.agents = {
            0: _Agent(_Vec(0, 0), _Vec(0, 0), _Vec(10, 0)),
            1: _Agent(_Vec(5, 5), _Vec(0, 0), _Vec(0, 0)),
        }
        self.current_time = 0.0
        self.duration = 100.0
        self.total_collisions = 0

    def step(self):
        for agent in self.agents.values():
            agent.position.x += 1
        self.current_time += 1
        return [_Event()]

    def reset(self, seed=None):
        self.current_time = 0.0
        for agent in self.agents.values():
            agent.reached_goal = False


def test_gym_env_spaces_and_step():
    env = RobotGymEnv(_Engine(), agent_id=0)
    obs, _info = env.reset(seed=7)
    assert env.observation_space.contains(obs)
    assert env.action_space.shape == (2,)
    obs, reward, terminated, _truncated, _info = env.step(np.array([1.0, 2.0]))
    assert env.observation_space.contains(obs)
    assert isinstance(reward, float)
    assert terminated is False


def test_parallel_env_step():
    env = RobotParallelEnv(_Engine())
    obs, _infos = env.reset(seed=3)
    assert set(obs) == {"0", "1"}
    actions = {agent: np.array([1.0, 1.0]) for agent in env.agents}
    obs, rewards, _terms, _truncs, _infos = env.step(actions)
    assert set(rewards) == {"0", "1"}
    assert all(isinstance(v, float) for v in rewards.values())
