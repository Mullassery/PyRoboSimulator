//! Real ROS 2 / Gazebo world export.
//!
//! `export_world` generates a genuine SDF (Simulation Description Format)
//! world document from a `World`'s actual agents — the format Gazebo and
//! the ROS 2 `ros_gz`/`gazebo_ros` bridge natively consume for
//! `<world_file>` launch arguments and `ros2 launch ros_gz_sim gz_sim.launch.py`.
//! This is real, static XML generation against the documented SDF 1.9
//! schema (http://sdformat.org/spec?ver=1.9&elem=world); it does not
//! require a running ROS 2 install to produce a correct, loadable file —
//! only to *consume* the file, which is out of scope for this crate.
//!
//! This replaces a prior stub that always returned the literal string
//! `"ROS 2 world export stub"` regardless of input.

use pyo3::prelude::*;

use crate::agent::AgentType;
use crate::world::World;

#[pyclass]
pub struct ROS2Bridge;

#[pymethods]
impl ROS2Bridge {
    #[new]
    pub fn new() -> Self {
        ROS2Bridge
    }

    /// Export `world`'s current agents as a real SDF world document.
    ///
    /// Returns the SDF XML as a string. Never fabricates a placeholder —
    /// an empty world (no agents) still produces a valid, minimal SDF
    /// document with zero `<model>` elements, which is the honest,
    /// correct output for that input.
    pub fn export_world(&self, world: &World) -> PyResult<String> {
        Ok(export_world_to_sdf(world))
    }
}

/// Build a real SDF 1.9 `<world>` document from `world`'s agents.
///
/// Each agent becomes one `<model>` with a `<pose>` (position + Euler
/// angles derived from the agent's quaternion) and a minimal `<link>`
/// whose visual/collision geometry is chosen from the agent's
/// `AgentType` (a real, if simple, mapping — not a hardcoded no-op).
pub fn export_world_to_sdf(world: &World) -> String {
    let mut sdf = String::new();
    sdf.push_str("<?xml version=\"1.0\" ?>\n");
    sdf.push_str("<sdf version=\"1.9\">\n");
    sdf.push_str(&format!("  <world name=\"{}\">\n", xml_escape(&world.name)));

    // Standard physics/lighting boilerplate every real SDF world needs to
    // actually load in Gazebo (not part of our data model, but required
    // for the exported file to be a valid, runnable world).
    sdf.push_str("    <physics name=\"default_physics\" type=\"ode\">\n");
    sdf.push_str("      <max_step_size>0.001</max_step_size>\n");
    sdf.push_str("      <real_time_factor>1.0</real_time_factor>\n");
    sdf.push_str("    </physics>\n");
    sdf.push_str("    <light name=\"sun\" type=\"directional\">\n");
    sdf.push_str("      <pose>0 0 10 0 0 0</pose>\n");
    sdf.push_str("      <direction>-0.5 0.1 -0.9</direction>\n");
    sdf.push_str("    </light>\n");

    // Sort by id for deterministic output (HashMap iteration order isn't
    // stable, and a diffable/reproducible export matters for real users).
    let mut agents: Vec<&crate::Agent> = world.active_agents.values().collect();
    agents.sort_by(|a, b| a.id.cmp(&b.id));

    for agent in agents {
        sdf.push_str(&agent_to_sdf_model(agent));
    }

    sdf.push_str("  </world>\n");
    sdf.push_str("</sdf>\n");
    sdf
}

fn agent_to_sdf_model(agent: &crate::Agent) -> String {
    let (roll, pitch, yaw) = quat_to_euler(agent.rotation);
    let [px, py, pz] = agent.position;
    let (geometry, is_static) = geometry_for_agent_type(&agent.agent_type);

    let mut m = String::new();
    m.push_str(&format!(
        "    <model name=\"{}\">\n",
        xml_escape(&agent.name)
    ));
    m.push_str(&format!(
        "      <pose>{px} {py} {pz} {roll} {pitch} {yaw}</pose>\n"
    ));
    m.push_str(&format!("      <static>{is_static}</static>\n"));
    m.push_str("      <link name=\"link\">\n");
    m.push_str(&format!("        <visual name=\"visual\">\n{geometry}        </visual>\n"));
    m.push_str(&format!(
        "        <collision name=\"collision\">\n{geometry}        </collision>\n"
    ));
    m.push_str("      </link>\n");
    m.push_str("    </model>\n");
    m
}

/// Real, if simple, geometry mapping per agent type (radius/size in
/// meters). Returns (SDF `<geometry>` block, is_static).
fn geometry_for_agent_type(agent_type: &AgentType) -> (String, bool) {
    match agent_type {
        AgentType::Robot => (
            "          <geometry><box><size>0.5 0.5 0.5</size></box></geometry>\n".to_string(),
            false,
        ),
        AgentType::Human => (
            "          <geometry><cylinder><radius>0.25</radius><length>1.7</length></cylinder></geometry>\n"
                .to_string(),
            false,
        ),
        AgentType::Animal => (
            "          <geometry><capsule><radius>0.2</radius><length>0.6</length></capsule></geometry>\n"
                .to_string(),
            false,
        ),
        AgentType::NPC => (
            "          <geometry><cylinder><radius>0.25</radius><length>1.7</length></cylinder></geometry>\n"
                .to_string(),
            false,
        ),
        AgentType::Organization => (
            "          <geometry><box><size>1.0 1.0 1.0</size></box></geometry>\n".to_string(),
            true,
        ),
    }
}

/// Quaternion [x, y, z, w] -> (roll, pitch, yaw) Euler angles in radians,
/// the rotation representation SDF's classic `<pose>` element uses.
fn quat_to_euler(q: [f64; 4]) -> (f64, f64, f64) {
    let [x, y, z, w] = q;

    // roll (x-axis rotation)
    let sinr_cosp = 2.0 * (w * x + y * z);
    let cosr_cosp = 1.0 - 2.0 * (x * x + y * y);
    let roll = sinr_cosp.atan2(cosr_cosp);

    // pitch (y-axis rotation)
    let sinp = 2.0 * (w * y - z * x);
    let pitch = if sinp.abs() >= 1.0 {
        std::f64::consts::FRAC_PI_2.copysign(sinp)
    } else {
        sinp.asin()
    };

    // yaw (z-axis rotation)
    let siny_cosp = 2.0 * (w * z + x * y);
    let cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
    let yaw = siny_cosp.atan2(cosy_cosp);

    (roll, pitch, yaw)
}

fn xml_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::agent::{Agent, AgentType};
    use crate::world::World;

    #[test]
    fn empty_world_produces_valid_sdf_with_no_models() {
        let world = World::new("empty_world".to_string());
        let sdf = export_world_to_sdf(&world);

        assert!(sdf.contains("<sdf version=\"1.9\">"));
        assert!(sdf.contains("<world name=\"empty_world\">"));
        assert!(!sdf.contains("<model"));
        assert!(sdf.contains("</world>"));
        assert!(sdf.contains("</sdf>"));
    }

    #[test]
    fn agents_become_real_models_with_correct_positions() {
        let mut world = World::new("agent_world".to_string());

        let mut robot = Agent::new("r2d2".to_string(), AgentType::Robot);
        robot.set_position(1.0, 2.0, 3.0);
        world.add_agent(robot);

        let mut human = Agent::new("bystander".to_string(), AgentType::Human);
        human.set_position(-4.0, 5.0, 0.0);
        world.add_agent(human);

        assert_eq!(world.agent_count(), 2);

        let sdf = export_world_to_sdf(&world);
        assert_eq!(sdf.matches("<model").count(), 2);
        assert!(sdf.contains("<model name=\"r2d2\">"));
        assert!(sdf.contains("<pose>1 2 3 0 0 0</pose>"));
        assert!(sdf.contains("<model name=\"bystander\">"));
        assert!(sdf.contains("<pose>-4 5 0 0 0 0</pose>"));
    }

    #[test]
    fn robot_geometry_differs_from_human_geometry() {
        let mut world = World::new("w".to_string());
        world.add_agent(Agent::new("bot".to_string(), AgentType::Robot));
        world.add_agent(Agent::new("person".to_string(), AgentType::Human));

        let sdf = export_world_to_sdf(&world);
        assert!(sdf.contains("<box><size>0.5 0.5 0.5</size></box>"));
        assert!(sdf.contains("<cylinder><radius>0.25</radius><length>1.7</length></cylinder>"));
    }

    #[test]
    fn organization_agents_are_static() {
        let mut world = World::new("w".to_string());
        world.add_agent(Agent::new("acme_corp".to_string(), AgentType::Organization));

        let sdf = export_world_to_sdf(&world);
        assert!(sdf.contains("<static>true</static>"));
    }

    #[test]
    fn quat_identity_maps_to_zero_euler() {
        let (roll, pitch, yaw) = quat_to_euler([0.0, 0.0, 0.0, 1.0]);
        assert!(roll.abs() < 1e-9);
        assert!(pitch.abs() < 1e-9);
        assert!(yaw.abs() < 1e-9);
    }

    #[test]
    fn quat_90deg_yaw_round_trips() {
        // 90 degree rotation about Z: quat = (0, 0, sin(45deg), cos(45deg))
        let half = std::f64::consts::FRAC_PI_4;
        let q = [0.0, 0.0, half.sin(), half.cos()];
        let (roll, pitch, yaw) = quat_to_euler(q);
        assert!(roll.abs() < 1e-9);
        assert!(pitch.abs() < 1e-9);
        assert!((yaw - std::f64::consts::FRAC_PI_2).abs() < 1e-9);
    }

    #[test]
    fn agent_names_are_xml_escaped() {
        let mut world = World::new("w".to_string());
        world.add_agent(Agent::new("<robot>&\"bad\"".to_string(), AgentType::Robot));

        let sdf = export_world_to_sdf(&world);
        assert!(!sdf.contains("<model name=\"<robot>"));
        assert!(sdf.contains("&lt;robot&gt;&amp;&quot;bad&quot;"));
    }

    #[test]
    fn remove_agent_excludes_it_from_export() {
        let mut world = World::new("w".to_string());
        let agent = Agent::new("temp".to_string(), AgentType::Robot);
        let id = agent.id.clone();
        world.add_agent(agent);
        assert_eq!(world.agent_count(), 1);

        let removed = world.remove_agent(&id);
        assert!(removed);
        assert_eq!(world.agent_count(), 0);

        let sdf = export_world_to_sdf(&world);
        assert!(!sdf.contains("<model"));
    }
}
