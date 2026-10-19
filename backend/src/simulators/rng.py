"""Seeded random-number helpers for simulator backends.

Every stochastic simulator operation (domain randomization, mock sensor
data, raycasts) must draw from a generator threaded from the scenario /
simulator config so that two runs with the same seed produce identical
outputs. This module centralises that construction so no backend calls
``np.random.default_rng()`` without a seed.
"""

from typing import Optional

import numpy as np

#: Seed used when the caller does not supply one. A deterministic default
#: keeps visual/domain-randomization metadata reproducible out of the box;
#: callers that want a different stream can pass an explicit seed.
DEFAULT_SEED = 0


def make_rng(seed: Optional[int] = None) -> np.random.Generator:
    """Return a NumPy ``Generator`` seeded from ``seed``.

    Args:
        seed: Scenario/simulator seed. ``None`` selects :data:`DEFAULT_SEED`
            so the default is still reproducible.

    Returns:
        A fresh ``numpy.random.Generator``.
    """
    return np.random.default_rng(DEFAULT_SEED if seed is None else seed)
