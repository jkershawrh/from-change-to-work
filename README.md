# From Change to Work

**Deliver an approved task from remote engineering to a robot cell. Keep execution control local.**

A public, standalone Red Hat × Intel robotics demo, dashboard, simulator workflow, and hardware-testing handoff. The first use case is aerospace inspection positioning. Rework positioning exercises the same transfer and recovery mechanism; additional cell types require separately reviewed adapters.

The business hypothesis is that a repeatable, accountable handoff can reduce the effort between an approved engineering change and accepted work. Factory delay, inspection accuracy, production savings, physical robot performance, and accelerator benefit have not been measured by this demo.

## Watch the demo

The complete narrated film is **5:31**. It opens with “From change to work. A Red Hat and Intel robotics story,” then follows the work package through delivery, local acceptance, disconnection, recovery, reuse, and a bounded pilot.

- Local video: [`presentation/public/film/from-change-to-work-announced.mp4`](presentation/public/film/from-change-to-work-announced.mp4).
- Interactive presentation after startup: **http://127.0.0.1:8090/show/**.
- Dashboard and agent start packet: **http://127.0.0.1:8090/**.
- Transfer and simulator workbench: **http://127.0.0.1:8090/?actions=1**.

The movie includes music, the approved Kersh voice, and Red Hat and Intel logos. It has no burned-in captions, voice-production footer, or decorative playback bar. The interactive presentation retains working controls and optional captions. CGI and recorded simulator playback are labeled; playing or seeking the story never starts a robot action.

## Clone and run

Prerequisites: Git LFS, Python 3.12, Rust/Cargo 1.90 or newer, and Node 22.12+ or 24. Setup installs project dependencies and builds the native executor; no kernel or driver change is required.

```bash
git clone https://github.com/jkershawrh/from-change-to-work.git
cd from-change-to-work
git lfs pull
python3 scripts/doctor.py --out evidence/readiness-before-setup.json
./scripts/setup.sh
python3 scripts/doctor.py --out evidence/readiness-after-setup.json
./scripts/run-demo.sh
```

A doctor exit code of 2 means prerequisites are missing; read its next-step guidance and continue setup. A ready doctor report establishes prerequisites, not successful execution or hardware qualification.

Open the dashboard. For live simulator controls, use the generated operator code in `.action-lab/central/private/operator-code`. The viewer code is read-only. No cluster password, robot password, AI-provider key, or original chat history is required. Never commit generated state, codes, keys, or credentials.

## What actually transfers

The central service sends an immutable action request bound to a destination and release. The receiving runtime independently fetches a **signed, bounded joint-goal recipe**. Rust verifies its identity, signature, local approval, profile compatibility, expiry, and sequence; activates it only while idle; and pins the exact release to the task. MuJoCo and a local Rust controller execute the finite simulator task.

The package does not install arbitrary code, trained weights, a container, or a robot driver. Training, JEPA, OpenVINO, Gaudi acceleration, and physical actuation are not required or claimed by this proof. Compute and platform choices are qualified per target host and use case.

## Test the mechanism

1. Inspect the **Recorded proof** as historical evidence, then open **Live simulation** and unlock the operator session.
2. Select inspection and **Transfer & execute**.
3. After observed progress begins, **Disconnect central link**. This cuts the central data plane; the separately labeled management observer remains available. Wait for edge completion.
4. Reconnect and retry the same completed action ID. The stored receipt must return without another execution.
5. Start rework with a deliberately new action ID, then interrupt the simulator executor after committed progress.
6. Observe **RECOVERY REQUIRED**. Explicit recovery records the old task as interrupted; it does not resume motion.
7. Create a new action ID and execute again. Capture and independently audit the complete challenge.

```bash
./scripts/check.sh
.venv/bin/python scripts/capture_action_session.py --state .action-lab --out evidence/session-001
.venv/bin/python scripts/audit_action_session.py evidence/session-001
```

Use fresh evidence paths. After implementation changes, preserve the old session and prepare a new state directory before testing. Browser observations are not an independent audit. The capture/auditor verifies source identities, signed recipes, action/release binding, committed control and physics samples, duplicate-start rejection, disconnect/completion causality, and deliberate recovery.

## Handoff to Preston or a testing agent

Start with [the handoff checklist](docs/HANDOFF.md), [agent due diligence](docs/AGENT_START.md), and [hardware setup](docs/PRESTON.md). The machine-readable map is [`onboarding/manifest.json`](onboarding/manifest.json).

Give an agent this prompt:

> Read AGENTS.md, README.md, docs/HANDOFF.md, docs/AGENT_START.md, and onboarding/manifest.json. Explain the remote-to-local transfer and authority boundaries. Inventory this host, identify missing hardware facts, run the authorized simulator checks, and guide a fresh transfer/disconnect/recovery challenge. Capture and independently audit the evidence. Report scoped TDD, EDD, CDD, BDD, and CBT with red/amber/green and the next blocker. Do not infer hardware qualification from a readiness report, presentation, or historical proof. Do not activate physical motion or change a kernel, driver, trust policy, or controller limit.

**Testing hardware is pending confirmation.** Record the actual central/edge hosts, CPU, OS, topology, robot/controller if proposed, interface, tooling, calibration, and acceptance owner in a new hardware intake. Keep those details in the repository handoff; the audience demo stays focused on the business process.

## Evidence and acceptance

Retained separate-host simulator evidence ran on distinct Intel Xeon 6767P workers with RHEL 9.6 containers on OpenShift 4.21.10. Its independent audit accounts for 761 control ticks and 7,610 physics substeps. The failed attempt and successful attempt are both retained. This is a historical baseline, not qualification of Preston’s next host.

Local software checks, evidence audits, presentation verification, and media review have separate scopes. New-host acceptance requires its own inventory and challenge. Physical motion, robot safeguards, device attestation, and hard real time remain separate gates. No vendor certification or production ROI is asserted.

Read [architecture and authority](docs/ARCHITECTURE.md), [acceptance rubric](docs/ACCEPTANCE.md), and [the video review](docs/FINAL_VIDEO_REVIEW.md). The new repository’s hosted GitHub job was blocked before any steps ran by the account billing/spending restriction. All 128 local checks passed. The tracked-only historical proof package also passes its independent audit. See `verification/precommit-20261023/result.json`; no hosted pass is claimed.
