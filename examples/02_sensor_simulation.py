"""Sensor simulation example - RGB, Depth, Lidar, Thermal."""

from pyrobosimulator import Simulator, SensorConfig

# Create simulator
sim = Simulator(num_agents=1)

# Configure sensors
sensors = SensorConfig(
    rgb=True,      # RGB camera
    depth=True,    # Depth sensor
    lidar=True,    # Lidar
    thermal=True   # Thermal imaging
)

# Add agent with sensors
agent = sim.add_agent(sensors=sensors)

# Run and capture sensor data
data = sim.run(duration=10, record_sensors=True)

# Access sensor outputs
print(f"RGB frames captured: {len(data.rgb)}")
print(f"Depth frames captured: {len(data.depth)}")
print(f"Lidar scans: {len(data.lidar)}")
print(f"Thermal frames: {len(data.thermal)}")

print("✅ Sensor simulation complete!")
