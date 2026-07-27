pub struct ROS2Bridge;

impl ROS2Bridge {
    pub fn new() -> Self {
        ROS2Bridge
    }

    pub fn export_world(&self, _world_id: &str) -> Result<String, Box<dyn std::error::Error>> {
        Ok("ROS 2 world export stub".to_string())
    }
}
