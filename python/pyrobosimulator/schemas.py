"""World specification schemas for PyRoboSimulator."""

from enum import Enum
from typing import Optional, Dict, List, Tuple
from pydantic import BaseModel, Field, ConfigDict


class MaterialType(str, Enum):
    """Supported PBR material types."""
    ASPHALT = "asphalt"
    WET_ASPHALT = "wet_asphalt"
    CONCRETE = "concrete"
    GRASS = "grass"
    BARK = "bark"
    LEAVES = "leaves"
    WATER = "water"
    METAL = "metal"
    GLASS = "glass"
    BRICK = "brick"
    WOOD = "wood"


class MaterialDefinition(BaseModel):
    """PBR material definition with physical properties."""
    type: MaterialType
    color_rgb: Tuple[float, float, float] = Field(
        ..., description="RGB color (0.0-1.0)"
    )
    roughness: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Surface roughness (0=glossy, 1=rough)"
    )
    metallic: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Metallic factor (0=dielectric, 1=metal)"
    )
    normal_strength: float = Field(
        default=1.0, ge=0.0, le=2.0,
        description="Normal map intensity"
    )
    emissivity: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Thermal emissivity (0=reflective, 1=blackbody)"
    )


class ObjectDefinition(BaseModel):
    """Scene object (building, vehicle, tree, etc.)."""
    id: str
    name: str
    type: str = Field(
        default="generic",
        description="Object type: building, vehicle, tree, pole, sign, etc."
    )
    position: Tuple[float, float, float] = Field(
        ..., description="XYZ position in world"
    )
    rotation: Tuple[float, float, float] = Field(
        default=(0.0, 0.0, 0.0),
        description="Roll, pitch, yaw in radians"
    )
    scale: Tuple[float, float, float] = Field(
        default=(1.0, 1.0, 1.0),
        description="XYZ scale multipliers"
    )
    material: Optional[MaterialType] = None
    physics_enabled: bool = Field(
        default=True,
        description="Whether object has physics collision"
    )


class LightingConfig(BaseModel):
    """Dynamic lighting configuration."""
    sun_intensity: float = Field(
        default=1.0, ge=0.0, le=2.0,
        description="Sun brightness multiplier"
    )
    sun_angle_elevation: float = Field(
        default=45.0, ge=-90.0, le=90.0,
        description="Sun elevation angle in degrees"
    )
    sun_angle_azimuth: float = Field(
        default=0.0, ge=0.0, le=360.0,
        description="Sun azimuth angle in degrees"
    )
    ambient_intensity: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Ambient light intensity"
    )
    shadow_distance: float = Field(
        default=500.0, gt=0.0,
        description="Shadow rendering distance in meters"
    )


class WeatherConfig(BaseModel):
    """Weather and atmospheric effects."""
    rain_intensity: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Rain intensity (0=none, 1=heavy)"
    )
    cloud_coverage: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Cloud coverage (0=clear, 1=overcast)"
    )
    fog_density: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Fog density"
    )
    fog_color_rgb: Tuple[float, float, float] = Field(
        default=(0.8, 0.8, 0.9),
        description="Fog color"
    )
    fog_distance: float = Field(
        default=1000.0, gt=0.0,
        description="Fog viewing distance in meters"
    )
    wind_speed: float = Field(
        default=0.0, ge=0.0,
        description="Wind speed in m/s"
    )
    temperature_celsius: float = Field(
        default=20.0,
        description="Air temperature for thermal simulation"
    )


class TimeOfDayConfig(BaseModel):
    """Time and seasonal settings."""
    hour: int = Field(default=12, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    day_of_year: int = Field(
        default=180, ge=1, le=365,
        description="1-365 for seasonal color/lighting"
    )
    season: str = Field(
        default="summer",
        description="spring, summer, fall, winter for vegetation/colors"
    )


class RenderingProfile(str, Enum):
    """Rendering quality profiles."""
    CINEMATIC = "cinematic"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    EDGE = "edge"


class RenderingConfig(BaseModel):
    """Rendering quality and output settings."""
    profile: RenderingProfile = RenderingProfile.MEDIUM
    resolution_width: int = Field(
        default=1920, ge=640, le=8192,
        description="Output width in pixels"
    )
    resolution_height: int = Field(
        default=1080, ge=480, le=8192,
        description="Output height in pixels"
    )
    fps: int = Field(
        default=30, ge=1, le=120,
        description="Target frames per second"
    )
    ray_tracing: bool = Field(
        default=True,
        description="Enable ray tracing (high quality)"
    )
    motion_blur: bool = Field(
        default=False,
        description="Enable motion blur"
    )
    depth_of_field: bool = Field(
        default=False,
        description="Enable depth of field"
    )


class SensorConfig(BaseModel):
    """Sensor output configuration."""
    rgb_enabled: bool = Field(default=True)
    depth_enabled: bool = Field(default=True)
    lidar_enabled: bool = Field(default=True)
    thermal_enabled: bool = Field(default=True)
    lidar_channels: int = Field(default=16, ge=1, le=128)
    lidar_range_max: float = Field(default=100.0, gt=0.0)
    save_to_disk: bool = Field(default=True)
    output_format_rgb: str = Field(default="png")
    output_format_depth: str = Field(default="npy")
    output_format_lidar: str = Field(default="pcd")


class CameraConfig(BaseModel):
    """Camera/viewpoint configuration."""
    position: Tuple[float, float, float]
    looking_at: Tuple[float, float, float]
    fov_degrees: float = Field(default=90.0, gt=0.0, lt=180.0)


class WorldSpec(BaseModel):
    """Complete world specification for rendering and simulation."""
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary metadata (name, description, etc.)"
    )

    scene_bounds_min: Tuple[float, float, float] = Field(
        default=(-250.0, -250.0, 0.0),
        description="Minimum world bounds (XYZ)"
    )
    scene_bounds_max: Tuple[float, float, float] = Field(
        default=(250.0, 250.0, 100.0),
        description="Maximum world bounds (XYZ)"
    )

    materials: Dict[str, MaterialDefinition] = Field(
        default_factory=dict,
        description="Named material definitions"
    )

    objects: List[ObjectDefinition] = Field(
        default_factory=list,
        description="Scene objects (buildings, vehicles, etc.)"
    )

    lighting: LightingConfig = Field(
        default_factory=LightingConfig,
        description="Lighting configuration"
    )

    weather: WeatherConfig = Field(
        default_factory=WeatherConfig,
        description="Weather and atmospheric effects"
    )

    time_of_day: TimeOfDayConfig = Field(
        default_factory=TimeOfDayConfig,
        description="Time and seasonal settings"
    )

    rendering: RenderingConfig = Field(
        default_factory=RenderingConfig,
        description="Rendering quality settings"
    )

    sensors: SensorConfig = Field(
        default_factory=SensorConfig,
        description="Sensor output configuration"
    )

    camera: Optional[CameraConfig] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metadata": {
                    "name": "parking_lot_demo",
                    "description": "200m parking lot with light traffic"
                },
                "lighting": {
                    "sun_intensity": 1.0,
                    "sun_angle_elevation": 45.0,
                    "sun_angle_azimuth": 135.0
                },
                "weather": {
                    "rain_intensity": 0.0,
                    "cloud_coverage": 0.3
                },
                "rendering": {
                    "profile": "high",
                    "resolution_width": 1920,
                    "resolution_height": 1080,
                    "fps": 30
                }
            }
        }
    )
