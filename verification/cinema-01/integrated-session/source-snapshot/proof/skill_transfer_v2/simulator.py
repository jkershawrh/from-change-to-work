"""Pinned, local-only MuJoCo adapter. No network, release parsing or robot driver.

Each input advances at most one 20 ms interval. EOF stops the process; no task
continues autonomously after the Rust executor dies. Uses the read-only existing
plant and inverse dynamics helpers, never their experiment runner or outputs.
"""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
import mujoco
import numpy as np

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / 'proof/control_v2/run_control.py'
JOINTS = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
          'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']


def plant_identity():
    files = [SOURCE, REPO / 'proof/control_v2/scene.xml']
    files += sorted(p for p in (REPO / 'proof/control/assets/ur5e').rglob('*') if p.is_file())
    inventory = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    raw = json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest(), inventory


def emit(value):
    print(json.dumps(value, allow_nan=False, separators=(',', ':')), flush=True)


def main():
    spec = importlib.util.spec_from_file_location('transfer_existing_control', SOURCE)
    control = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(control)
    plant, nominal = control.load_model(), control.load_model()
    data, inverse, check = mujoco.MjData(plant), mujoco.MjData(nominal), mujoco.MjData(plant)
    mujoco.mj_resetDataKeyframe(plant, data, 0)
    data.ctrl[:] = 0
    mujoco.mj_forward(plant, data)
    assert [plant.joint(i).name for i in range(plant.njnt)] == JOINTS
    emit({'kind': 'Ready', 'plant_sha256': plant_identity()[0],
          'runtime_version': mujoco.__version__, 'joint_names': JOINTS})
    def state():
        return {'q': data.qpos.tolist(), 'velocity': data.qvel.tolist(),
                'simulation_seconds': float(data.time)}
    while True:
        line = sys.stdin.buffer.readline(65537)
        if not line:
            return
        if len(line) > 65536 or not line.endswith(b'\n'):
            raise ValueError('bounded adapter protocol')
        request = json.loads(line)
        kind = request['kind']
        if kind == 'observe' and set(request) == {'kind'}:
            emit({'kind': 'Observed', 'state': state()})
        elif kind == 'check' and set(request) == {'kind', 'positions'}:
            positions = np.asarray(request['positions'], dtype=float)
            assert positions.ndim == 2 and positions.shape[1] == 6 and 1 <= len(positions) <= 20
            assert np.all(np.isfinite(positions))
            clear, _ = control.clear_path(plant, check, data.qpos.tolist(), positions.tolist())
            emit({'kind': 'Checked', 'clear': clear})
        elif kind == 'step' and set(request) == {'kind', 'acceleration'}:
            acceleration = np.asarray(request['acceleration'], dtype=float)
            assert acceleration.shape == (6,) and np.all(np.isfinite(acceleration))
            assert np.max(np.abs(acceleration)) <= .85 + 1e-9
            # Approximate presentation pacing only. The stepped plant pauses for IPC,
            # persistence and computation. This is not a real-time scheduler test.
            time.sleep(.02)
            _, _, steps = control.simulate_interval(plant, data, nominal, inverse, acceleration, np.zeros(6))
            emit({'kind': 'Stepped', 'state': state(), 'substeps': steps})
        else:
            raise ValueError('unknown adapter operation')


if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
