use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[pyclass(eq, eq_int)]
pub enum AgentType {
    Robot,
    Human,
    NPC,
    Organization,
    Animal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Agent {
    pub id: String,
    pub agent_type: AgentType,
    pub name: String,
    pub position: [f64; 3],
    pub velocity: [f64; 3],
    pub rotation: [f64; 4],
    /// Accumulated this-frame force-derived acceleration (F/mass), reset to
    /// zero at the end of every `step()`. Real Newtonian state -- previously
    /// this struct had no acceleration/mass/step at all, so `velocity` was
    /// set once at construction and never advanced by anything: the pip
    /// core had zero physics simulation despite the project's "100K+
    /// agents, full physics" claim, verified via real-world benchmarking
    /// against PyBullet.
    pub acceleration: [f64; 3],
    pub mass: f64,
    pub max_velocity: f64,
    pub collision_radius: f64,
}

#[pymethods]
impl Agent {
    #[new]
    pub fn new(name: String, agent_type: AgentType) -> Self {
        Agent {
            id: Uuid::new_v4().to_string(),
            agent_type,
            name,
            position: [0.0, 0.0, 0.0],
            velocity: [0.0, 0.0, 0.0],
            rotation: [0.0, 0.0, 0.0, 1.0],
            acceleration: [0.0, 0.0, 0.0],
            mass: 1.0,
            max_velocity: 50.0,
            collision_radius: 0.5,
        }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn agent_type(&self) -> AgentType {
        self.agent_type.clone()
    }

    pub fn position(&self) -> [f64; 3] {
        self.position
    }

    pub fn set_position(&mut self, x: f64, y: f64, z: f64) {
        self.position = [x, y, z];
    }

    pub fn velocity(&self) -> [f64; 3] {
        self.velocity
    }

    pub fn set_velocity(&mut self, x: f64, y: f64, z: f64) {
        self.velocity = [x, y, z];
    }

    pub fn set_mass(&mut self, mass: f64) {
        self.mass = mass.max(f64::MIN_POSITIVE);
    }

    pub fn set_max_velocity(&mut self, max_velocity: f64) {
        self.max_velocity = max_velocity.max(0.0);
    }

    pub fn set_collision_radius(&mut self, radius: f64) {
        self.collision_radius = radius.max(0.0);
    }

    /// Apply a force for this step (F = m*a, so a += F/mass). Cleared to
    /// zero every `step()`, matching how forces work in a real physics
    /// loop -- you re-apply thrust/gravity/etc. every frame, you don't set
    /// it once.
    pub fn apply_force(&mut self, fx: f64, fy: f64, fz: f64) {
        self.acceleration[0] += fx / self.mass;
        self.acceleration[1] += fy / self.mass;
        self.acceleration[2] += fz / self.mass;
    }

    /// Advance this agent's real position/velocity by `dt` seconds using
    /// explicit (forward) Euler integration: position is advanced using the
    /// velocity from the START of this step, then velocity is updated from
    /// this step's accumulated acceleration -- not the other way around,
    /// which would silently be semi-implicit (symplectic) Euler instead, a
    /// different (also valid, but different) integration scheme. Mirrors
    /// the real Python reference implementation in
    /// `backend/src/services/simulation_engine.py::update_physics`.
    pub fn step(&mut self, dt: f64) {
        let old_velocity = self.velocity;

        for i in 0..3 {
            self.velocity[i] += self.acceleration[i] * dt;
        }

        let speed = (self.velocity[0].powi(2) + self.velocity[1].powi(2) + self.velocity[2].powi(2))
            .sqrt();
        if speed > self.max_velocity && speed > 0.0 {
            let scale = self.max_velocity / speed;
            for v in &mut self.velocity {
                *v *= scale;
            }
        }

        for i in 0..3 {
            self.position[i] += old_velocity[i] * dt;
        }

        self.acceleration = [0.0, 0.0, 0.0];
    }

    /// Real Euclidean distance to another agent's current position.
    pub fn distance_to(&self, other: &Agent) -> f64 {
        let dx = self.position[0] - other.position[0];
        let dy = self.position[1] - other.position[1];
        let dz = self.position[2] - other.position[2];
        (dx * dx + dy * dy + dz * dz).sqrt()
    }

    /// True if this agent's and `other`'s collision spheres actually
    /// overlap right now, based on real current positions and radii.
    pub fn collides_with(&self, other: &Agent) -> bool {
        self.distance_to(other) < (self.collision_radius + other.collision_radius)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const EPS: f64 = 1e-9;

    #[test]
    fn velocity_is_stored_and_readable_not_a_dead_field() {
        // Regression test for a real, previously-shipped gap: `velocity` had
        // no getter or setter at all, and was never advanced by anything.
        let mut a = Agent::new("a".into(), AgentType::Robot);
        assert_eq!(a.velocity(), [0.0, 0.0, 0.0]);
        a.set_velocity(1.0, 2.0, 3.0);
        assert_eq!(a.velocity(), [1.0, 2.0, 3.0]);
    }

    #[test]
    fn constant_velocity_moves_position_by_real_kinematics() {
        // No forces applied: x(t) = x0 + v*t, exactly, every step.
        let mut a = Agent::new("a".into(), AgentType::Robot);
        a.set_velocity(2.0, 0.0, 0.0);
        for _ in 0..10 {
            a.step(0.1);
        }
        assert!((a.position()[0] - 2.0).abs() < EPS, "got {:?}", a.position());
    }

    #[test]
    fn constant_acceleration_matches_closed_form_free_fall() {
        // A real, standard kinematics check: under constant acceleration g
        // (no clamping in range), position and velocity after time t should
        // match the closed-form solution v = v0 + g*t, x = x0 + v0*t +
        // 0.5*g*t^2 to within float error accumulated over N discrete
        // explicit-Euler steps (explicit Euler is O(dt) accurate, so a
        // small but real per-step error is expected and tolerated here --
        // this is verifying the *scheme* is real Euler integration, not
        // exact continuous-time physics).
        let mut a = Agent::new("a".into(), AgentType::Robot);
        a.set_max_velocity(1_000.0); // don't clamp -- isolate the integration itself
        let g = -9.81;
        let dt = 0.001;
        let steps = 1000; // 1 real second of simulated time
        for _ in 0..steps {
            a.apply_force(0.0, 0.0, g * a.mass);
            a.step(dt);
        }
        let t = steps as f64 * dt;
        let expected_v = g * t;
        let expected_x = 0.5 * g * t * t;
        assert!(
            (a.velocity()[2] - expected_v).abs() < 0.01,
            "velocity: got {}, expected ~{}",
            a.velocity()[2],
            expected_v
        );
        assert!(
            (a.position()[2] - expected_x).abs() < 0.1,
            "position: got {}, expected ~{}",
            a.position()[2],
            expected_x
        );
    }

    #[test]
    fn velocity_is_clamped_to_max_velocity() {
        let mut a = Agent::new("a".into(), AgentType::Robot);
        a.set_max_velocity(5.0);
        // A huge one-shot force should still leave speed capped at 5.0.
        a.apply_force(0.0, 0.0, 100_000.0);
        a.step(1.0);
        let speed = (a.velocity()[0].powi(2) + a.velocity()[1].powi(2) + a.velocity()[2].powi(2))
            .sqrt();
        assert!(speed <= 5.0 + EPS, "got speed {speed}");
    }

    #[test]
    fn acceleration_resets_every_step_forces_are_not_permanent() {
        let mut a = Agent::new("a".into(), AgentType::Robot);
        a.apply_force(10.0, 0.0, 0.0);
        a.step(1.0);
        let v_after_one_push = a.velocity()[0];
        // No force applied this time -- velocity should NOT keep climbing.
        a.step(1.0);
        assert!((a.velocity()[0] - v_after_one_push).abs() < EPS);
    }

    #[test]
    fn collision_detection_uses_real_positions_and_radii() {
        let mut a = Agent::new("a".into(), AgentType::Robot);
        let mut b = Agent::new("b".into(), AgentType::Robot);
        a.set_position(0.0, 0.0, 0.0);
        b.set_position(0.6, 0.0, 0.0);
        // default radius 0.5 each -> sum 1.0 > distance 0.6 -> real overlap
        assert!(a.collides_with(&b));

        b.set_position(2.0, 0.0, 0.0);
        assert!(!a.collides_with(&b));
    }
}
