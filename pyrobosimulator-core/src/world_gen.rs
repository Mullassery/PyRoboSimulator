pub struct WorldGenerator;

impl WorldGenerator {
    pub fn new() -> Self {
        WorldGenerator
    }

    pub fn from_description(&self, _description: &str) -> Result<String, Box<dyn std::error::Error>> {
        Ok("World generation from NL stub".to_string())
    }
}
