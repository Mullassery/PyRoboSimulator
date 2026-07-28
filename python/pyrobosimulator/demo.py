"""Demo script for PyRoboSimulator Phase 0 PoC."""

import json
import requests
from pathlib import Path

from .schemas import (
    WorldSpec,
    ObjectDefinition,
    MaterialType,
    MaterialDefinition,
    LightingConfig,
    WeatherConfig,
    TimeOfDayConfig,
    RenderingConfig,
    RenderingProfile,
    SensorConfig,
    CameraConfig,
)


def demo_parking_lot_world():
    """Create and load a parking lot world via API."""
    print("=" * 70)
    print("PyRoboSimulator Phase 0 Demo: Parking Lot World")
    print("=" * 70)

    api_url = "http://localhost:8000"

    spec = WorldSpec(
        metadata={
            "name": "parking_lot_demo",
            "description": "200m x 200m parking lot with parked vehicles",
            "demo": True,
        },
        scene_bounds_min=(-100.0, -100.0, 0.0),
        scene_bounds_max=(100.0, 100.0, 50.0),
        materials={
            "asphalt": MaterialDefinition(
                type=MaterialType.ASPHALT,
                color_rgb=(0.15, 0.15, 0.15),
                roughness=0.7,
                emissivity=0.95,
            ),
            "wet_asphalt": MaterialDefinition(
                type=MaterialType.WET_ASPHALT,
                color_rgb=(0.10, 0.10, 0.10),
                roughness=0.3,
                emissivity=0.97,
            ),
            "concrete": MaterialDefinition(
                type=MaterialType.CONCRETE,
                color_rgb=(0.6, 0.6, 0.6),
                roughness=0.8,
                metallic=0.0,
            ),
        },
        objects=[
            ObjectDefinition(
                id="car_001",
                name="Sedan",
                type="vehicle",
                position=(20.0, 20.0, 0.5),
                rotation=(0.0, 0.0, 0.0),
                scale=(1.8, 1.0, 1.5),
                material=MaterialType.METAL,
                physics_enabled=True,
            ),
            ObjectDefinition(
                id="car_002",
                name="SUV",
                type="vehicle",
                position=(20.0, -20.0, 0.5),
                rotation=(0.0, 0.0, 0.0),
                scale=(2.2, 1.1, 1.7),
                material=MaterialType.METAL,
                physics_enabled=True,
            ),
            ObjectDefinition(
                id="building_001",
                name="Parking Garage",
                type="building",
                position=(70.0, 0.0, 0.0),
                scale=(15.0, 30.0, 15.0),
                material=MaterialType.CONCRETE,
                physics_enabled=True,
            ),
            ObjectDefinition(
                id="light_pole_001",
                name="Street Light 1",
                type="pole",
                position=(0.0, 50.0, 0.0),
                scale=(0.3, 0.3, 8.0),
                material=MaterialType.METAL,
                physics_enabled=False,
            ),
        ],
        lighting=LightingConfig(
            sun_intensity=1.0,
            sun_angle_elevation=45.0,
            sun_angle_azimuth=135.0,
            shadow_distance=500.0,
        ),
        weather=WeatherConfig(
            rain_intensity=0.0,
            cloud_coverage=0.3,
            fog_density=0.0,
            wind_speed=0.0,
            temperature_celsius=22.0,
        ),
        time_of_day=TimeOfDayConfig(
            hour=14,
            minute=30,
            day_of_year=180,
            season="summer",
        ),
        rendering=RenderingConfig(
            profile=RenderingProfile.HIGH,
            resolution_width=1920,
            resolution_height=1080,
            fps=30,
            ray_tracing=True,
            motion_blur=False,
            depth_of_field=False,
        ),
        sensors=SensorConfig(
            rgb_enabled=True,
            depth_enabled=True,
            lidar_enabled=True,
            thermal_enabled=True,
            lidar_channels=16,
            lidar_range_max=100.0,
            save_to_disk=True,
        ),
        camera=CameraConfig(
            position=(0.0, -80.0, 10.0),
            looking_at=(0.0, 0.0, 1.0),
            fov_degrees=90.0,
        ),
    )

    print("\n1. Loading world specification via API...")
    load_response = requests.post(
        f"{api_url}/api/v1/load-world",
        json={"spec": json.loads(spec.model_dump_json())},
    )

    if load_response.status_code != 200:
        print(f"✗ Failed to load world: {load_response.status_code}")
        print(load_response.text)
        return

    load_data = load_response.json()
    world_id = load_data["world_id"]
    print(f"✓ World loaded: {world_id}")
    print(f"  Status: {load_data['status']}")
    print(f"  Message: {load_data['message']}")

    print("\n2. Retrieving world specification...")
    get_response = requests.get(f"{api_url}/api/v1/worlds/{world_id}")
    if get_response.status_code == 200:
        retrieved_spec = get_response.json()
        print(f"✓ World retrieved successfully")
        print(f"  Objects: {len(retrieved_spec['objects'])}")
        print(f"  Rendering: {retrieved_spec['rendering']['profile']}")

    print("\n3. Requesting sensor outputs...")
    sensors = [
        ("rgb", "PNG image"),
        ("depth", "Depth map"),
        ("lidar", "Lidar point cloud"),
        ("thermal", "Thermal image"),
    ]

    for sensor_type, description in sensors:
        response = requests.get(
            f"{api_url}/api/v1/sensors/{world_id}/{sensor_type}?frame=0"
        )
        if response.status_code == 200:
            sensor_data = response.json()
            print(f"✓ {sensor_type.upper()}: {description}")
            print(f"  Path: {sensor_data['data_path']}")
            print(f"  Preview: {sensor_data['preview']}")
        else:
            print(f"✗ Failed to get {sensor_type}: {response.status_code}")

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. In Week 2: Implement UE5 scene rendering")
    print("2. In Week 3: Capture actual sensor outputs from UE5")
    print("\nAPI Documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn
    from .api import create_app

    print("\nStarting PyRoboSimulator API server...")
    app = create_app()

    import threading
    import time

    server_thread = threading.Thread(
        target=lambda: uvicorn.run(
            app, host="0.0.0.0", port=8000, log_level="warning"
        ),
        daemon=True,
    )
    server_thread.start()

    time.sleep(2)

    try:
        demo_parking_lot_world()
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API server")
        print("  Make sure it's running: python -m pyrobosimulator.api")
