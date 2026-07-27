use pyo3::prelude::*;

pub mod world;
pub mod agent;
pub mod mission;
pub mod narrative;
pub mod ros2;
pub mod world_gen;
pub mod storage;

pub use world::{World, WorldConfig};
pub use agent::{Agent, AgentType};
pub use mission::Mission;
pub use narrative::NarrativeEngine;

#[pymodule]
fn _core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<World>()?;
    m.add_class::<Agent>()?;
    m.add_class::<Mission>()?;
    m.add_class::<NarrativeEngine>()?;

    Ok(())
}
