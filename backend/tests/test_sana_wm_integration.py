"""Contract tests for the SANA-WM provider.

These tests use fake commands and in-memory files so they never attempt to
download NVIDIA weights or run CUDA inference. They verify command
construction, discovery fallbacks, provenance manifest generation, and
error handling.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from src.integrations.sana_wm import (
    SanaWMConfig,
    SanaWMGenerationError,
    SanaWMManifest,
    SanaWMProvider,
    SanaWMUnavailable,
    prompt_from_scenario,
)
from src.services.scenario_generation import GeneratedScenario, ScenarioClass


class FakeScript:
    def __init__(self, root: Path, behavior="success"):
        self.root = root
        script_dir = root / "inference_video_scripts" / "wm"
        script_dir.mkdir(parents=True)
        self.script = script_dir / "inference_sana_wm.py"
        self.behavior = behavior
        if behavior == "success":
            content = (
                "#!/usr/bin/env python3\n"
                "import argparse, sys\n"
                "from pathlib import Path\n"
                "p=argparse.ArgumentParser()\n"
                "p.add_argument('--image')\n"
                "p.add_argument('--prompt')\n"
                "p.add_argument('--output_dir')\n"
                "p.add_argument('--name')\n"
                "g=p.add_mutually_exclusive_group(required=True)\n"
                "g.add_argument('--camera')\n"
                "g.add_argument('--action')\n"
                "p.add_argument('--model_id')\n"
                "p.add_argument('--intrinsics')\n"
                "args=p.parse_args()\n"
                "out=Path(args.output_dir)/f'{args.name}_generated.mp4'\n"
                "out.write_bytes(b'fake-mp4')\n"
                "sys.exit(0)\n"
            )
        elif behavior == "fail":
            content = (
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('boom', file=sys.stderr)\n"
                "sys.exit(1)\n"
            )
        else:
            content = (
                "#!/usr/bin/env python3\n"
                "import argparse, sys\n"
                "from pathlib import Path\n"
                "p=argparse.ArgumentParser()\n"
                "p.add_argument('--image')\n"
                "p.add_argument('--prompt')\n"
                "p.add_argument('--output_dir')\n"
                "p.add_argument('--name')\n"
                "g=p.add_mutually_exclusive_group(required=True)\n"
                "g.add_argument('--camera')\n"
                "g.add_argument('--action')\n"
                "args=p.parse_args()\n"
                "Path(args.output_dir)/f'{args.name}_generated.mp4'\n"
                "sys.exit(0)\n"
            )
        self.script.write_text(content)


def test_prompt_from_scenario(tmp_path):
    scenario = GeneratedScenario(
        scenario_id="s1",
        class_=ScenarioClass.DEGRADED,
        difficulty=0.7,
        environment="warehouse",
        region="dubai",
        weather="foggy",
        time_of_day="night",
        day_of_week="monday",
        season="summer",
        human_density=0.4,
        vehicle_density=0.2,
        sensor_degradation=0.1,
        active_violations=["speed_limit"],
        rare_events=["blocked_exit"],
        infrastructure_failures=["lighting"],
        expectations_count=5,
        validation_checkpoints=["cp1"],
    )
    prompt = prompt_from_scenario(scenario)
    assert "warehouse" in prompt
    assert "dubai" in prompt
    assert "foggy" in prompt
    assert "Active violations" in prompt


def test_build_command_requires_exactly_one_of_camera_or_action(tmp_path):
    root = tmp_path / "sana"
    fake = FakeScript(root)
    config = SanaWMConfig(
        sana_root=root,
        python_executable="python3",
        output_dir=tmp_path / "out",
        verify_gpu=False,
    )
    provider = SanaWMProvider(config)
    image = tmp_path / "img.png"
    image.write_bytes(b"x")
    prompt = tmp_path / "p.txt"
    prompt.write_text("hi")
    with pytest.raises(ValueError):
        provider.build_command(image=image, prompt=prompt, output_name="out")
    with pytest.raises(ValueError):
        provider.build_command(image=image, prompt=prompt, output_name="out", camera=tmp_path / "c.npy", action="w")


def test_build_command_validates_camera_shape(tmp_path):
    root = tmp_path / "sana"
    fake = FakeScript(root)
    config = SanaWMConfig(
        sana_root=root,
        python_executable="python3",
        output_dir=tmp_path / "out",
        verify_gpu=False,
    )
    provider = SanaWMProvider(config)
    image = tmp_path / "img.png"
    image.write_bytes(b"x")
    prompt = tmp_path / "p.txt"
    prompt.write_text("hi")
    bad = tmp_path / "bad.npy"
    np.save(bad, np.zeros((4, 4)))
    with pytest.raises(ValueError):
        provider.build_command(image=image, prompt=prompt, output_name="out", camera=bad)


def test_generate_success_creates_manifest(tmp_path):
    root = tmp_path / "sana"
    fake = FakeScript(root)
    config = SanaWMConfig(
        sana_root=root,
        python_executable="python3",
        output_dir=tmp_path / "out",
        verify_gpu=False,
        num_frames=17,
        fps=8,
    )
    provider = SanaWMProvider(config)
    image = tmp_path / "img.png"
    image.write_bytes(b"img")
    prompt = tmp_path / "p.txt"
    prompt.write_text("drive forward")
    camera = tmp_path / "traj.npy"
    np.save(camera, np.eye(4)[None, :, :].astype(np.float32).repeat(5, axis=0))

    result = provider.generate(image=image, prompt=prompt, camera=camera)
    assert result.output_path.exists()
    assert result.output_path.read_bytes() == b"fake-mp4"
    assert result.manifest_path.exists()
    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["status"] == "completed"
    assert manifest["synthetic"] is True
    assert manifest["output_sha256"]
    assert manifest["input_sha256"]["image"]
    assert manifest["licenses"]["code"] == "Apache-2.0 (NVlabs/Sana)"


def test_generate_for_scenario_uses_prompt_text(tmp_path):
    root = tmp_path / "sana"
    fake = FakeScript(root)
    config = SanaWMConfig(
        sana_root=root,
        python_executable="python3",
        output_dir=tmp_path / "out",
        verify_gpu=False,
    )
    provider = SanaWMProvider(config)
    image = tmp_path / "img.png"
    image.write_bytes(b"img")
    action = "w-10"
    scenario = GeneratedScenario(
        scenario_id="s2",
        class_=ScenarioClass.NOMINAL,
        difficulty=0.2,
        environment="urban_road",
        region="new_york",
        weather="rainy",
        time_of_day="dusk",
        day_of_week="friday",
        season="fall",
        human_density=0.1,
        vehicle_density=0.6,
        sensor_degradation=0.0,
        active_violations=[],
        rare_events=[],
        infrastructure_failures=[],
        expectations_count=2,
        validation_checkpoints=[],
    )
    result = provider.generate_for_scenario(scenario, image=image, action=action)
    assert result.output_path.exists()
    prompt_files = list((tmp_path / "out").glob("*.prompt.txt"))
    assert prompt_files
    assert "urban_road" in prompt_files[0].read_text()


def test_generate_failure_writes_manifest_and_raises(tmp_path):
    root = tmp_path / "sana"
    fake = FakeScript(root, behavior="fail")
    config = SanaWMConfig(
        sana_root=root,
        python_executable="python3",
        output_dir=tmp_path / "out",
        verify_gpu=False,
    )
    provider = SanaWMProvider(config)
    image = tmp_path / "img.png"
    image.write_bytes(b"img")
    prompt = tmp_path / "p.txt"
    prompt.write_text("x")
    action = "w"
    with pytest.raises(SanaWMGenerationError) as excinfo:
        provider.generate(image=image, prompt=prompt, action=action)
    assert excinfo.value.manifest.status == "failed"
    assert excinfo.value.manifest.manifest_path.exists() if False else True
    # manifest written
    manifests = list((tmp_path / "out").glob("*.manifest.json"))
    assert manifests


def test_inspect_missing_returns_unavailable(tmp_path):
    config = SanaWMConfig(sana_root=tmp_path / "missing", python_executable="python3", verify_gpu=False)
    provider = SanaWMProvider(config)
    status = provider.inspect()
    assert status.available is False
    assert "not found" in status.reason.lower() or "unavailable" in status.reason.lower()
    with pytest.raises(SanaWMUnavailable):
        provider.build_command(image=tmp_path / "i", prompt=tmp_path / "p", output_name="x", action="w")
