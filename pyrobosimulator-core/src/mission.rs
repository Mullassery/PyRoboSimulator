use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Mission {
    pub id: String,
    pub world_id: String,
    pub name: String,
    pub objectives: Vec<String>,
}

#[pymethods]
impl Mission {
    #[new]
    pub fn new(world_id: String, name: String) -> Self {
        Mission {
            id: Uuid::new_v4().to_string(),
            world_id,
            name,
            objectives: Vec::new(),
        }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn add_objective(&mut self, objective: String) {
        self.objectives.push(objective);
    }
}
