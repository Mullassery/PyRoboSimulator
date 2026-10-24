"""SANA-WM provider for camera-controlled synthetic video generation.

This module is a real adapter for NVIDIA's SANA-WM inference CLI, not a
simulated world-model implementation. It does three things:

* discovers an upstream ``NVlabs/Sana`` checkout and a Python 3.11+
  interpreter (with explicit environment-variable fallbacks);
* builds and executes the documented ``inference_video_scripts/wm/
  inference_sana_wm.py`` command without a shell;
* records provenance for the resulting MP4 (input hashes, upstream git
  revision, model id, command, output SHA-256, and license boundaries).

The adapter deliberately does **not** claim that model weights, CUDA, or an
NVIDIA GPU have been verified just because the script exists. ``inspect()``
reports only what it can actually observe. ``generate()`` raises
``SanaWMUnavailable`` with the observed reason when prerequisites are
missing. Output is always marked as synthetic data; it is never presented as
recorded sensor evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np

SANA_UPSTREAM_REPO = "https://github.com/NVlabs/Sana"
SANA_SCRIPT_RELATIVE = Path("inference_video_scripts/wm/inference_sana_wm.py")
SANA_MODEL_ID = "Efficient-Large-Model/SANA-WM_bidirectional"
SANA_OUTPUT_SUFFIX = "_generated.mp4"
SANA_WIDTH = 1280
SANA_HEIGHT = 704
SANA_FPS = 16
SANA_INPUT_INTRINSICS_SHAPES = ((3, 3), (4,))

SANA_LICENSES: Dict[str, str] = {
    "code": "Apache-2.0 (NVlabs/Sana)",
    "model_card": "Apache-2.0 (Efficient-Large-Model/SANA-WM_bidirectional)",
    "ltx2_refiner_vae": "Inherited Lightricks/LTX-2 terms; review before redistribution",
    "gemma_text_encoder": "Gemma terms; review before redistribution",
}
SYNTHETIC_DATA_NOTICE = (
    "SANA-WM output is generated synthetic video. It is not recorded sensor "
    "data and must not be represented as real-world evidence without an "
    "explicit synthetic-data label."
)


class SanaWMUnavailable(RuntimeError):
    """Raised when the SANA-WM upstream CLI or required runtime is absent."""


class SanaWMGenerationError(RuntimeError):
    """Raised when SANA-WM was launched but did not produce a valid MP4."""

    def __init__(self, message: str, manifest: "SanaWMManifest"):
        super().__init__(message)
        self.manifest = manifest


@dataclass
class SanaWMConfig:
    """Configuration for invoking the upstream SANA-WM inference script.

    All paths are optional and have environment-variable fallbacks:

    ``SANA_WM_ROOT``
        Upstream ``NVlabs/Sana`` checkout.
    ``SANA_WM_SCRIPT``
        Explicit path to ``inference_sana_wm.py``.
    ``SANA_WM_PYTHON``
        Python 3.11+ interpreter from the SANA environment (may differ from
        the interpreter running PyRoboSimulator).
    ``SANA_WM_OUTPUT_DIR``
        Default output directory for generated clips.
    ``SANA_WM_MODEL_ID``
        Hugging Face model id, defaulting to ``SANA-WM_bidirectional``.
    ``SANA_WM_SKIP_GPU_CHECK``
        Set to ``1`` to allow command construction/inspection on a machine
        where ``nvidia-smi`` is not on ``PATH``. Inference still needs a GPU.
    """

    sana_root: Optional[Path] = None
    script_path: Optional[Path] = None
    python_executable: Optional[str] = None
    output_dir: Optional[Path] = None
    model_id: str = SANA_MODEL_ID
    model_path: Optional[Path] = None
    inference_config: Optional[Path] = None
    refiner_root: Optional[Path] = None
    refiner_gemma_root: Optional[Path] = None
    num_frames: int = 161
    fps: int = SANA_FPS
    step: int = 60
    cfg_scale: float = 5.0
    seed: int = 42
    negative_prompt: str = ""
    offload_vae: bool = False
    no_refiner: bool = False
    translation_speed: Optional[float] = None
    rotation_speed_deg: Optional[float] = None
    verify_gpu: bool = True
    timeout_sec: Optional[float] = None
    extra_args: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Apply environment fallbacks after dataclass construction."""
        if self.sana_root is None:
            env_root = os.environ.get("SANA_WM_ROOT")
            if env_root:
                self.sana_root = Path(env_root).expanduser()
        if self.script_path is None:
            env_script = os.environ.get("SANA_WM_SCRIPT")
            if env_script:
                self.script_path = Path(env_script).expanduser()
        if self.python_executable is None:
            self.python_executable = os.environ.get("SANA_WM_PYTHON") or sys.executable
        if self.output_dir is None:
            env_output = os.environ.get("SANA_WM_OUTPUT_DIR")
            if env_output:
                self.output_dir = Path(env_output).expanduser()
        if self.model_id == SANA_MODEL_ID:
            self.model_id = os.environ.get("SANA_WM_MODEL_ID", self.model_id)
        if os.environ.get("SANA_WM_SKIP_GPU_CHECK", "").lower() in {"1", "true", "yes"}:
            self.verify_gpu = False


@dataclass(frozen=True)
class SanaWMStatus:
    """Observable prerequisites for running SANA-WM."""

    available: bool
    reason: str
    script_path: Optional[Path]
    sana_root: Optional[Path]
    python_executable: str
    python_version: Optional[str]
    gpu: Optional[str]
    missing: Tuple[str, ...]
    model_id: str
    model_weights_verified: bool = False
    runtime_verified: bool = False
    upstream_revision: Optional[str] = None
    upstream_dirty: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation."""
        data = asdict(self)
        for key in ("script_path", "sana_root"):
            value = data.get(key)
            data[key] = str(value) if value is not None else None
        data["missing"] = list(self.missing)
        return data


@dataclass
class SanaWMManifest:
    """Provenance record written next to each generated clip."""

    provider: str
    model_id: str
    upstream_repo: str
    upstream_revision: Optional[str]
    upstream_dirty: Optional[bool]
    command: Tuple[str, ...]
    cwd: Optional[str]
    python_executable: str
    python_version: Optional[str]
    platform: str
    gpu: Optional[str]
    started_at: str
    finished_at: str
    duration_sec: float
    returncode: Optional[int]
    status: str
    output_path: Optional[str]
    output_sha256: Optional[str]
    output_bytes: Optional[int]
    output_width: int
    output_height: int
    num_frames: int
    fps: int
    seed: int
    input_paths: Dict[str, str] = field(default_factory=dict)
    input_sha256: Dict[str, str] = field(default_factory=dict)
    action: Optional[str] = None
    synthetic: bool = True
    synthetic_data_notice: str = SYNTHETIC_DATA_NOTICE
    execution_completed: bool = False
    licenses: Dict[str, str] = field(default_factory=lambda: dict(SANA_LICENSES))
    stdout_tail: Optional[str] = None
    stderr_tail: Optional[str] = None
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation."""
        data = asdict(self)
        data["command"] = list(self.command)
        data["notes"] = list(self.notes)
        return data

    def write(self, path: Path) -> None:
        """Atomically write the manifest as pretty JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(path.parent), delete=False
        ) as handle:
            handle.write(payload)
            temp_name = handle.name
        os.replace(temp_name, path)


@dataclass
class SanaWMResult:
    """A completed SANA-WM inference result."""

    output_path: Path
    manifest_path: Path
    manifest: SanaWMManifest


class SanaWMProvider:
    """Invoke NVIDIA's SANA-WM inference CLI and record provenance."""

    def __init__(self, config: Optional[SanaWMConfig] = None):
        self.config = config or SanaWMConfig()

    # ==================== DISCOVERY / STATUS ====================

    def _candidate_roots(self) -> Tuple[Path, ...]:
        candidates = []
        if self.config.sana_root is not None:
            candidates.append(self.config.sana_root)
        cwd = Path.cwd()
        candidates.extend([cwd, *cwd.parents])
        home = Path.home()
        candidates.extend([home / "Sana", home / "sana", Path("/opt/Sana"), Path("/workspace/Sana")])
        seen = set()
        unique = []
        for candidate in candidates:
            resolved = candidate.expanduser()
            key = str(resolved)
            if key not in seen:
                seen.add(key)
                unique.append(resolved)
        return tuple(unique)

    def _resolve_sana_root(self) -> Optional[Path]:
        explicit = self.config.sana_root
        if explicit is not None:
            return explicit.expanduser()
        for candidate in self._candidate_roots():
            if (candidate / SANA_SCRIPT_RELATIVE).is_file():
                return candidate
        return None

    def _resolve_script(self) -> Optional[Path]:
        if self.config.script_path is not None:
            return self.config.script_path.expanduser()
        root = self._resolve_sana_root()
        if root is not None:
            return root / SANA_SCRIPT_RELATIVE
        return None

    def _resolve_python(self) -> str:
        executable = self.config.python_executable or sys.executable
        return shutil.which(executable) or executable

    def inspect(self) -> SanaWMStatus:
        """Report only observable SANA-WM prerequisites."""
        missing = []
        script = self._resolve_script()
        if script is None:
            missing.append("SANA-WM script not found (set SANA_WM_ROOT or SANA_WM_SCRIPT)")
        elif not script.is_file():
            missing.append(f"SANA-WM script does not exist: {script}")

        python = self._resolve_python()
        python_version = self._probe_python(python)
        if python_version is None:
            missing.append(f"Python interpreter is not runnable: {python}")
        else:
            major, minor = (int(part) for part in python_version.split(".")[:2])
            if (major, minor) < (3, 11):
                missing.append(f"SANA-WM needs Python >= 3.11; found {python_version}")

        if self.config.model_path is not None and not self.config.model_path.exists():
            missing.append(f"model_path does not exist: {self.config.model_path}")

        gpu = self._probe_gpu()
        if self.config.verify_gpu and gpu is None:
            missing.append("no NVIDIA GPU detected via nvidia-smi")

        root = self._resolve_sana_root()
        revision, dirty = self._git_metadata(root)
        weights_verified = bool(
            self.config.model_path is not None and self.config.model_path.exists()
        )

        if missing:
            reason = "SANA-WM unavailable: " + "; ".join(missing)
        else:
            reason = (
                "SANA-WM upstream script and Python are present"
                + (f"; GPU observed: {gpu}" if gpu else "; GPU check skipped")
                + "; model weights and actual inference remain unverified until generate() runs."
            )

        return SanaWMStatus(
            available=not missing,
            reason=reason,
            script_path=script,
            sana_root=root,
            python_executable=python,
            python_version=python_version,
            gpu=gpu,
            missing=tuple(missing),
            model_id=self.config.model_id,
            model_weights_verified=weights_verified,
            runtime_verified=False,
            upstream_revision=revision,
            upstream_dirty=dirty,
        )

    # ==================== COMMAND CONSTRUCTION ====================

    def build_command(
        self,
        *,
        image: Path,
        prompt: Path,
        output_name: str,
        camera: Optional[Path] = None,
        action: Optional[str] = None,
        intrinsics: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ) -> Tuple[str, ...]:
        """Build an argv list for the upstream SANA-WM CLI.

        Exactly one of ``camera`` (an ``(F, 4, 4)`` ``.npy``) or ``action``
        (e.g. ``"w-80,jw-40,w-40"``) is required, matching upstream's
        mutually-exclusive group. No shell is involved.
        """
        if (camera is None) == (action is None):
            raise ValueError("provide exactly one of camera or action")

        script = self._resolve_script()
        if script is None:
            raise SanaWMUnavailable(
                "SANA-WM script not found; set SANA_WM_ROOT or SANA_WM_SCRIPT"
            )
        if not script.is_file():
            raise SanaWMUnavailable(f"SANA-WM script does not exist: {script}")

        image = Path(image).expanduser()
        prompt = Path(prompt).expanduser()
        if not image.is_file():
            raise FileNotFoundError(f"SANA-WM starting image not found: {image}")
        if not prompt.is_file():
            raise FileNotFoundError(f"SANA-WM prompt file not found: {prompt}")

        if camera is not None:
            camera = Path(camera).expanduser()
            self._validate_camera(camera)
        if action is not None and not action.strip():
            raise ValueError("action must be a non-empty SANA-WM action string")
        if intrinsics is not None:
            intrinsics = Path(intrinsics).expanduser()
            self._validate_intrinsics(intrinsics)
        if not output_name or Path(output_name).name != output_name:
            raise ValueError("output_name must be a plain filename stem")
        if output_dir is None:
            output_dir = self.config.output_dir
        if output_dir is None:
            raise ValueError("output_dir is required (pass output_dir or set SANA_WM_OUTPUT_DIR)")
        output_dir = Path(output_dir).expanduser()

        cmd = [
            self._resolve_python(),
            str(script),
            "--image",
            str(image),
            "--prompt",
            str(prompt),
            "--output_dir",
            str(output_dir),
            "--name",
            output_name,
        ]
        if camera is not None:
            cmd.extend(["--camera", str(camera)])
        else:
            cmd.extend(["--action", str(action)])
        if intrinsics is not None:
            cmd.extend(["--intrinsics", str(intrinsics)])

        cmd.extend(["--num_frames", str(self.config.num_frames)])
        cmd.extend(["--fps", str(self.config.fps)])
        cmd.extend(["--step", str(self.config.step)])
        cmd.extend(["--cfg_scale", str(self.config.cfg_scale)])
        cmd.extend(["--seed", str(self.config.seed)])
        if self.config.negative_prompt:
            cmd.extend(["--negative_prompt", self.config.negative_prompt])
        if self.config.model_path is not None:
            cmd.extend(["--model_path", str(self.config.model_path)])
        if self.config.inference_config is not None:
            cmd.extend(["--config", str(self.config.inference_config)])
        if self.config.refiner_root is not None:
            cmd.extend(["--refiner_root", str(self.config.refiner_root)])
        if self.config.refiner_gemma_root is not None:
            cmd.extend(["--refiner_gemma_root", str(self.config.refiner_gemma_root)])
        if self.config.translation_speed is not None:
            cmd.extend(["--translation_speed", str(self.config.translation_speed)])
        if self.config.rotation_speed_deg is not None:
            cmd.extend(["--rotation_speed_deg", str(self.config.rotation_speed_deg)])
        if self.config.offload_vae:
            cmd.append("--offload_vae")
        if self.config.no_refiner:
            cmd.append("--no_refiner")
        cmd.extend(self.config.extra_args)
        return tuple(cmd)

    # ==================== GENERATION ====================

    def generate(
        self,
        *,
        image: Path,
        prompt: Optional[Path] = None,
        prompt_text: Optional[str] = None,
        camera: Optional[Path] = None,
        action: Optional[str] = None,
        intrinsics: Optional[Path] = None,
        output_name: Optional[str] = None,
        output_dir: Optional[Path] = None,
        timeout_sec: Optional[float] = None,
    ) -> SanaWMResult:
        """Run SANA-WM and write an MP4 plus a provenance manifest.

        Either ``prompt`` (an existing UTF-8 file) or ``prompt_text`` (written
        to a sidecar file) must be supplied. A non-zero exit or missing output
        MP4 raises ``SanaWMGenerationError`` after recording the failed
        manifest, so failed runs also leave provenance behind.
        """
        status = self.inspect()
        if not status.available:
            raise SanaWMUnavailable(status.reason)
        if (prompt is None) == (prompt_text is None):
            raise ValueError("provide exactly one of prompt or prompt_text")

        if output_dir is None:
            output_dir = self.config.output_dir
        if output_dir is None:
            raise ValueError("output_dir is required (pass output_dir or set SANA_WM_OUTPUT_DIR)")
        output_dir = Path(output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        name = output_name or f"sana_wm_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        if prompt is None:
            assert prompt_text is not None
            prompt_path = output_dir / f"{name}.prompt.txt"
            prompt_path.write_text(prompt_text, encoding="utf-8")
            prompt = prompt_path
        prompt = Path(prompt).expanduser()

        command = self.build_command(
            image=Path(image),
            prompt=prompt,
            output_name=name,
            camera=Path(camera) if camera is not None else None,
            action=action,
            intrinsics=Path(intrinsics) if intrinsics is not None else None,
            output_dir=output_dir,
        )
        output_path = output_dir / f"{name}{SANA_OUTPUT_SUFFIX}"
        input_paths, input_hashes = self._hash_inputs(
            image=Path(image),
            prompt=prompt,
            camera=Path(camera) if camera is not None else None,
            intrinsics=Path(intrinsics) if intrinsics is not None else None,
            action=action,
        )

        started_at = datetime.now(timezone.utc)
        start = time.monotonic()
        returncode: Optional[int] = None
        stdout = ""
        stderr = ""
        try:
            completed = subprocess.run(
                command,
                cwd=str(status.sana_root) if status.sana_root is not None else None,
                capture_output=True,
                text=True,
                timeout=timeout_sec if timeout_sec is not None else self.config.timeout_sec,
                check=False,
                env=self._subprocess_env(),
            )
            returncode = completed.returncode
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
        except subprocess.TimeoutExpired as exc:
            stderr = f"SANA-WM timed out after {exc.timeout} seconds"
        except OSError as exc:
            stderr = f"failed to launch SANA-WM: {exc}"

        duration = time.monotonic() - start
        finished_at = datetime.now(timezone.utc)
        manifest = SanaWMManifest(
            provider="sana-wm",
            model_id=self.config.model_id,
            upstream_repo=SANA_UPSTREAM_REPO,
            upstream_revision=status.upstream_revision,
            upstream_dirty=status.upstream_dirty,
            command=command,
            cwd=str(status.sana_root) if status.sana_root is not None else None,
            python_executable=status.python_executable,
            python_version=status.python_version,
            platform=platform.platform(),
            gpu=status.gpu,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_sec=duration,
            returncode=returncode,
            status="failed",
            output_path=str(output_path),
            output_sha256=None,
            output_bytes=None,
            output_width=SANA_WIDTH,
            output_height=SANA_HEIGHT,
            num_frames=self.config.num_frames,
            fps=self.config.fps,
            seed=self.config.seed,
            input_paths=input_paths,
            input_sha256=input_hashes,
            action=action,
            stdout_tail=self._tail(stdout),
            stderr_tail=self._tail(stderr),
            notes=(
                "Generated by the upstream SANA-WM CLI; NVIDIA hardware execution is required.",
                SYNTHETIC_DATA_NOTICE,
            ),
        )
        manifest_path = output_dir / f"{name}.manifest.json"

        if returncode != 0 or not output_path.is_file() or output_path.stat().st_size == 0:
            manifest.write(manifest_path)
            detail = (stderr or stdout or "no output produced").strip()
            raise SanaWMGenerationError(
                f"SANA-WM failed (returncode={returncode}): {detail[-1000:]}",
                manifest,
            )

        manifest.status = "completed"
        manifest.execution_completed = True
        manifest.output_sha256 = self._hash_file(output_path)
        manifest.output_bytes = output_path.stat().st_size
        manifest.write(manifest_path)
        return SanaWMResult(
            output_path=output_path,
            manifest_path=manifest_path,
            manifest=manifest,
        )

    def generate_for_scenario(
        self,
        scenario: Any,
        *,
        image: Path,
        camera: Optional[Path] = None,
        action: Optional[str] = None,
        intrinsics: Optional[Path] = None,
        output_name: Optional[str] = None,
        output_dir: Optional[Path] = None,
        timeout_sec: Optional[float] = None,
    ) -> SanaWMResult:
        """Generate a clip using a prompt derived from a generated scenario."""
        return self.generate(
            image=image,
            prompt_text=prompt_from_scenario(scenario),
            camera=camera,
            action=action,
            intrinsics=intrinsics,
            output_name=output_name,
            output_dir=output_dir,
            timeout_sec=timeout_sec,
        )

    # ==================== INTERNALS ====================

    @staticmethod
    def _validate_camera(path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"SANA-WM camera trajectory not found: {path}")
        try:
            array = np.load(path, mmap_mode="r")
        except (OSError, ValueError) as exc:
            raise ValueError(f"SANA-WM camera must be a .npy file: {path}") from exc
        if array.ndim != 3 or array.shape[1:] != (4, 4) or array.shape[0] < 1:
            raise ValueError(
                f"SANA-WM camera must have shape (F, 4, 4); got {tuple(array.shape)}"
            )

    @staticmethod
    def _validate_intrinsics(path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"SANA-WM intrinsics not found: {path}")
        try:
            array = np.load(path, mmap_mode="r")
        except (OSError, ValueError) as exc:
            raise ValueError(f"SANA-WM intrinsics must be a .npy file: {path}") from exc
        valid = array.shape in SANA_INPUT_INTRINSICS_SHAPES
        if array.ndim == 3 and array.shape[1:] == (3, 3) and array.shape[0] >= 1:
            valid = True
        if not valid:
            raise ValueError(
                "SANA-WM intrinsics must have shape (3, 3), (F, 3, 3), or (4,); "
                f"got {tuple(array.shape)}"
            )

    @staticmethod
    def _probe_python(executable: str) -> Optional[str]:
        try:
            completed = subprocess.run(
                [
                    executable,
                    "-c",
                    "import sys; print('%d.%d.%d' % sys.version_info[:3])",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        version = completed.stdout.strip()
        return version or None

    @staticmethod
    def _probe_gpu() -> Optional[str]:
        executable = shutil.which("nvidia-smi")
        if executable is None:
            return None
        try:
            completed = subprocess.run(
                [
                    executable,
                    "--query-gpu=name,memory.total,driver_version",
                    "--format=csv,noheader",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        return lines[0] if lines else None

    @staticmethod
    def _git_metadata(root: Optional[Path]) -> Tuple[Optional[str], Optional[bool]]:
        if root is None or not (root / ".git").exists():
            return None, None

        def run_git(*args: str) -> Optional[str]:
            git = shutil.which("git")
            if git is None:
                return None
            try:
                completed = subprocess.run(
                    [git, "-C", str(root), *args],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError):
                return None
            return completed.stdout.strip() if completed.returncode == 0 else None

        revision = run_git("rev-parse", "HEAD")
        status = run_git("status", "--porcelain")
        dirty = bool(status) if status is not None else None
        return revision, dirty

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _hash_inputs(
        self,
        *,
        image: Path,
        prompt: Path,
        camera: Optional[Path],
        intrinsics: Optional[Path],
        action: Optional[str],
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        paths: Dict[str, str] = {"image": str(image), "prompt": str(prompt)}
        hashes: Dict[str, str] = {
            "image": self._hash_file(image),
            "prompt": self._hash_file(prompt),
        }
        if camera is not None:
            paths["camera"] = str(camera)
            hashes["camera"] = self._hash_file(camera)
        if intrinsics is not None:
            paths["intrinsics"] = str(intrinsics)
            hashes["intrinsics"] = self._hash_file(intrinsics)
        if action is not None:
            hashes["action"] = hashlib.sha256(f"action:{action}".encode("utf-8")).hexdigest()
        return paths, hashes

    @staticmethod
    def _subprocess_env() -> Mapping[str, str]:
        keep = {
            "PATH",
            "HOME",
            "USER",
            "LANG",
            "LC_ALL",
            "TMPDIR",
            "CUDA_VISIBLE_DEVICES",
            "HF_HOME",
            "HF_TOKEN",
            "TRANSFORMERS_CACHE",
            "TORCH_HOME",
            "PYTHONPATH",
            "LD_LIBRARY_PATH",
        }
        return {key: value for key, value in os.environ.items() if key in keep}

    @staticmethod
    def _tail(text: str, limit: int = 20000) -> Optional[str]:
        if not text:
            return None
        return text[-limit:]


def prompt_from_scenario(scenario: Any) -> str:
    """Build a deterministic SANA-WM prompt from a generated scenario.

    The function accepts ``GeneratedScenario`` or any object exposing the
    same attributes, so it does not create an import cycle with the scenario
    service.
    """

    def value(name: str, default: Any) -> Any:
        return getattr(scenario, name, default)

    environment = value("environment", "unknown environment")
    region = value("region", "unspecified region")
    weather = value("weather", "clear")
    time_of_day = value("time_of_day", "day")
    season = value("season", "unspecified season")
    human_density = float(value("human_density", 0.0) or 0.0)
    vehicle_density = float(value("vehicle_density", 0.0) or 0.0)
    scenario_class = value("class_", None)
    class_name = getattr(scenario_class, "value", scenario_class) or "nominal"
    difficulty = float(value("difficulty", 0.0) or 0.0)

    parts = [
        f"A first-person robot camera view in a {environment} located in {region}.",
        f"Time of day: {time_of_day}; season: {season}; weather: {weather}.",
        (
            f"Human density is {human_density:.0%} and vehicle density is "
            f"{vehicle_density:.0%}."
        ),
        f"Scenario class: {class_name}; difficulty: {difficulty:.2f}.",
    ]
    for label, attr in (
        ("Active violations", "active_violations"),
        ("Rare events", "rare_events"),
        ("Infrastructure failures", "infrastructure_failures"),
    ):
        items = value(attr, None) or []
        if items:
            parts.append(f"{label}: {', '.join(str(item) for item in items)}.")
    return " ".join(parts)
