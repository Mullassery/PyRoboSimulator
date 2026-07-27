use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct World {
    pub id: String,
    pub name: String,
    pub creation_time: String,
    pub active_agents: HashMap<String, crate::Agent>,
    pub metadata: WorldMetadata,
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
}
