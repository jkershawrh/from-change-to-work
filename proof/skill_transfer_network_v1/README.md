# Intel × Red Hat: EVY to an edge capability executor

This proof deploys the existing EVY FastAPI gateway with its private capability-action patch on one Flightpath worker and the existing Rust transfer executor with MuJoCo on another. It transfers signed deterministic joint-goal recipes. It does not train a policy, deliver arbitrary executable code, or qualify a physical robot.

The reusable process is:

1. An authenticated EVY operator selects an enrolled edge, capability and exact approved release digest.
2. EVY durably binds the action ID and configured destination. A viewer can observe but cannot submit.
3. A small HTTPS reference adapter durably accepts the request in a bounded inbox. Its HTTP implementation is Python; Rust retains release verification, compatibility, sequence, activation, execution ownership and receipts.
4. Rust fetches signed recipe bytes from the central publisher, verifies operator-local trust and approval, activates only while idle, and pins the release to the task.
5. The local Rust controller drives the existing six-axis MuJoCo adapter. Control has no synchronous dependency on the central network.
6. Reconnection returns the retained result. Retrying the same terminal action does not execute again. A killed executor requires explicit local Rust recovery and a new deliberate action ID.

## Evidence and acceptance

`registration.json` records the initial gates before deployment. `registration-addendum-001.json` records the timing repair before the second attempt. Each run contains source snapshots, deployed-byte hashes, signed bundles, public application CA, node/CPU/OS identities, operation transcripts, SQLite snapshots, execution traces and the Linux binary.

`runs/flightpath-001` is retained as **FAIL**. Inspection delivery, central isolation/completion, reconnection, idempotency and gateway restart passed, but its single-pose rework task completed before the coordinator could inject executor death. That run does not establish crash recovery. The next attempt uses four alternating rework poses and observes committed motion and injects SIGKILL within one edge-local helper. No control limits or success thresholds change.

The independent auditor imports only the previous independent trace-accounting auditor from the saved source snapshot. It checks signatures and delivered bytes, task/version bindings, all retained physics substeps, expected task/start counts, EVY/edge request identity, distinct node/system identities and the causal order of isolation/refusal/control/completion/reconnection. It does not trust a status badge or an HTTP 202 as execution evidence.

A failed wrong-release request may retain its immutable action binding. The rejection gate requires the active release, sequence floor and execution state to remain usable; it does not require the refusal to leave no audit trail.

## Run and audit

The current lab registration uses a fresh, explicitly owned namespace and two fixed worker selections. Its resources have no host mounts, privileged mode or service-account token, and have CPU/memory/deadline bounds. Credentials, signing keys, application TLS private keys and bearer tokens stay outside the repository. The application CA is generated locally and known; control-plane CA bootstrap is provisional TOFU and remains **AMBER**.

Preparation requires the existing source closure, a Linux Rust 1.90.0 toolchain, locked vendored Cargo dependencies and the inventoried Linux wheels. `bootstrap.sh` builds and tests Rust offline; `offline-python.sh` installs the wheels offline. The first image-default Python install failure is retained in exported logs. The inventories bind package/archive hashes without committing reusable credentials or temporary private keys.

With the isolated pods prepared, the proof coordinator is invoked with explicit paths:

```sh
python -B proof/skill_transfer_network_v1/run.py \
  --kubeconfig /private/path/flightpath.kubeconfig \
  --evy /private/path/evy-capability-action \
  --out proof/skill_transfer_network_v1/runs/NEW_ATTEMPT
python -B proof/skill_transfer_network_v1/audit.py \
  proof/skill_transfer_network_v1/runs/COMPLETED_ATTEMPT
AERIS_NETWORK_PROOF_DIR=proof/skill_transfer_network_v1/runs/COMPLETED_ATTEMPT \
  python -B -m unittest discover -s proof/skill_transfer_network_v1 -p 'test_*.py' -v
```

An output directory must be new. Repeating an entire trial requires a fresh isolated database/configuration fixture; replaying a business action uses the existing durable databases and action ID. Those are different operations. The retained reset receipts concern only exported temporary trial state, never a customer device or existing EVY deployment.

## Scope of the claim

A passing audit establishes a finite simulator workflow across two distinct OpenShift worker nodes with observed Intel CPUs and Red Hat operating systems. It does not establish independent physical-host attestation, hard real time, power-loss durability, fleet rollout, production EVY approval integration, model-weight streaming, ROS/OEM interoperability, immutable external anchoring, inspection accuracy or vendor certification. Gaudi acceleration and OpenVINO optimization are not part of this transfer gate.

New robot/use-case profiles reuse the dispatch/transport/lifecycle pattern, but must supply their own reviewed local adapter, compatibility and resource rules, business acceptance checks and execution/failure evidence. The existing profile remains simulation-only; network requests cannot introduce trust roots, interpreter paths, shell commands or physical-motion authority.
