"""Sensor configuration and material properties for realistic sensor simulation."""

from dataclasses import dataclass


@dataclass
class RGBNoiseConfig:
    """RGB camera noise and distortion parameters."""

    gaussian_sigma: float = 5.0
    distortion_k1: float = 0.0
    distortion_k2: float = 0.0
    motion_blur_enabled: bool = False
    motion_blur_max_kernel: int = 15
    color_grading: str = "none"  # "none" | "daylight" | "night" | "thermal_tint"


@dataclass
class DepthNoiseConfig:
    """Depth sensor accuracy and range parameters."""

    gaussian_sigma: float = 2.0
    quantization_step: float = 0.0  # 0 disables; e.g. 0.001 = 1mm
    near_clip: float = 0.0
    far_clip: float = 300.0
    temporal_window: int = 1  # 1 = no averaging; >1 = frame averaging
    edge_artifact_strength: float = 0.0


@dataclass
class LidarBeamConfig:
    """Lidar beam characteristics and reflectivity parameters."""

    beam_divergence_deg: float = 0.0
    reflectivity_enabled: bool = False
    multi_bounce_enabled: bool = False
    intensity_falloff_enabled: bool = False
    max_range: float = 300.0


@dataclass
class ThermalNoiseConfig:
    """Thermal camera emulation parameters."""

    gaussian_sigma: float = 1.0
    ambient_temp: float = 20.0
    thermal_lag_tau: float = 0.0  # 0 = no lag; >0 = exponential smoothing time constant
    non_uniformity_strength: float = 0.0
    lens_aberration_strength: float = 0.0
    material_emissivity_enabled: bool = False


# Material properties from PHASE0_WEEK3_SENSORS.md
MATERIAL_EMISSIVITY = {
    "asphalt": 0.95,
    "water": 0.93,
    "concrete": 0.90,
    "metal": 0.15,
    "grass": 0.98,
    "leaves": 0.97,
    "default": 0.90,
}

# Lidar material reflectivity (pseudo-materials for synthetic sim)
LIDAR_MATERIAL_REFLECTIVITY = {
    "asphalt": 0.10,
    "concrete": 0.25,
    "metal": 0.85,
    "glass": 0.05,
    "grass": 0.15,
    "water": 0.02,
    "default": 0.20,
}
