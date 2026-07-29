"""Shared sensor effect helpers for numpy-based image/data processing."""

import numpy as np


def apply_radial_distortion(image: np.ndarray, k1: float, k2: float) -> np.ndarray:
    """Apply barrel/pincushion lens distortion via radial polynomials.

    Args:
        image: H×W×3 RGB image (0-255 uint8 or float)
        k1, k2: Radial distortion coefficients

    Returns:
        Distorted image, same shape/dtype as input
    """
    if k1 == 0 and k2 == 0:
        return image

    h, w = image.shape[:2]
    center_x, center_y = w / 2, h / 2
    max_radius = np.sqrt(center_x**2 + center_y**2)

    # Build coordinate grids
    yy, xx = np.mgrid[0:h, 0:w]
    xx = xx.astype(np.float32)
    yy = yy.astype(np.float32)

    # Normalize coordinates
    xx_norm = (xx - center_x) / max_radius
    yy_norm = (yy - center_y) / max_radius
    radius_sq = xx_norm**2 + yy_norm**2

    # Radial distortion factor: 1 + k1*r^2 + k2*r^4
    distortion_factor = 1 + k1 * radius_sq + k2 * (radius_sq**2)

    # Map source coordinates
    src_xx = xx_norm * distortion_factor * max_radius + center_x
    src_yy = yy_norm * distortion_factor * max_radius + center_y

    # Clip to image bounds
    src_xx = np.clip(src_xx, 0, w - 1)
    src_yy = np.clip(src_yy, 0, h - 1)

    # Bilinear interpolation
    x0 = np.floor(src_xx).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y0 = np.floor(src_yy).astype(np.int32)
    y1 = np.clip(y0 + 1, 0, h - 1)

    dx = src_xx - x0
    dy = src_yy - y0

    result = (
        image[y0, x0] * (1 - dx) * (1 - dy)
        + image[y0, x1] * dx * (1 - dy)
        + image[y1, x0] * (1 - dx) * dy
        + image[y1, x1] * dx * dy
    )

    return result.astype(image.dtype)


def apply_motion_blur(
    image: np.ndarray, speed: float, direction_xy: tuple[float, float], max_kernel: int = 15
) -> np.ndarray:
    """Apply motion blur based on agent velocity and direction.

    Args:
        image: H×W×3 RGB image
        speed: Speed magnitude (affects blur kernel size)
        direction_xy: (dx, dy) normalized direction vector
        max_kernel: Maximum blur kernel size

    Returns:
        Motion-blurred image
    """
    if speed < 0.1:
        return image

    # Scale speed to kernel size
    kernel_size = min(int(speed / 2), max_kernel)
    if kernel_size < 2:
        return image

    kernel_size = kernel_size if kernel_size % 2 == 1 else kernel_size + 1

    # Create motion blur kernel
    dx, dy = direction_xy
    kernel = np.zeros((kernel_size, kernel_size))
    cx, cy = kernel_size // 2, kernel_size // 2
    for i in range(kernel_size):
        x = int(cx + (i - kernel_size // 2) * dx)
        y = int(cy + (i - kernel_size // 2) * dy)
        if 0 <= x < kernel_size and 0 <= y < kernel_size:
            kernel[y, x] = 1
    kernel /= np.sum(kernel) if np.sum(kernel) > 0 else 1

    # Apply convolution per channel
    from scipy import signal

    result = np.zeros_like(image, dtype=np.float32)
    for c in range(image.shape[2]):
        result[:, :, c] = signal.convolve2d(image[:, :, c], kernel, mode="same", boundary="fill")

    return np.clip(result, 0, 255).astype(image.dtype)


def apply_color_grading(image: np.ndarray, preset: str) -> np.ndarray:
    """Apply color grading presets.

    Args:
        image: H×W×3 RGB image
        preset: "none", "daylight", "night", or "thermal_tint"

    Returns:
        Color-graded image
    """
    if preset == "none":
        return image

    result = image.astype(np.float32)

    if preset == "daylight":
        # Boost greens, warm yellows
        result[:, :, 0] *= 1.1  # Red +10%
        result[:, :, 1] *= 1.15  # Green +15%
        result[:, :, 2] *= 0.95  # Blue -5%
    elif preset == "night":
        # Reduce overall brightness, boost blues, reduce reds
        result *= 0.6
        result[:, :, 2] *= 1.3  # Blue boost
        result[:, :, 0] *= 0.8  # Red reduction
    elif preset == "thermal_tint":
        # Thermal-like color cast (yellows/reds)
        result[:, :, 0] *= 1.2  # Red boost
        result[:, :, 1] *= 1.1  # Green slight boost
        result[:, :, 2] *= 0.6  # Blue reduction

    return np.clip(result, 0, 255).astype(image.dtype)


def add_gaussian_noise(array: np.ndarray, sigma: float, value_min: float, value_max: float) -> np.ndarray:
    """Add Gaussian noise to an array, clipped to range.

    Args:
        array: Input array (any shape)
        sigma: Standard deviation of noise
        value_min, value_max: Clipping range

    Returns:
        Noisy array, clipped and same dtype as input
    """
    if sigma == 0:
        return array

    noise = np.random.normal(0, sigma, array.shape)
    result = array.astype(np.float32) + noise
    return np.clip(result, value_min, value_max).astype(array.dtype)


def quantize(array: np.ndarray, step: float) -> np.ndarray:
    """Quantize values to discrete steps.

    Args:
        array: Input array (float)
        step: Quantization step size (0 disables)

    Returns:
        Quantized array
    """
    if step == 0 or step < 1e-6:
        return array

    return np.round(array / step) * step
