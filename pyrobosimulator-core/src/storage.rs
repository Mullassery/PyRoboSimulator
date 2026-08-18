//! RocksDB-backed event log for world history.
//!
//! Opens a real on-disk RocksDB database and writes/reads real key-value
//! pairs. Keys are `{world_id}\0{timestamp_nanos:020}\0{uuid}` so that
//! seeking to a `{world_id}\0` prefix and iterating forward yields events
//! in insertion order for that world only.

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use rocksdb::{Options, DB};
use uuid::Uuid;

#[pyclass]
pub struct StorageEngine {
    db: DB,
}

#[pymethods]
impl StorageEngine {
    #[new]
    pub fn new(db_path: &str) -> PyResult<Self> {
        let mut opts = Options::default();
        opts.create_if_missing(true);
        let db = DB::open(&opts, db_path).map_err(|e| {
            PyRuntimeError::new_err(format!("failed to open RocksDB at {db_path}: {e}"))
        })?;
        Ok(StorageEngine { db })
    }

    pub fn save_event(&self, world_id: &str, event: String) -> PyResult<()> {
        let key = Self::event_key(world_id);
        self.db
            .put(key, event.as_bytes())
            .map_err(|e| PyRuntimeError::new_err(format!("failed to save event: {e}")))
    }

    pub fn load_world_history(&self, world_id: &str) -> PyResult<Vec<String>> {
        let prefix = format!("{world_id}\0");
        let mut events = Vec::new();
        for item in self.db.prefix_iterator(prefix.as_bytes()) {
            let (key, value) = item
                .map_err(|e| PyRuntimeError::new_err(format!("failed to read event: {e}")))?;
            // RocksDB's prefix_iterator (without a configured prefix extractor)
            // can run past the end of the matching keyspace; stop explicitly.
            if !key.starts_with(prefix.as_bytes()) {
                break;
            }
            events.push(String::from_utf8_lossy(&value).into_owned());
        }
        Ok(events)
    }
}

impl StorageEngine {
    fn event_key(world_id: &str) -> String {
        let ts_nanos = chrono::Utc::now().timestamp_nanos_opt().unwrap_or(0);
        format!("{world_id}\0{ts_nanos:020}\0{}", Uuid::new_v4())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn temp_db_path(name: &str) -> String {
        let dir = std::env::temp_dir().join(format!(
            "pyrobosimulator-storage-test-{name}-{}",
            Uuid::new_v4()
        ));
        dir.to_string_lossy().into_owned()
    }

    #[test]
    fn save_and_load_round_trips_real_events_in_order() {
        let path = temp_db_path("roundtrip");
        let storage = StorageEngine::new(&path).expect("real RocksDB should open");

        storage.save_event("world-a", "spawned agent-1".to_string()).unwrap();
        storage.save_event("world-a", "spawned agent-2".to_string()).unwrap();
        storage.save_event("world-a", "agent-1 collided".to_string()).unwrap();

        let history = storage.load_world_history("world-a").unwrap();
        assert_eq!(
            history,
            vec![
                "spawned agent-1".to_string(),
                "spawned agent-2".to_string(),
                "agent-1 collided".to_string(),
            ]
        );

        let _ = std::fs::remove_dir_all(&path);
    }

    #[test]
    fn load_world_history_is_scoped_to_one_world_id() {
        let path = temp_db_path("scoped");
        let storage = StorageEngine::new(&path).expect("real RocksDB should open");

        storage.save_event("world-a", "event-a".to_string()).unwrap();
        storage.save_event("world-b", "event-b".to_string()).unwrap();

        assert_eq!(storage.load_world_history("world-a").unwrap(), vec!["event-a".to_string()]);
        assert_eq!(storage.load_world_history("world-b").unwrap(), vec!["event-b".to_string()]);

        let _ = std::fs::remove_dir_all(&path);
    }

    #[test]
    fn load_world_history_for_unknown_world_is_empty_not_an_error() {
        let path = temp_db_path("unknown");
        let storage = StorageEngine::new(&path).expect("real RocksDB should open");

        assert_eq!(storage.load_world_history("no-such-world").unwrap(), Vec::<String>::new());

        let _ = std::fs::remove_dir_all(&path);
    }

    #[test]
    fn events_actually_persist_to_disk_across_a_reopen() {
        let path = temp_db_path("persist");
        {
            let storage = StorageEngine::new(&path).expect("real RocksDB should open");
            storage.save_event("world-a", "durable-event".to_string()).unwrap();
        }
        {
            let reopened = StorageEngine::new(&path).expect("real RocksDB should reopen");
            assert_eq!(
                reopened.load_world_history("world-a").unwrap(),
                vec!["durable-event".to_string()]
            );
        }

        let _ = std::fs::remove_dir_all(&path);
    }
}
