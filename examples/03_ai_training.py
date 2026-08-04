"""AI training example - generate synthetic data for perception models."""

from pyrobosimulator import Simulator

# Create simulator for data generation
sim = Simulator(num_agents=50, randomize=True)

# Generate 1000 frames of synthetic training data
dataset = sim.generate_dataset(
    frames=1000,
    include_labels=True,
    randomize_weather=True,
    randomize_lighting=True
)

# Export as training dataset
dataset.export('training_data.parquet')
dataset.create_splits(train=0.8, val=0.1, test=0.1)

print(f"Generated {len(dataset)} training samples")
print("✅ Training dataset ready for model training!")
