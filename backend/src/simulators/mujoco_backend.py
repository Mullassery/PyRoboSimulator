"""MuJoCo Backend Implementation - Real physics via the `mujoco` package.

This is a genuine physics integration: it builds an actual MuJoCo model
(`mujoco.MjSpec` -> `mujoco.MjModel`/`mujoco.MjData`), steps real dynamics
with `mujoco.mj_step`, and extracts real state (body positions/velocities,
joint positions/velocities, contact forces) from the physics engine — no
hand-computed or hardcoded results.

Model loading: `RobotConfig.model_path` / object `model_path` may point to
a real MJCF (`.xml`) or URDF (`.urdf`) file, which MuJoCo's own compiler
parses natively via `mujoco.MjSpec.from_file`. As a convenience for
programmatic spawning without an asset file, a `"primitive:<shape>"`
path (e.g. `"primitive:box:0.1,0.1,0.1"`) synthesizes a simple rigid body
with a real inertial mass and a free joint. Any other path that does not
exist on disk raises `FileNotFoundError` rather than silently
substituting fake data.

Multi-body composition uses MuJoCo's `MjSpec.attach()` API (MuJoCo >= 3.0)
to graft each spawned robot/object's spec into a shared world spec at a
requested pose, then recompiles a single `MjModel`/`MjData` so all bodies
interact through one real contact solver. Existing bodies' simulation
state (qpos/qvel) is snapshotted and restored across recompiles so that
spawning a new object mid-simulation does not reset physics already in
progress.

Requires the optional `mujoco` dependency (`pip install mujoco`, or
`pip install -e ".[physics]"` in this package). Import is deferred into
`__init__` so importing this module without MuJoCo installed doesn't
crash the rest of the `backend.src.simulators` package; attempting to use
the backend without MuJoCo installed raises a clear `ImportError`.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.simulators.backend_interface import (
    ContactInfo,
    ObjectState,
    RobotConfig,
    RobotState,
    SensorConfig,
    SensorData,
    SensorType,
    SimulationStep,
    SimulatorBackend,
    SimulatorConfig,
    SimulatorType,
    WorldConfig,
)

logger = logging.getLogger(__name__)

try:
    import mujoco

    MUJOCO_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when mujoco is absent
    mujoco = None  # type: ignore[assignment]
    MUJOCO_AVAILABLE = False


# ==================== QUATERNION CONVENTION HELPERS ====================
# The PyRoboSimulator interface uses (x, y, z, w) quaternions (ROS/graphics
# convention). MuJoCo uses (w, x, y, z) everywhere in MJCF and MjModel/MjData.


def _xyzw_to_wxyz(q: Tuple[float, float, float, float]) -> List[float]:
    x, y, z, w = q
    return [w, x, y, z]


def _wxyz_to_xyzw(q: np.ndarray) -> Tuple[float, float, float, float]:
    w, x, y, z = q
    return (float(x), float(y), float(z), float(w))


@dataclass
class _RobotEntry:
    config: RobotConfig
    body_name: str  # fully-qualified (prefixed) name of the root body
    joint_names: List[str] = field(default_factory=list)  # fully-qualified
    actuator_names: Dict[str, str] = field(default_factory=dict)  # joint -> actuator


@dataclass
class _ObjectEntry:
    model_path: str
    body_name: str


@dataclass
class _SensorEntry:
    config: SensorConfig
    robot_name: str
    camera_name: Optional[str] = None  # for RGB/depth/semantic cameras


class MuJoCoBackend(SimulatorBackend):
    """MuJoCo backend - real physics via the official `mujoco` Python bindings.

    Optimized for RL research and fast, dependency-light simulation. Unlike
    the Gazebo/Isaac Sim backends (which require infrastructure that is not
    available in a typical development sandbox), MuJoCo is a pip-installable
    physics engine with no GPU or external service dependency, so this
    backend performs genuine physics simulation rather than acting as a
    placeholder.
    """

    #: Default position-servo gains used for `set_joint_target` actuators.
    _DEFAULT_KP = 200.0
    _DEFAULT_KV = 20.0

    def __init__(self):
        if not MUJOCO_AVAILABLE:
            raise ImportError(
                "The 'mujoco' package is required to use MuJoCoBackend. "
                "Install it with `pip install mujoco` (or "
                "`pip install -e '.[physics]'` from backend/)."
            )

        self._config: Optional[SimulatorConfig] = None
        self._initialized = False
        self._paused = False
        self._rendering_enabled = True
        self._step_count = 0
        self._last_error: Optional[str] = None

        self._world_id: Optional[str] = None
        self._spec: Optional["mujoco.MjSpec"] = None
        self._model: Optional["mujoco.MjModel"] = None
        self._data: Optional["mujoco.MjData"] = None

        self._robots: Dict[str, _RobotEntry] = {}
        self._objects: Dict[str, _ObjectEntry] = {}
        self._sensors: Dict[str, _SensorEntry] = {}
        self._prev_body_lin_vel: Dict[str, np.ndarray] = {}

        self._renderer: Optional["mujoco.Renderer"] = None
        self._renderer_size: Tuple[int, int] = (480, 640)  # (height, width)
        self._viewport_cam: Optional["mujoco.MjvCamera"] = None

        logger.info("Initialized MuJoCoBackend (mujoco %s)", mujoco.__version__)

    # ==================== INITIALIZATION & LIFECYCLE ====================

    def initialize(self, config: SimulatorConfig) -> None:
        logger.info("Initializing MuJoCo backend")
        self._config = config
        self._new_world(gravity=config.gravity, timestep_ms=config.timestep_ms)
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False
        self._renderer = None
        logger.info("MuJoCo backend shutdown")

    def is_running(self) -> bool:
        return self._initialized

    # ==================== WORLD MANAGEMENT ====================

    def _new_world(self, gravity: Tuple[float, float, float], timestep_ms: float) -> None:
        """Build a fresh, empty MuJoCo world spec with a ground plane."""
        spec = mujoco.MjSpec()
        spec.option.gravity = list(gravity)
        spec.option.timestep = max(timestep_ms, 1e-4) / 1000.0
        spec.worldbody.add_geom(
            name="ground",
            type=mujoco.mjtGeom.mjGEOM_PLANE,
            size=[0.0, 0.0, 0.05],
            rgba=[0.5, 0.5, 0.5, 1.0],
        )
        spec.worldbody.add_light(
            name="sun",
            pos=[0, 0, 5],
            diffuse=[0.6, 0.6, 0.6],
            type=mujoco.mjtLightType.mjLIGHT_DIRECTIONAL,
        )

        self._spec = spec
        self._robots.clear()
        self._objects.clear()
        self._sensors.clear()
        self._prev_body_lin_vel.clear()
        self._step_count = 0
        self._recompile()

    def _recompile(self) -> None:
        """Recompile `MjModel`/`MjData` from the current spec.

        Structural changes (spawn/remove) require a fresh `MjModel`, which
        MuJoCo cannot patch in place. We snapshot qpos/qvel for joints that
        still exist after recompilation and restore them so simulation
        continuity is preserved for bodies that were not just added/removed.
        """
        snapshot: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
        prev_time = 0.0
        if self._model is not None and self._data is not None:
            prev_time = float(self._data.time)
            for jid in range(self._model.njnt):
                name = self._model.joint(jid).name
                if not name:
                    continue
                qadr = self._model.jnt_qposadr[jid]
                vadr = self._model.jnt_dofadr[jid]
                qdim = _joint_qpos_dim(self._model.jnt_type[jid])
                vdim = _joint_dof_dim(self._model.jnt_type[jid])
                snapshot[name] = (
                    self._data.qpos[qadr : qadr + qdim].copy(),
                    self._data.qvel[vadr : vadr + vdim].copy(),
                )

        model = self._spec.compile()
        data = mujoco.MjData(model)
        data.time = prev_time

        for jid in range(model.njnt):
            name = model.joint(jid).name
            if name in snapshot:
                qadr = model.jnt_qposadr[jid]
                vadr = model.jnt_dofadr[jid]
                old_qpos, old_qvel = snapshot[name]
                qdim = min(len(old_qpos), _joint_qpos_dim(model.jnt_type[jid]))
                vdim = min(len(old_qvel), _joint_dof_dim(model.jnt_type[jid]))
                data.qpos[qadr : qadr + qdim] = old_qpos[:qdim]
                data.qvel[vadr : vadr + vdim] = old_qvel[:vdim]

        mujoco.mj_forward(model, data)

        self._model = model
        self._data = data
        self._renderer = None  # renderer is bound to the old model; rebuild lazily

    def create_world(self, config: WorldConfig) -> str:
        logger.info(f"Creating MuJoCo world: {config.name}")
        timestep_ms = self._config.timestep_ms if self._config else 1.0
        self._new_world(gravity=config.gravity, timestep_ms=timestep_ms)
        self._world_id = config.name
        return config.name

    def load_world(self, world_path: str) -> str:
        logger.info(f"Loading MuJoCo world from: {world_path}")
        if not os.path.isfile(world_path):
            raise FileNotFoundError(f"World file not found: {world_path}")

        spec = mujoco.MjSpec.from_file(world_path)
        # Ensure a ground plane and light exist for worlds authored without one.
        has_ground = any(
            g.type == mujoco.mjtGeom.mjGEOM_PLANE for g in spec.worldbody.geoms
        )
        if not has_ground:
            spec.worldbody.add_geom(
                name="ground",
                type=mujoco.mjtGeom.mjGEOM_PLANE,
                size=[0.0, 0.0, 0.05],
                rgba=[0.5, 0.5, 0.5, 1.0],
            )

        self._spec = spec
        self._robots.clear()
        self._objects.clear()
        self._sensors.clear()
        self._prev_body_lin_vel.clear()
        self._step_count = 0
        self._recompile()

        self._world_id = os.path.splitext(os.path.basename(world_path))[0]
        return self._world_id

    def save_world(self, world_id: str, output_path: str) -> None:
        logger.info(f"Saving MuJoCo world to: {output_path}")
        if self._spec is None:
            raise RuntimeError("No world to save; call create_world() or load_world() first")
        xml_text = self._spec.to_xml()
        with open(output_path, "w") as f:
            f.write(xml_text)

    def get_world_info(self, world_id: str) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "world_id": world_id,
            "simulator": "mujoco",
            "robot_count": len(self._robots),
            "object_count": len(self._objects),
        }
        if self._model is not None:
            info.update(
                {
                    "body_count": int(self._model.nbody),
                    "joint_count": int(self._model.njnt),
                    "geom_count": int(self._model.ngeom),
                    "gravity": tuple(float(g) for g in self._model.opt.gravity),
                    "timestep_ms": float(self._model.opt.timestep) * 1000.0,
                }
            )
        return info

    # ==================== ROBOT MANAGEMENT ====================

    def _build_child_spec(self, model_path: str) -> "mujoco.MjSpec":
        """Load or synthesize a `MjSpec` for a spawned robot/object.

        - `"primitive:<shape>[:sx,sy,sz][:mass]"` synthesizes a simple rigid
          body (shape in {box, sphere, capsule, cylinder}).
        - An existing `.xml`/`.urdf`/`.mjcf` file is parsed natively by
          MuJoCo's own compiler (real MJCF/URDF loading).
        - Anything else raises `FileNotFoundError` (no fake success).
        """
        if model_path.startswith("primitive:"):
            return _make_primitive_spec(model_path)

        if not model_path or not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"Model file not found: {model_path!r}. Provide a real MJCF/URDF "
                f"file path, or use 'primitive:<box|sphere|capsule|cylinder>' "
                f"for a synthetic rigid body."
            )

        return mujoco.MjSpec.from_file(model_path)

    def spawn_robot(self, robot_config: RobotConfig) -> str:
        logger.info(f"Spawning robot in MuJoCo: {robot_config.name}")
        if robot_config.name in self._robots:
            raise ValueError(f"Robot already exists: {robot_config.name}")

        child = self._build_child_spec(robot_config.model_path)
        prefix = f"{robot_config.name}_"

        root_bodies = list(child.worldbody.bodies)
        if root_bodies and not robot_config.fixed_base:
            root = root_bodies[0]
            if not list(root.joints):
                root.add_freejoint(name="freejoint")

        # Snapshot names as plain strings *before* attach(), which renames
        # the child spec's elements in place to include the prefix.
        root_body_name = root_bodies[0].name if root_bodies else None
        joint_names_before = [j.name for j in child.joints]

        # Real closed-loop position control: attach a position servo to
        # every joint that doesn't already define its own actuator.
        actuated: Dict[str, str] = {}
        existing_actuator_targets = {a.target for a in child.actuators}
        gainprm = [0.0] * 10
        gainprm[0] = self._DEFAULT_KP
        biasprm = [0.0] * 10
        biasprm[1] = -self._DEFAULT_KP
        biasprm[2] = -self._DEFAULT_KV
        for jname in joint_names_before:
            if jname in existing_actuator_targets:
                continue
            act_name = f"act_{jname}"
            child.add_actuator(
                name=act_name,
                target=jname,
                trntype=mujoco.mjtTrn.mjTRN_JOINT,
                gaintype=mujoco.mjtGain.mjGAIN_FIXED,
                gainprm=gainprm,
                biastype=mujoco.mjtBias.mjBIAS_AFFINE,
                biasprm=biasprm,
                ctrlrange=[-1e6, 1e6],
                ctrllimited=True,
            )
            actuated[jname] = act_name

        frame = self._spec.worldbody.add_frame(
            pos=list(robot_config.position),
            quat=_xyzw_to_wxyz(robot_config.rotation),
        )
        self._spec.attach(child, prefix=prefix, frame=frame)

        try:
            self._recompile()
        except Exception as exc:  # pragma: no cover - defensive
            self._last_error = str(exc)
            raise RuntimeError(f"Failed to spawn robot {robot_config.name}: {exc}") from exc

        body_name = f"{prefix}{root_body_name}" if root_body_name else prefix.rstrip("_")
        entry = _RobotEntry(
            config=robot_config,
            body_name=body_name,
            joint_names=[f"{prefix}{j}" for j in joint_names_before],
            actuator_names={f"{prefix}{j}": f"{prefix}{a}" for j, a in actuated.items()},
        )
        self._robots[robot_config.name] = entry
        return robot_config.name

    def remove_robot(self, robot_name: str) -> None:
        if robot_name not in self._robots:
            return
        entry = self._robots.pop(robot_name)
        self._prev_body_lin_vel.pop(entry.body_name, None)
        try:
            body = self._spec.body(entry.body_name)
            self._spec.delete(body)
            self._recompile()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Failed to cleanly remove robot {robot_name}: {exc}")

    def reset_robot(self, robot_name: str) -> None:
        entry = self._robots.get(robot_name)
        if entry is None:
            raise KeyError(f"Robot not found: {robot_name}")
        for jname in entry.joint_names:
            jid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_JOINT, jname)
            if jid < 0:
                continue
            qadr = self._model.jnt_qposadr[jid]
            vadr = self._model.jnt_dofadr[jid]
            qdim = _joint_qpos_dim(self._model.jnt_type[jid])
            vdim = _joint_dof_dim(self._model.jnt_type[jid])
            self._data.qpos[qadr : qadr + qdim] = self._model.qpos0[qadr : qadr + qdim]
            self._data.qvel[vadr : vadr + vdim] = 0.0
        mujoco.mj_forward(self._model, self._data)

    def _body_state(self, body_name: str) -> Tuple[
        Tuple[float, float, float],
        Tuple[float, float, float, float],
        Tuple[float, float, float],
        Tuple[float, float, float],
    ]:
        bid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if bid < 0:
            raise KeyError(f"Body not found in compiled model: {body_name}")

        pos = tuple(float(v) for v in self._data.xpos[bid])
        rot = _wxyz_to_xyzw(self._data.xquat[bid])

        vel6 = np.zeros(6)
        mujoco.mj_objectVelocity(self._model, self._data, mujoco.mjtObj.mjOBJ_BODY, bid, vel6, 0)
        angular = tuple(float(v) for v in vel6[0:3])
        linear = tuple(float(v) for v in vel6[3:6])
        return pos, rot, linear, angular

    def get_robot_state(self, robot_name: str) -> RobotState:
        entry = self._robots.get(robot_name)
        if entry is None:
            raise KeyError(f"Robot not found: {robot_name}")

        position, rotation, linear_velocity, angular_velocity = self._body_state(
            entry.body_name
        )

        joint_positions: Dict[str, float] = {}
        joint_velocities: Dict[str, float] = {}
        joint_forces: Dict[str, float] = {}
        for jname in entry.joint_names:
            jid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_JOINT, jname)
            if jid < 0:
                continue
            short = jname[len(f"{robot_name}_") :]
            qadr = self._model.jnt_qposadr[jid]
            vadr = self._model.jnt_dofadr[jid]
            joint_positions[short] = float(self._data.qpos[qadr])
            joint_velocities[short] = float(self._data.qvel[vadr])
            joint_forces[short] = float(self._data.qfrc_applied[vadr])

        return RobotState(
            robot_name=robot_name,
            position=position,
            rotation=rotation,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity,
            joint_positions=joint_positions,
            joint_velocities=joint_velocities,
            joint_forces=joint_forces,
            timestamp=float(self._data.time),
        )

    def set_robot_pose(
        self,
        robot_name: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
    ) -> None:
        entry = self._robots.get(robot_name)
        if entry is None:
            raise KeyError(f"Robot not found: {robot_name}")

        bid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_BODY, entry.body_name)
        jadr = self._model.body_jntadr[bid]
        jnum = self._model.body_jntnum[bid]
        if jnum == 1 and self._model.jnt_type[jadr] == mujoco.mjtJoint.mjJNT_FREE:
            qadr = self._model.jnt_qposadr[jadr]
            self._data.qpos[qadr : qadr + 3] = position
            self._data.qpos[qadr + 3 : qadr + 7] = _xyzw_to_wxyz(rotation)
            mujoco.mj_forward(self._model, self._data)
        else:
            raise RuntimeError(
                f"Cannot reposition robot '{robot_name}' at runtime: its base is "
                f"fixed (fixed_base=True or no free joint). Fixed-base pose is set "
                f"at spawn time via RobotConfig.position/rotation."
            )

    def set_joint_target(
        self,
        robot_name: str,
        joint_name: str,
        target_value: float,
        velocity: float = 0.0,
        force: float = 1000.0,
    ) -> None:
        entry = self._robots.get(robot_name)
        if entry is None:
            raise KeyError(f"Robot not found: {robot_name}")
        full_joint = f"{robot_name}_{joint_name}"
        actuator_name = entry.actuator_names.get(full_joint)
        if actuator_name is None:
            raise KeyError(
                f"No controllable actuator for joint '{joint_name}' on robot "
                f"'{robot_name}' (joint has its own actuator defined in its "
                f"source model, or does not exist)."
            )
        aid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_name)
        if aid < 0:
            raise KeyError(f"Actuator not found in compiled model: {actuator_name}")
        self._data.ctrl[aid] = target_value

    def apply_joint_force(self, robot_name: str, joint_name: str, force: float) -> None:
        entry = self._robots.get(robot_name)
        if entry is None:
            raise KeyError(f"Robot not found: {robot_name}")
        full_joint = f"{robot_name}_{joint_name}"
        jid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_JOINT, full_joint)
        if jid < 0:
            raise KeyError(f"Joint not found: {joint_name}")
        vadr = self._model.jnt_dofadr[jid]
        self._data.qfrc_applied[vadr] = force

    def get_joint_state(self, robot_name: str, joint_name: str) -> Dict[str, float]:
        entry = self._robots.get(robot_name)
        if entry is None:
            raise KeyError(f"Robot not found: {robot_name}")
        full_joint = f"{robot_name}_{joint_name}"
        jid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_JOINT, full_joint)
        if jid < 0:
            raise KeyError(f"Joint not found: {joint_name}")
        qadr = self._model.jnt_qposadr[jid]
        vadr = self._model.jnt_dofadr[jid]
        return {
            "position": float(self._data.qpos[qadr]),
            "velocity": float(self._data.qvel[vadr]),
            "force": float(self._data.qfrc_applied[vadr]),
        }

    # ==================== OBJECT/ASSET MANAGEMENT ====================

    def spawn_object(
        self,
        name: str,
        model_path: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
        scale: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        if name in self._objects:
            raise ValueError(f"Object already exists: {name}")

        static = bool((metadata or {}).get("static", False))
        child = self._build_child_spec(model_path)
        prefix = f"{name}_"

        root_bodies = list(child.worldbody.bodies)
        if root_bodies and not static and not list(root_bodies[0].joints):
            root_bodies[0].add_freejoint(name="freejoint")

        # Snapshot the name as a plain string *before* attach(), which
        # renames the child spec's elements in place to include the prefix.
        root_body_name = root_bodies[0].name if root_bodies else None

        frame = self._spec.worldbody.add_frame(
            pos=list(position), quat=_xyzw_to_wxyz(rotation)
        )
        self._spec.attach(child, prefix=prefix, frame=frame)
        self._recompile()

        body_name = f"{prefix}{root_body_name}" if root_body_name else prefix.rstrip("_")
        self._objects[name] = _ObjectEntry(model_path=model_path, body_name=body_name)
        return name

    def remove_object(self, object_name: str) -> None:
        if object_name not in self._objects:
            return
        entry = self._objects.pop(object_name)
        self._prev_body_lin_vel.pop(entry.body_name, None)
        try:
            body = self._spec.body(entry.body_name)
            self._spec.delete(body)
            self._recompile()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Failed to cleanly remove object {object_name}: {exc}")

    def get_object_state(self, object_name: str) -> ObjectState:
        entry = self._objects.get(object_name)
        if entry is None:
            raise KeyError(f"Object not found: {object_name}")
        position, rotation, linear_velocity, angular_velocity = self._body_state(
            entry.body_name
        )
        return ObjectState(
            object_name=object_name,
            position=position,
            rotation=rotation,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity,
            timestamp=float(self._data.time),
        )

    def set_object_pose(
        self,
        object_name: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
    ) -> None:
        entry = self._objects.get(object_name)
        if entry is None:
            raise KeyError(f"Object not found: {object_name}")
        bid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_BODY, entry.body_name)
        jadr = self._model.body_jntadr[bid]
        jnum = self._model.body_jntnum[bid]
        if jnum == 1 and self._model.jnt_type[jadr] == mujoco.mjtJoint.mjJNT_FREE:
            qadr = self._model.jnt_qposadr[jadr]
            self._data.qpos[qadr : qadr + 3] = position
            self._data.qpos[qadr + 3 : qadr + 7] = _xyzw_to_wxyz(rotation)
            mujoco.mj_forward(self._model, self._data)
        else:
            raise RuntimeError(
                f"Cannot reposition static object '{object_name}' at runtime "
                f"(spawned with metadata={{'static': True}})."
            )

    # ==================== SENSOR MANAGEMENT ====================

    def attach_sensor(self, robot_name: str, sensor_config: SensorConfig) -> str:
        if robot_name not in self._robots and robot_name != "__world__":
            raise KeyError(f"Robot not found: {robot_name}")
        sensor_id = f"{robot_name}_{sensor_config.name}"

        camera_name = None
        if sensor_config.sensor_type in (
            SensorType.RGB_CAMERA,
            SensorType.DEPTH_CAMERA,
            SensorType.SEMANTIC_CAMERA,
            SensorType.INSTANCE_SEGMENTATION,
            SensorType.THERMAL_CAMERA,
        ):
            entry = self._robots.get(robot_name)
            parent_body = entry.body_name if entry else "world"
            try:
                body = self._spec.body(parent_body)
            except Exception:
                body = self._spec.worldbody
            camera_name = f"{sensor_id}_cam"
            body.add_camera(
                name=camera_name,
                pos=list(sensor_config.position),
                quat=_xyzw_to_wxyz(sensor_config.rotation),
            )
            self._recompile()

        self._sensors[sensor_id] = _SensorEntry(
            config=sensor_config, robot_name=robot_name, camera_name=camera_name
        )
        return sensor_id

    def remove_sensor(self, robot_name: str, sensor_name: str) -> None:
        sensor_id = f"{robot_name}_{sensor_name}"
        entry = self._sensors.pop(sensor_id, None)
        if entry and entry.camera_name:
            try:
                cam = self._spec.camera(entry.camera_name)
                self._spec.delete(cam)
                self._recompile()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"Failed to remove sensor camera: {exc}")

    def get_sensor_data(self, robot_name: str, sensor_name: str) -> SensorData:
        sensor_id = f"{robot_name}_{sensor_name}"
        entry = self._sensors.get(sensor_id)
        if entry is None:
            raise KeyError(f"Sensor not found: {sensor_id}")

        if entry.config.sensor_type == SensorType.LIDAR:
            raw = self.get_lidar_scan(robot_name, sensor_name)
        elif entry.config.sensor_type == SensorType.IMU:
            raw = self.get_imu_data(robot_name, sensor_name)
        elif entry.camera_name:
            raw = self.get_camera_image(robot_name, sensor_name)
        else:
            raw = {}

        return SensorData(
            sensor_name=sensor_id,
            sensor_type=entry.config.sensor_type,
            timestamp=float(self._data.time),
            raw_data=raw,
        )

    def get_camera_image(
        self,
        robot_name: str,
        camera_name: str,
        include_depth: bool = False,
        include_segmentation: bool = False,
    ) -> Dict[str, Any]:
        sensor_id = f"{robot_name}_{camera_name}"
        entry = self._sensors.get(sensor_id)
        if entry is None or not entry.camera_name:
            raise KeyError(f"Camera sensor not found: {sensor_id}")
        if not self._rendering_enabled:
            raise RuntimeError("Rendering is disabled; call enable_rendering() first")

        width = getattr(entry.config, "width", 640)
        height = getattr(entry.config, "height", 480)
        renderer = mujoco.Renderer(self._model, height=height, width=width)
        try:
            renderer.update_scene(self._data, camera=entry.camera_name)
            rgb = renderer.render().copy()

            result: Dict[str, Any] = {"rgb": rgb, "timestamp": float(self._data.time)}

            if include_depth:
                renderer.enable_depth_rendering()
                renderer.update_scene(self._data, camera=entry.camera_name)
                result["depth"] = renderer.render().copy()
                renderer.disable_depth_rendering()

            if include_segmentation:
                renderer.enable_segmentation_rendering()
                renderer.update_scene(self._data, camera=entry.camera_name)
                result["segmentation"] = renderer.render().copy()
                renderer.disable_segmentation_rendering()

            return result
        finally:
            renderer.close()

    def get_lidar_scan(self, robot_name: str, lidar_name: str) -> Dict[str, Any]:
        sensor_id = f"{robot_name}_{lidar_name}"
        entry = self._sensors.get(sensor_id)
        if entry is None:
            raise KeyError(f"Lidar sensor not found: {sensor_id}")

        cfg = entry.config
        num_beams = getattr(cfg, "num_beams", 32)
        max_range = getattr(cfg, "max_range", 100.0)
        h_fov = getattr(cfg, "horizontal_fov", 360.0)

        robot_entry = self._robots.get(robot_name)
        if robot_entry is not None:
            bid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_BODY, robot_entry.body_name)
            origin = self._data.xpos[bid].copy()
        else:
            origin = np.zeros(3)
        origin = origin + np.array(cfg.position)

        points = np.zeros((num_beams, 3), dtype=np.float32)
        intensities = np.zeros(num_beams, dtype=np.float32)
        geomid = np.array([-1], dtype=np.int32)

        angles = np.linspace(0, np.deg2rad(h_fov), num_beams, endpoint=False)
        for i, angle in enumerate(angles):
            direction = np.array([np.cos(angle), np.sin(angle), 0.0])
            dist = mujoco.mj_ray(
                self._model, self._data, origin, direction, None, 1, -1, geomid
            )
            if dist is not None and dist >= 0 and dist <= max_range:
                points[i] = origin + direction * dist
                intensities[i] = 1.0 - (dist / max_range)
            else:
                points[i] = origin + direction * max_range
                intensities[i] = 0.0

        return {
            "points": points,
            "intensities": intensities,
            "timestamps": np.full(num_beams, self._data.time, dtype=np.float64),
            "num_points": num_beams,
        }

    def get_imu_data(self, robot_name: str, imu_name: str) -> Dict[str, Any]:
        sensor_id = f"{robot_name}_{imu_name}"
        entry = self._sensors.get(sensor_id)
        if entry is None:
            raise KeyError(f"IMU sensor not found: {sensor_id}")

        robot_entry = self._robots.get(robot_name)
        if robot_entry is None:
            raise KeyError(f"Robot not found: {robot_name}")

        bid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_BODY, robot_entry.body_name)
        vel6 = np.zeros(6)
        # flg_local=1: velocity expressed in the body's own frame, like a real IMU.
        mujoco.mj_objectVelocity(self._model, self._data, mujoco.mjtObj.mjOBJ_BODY, bid, vel6, 1)
        gyro = vel6[0:3]
        lin_vel = vel6[3:6]

        prev = self._prev_body_lin_vel.get(robot_entry.body_name)
        dt = self._model.opt.timestep
        if prev is not None and dt > 0:
            accel = (lin_vel - prev) / dt
        else:
            accel = np.zeros(3)
        # Real accelerometers measure proper acceleration (excludes gravity's
        # free-fall contribution): subtract gravity, expressed in body frame.
        gravity_world = np.array(self._model.opt.gravity)
        xmat = self._data.xmat[bid].reshape(3, 3)
        gravity_body = xmat.T @ gravity_world
        proper_accel = accel - gravity_body

        self._prev_body_lin_vel[robot_entry.body_name] = lin_vel.copy()

        quat = _wxyz_to_xyzw(self._data.xquat[bid])
        return {
            "accel": tuple(float(v) for v in proper_accel),
            "gyro": tuple(float(v) for v in gyro),
            "quat": quat,
            "timestamp": float(self._data.time),
        }

    # ==================== PHYSICS & DYNAMICS ====================

    def set_gravity(self, gravity: Tuple[float, float, float]) -> None:
        self._spec.option.gravity = list(gravity)
        if self._model is not None:
            self._model.opt.gravity[:] = gravity

    def get_gravity(self) -> Tuple[float, float, float]:
        if self._model is not None:
            return tuple(float(g) for g in self._model.opt.gravity)
        return tuple(float(g) for g in self._spec.option.gravity)

    def set_timestep(self, timestep_ms: float) -> None:
        timestep_s = max(timestep_ms, 1e-4) / 1000.0
        self._spec.option.timestep = timestep_s
        if self._model is not None:
            self._model.opt.timestep = timestep_s

    def get_contacts(self) -> List[ContactInfo]:
        if self._data is None:
            return []
        contacts: List[ContactInfo] = []
        for i in range(self._data.ncon):
            c = self._data.contact[i]
            name_a = self._model.geom(c.geom1).name or f"geom_{c.geom1}"
            name_b = self._model.geom(c.geom2).name or f"geom_{c.geom2}"
            force6 = np.zeros(6)
            mujoco.mj_contactForce(self._model, self._data, i, force6)
            force_mag = float(np.linalg.norm(force6[:3]))
            contacts.append(
                ContactInfo(
                    body_a=name_a,
                    body_b=name_b,
                    position=tuple(float(v) for v in c.pos),
                    normal=tuple(float(v) for v in c.frame[:3]),
                    distance=float(c.dist),
                    force_magnitude=force_mag,
                )
            )
        return contacts

    def raycast(
        self,
        origin: Tuple[float, float, float],
        direction: Tuple[float, float, float],
        max_distance: float = 1000.0,
    ) -> Optional[Dict[str, Any]]:
        if self._data is None:
            return None
        direction_arr = np.array(direction, dtype=np.float64)
        norm = np.linalg.norm(direction_arr)
        if norm == 0:
            return None
        direction_arr = direction_arr / norm

        geomid = np.array([-1], dtype=np.int32)
        dist = mujoco.mj_ray(
            self._model,
            self._data,
            np.array(origin, dtype=np.float64),
            direction_arr,
            None,
            1,
            -1,
            geomid,
        )
        if dist is None or dist < 0 or dist > max_distance or geomid[0] < 0:
            return None

        hit_pos = np.array(origin) + direction_arr * dist
        body_id = self._model.geom_bodyid[geomid[0]]
        body_name = self._model.body(body_id).name

        return {
            "body_name": body_name,
            "position": tuple(float(v) for v in hit_pos),
            "normal": tuple(float(v) for v in direction_arr),
            "distance": float(dist),
        }

    # ==================== SIMULATION CONTROL ====================

    def step(self, num_steps: int = 1) -> SimulationStep:
        if self._paused:
            raise RuntimeError("Cannot step while paused")
        if self._model is None or self._data is None:
            raise RuntimeError("No world initialized; call create_world() first")

        for _ in range(num_steps):
            mujoco.mj_step(self._model, self._data)
            self._step_count += 1

        # mj_step's internal forward pass computes xpos/xquat/etc. from the
        # *pre-integration* qpos, so after stepping they lag qpos/qvel by one
        # step. Re-run forward kinematics so state reads below (and any
        # get_robot_state/get_object_state call after this returns) reflect
        # the just-integrated state, not a stale one.
        mujoco.mj_forward(self._model, self._data)

        robot_states = {name: self.get_robot_state(name) for name in self._robots}
        object_states = {name: self.get_object_state(name) for name in self._objects}

        return SimulationStep(
            step_count=self._step_count,
            elapsed_time_sec=float(self._data.time),
            timestep_ms=float(self._model.opt.timestep) * 1000.0,
            robot_states=robot_states,
            object_states=object_states,
            contacts=self.get_contacts(),
            sensor_data={},
        )

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def reset(self) -> None:
        if self._model is not None and self._data is not None:
            mujoco.mj_resetData(self._model, self._data)
            mujoco.mj_forward(self._model, self._data)
        self._step_count = 0
        self._prev_body_lin_vel.clear()

    def is_paused(self) -> bool:
        return self._paused

    # ==================== RENDERING & VISUALIZATION ====================

    def enable_rendering(self) -> None:
        self._rendering_enabled = True

    def disable_rendering(self) -> None:
        self._rendering_enabled = False
        self._renderer = None

    def set_camera_view(
        self,
        position: Tuple[float, float, float],
        target: Tuple[float, float, float],
        up: Tuple[float, float, float] = (0.0, 0.0, 1.0),
    ) -> None:
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = target
        offset = np.array(position) - np.array(target)
        distance = float(np.linalg.norm(offset)) or 1.0
        cam.distance = distance
        cam.azimuth = float(np.degrees(np.arctan2(offset[1], offset[0])))
        horiz = float(np.linalg.norm(offset[:2])) or 1e-6
        cam.elevation = float(np.degrees(np.arctan2(offset[2], horiz)))
        self._viewport_cam = cam

    def render_frame(self) -> Optional[bytes]:
        if not self._rendering_enabled or self._model is None or self._data is None:
            return None
        height, width = self._renderer_size
        renderer = mujoco.Renderer(self._model, height=height, width=width)
        try:
            if self._viewport_cam is not None:
                renderer.update_scene(self._data, camera=self._viewport_cam)
            else:
                renderer.update_scene(self._data)
            rgb = renderer.render()
            return rgb.tobytes()
        finally:
            renderer.close()

    # ==================== DOMAIN RANDOMIZATION ====================
    # These mutate the compiled MjModel's numeric arrays in place, which is
    # the standard MuJoCo technique for domain randomization (no recompile
    # needed, so simulation state is preserved).

    def randomize_lighting(
        self,
        intensity_range: Tuple[float, float],
        color_range: Optional[
            Tuple[Tuple[float, float, float], Tuple[float, float, float]]
        ] = None,
    ) -> None:
        if self._model is None or self._model.nlight == 0:
            return
        rng = np.random.default_rng()
        for i in range(self._model.nlight):
            intensity = rng.uniform(intensity_range[0], intensity_range[1])
            if color_range is not None:
                lo, hi = np.array(color_range[0]), np.array(color_range[1])
                color = rng.uniform(lo, hi)
            else:
                color = np.array([intensity, intensity, intensity])
            self._model.light_diffuse[i] = color

    def randomize_friction(
        self, object_name: str, friction_range: Tuple[float, float]
    ) -> None:
        if self._model is None:
            return
        entry = self._objects.get(object_name) or self._robots.get(object_name)
        if entry is None:
            raise KeyError(f"Object/robot not found: {object_name}")
        bid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_BODY, entry.body_name)
        rng = np.random.default_rng()
        for gid in range(self._model.ngeom):
            if self._model.geom_bodyid[gid] == bid:
                mu = rng.uniform(friction_range[0], friction_range[1])
                self._model.geom_friction[gid, 0] = mu

    def randomize_mass(self, object_name: str, mass_range: Tuple[float, float]) -> None:
        if self._model is None:
            return
        entry = self._objects.get(object_name) or self._robots.get(object_name)
        if entry is None:
            raise KeyError(f"Object/robot not found: {object_name}")
        bid = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_BODY, entry.body_name)
        rng = np.random.default_rng()
        new_mass = rng.uniform(mass_range[0], mass_range[1])
        old_mass = self._model.body_mass[bid]
        if old_mass > 0:
            ratio = new_mass / old_mass
            self._model.body_inertia[bid] *= ratio
        self._model.body_mass[bid] = new_mass

    # ==================== UTILITIES & INFO ====================

    def get_simulator_type(self) -> SimulatorType:
        return SimulatorType.MUJOCO

    def get_simulation_info(self) -> Dict[str, Any]:
        info = {
            "simulator": "mujoco",
            "mujoco_version": mujoco.__version__,
            "step_count": self._step_count,
            "robot_count": len(self._robots),
            "object_count": len(self._objects),
        }
        if self._data is not None:
            info["elapsed_time_sec"] = float(self._data.time)
        if self._model is not None:
            info["body_count"] = int(self._model.nbody)
        return info

    def list_robots(self) -> List[str]:
        return list(self._robots.keys())

    def list_objects(self) -> List[str]:
        return list(self._objects.keys())

    def get_robot_info(self, robot_name: str) -> Dict[str, Any]:
        entry = self._robots.get(robot_name)
        if entry is None:
            raise KeyError(f"Robot not found: {robot_name}")
        return {
            "name": robot_name,
            "type": entry.config.robot_type.value,
            "body_name": entry.body_name,
            "joints": [j[len(f"{robot_name}_") :] for j in entry.joint_names],
            "actuated_joints": [
                j[len(f"{robot_name}_") :] for j in entry.actuator_names
            ],
        }

    # ==================== ERROR HANDLING & VALIDATION ====================

    def validate_configuration(self, config: SimulatorConfig) -> bool:
        if config.timestep_ms <= 0:
            self._last_error = "timestep_ms must be positive"
            return False
        if not isinstance(config.gravity, tuple) or len(config.gravity) != 3:
            self._last_error = "gravity must be a 3-tuple"
            return False
        return True

    def get_last_error(self) -> Optional[str]:
        return self._last_error


# ==================== MODULE-LEVEL HELPERS ====================


def _joint_qpos_dim(jnt_type: int) -> int:
    """Number of qpos scalars consumed by a joint of this mjtJoint type."""
    if jnt_type == mujoco.mjtJoint.mjJNT_FREE:
        return 7
    if jnt_type == mujoco.mjtJoint.mjJNT_BALL:
        return 4
    return 1  # slide or hinge


def _joint_dof_dim(jnt_type: int) -> int:
    """Number of qvel/dof scalars consumed by a joint of this mjtJoint type."""
    if jnt_type == mujoco.mjtJoint.mjJNT_FREE:
        return 6
    if jnt_type == mujoco.mjtJoint.mjJNT_BALL:
        return 3
    return 1  # slide or hinge


def _make_primitive_spec(spec_str: str) -> "mujoco.MjSpec":
    """Build a `MjSpec` for a `"primitive:<shape>[:sx,sy,sz][:mass]"` string.

    Examples:
        "primitive:box"                 -> 0.1x0.1x0.1 m box, 1 kg
        "primitive:sphere:0.05"         -> 0.05 m radius sphere, 1 kg
        "primitive:box:0.2,0.1,0.1:2.5" -> 0.2x0.1x0.1 m box, 2.5 kg
    """
    parts = spec_str.split(":")
    shape = parts[1] if len(parts) > 1 else "box"
    size_str = parts[2] if len(parts) > 2 else None
    mass_str = parts[3] if len(parts) > 3 else None

    mass = float(mass_str) if mass_str else 1.0

    shape_map = {
        "box": mujoco.mjtGeom.mjGEOM_BOX,
        "sphere": mujoco.mjtGeom.mjGEOM_SPHERE,
        "capsule": mujoco.mjtGeom.mjGEOM_CAPSULE,
        "cylinder": mujoco.mjtGeom.mjGEOM_CYLINDER,
    }
    if shape not in shape_map:
        raise ValueError(
            f"Unknown primitive shape '{shape}'. Supported: {list(shape_map)}"
        )

    if size_str:
        size = [float(x) for x in size_str.split(",")]
    elif shape == "sphere":
        size = [0.1]
    elif shape in ("capsule", "cylinder"):
        size = [0.05, 0.1]
    else:
        size = [0.1, 0.1, 0.1]

    spec = mujoco.MjSpec()
    body = spec.worldbody.add_body(name="root", pos=[0, 0, 0])
    body.add_geom(
        name="geom",
        type=shape_map[shape],
        size=size,
        mass=mass,
        rgba=[0.7, 0.3, 0.3, 1.0],
    )
    return spec
