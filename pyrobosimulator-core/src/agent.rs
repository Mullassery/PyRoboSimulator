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
}
