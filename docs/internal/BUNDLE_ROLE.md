# Bundle role — Robotics data & fleet loop (deferred)

Portfolio-level decision: **deferred**. See
[`Mullassery/BUNDLES.md`](../Mullassery/blob/main/BUNDLES.md).

- **Role:** Simulation and scenario generation
- **Upstream/downstream:** PyRoboFrames, PyRoboReplay
- **Unlock condition:** Ship the core in the wheel, fix the failing tests, publish a benchmark, then emit ROS 2/LeRobot-compatible output.
- **Current status:** standalone; not a dependency of the other bundle members.

Do not add cross-repo runtime dependencies until the unlock condition is met.
When it is, add a versioned interface (not a git URL), a shared
observation/mission schema, and an end-to-end demo.
