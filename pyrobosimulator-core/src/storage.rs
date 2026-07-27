pub struct StorageEngine;

impl StorageEngine {
    pub fn new(_db_path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        Ok(StorageEngine)
    }

    pub fn save_event(&self, _world_id: &str, _event: String) -> Result<(), Box<dyn std::error::Error>> {
        Ok(())
    }

    pub fn load_world_history(&self, _world_id: &str) -> Result<Vec<String>, Box<dyn std::error::Error>> {
        Ok(Vec::new())
    }
}
