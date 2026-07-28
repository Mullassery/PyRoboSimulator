"""Tests for world specification schemas."""

import pytest
from ..schemas import (
    MaterialDefinition,
    MaterialType,
    ObjectDefinition,
    LightingConfig,
    WeatherConfig,
    TimeOfDayConfig,
    RenderingConfig,
    RenderingProfile,
    SensorConfig,
    CameraConfig,
    WorldSpec,
)


class TestMaterialDefinition:
    """Test PBR material definitions."""

    def test_material_creation_with_defaults(self):
        mat = MaterialDefinition(
            type=MaterialType.ASPHALT,
            color_rgb=(0.2, 0.2, 0.2),
        )
        assert mat.type == MaterialType.ASPHALT
        assert mat.roughness == 0.5
        assert mat.metallic == 0.0
        assert mat.emissivity == 0.0

    def test_material_custom_properties(self):
        mat = MaterialDefinition(
            type=MaterialType.WET_ASPHALT,
            color_rgb=(0.15, 0.15, 0.15),
            roughness=0.3,
            emissivity=0.95,
        )
        assert mat.roughness == 0.3
        assert mat.emissivity == 0.95

    def test_material_validates_ranges(self):
        with pytest.raises(ValueError):
            MaterialDefinition(
                type=MaterialType.ASPHALT,
                color_rgb=(0.5, 0.5, 0.5),
                roughness=1.5,  # Invalid: > 1.0
            )


class TestObjectDefinition:
    """Test scene object definitions."""

    def test_object_creation(self):
        obj = ObjectDefinition(
            id="building_001",
            name="Main Building",
            type="building",
            position=(10.0, 20.0, 0.0),
            material=MaterialType.BRICK,
        )
        assert obj.id == "building_001"
        assert obj.position == (10.0, 20.0, 0.0)
        assert obj.rotation == (0.0, 0.0, 0.0)

    def test_object_with_rotation(self):
        obj = ObjectDefinition(
            id="vehicle_001",
            name="Car",
            type="vehicle",
            position=(0.0, 0.0, 0.5),
            rotation=(0.0, 0.0, 1.57),  # 90 degrees
            scale=(2.0, 1.0, 1.5),
        )
        assert obj.scale == (2.0, 1.0, 1.5)


class TestLightingConfig:
    """Test lighting configuration."""

    def test_default_lighting(self):
        lighting = LightingConfig()
        assert lighting.sun_intensity == 1.0
        assert lighting.sun_angle_elevation == 45.0
        assert lighting.ambient_intensity == 0.3

    def test_sunset_lighting(self):
        lighting = LightingConfig(
            sun_angle_elevation=-10.0,
            sun_angle_azimuth=280.0,
        )
        assert lighting.sun_angle_elevation == -10.0
        assert lighting.sun_angle_azimuth == 280.0


class TestWeatherConfig:
    """Test weather configuration."""

    def test_clear_weather(self):
        weather = WeatherConfig(
            rain_intensity=0.0,
            cloud_coverage=0.1,
            fog_density=0.0,
        )
        assert weather.rain_intensity == 0.0
        assert weather.cloud_coverage == 0.1

    def test_rainy_weather(self):
        weather = WeatherConfig(
            rain_intensity=0.8,
            cloud_coverage=0.9,
            wind_speed=5.0,
        )
        assert weather.rain_intensity == 0.8
        assert weather.wind_speed == 5.0


class TestTimeOfDayConfig:
    """Test time and season settings."""

    def test_midday(self):
        time = TimeOfDayConfig(hour=12, minute=0, season="summer")
        assert time.hour == 12
        assert time.season == "summer"

    def test_sunrise(self):
        time = TimeOfDayConfig(hour=6, minute=30, season="spring")
        assert time.hour == 6


class TestRenderingConfig:
    """Test rendering configuration."""

    def test_cinematic_profile(self):
        render = RenderingConfig(
            profile=RenderingProfile.CINEMATIC,
            resolution_width=3840,
            resolution_height=2160,
            fps=24,
            ray_tracing=True,
        )
        assert render.profile == RenderingProfile.CINEMATIC
        assert render.resolution_width == 3840

    def test_edge_profile(self):
        render = RenderingConfig(
            profile=RenderingProfile.EDGE,
            resolution_width=640,
            resolution_height=480,
            fps=15,
            ray_tracing=False,
        )
        assert render.profile == RenderingProfile.EDGE
        assert render.ray_tracing is False


class TestSensorConfig:
    """Test sensor configuration."""

    def test_all_sensors_enabled(self):
        sensors = SensorConfig(
            rgb_enabled=True,
            depth_enabled=True,
            lidar_enabled=True,
            thermal_enabled=True,
        )
        assert sensors.rgb_enabled is True
        assert sensors.lidar_channels == 16

    def test_lidar_configuration(self):
        sensors = SensorConfig(
            lidar_enabled=True,
            lidar_channels=32,
            lidar_range_max=200.0,
        )
        assert sensors.lidar_channels == 32
        assert sensors.lidar_range_max == 200.0


class TestCameraConfig:
    """Test camera configuration."""

    def test_camera_setup(self):
        camera = CameraConfig(
            position=(0.0, 0.0, 2.0),
            looking_at=(10.0, 0.0, 0.0),
            fov_degrees=90.0,
        )
        assert camera.position == (0.0, 0.0, 2.0)
        assert camera.fov_degrees == 90.0


class TestWorldSpec:
    """Test complete world specification."""

    def test_minimal_world(self):
        spec = WorldSpec()
        assert spec.scene_bounds_min == (-250.0, -250.0, 0.0)
        assert spec.scene_bounds_max == (250.0, 250.0, 100.0)
        assert len(spec.objects) == 0

    def test_world_with_objects(self):
        obj = ObjectDefinition(
            id="test_obj",
            name="Test",
            position=(0.0, 0.0, 0.0),
        )
        spec = WorldSpec(objects=[obj])
        assert len(spec.objects) == 1

    def test_world_serialization(self):
        spec = WorldSpec(
            metadata={"name": "test_world"},
            objects=[
                ObjectDefinition(
                    id="obj1",
                    name="Object 1",
                    position=(0.0, 0.0, 0.0),
                )
            ],
        )
        spec_dict = spec.model_dump()
        assert spec_dict["metadata"]["name"] == "test_world"
        assert len(spec_dict["objects"]) == 1

        spec_reconstructed = WorldSpec(**spec_dict)
        assert spec_reconstructed.metadata["name"] == "test_world"

    def test_parking_lot_world(self):
        """Test a realistic parking lot world spec."""
        spec = WorldSpec(
            metadata={
                "name": "parking_lot_demo",
                "description": "200m parking lot",
            },
            scene_bounds_min=(-100.0, -100.0, 0.0),
            scene_bounds_max=(100.0, 100.0, 50.0),
            materials={
                "asphalt": MaterialDefinition(
                    type=MaterialType.ASPHALT,
                    color_rgb=(0.2, 0.2, 0.2),
                    roughness=0.7,
                ),
                "wet_asphalt": MaterialDefinition(
                    type=MaterialType.WET_ASPHALT,
                    color_rgb=(0.15, 0.15, 0.15),
                    roughness=0.3,
                ),
            },
            objects=[
                ObjectDefinition(
                    id="car_001",
                    name="Parked Car",
                    type="vehicle",
                    position=(10.0, 10.0, 0.5),
                    material=MaterialType.METAL,
                ),
            ],
            lighting=LightingConfig(
                sun_intensity=1.0,
                sun_angle_elevation=45.0,
            ),
            weather=WeatherConfig(
                rain_intensity=0.0,
                cloud_coverage=0.3,
            ),
            rendering=RenderingConfig(
                profile=RenderingProfile.HIGH,
                resolution_width=1920,
                resolution_height=1080,
            ),
            sensors=SensorConfig(
                rgb_enabled=True,
                depth_enabled=True,
                lidar_enabled=True,
            ),
        )

        assert spec.metadata["name"] == "parking_lot_demo"
        assert len(spec.materials) == 2
        assert len(spec.objects) == 1
        assert spec.rendering.profile == RenderingProfile.HIGH
