//! Natural-language world generation.
//!
//! **Not implemented.** A real implementation needs an LLM call (to turn a
//! free-text description into a structured world spec) plus a constraint
//! validator for the result — a genuine feature-development effort, not a
//! bug fix, and out of scope for this pass (see the Python-side
//! `narratives`/`ari` packages for the equivalent, real, Claude-backed
//! functionality already implemented at the FastAPI layer). This type
//! intentionally returns `Err` rather than a fake success string so
//! callers can't mistake "not built yet" for "ran and did nothing".

pub struct WorldGenerator;

impl WorldGenerator {
    pub fn new() -> Self {
        WorldGenerator
    }

    pub fn from_description(&self, _description: &str) -> Result<String, Box<dyn std::error::Error>> {
        Err("WorldGenerator::from_description is not implemented in pyrobosimulator-core; \
             natural-language world generation requires an LLM integration that hasn't been \
             built here yet.".into())
    }
}
