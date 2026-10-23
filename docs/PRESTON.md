# From Change to Work — Preston’s hardware validation handoff

Start with **compute hardware running the simulator**. Connecting an actual arm is a separate profile/driver and safety acceptance step; nothing in this repository authorizes physical motion.

## Agent-assisted start

Give the testing agent `AGENTS.md`, `docs/AGENT_START.md` and the dashboard start packet. Run `python3 scripts/doctor.py --out evidence/readiness-001.json` on each host. Proposed hardware intake is unverified; readiness observes the process host only and cannot qualify a robot or cluster. The dashboard is the root URL; the 3D transfer workbench remains `/?actions=1`.

## First local acceptance

Clone this private repository with Git LFS, run `scripts/setup.sh`, then `scripts/run-demo.sh`. Complete the browser challenge sequence in the README. Capture the full session and run the independent auditor. Keep the recorded Flightpath proof visibly historical while qualifying your own host.

Record host manufacturer/model, CPU vendor/model, firmware, OS/kernel, architecture, container image digest if applicable, runtime/dependency versions, available cores/memory, cgroup limits, network topology and simulator/controller identities. Preserve CPU/memory pressure, solver/deadline refusals and measured results; do not replace failures with a presentation animation.

## Two-host compute acceptance

Use a central host for the console/dispatcher/publisher/relay and a distinct edge host for the Rust executor and simulator. No kubeadmin credential or former lab token is supplied or needed.

1. On **both** hosts, clone this repo, install the pinned software and build Rust locally. Use a trusted internal path to transfer generated private material. The application’s ephemeral CA is a lab fixture; customer PKI is a separate gate.
2. On the **edge** host, produce its actual inventory:

   ```bash
   .venv/bin/python scripts/action_lab.py inventory --out edge-inventory.json
   ```

   Copy that public inventory to central. It includes actual target/plant/interpreter/executor identities, not credentials. Do not invent or substitute an Intel identity.
3. On **central**, provision a new session using that inventory and the actual absolute paths that will exist on edge:

   ```bash
   .venv/bin/python scripts/action_lab.py prepare --state .action-lab-hardware \
     --central-host CENTRAL_DNS --edge-host EDGE_DNS \
     --inventory edge-inventory.json \
     --edge-root /absolute/path/from-change-to-work \
     --edge-state /absolute/path/hardware-state/edge \
     --edge-python /absolute/path/from-change-to-work/.venv/bin/python
   ```

4. Transfer the generated `edge/` directory, `session.json` and `source-freeze.json` privately to `/absolute/path/hardware-state/`. Preserve file permissions. Do not commit those generated files. Run on **edge**:

   ```bash
   .venv/bin/python scripts/action_lab.py start --role edge --state /absolute/path/hardware-state
   ```

   On **central**, run:

   ```bash
   .venv/bin/python scripts/action_lab.py start --role central --state .action-lab-hardware
   ```

5. Keep the browser console loopback-bound and forward its port through your trusted access path. Allow only the required site-local TLS ports: default central relays `28453–28455`, edge gateway `28445`. The central publisher/dispatcher and control endpoints remain local. Protect the independent observer channel explicitly; a disconnection test is a data-plane cut, not a physical safety stop.
6. Complete the same browser sequence. Retain actual identities from both hosts and prove they are distinct. The UI’s **TWO ENDPOINTS** label means configured endpoints; it is not host attestation or hardware qualification.
7. Capture each role into separate fresh output directories:

   ```bash
   # Edge:
   .venv/bin/python scripts/capture_action_session.py --role edge --state /absolute/path/hardware-state --out evidence/edge-001
   # Central:
   .venv/bin/python scripts/capture_action_session.py --role central --state .action-lab-hardware --out evidence/central-001
   ```

   Preserve each capture’s file hashes. Independently reconcile and audit the cross-host capture before marking hardware EDD green. The included all-in-one session auditor is qualified for local-mode captures; merging remote role captures and independent clock/host evidence is still a hardware gate, not an automatic green badge.

## Before a physical robot

Name the robot/controller, OEM-supported interface, cell owner, accepted task, calibration, tool/payload limits, watchdog/stop behavior and acceptance evidence. Implement a reviewed local profile adapter; preserve OEM/local safety authority and keep WAN/LLM traffic outside servo control. Repeat contract, rejection, disconnect, interruption, recovery and measured business acceptance tests on that profile. Do not point the MuJoCo adapter at a physical endpoint or change a simulation flag to claim qualification.

No kernel work is required for this software transfer gate. Scheduling/isolation/driver work belongs to a later measured hardware requirement. Retain any unmet timing or safeguarding requirement as red rather than broadening this proof’s claim.
