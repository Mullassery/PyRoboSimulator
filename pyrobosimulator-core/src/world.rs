use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::Utc;
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct World {
    pub id: String,
    pub name: String,
    pub creation_time: String,
    pub active_agents: HashMap<String, crate::Agent>,
    pub metadata: WorldMetadata,
    /// Applied to every agent every `step()`, standard real-world value by
    /// default (m/s^2, z-up). Set to [0,0,0] via `set_gravity` to disable.
    pub gravity: [f64; 3],
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorldMetadata {
    pub description: Option<String>,
    pub fidelity_level: String,  // Scientific | Robotics | Cinematic
    pub simulation_speed: f64,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorldConfig {
    pub name: String,
    pub description: Option<String>,
    pub fidelity_level: String,
    pub simulation_speed: f64,
}

#[pymethods]
impl World {
    #[new]
    pub fn new(name: String) -> Self {
        World {
            id: Uuid::new_v4().to_string(),
            name,
            creation_time: Utc::now().to_rfc3339(),
            active_agents: HashMap::new(),
            metadata: WorldMetadata::default(),
            gravity: [0.0, 0.0, -9.81],
        }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn creation_time(&self) -> &str {
        &self.creation_time
    }

    pub fn set_fidelity(&mut self, level: String) {
        self.metadata.fidelity_level = level;
    }

    pub fn fidelity(&self) -> &str {
        &self.metadata.fidelity_level
    }

    /// Add (or replace) an agent in this world, keyed by the agent's id.
    pub fn add_agent(&mut self, agent: crate::Agent) {
        self.active_agents.insert(agent.id.clone(), agent);
    }

    /// Remove an agent by id. Returns true if an agent was actually removed.
    pub fn remove_agent(&mut self, agent_id: &str) -> bool {
        self.active_agents.remove(agent_id).is_some()
    }

    /// This agent's real, current state (position/velocity/etc., reflecting
    /// any `step()`s run since it was added) -- `add_agent` takes an `Agent`
    /// by value (PyO3 clones across the FFI boundary), so a caller's own
    /// original Python `Agent` object never sees updates the World applies
    /// internally; this is the real way to observe them. Previously no
    /// getter of any kind existed, so nothing added to a World could ever
    /// be read back out of it.
    pub fn get_agent(&self, agent_id: &str) -> Option<crate::Agent> {
        self.active_agents.get(agent_id).cloned()
    }

    /// Every agent currently in this world, with their real current state.
    pub fn agents(&self) -> Vec<crate::Agent> {
        self.active_agents.values().cloned().collect()
    }

    /// Number of agents currently active in this world.
    pub fn agent_count(&self) -> usize {
        self.active_agents.len()
    }

    pub fn gravity(&self) -> [f64; 3] {
        self.gravity
    }

    pub fn set_gravity(&mut self, x: f64, y: f64, z: f64) {
        self.gravity = [x, y, z];
    }

    /// Advance every agent in this world by `dt` seconds of real physics:
    /// applies this world's gravity as a force (F = m*g) to each agent, then
    /// integrates each agent's own accumulated forces via its real
    /// `Agent::step()`. Previously this method did not exist at all -- the
    /// pip-installable core had no way to advance simulated time or apply
    /// forces to any agent, despite the project's "100K+ agents, full
    /// physics" claim (see `pyrobosimulator-core/src/agent.rs` for the real
    /// per-agent integration this drives).
    pub fn step(&mut self, dt: f64) {
        for agent in self.active_agents.values_mut() {
            let gx = self.gravity[0] * agent.mass;
            let gy = self.gravity[1] * agent.mass;
            let gz = self.gravity[2] * agent.mass;
            agent.apply_force(gx, gy, gz);
            agent.step(dt);
        }
    }

    /// Real pairwise collision check across every agent currently in this
    /// world, based on each agent's actual current position and collision
    /// radius (see `Agent::collides_with`). O(n^2) -- correct for real,
    /// moderate agent counts; a spatial-partitioning broad phase for
    /// 100K+-scale worlds is real, separate future work, not attempted
    /// here (the honest gap right now was that there was no collision
    /// detection at all, real or otherwise).
    pub fn detect_collisions(&self) -> Vec<(String, String)> {
        let mut pairs = Vec::new();
        let agents: Vec<&crate::Agent> = self.active_agents.values().collect();
        for i in 0..agents.len() {
            for j in (i + 1)..agents.len() {
                if agents[i].collides_with(agents[j]) {
                    pairs.push((agents[i].id.clone(), agents[j].id.clone()));
                }
            }
        }
        pairs
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::agent::AgentType;

    #[test]
    fn get_agent_reflects_real_state_after_add() {
        // Regression test for a real, previously-shipped gap: World had no
        // way at all to read an agent's state back out (no get_agent, no
        // agents()) -- add_agent takes Agent by value, so nothing added to
        // a World could ever be observed again through the World itself.
        let mut w = World::new("test".into());
        let mut a = crate::Agent::new("a".into(), AgentType::Robot);
        a.set_position(1.0, 2.0, 3.0);
        let id = a.id().to_string();
        w.add_agent(a);

        let fetched = w.get_agent(&id).expect("agent should be retrievable");
        assert_eq!(fetched.position(), [1.0, 2.0, 3.0]);
        assert!(w.get_agent("does-not-exist").is_none());
        assert_eq!(w.agents().len(), 1);
    }

    #[test]
    fn world_step_applies_real_gravity_to_every_agent() {
        // Regression test for the core finding: the pip-installable World
        // had no step() at all -- nothing in it could ever move. Verify a
        // real agent actually falls under this world's real gravity.
        let mut w = World::new("test".into());
        assert_eq!(w.gravity(), [0.0, 0.0, -9.81]);

        let a = crate::Agent::new("a".into(), AgentType::Robot);
        let id = a.id().to_string();
        w.add_agent(a);

        for _ in 0..100 {
            w.step(0.01); // 1 real second total
        }

        let after = w.get_agent(&id).unwrap();
        assert!(
            after.position()[2] < -4.0,
            "expected the agent to have fallen a real, non-trivial distance under \
             gravity after 1s, got z = {}",
            after.position()[2]
        );
        assert!(after.velocity()[2] < 0.0, "expected real downward velocity");
    }

    #[test]
    fn world_step_with_zero_gravity_leaves_a_resting_agent_in_place() {
        let mut w = World::new("test".into());
        w.set_gravity(0.0, 0.0, 0.0);
        let a = crate::Agent::new("a".into(), AgentType::Robot);
        let id = a.id().to_string();
        w.add_agent(a);

        w.step(1.0);

        let after = w.get_agent(&id).unwrap();
        assert_eq!(after.position(), [0.0, 0.0, 0.0]);
    }

    #[test]
    fn detect_collisions_finds_real_overlapping_agents_only() {
        let mut w = World::new("test".into());
        let mut a = crate::Agent::new("a".into(), AgentType::Robot);
        let mut b = crate::Agent::new("b".into(), AgentType::Robot);
        let mut c = crate::Agent::new("c".into(), AgentType::Robot);
        a.set_position(0.0, 0.0, 0.0);
        b.set_position(0.5, 0.0, 0.0); // overlaps a (radii 0.5 + 0.5 > 0.5)
        c.set_position(50.0, 0.0, 0.0); // far away, no overlap
        let (id_a, id_b) = (a.id().to_string(), b.id().to_string());
        w.add_agent(a);
        w.add_agent(b);
        w.add_agent(c);

        let pairs = w.detect_collisions();
        assert_eq!(pairs.len(), 1);
        let (p1, p2) = &pairs[0];
        let found: std::collections::HashSet<&str> = [p1.as_str(), p2.as_str()].into_iter().collect();
        assert!(found.contains(id_a.as_str()) && found.contains(id_b.as_str()));
    }
}
