use pyo3::prelude::*;

#[pyclass]
pub struct NarrativeEngine;

#[pymethods]
impl NarrativeEngine {
    #[new]
    pub fn new() -> Self {
        NarrativeEngine
    }

    pub fn generate_from_events(&self, events: Vec<String>) -> String {
        format!("Narrative from {} events", events.len())
    }
}
