//! RocksDB-backed event log for world history.
//!
//! **Not implemented.** `rocksdb` is a real dependency of this crate
//! (see Cargo.toml) but no code here actually opens a database or writes
//! to it: `save_event`/`load_world_history` were previously silent no-ops
//! that returned `Ok(())`/`Ok(vec![])` regardless of input, which would
//! make a caller believe events were being persisted when nothing was
//! written. They now return `Err` instead so that failure is visible
//! rather than silently discarding data.

pub struct StorageEngine;

impl StorageEngine {
    pub fn new(_db_path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        Err("StorageEngine is not implemented: no RocksDB database is actually opened here. \
             Wire this up to `rocksdb::DB::open` before relying on it for persistence."
            .into())
    }

    pub fn save_event(&self, _world_id: &str, _event: String) -> Result<(), Box<dyn std::error::Error>> {
        Err("StorageEngine::save_event is not implemented; events are not being persisted.".into())
    }

    pub fn load_world_history(&self, _world_id: &str) -> Result<Vec<String>, Box<dyn std::error::Error>> {
        Err("StorageEngine::load_world_history is not implemented; no history is stored.".into())
    }
}
