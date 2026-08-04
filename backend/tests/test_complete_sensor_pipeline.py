"""Complete end-to-end sensor pipeline validation tests (Phase 1C.7)."""

import base64
import io
import time

import numpy as np
import pytest
from PIL import Image

from services.simulation_engine import Agent, SimulationEngine, Vector3
from services.sensor_fusion import SensorFusionPipeline


class TestCompleteSensorPipeline:
    """Complete validation of all 4 sensors + fusion as integrated system."""

    def test_agent_all_sensors_synchronized(self):
        """Test all 4 sensors from agent generate synchronized frames."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 5, 0),
            acceleration=Vector3(0, 0, 0),
        )

        base_time = 1000.0

        # Generate all sensors
        rgb_b64 = agent.generate_rgb_frame(iso=100, color_grading="daylight")
        depth_b64 = agent.generate_depth_map(min_range=0.1, max_range=300, temporal_filter=False)
        lidar_points = agent.generate_lidar_cloud(rain_intensity=0.0, multipath_probability=0.0)
        thermal_b64 = agent.generate_thermal_image(min_temp=-20, max_temp=60)

        # Decode
        rgb_bytes = base64.b64decode(rgb_b64)
        rgb_img = Image.open(io.BytesIO(rgb_bytes))
        rgb_data = np.array(rgb_img)

        depth_bytes = base64.b64decode(depth_b64)
        depth_data = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_data = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        # Validate sensor properties
        assert rgb_data.shape == (480, 640, 3), f"RGB shape {rgb_data.shape} != (480, 640, 3)"
        assert depth_data.shape == (512, 512), f"Depth shape {depth_data.shape} != (512, 512)"
        assert len(lidar_points) > 7000, f"Lidar points {len(lidar_points)} < 7000"
        assert thermal_data.shape == (256, 256), f"Thermal shape {thermal_data.shape} != (256, 256)"

        print(f"\n✓ All sensors generated:")
        print(f"  - RGB: {rgb_data.shape}")
        print(f"  - Depth: {depth_data.shape}")
        print(f"  - Lidar: {len(lidar_points)} points")
        print(f"  - Thermal: {thermal_data.shape}")

    def test_sensor_fusion_integration(self):
        """Test complete sensor fusion with all 4 sensor types."""
        agent = Agent(
            id=1,
            position=Vector3(150, 150, 0),
            velocity=Vector3(3, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        fusion = SensorFusionPipeline(agent_id=agent.id, max_sync_deviation_ms=10.0)

        # Generate all sensors
        base_time = 2000.0

        rgb_b64 = agent.generate_rgb_frame(iso=400, color_grading="daylight")
        depth_b64 = agent.generate_depth_map()
        lidar_points = agent.generate_lidar_cloud(rain_intensity=0.1)
        thermal_b64 = agent.generate_thermal_image()

        # Decode
        rgb_bytes = base64.b64decode(rgb_b64)
        rgb_img = Image.open(io.BytesIO(rgb_bytes))
        rgb_data = np.array(rgb_img)

        depth_bytes = base64.b64decode(depth_b64)
        depth_data = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_data = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        # Push to fusion
        fusion.push_rgb_reading(rgb_data, base_time)
        fusion.push_depth_reading(depth_data, base_time)
        fusion.push_lidar_reading(lidar_points, base_time)
        fusion.push_thermal_reading(thermal_data, base_time)

        # Fuse
        fused = fusion.fuse((agent.position.x, agent.position.y, agent.position.z))

        assert fused is not None, "Fusion failed"
        assert fused.num_sensors_fused == 4, f"Expected 4 sensors, got {fused.num_sensors_fused}"
        assert fused.fusion_latency_ms < 50, f"Latency {fused.fusion_latency_ms}ms > 50ms"

        print(f"\n✓ Complete 4-sensor fusion:")
        print(f"  - Latency: {fused.fusion_latency_ms:.2f}ms")
        print(f"  - Timestamp deviation: {fused.timestamp_deviation_ms:.2f}ms")
        print(f"  - RGB transform: {fused.rgb_to_world.shape}")

    def test_multi_frame_pipeline(self):
        """Test streaming multiple frames through complete pipeline."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(1, 1, 0),
            acceleration=Vector3(0, 0, 0),
        )

        fusion = SensorFusionPipeline(agent_id=agent.id)

        frame_count = 5
        latencies = []

        for frame_idx in range(frame_count):
            # Update agent position
            agent.update_physics(0.033)  # 33ms timestep

            base_time = 3000.0 + frame_idx * 33.33

            # Generate sensors
            rgb_b64 = agent.generate_rgb_frame(iso=100)
            depth_b64 = agent.generate_depth_map()
            lidar_points = agent.generate_lidar_cloud()
            thermal_b64 = agent.generate_thermal_image()

            # Decode
            rgb_bytes = base64.b64decode(rgb_b64)
            rgb_img = Image.open(io.BytesIO(rgb_bytes))
            rgb_data = np.array(rgb_img)

            depth_bytes = base64.b64decode(depth_b64)
            depth_data = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

            thermal_bytes = base64.b64decode(thermal_b64)
            thermal_data = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

            # Push and fuse
            fusion.push_rgb_reading(rgb_data, base_time)
            fusion.push_depth_reading(depth_data, base_time)
            fusion.push_lidar_reading(lidar_points, base_time)
            fusion.push_thermal_reading(thermal_data, base_time)

            fused = fusion.fuse((agent.position.x, agent.position.y, agent.position.z))

            if fused:
                latencies.append(fused.fusion_latency_ms)

        assert len(latencies) == frame_count, f"Expected {frame_count} fused frames"
        avg_latency = np.mean(latencies)

        print(f"\n✓ Multi-frame pipeline (5 frames):")
        print(f"  - Avg latency: {avg_latency:.2f}ms")
        print(f"  - Max latency: {np.max(latencies):.2f}ms")
        assert avg_latency < 50, f"Average latency {avg_latency}ms > 50ms"

    def test_engine_multi_agent_sensors(self):
        """Test simulation engine with multiple agents all sensors."""
        engine = SimulationEngine(num_agents=3, duration=1.0, timestep=0.016)

        # Verify all agents can generate all sensors
        # engine.agents is dict[int, Agent], iterate over values
        for agent in engine.agents.values():
            rgb_b64 = agent.generate_rgb_frame()
            depth_b64 = agent.generate_depth_map()
            lidar_pts = agent.generate_lidar_cloud()
            thermal_b64 = agent.generate_thermal_image()

            assert rgb_b64, f"Agent {agent.id} RGB generation failed"
            assert depth_b64, f"Agent {agent.id} depth generation failed"
            assert len(lidar_pts) > 0, f"Agent {agent.id} lidar generation failed"
            assert thermal_b64, f"Agent {agent.id} thermal generation failed"

        print(f"\n✓ Multi-agent sensor validation ({len(engine.agents)} agents):")
        for agent in engine.agents.values():
            print(f"  - Agent {agent.id}: all 4 sensors operational")

    def test_sensor_range_validation(self):
        """Validate all sensors output within spec ranges."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        # RGB: uint8 [0-255]
        rgb_b64 = agent.generate_rgb_frame()
        rgb_bytes = base64.b64decode(rgb_b64)
        rgb_img = Image.open(io.BytesIO(rgb_bytes))
        rgb_data = np.array(rgb_img)
        assert rgb_data.dtype == np.uint8
        assert np.min(rgb_data) >= 0 and np.max(rgb_data) <= 255

        # Depth: [0.1-300] meters
        depth_b64 = agent.generate_depth_map(min_range=0.1, max_range=300)
        depth_bytes = base64.b64decode(depth_b64)
        depth_data = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)
        assert np.min(depth_data) >= 0.1 and np.max(depth_data) <= 300

        # Lidar: variable point count, xyz coordinates
        lidar_pts = agent.generate_lidar_cloud()
        for pt in lidar_pts[:10]:  # Check first 10 points
            assert len(pt) == 3, "Lidar point must be [x, y, z]"
            assert all(isinstance(c, float) for c in pt)

        # Thermal: [-20, 60] °C
        thermal_b64 = agent.generate_thermal_image(min_temp=-20, max_temp=60)
        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_data = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)
        assert np.min(thermal_data) >= -20 and np.max(thermal_data) <= 60

        print(f"\n✓ Sensor range validation:")
        print(f"  - RGB: uint8 [0-255] ✓")
        print(f"  - Depth: float32 [0.1-300m] ✓")
        print(f"  - Lidar: {len(lidar_pts)} points [x,y,z] ✓")
        print(f"  - Thermal: float32 [-20, 60°C] ✓")

    def test_sensor_effects_applied(self):
        """Validate that realistic sensor effects are actually applied."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 5, 0),  # Fast movement for motion blur
            acceleration=Vector3(0, 0, 0),
        )

        # RGB with motion blur (velocity > 0)
        rgb_with_motion = agent.generate_rgb_frame(iso=100)
        rgb_no_motion = Agent(
            id=2,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),  # Stationary
            acceleration=Vector3(0, 0, 0),
        ).generate_rgb_frame(iso=100)

        # Should be different due to motion blur
        assert rgb_with_motion != rgb_no_motion, "Motion blur not applied"

        # Depth with range enforcement
        depth_limited = agent.generate_depth_map(min_range=10.0, max_range=100.0)
        depth_bytes = base64.b64decode(depth_limited)
        depth_data = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)
        assert np.min(depth_data) >= 10.0, "Min range not enforced"
        assert np.max(depth_data) <= 100.0, "Max range not enforced"

        # Lidar with rain occlusion
        lidar_no_rain = agent.generate_lidar_cloud(rain_intensity=0.0)
        lidar_rain = agent.generate_lidar_cloud(rain_intensity=1.0)
        assert len(lidar_rain) < len(lidar_no_rain), "Rain occlusion not applied"

        # Thermal with different grading
        thermal1 = agent.generate_thermal_image(calibration_error=0.0)
        thermal2 = agent.generate_thermal_image(calibration_error=5.0)
        # Should be different due to calibration error
        assert thermal1 != thermal2, "Calibration error not applied"

        print(f"\n✓ Sensor effects validation:")
        print(f"  - RGB motion blur: different frames ✓")
        print(f"  - Depth range enforcement: [10-100m] ✓")
        print(f"  - Lidar rain occlusion: {len(lidar_rain)} < {len(lidar_no_rain)} ✓")
        print(f"  - Thermal calibration: effects applied ✓")

    def test_complete_pipeline_performance(self):
        """End-to-end performance test: all sensors + fusion in production scenario."""
        print(f"\n✓ Complete pipeline performance (30 fps simulation):")

        agents = [
            Agent(
                id=i,
                position=Vector3(100 + i * 50, 100 + i * 50, 0),
                velocity=Vector3(2 + i, 1 + i, 0),
                acceleration=Vector3(0, 0, 0),
            )
            for i in range(3)
        ]

        fusions = [SensorFusionPipeline(agent_id=agent.id) for agent in agents]

        start = time.time()
        frames_processed = 0

        for frame_idx in range(10):  # 10 frames @ 33ms each = 330ms simulation
            base_time = 5000.0 + frame_idx * 33.33

            for agent_idx, (agent, fusion) in enumerate(zip(agents, fusions)):
                # Physics update
                agent.update_physics(0.033)

                # Generate sensors
                rgb_b64 = agent.generate_rgb_frame(iso=100 + agent_idx * 100)
                depth_b64 = agent.generate_depth_map()
                lidar_pts = agent.generate_lidar_cloud(rain_intensity=0.2)
                thermal_b64 = agent.generate_thermal_image(calibration_error=2.0)

                # Decode
                rgb_bytes = base64.b64decode(rgb_b64)
                rgb_img = Image.open(io.BytesIO(rgb_bytes))
                rgb_data = np.array(rgb_img)

                depth_bytes = base64.b64decode(depth_b64)
                depth_data = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

                thermal_bytes = base64.b64decode(thermal_b64)
                thermal_data = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

                # Fuse
                fusion.push_rgb_reading(rgb_data, base_time)
                fusion.push_depth_reading(depth_data, base_time)
                fusion.push_lidar_reading(lidar_pts, base_time)
                fusion.push_thermal_reading(thermal_data, base_time)

                fused = fusion.fuse((agent.position.x, agent.position.y, agent.position.z))
                if fused:
                    frames_processed += 1

        elapsed = time.time() - start
        fps = frames_processed / (elapsed / 1000.0) if elapsed > 0 else 0

        print(f"  - Frames processed: {frames_processed}")
        print(f"  - Total time: {elapsed:.3f}s")
        print(f"  - Equivalent FPS: {fps:.1f} fps")
        print(f"  - Agents: {len(agents)}")
        print(f"  - Sensors per frame: 4 (RGB, Depth, Lidar, Thermal)")

        # Should handle 3 agents × 10 frames × 4 sensors in reasonable time
        assert elapsed < 30, f"Performance too slow: {elapsed}s for 30 sensor captures"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
