"""Basic PyRoboSimulator example - create and run a simulation."""

from pyrobosimulator import Simulator

# Create simulator with 10 agents
sim = Simulator(num_agents=10, world_size=1000)

# Add terrain
sim.add_terrain('forest', density=0.3)
sim.add_terrain('grass', density=0.7)

# Run simulation
results = sim.run(duration=100)

# Analyze results
print(f"Agents spawned: {len(results.agents)}")
print(f"Collisions detected: {results.collision_count}")
print(f"Average distance traveled: {results.avg_distance:.2f}m")

print("✅ Simulation complete!")
