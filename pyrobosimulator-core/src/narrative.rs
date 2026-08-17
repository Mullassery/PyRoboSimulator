//! **Not implemented in the Rust core.** `generate_from_events` previously
//! returned a hardcoded `"Narrative from {n} events"` string regardless of
//! the actual event content — a fake result, not a real narrative. Real
//! event-to-narrative generation needs an LLM call; that functionality
//! already exists for real (Claude-backed) at the Python/FastAPI layer in
//! `backend/src/narratives/` (see `narrative_converter.py`,
//! `agent_interpreter.py`), which is the supported way to do this today.
//! This type is kept only so the pyo3 module's public shape doesn't change
//! out from under callers; it now reports failure honestly instead of
//! returning a templated non-answer.

use pyo3::prelude::*;

#[pyclass]
pub struct NarrativeEngine;

#[pymethods]
impl NarrativeEngine {
    #[new]
    pub fn new() -> Self {
        NarrativeEngine
    }

    pub fn generate_from_events(&self, events: Vec<String>) -> PyResult<String> {
        let _ = events;
        Err(pyo3::exceptions::PyNotImplementedError::new_err(
            "NarrativeEngine.generate_from_events is not implemented in pyrobosimulator-core. \
             Use the real, Claude-backed narrative generation in \
             backend.src.narratives.narrative_converter instead.",
        ))
    }
}
