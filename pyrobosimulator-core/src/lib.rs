use pyo3::prelude::*;

pub mod world;
pub mod agent;
pub mod mission;
pub mod narrative;
pub mod ros2;
pub mod storage;

pub use world::{World, WorldConfig};
pub use agent::{Agent, AgentType};
pub use mission::Mission;
pub use narrative::NarrativeEngine;
pub use ros2::ROS2Bridge;
pub use storage::StorageEngine;

#[pymodule]
fn _core(_py: Python, m: &pyo3::Bound<'_, pyo3::types::PyModule>) -> PyResult<()> {
    m.add_class::<World>()?;
    m.add_class::<Agent>()?;
    m.add_class::<AgentType>()?;
    m.add_class::<Mission>()?;
    m.add_class::<NarrativeEngine>()?;
    m.add_class::<ROS2Bridge>()?;
    m.add_class::<StorageEngine>()?;

    Ok(())
}
