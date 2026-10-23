# Durable remote capability transfer — simulator profile

This standalone Rust workspace implements signed capability delivery, durable staging, idle activation, task version pinning and explicit process recovery. The first executor is the existing six-axis MuJoCo plant driven by the existing Rust MPC. The transferred artifact is a **deterministic joint-goal behavior**, not trained weights. Training is not required.

The separate workspace preserves AERIS's root lockfile and frozen controller source. The path dependency reuses the controller source without rewriting its original build or evidence.

## Local operator interface

```sh
cargo test --locked --manifest-path crates/aeris-skill-transfer/Cargo.toml
cargo clippy --locked --all-targets --manifest-path crates/aeris-skill-transfer/Cargo.toml -- -D warnings
cargo build --locked --release --manifest-path crates/aeris-skill-transfer/Cargo.toml
```

The executable accepts `LOCAL_CONFIG DATABASE COMMAND [ARGUMENT]`:

- `fetch`: bounded authenticated HTTPS download from the locally configured publisher, then signature/approval/compatibility verification and staging.
- `stage BUNDLE_FILE`: the same verification for an offline received bundle. This is not evidence of network delivery.
- `activate MANIFEST_SHA256`: atomic idle activation of the latest verified sequence. Current-release acknowledgement retries are idempotent.
- `execute UNIQUE_TASK_ID`: run the active capability through the pinned local simulator adapter; persist task ownership, per-step samples and a terminal receipt. Completed task retries return the receipt without motion.
- `status` and `receipt TASK_ID`: consistent read snapshots of retained state and evidence.
- `recover`: obtain exclusive executor ownership and explicitly mark orphaned tasks INTERRUPTED. A new simulator task starts from home. No physical continuation is authorized.

Config paths, CA, endpoint, signing trust, approval allowlist and target identity are provisioned locally. The endpoint cannot submit its own trust context. The config identity is bound to the database; changing it requires a separately designed migration, not an implicit trust-policy replacement.

## Release v2 contract

`evy-aeris.transfer-bundle.v2` contains exactly `schema`, `manifest_json`, `signature_hex`, `behavior_json`. Ed25519 verifies the exact UTF-8 manifest bytes prefixed by `evy-aeris.transfer-release.v2` and a zero byte. Unknown and duplicate struct fields reject. There are no producer-controlled trust maps.

The manifest contains exactly:

- schema `evy-aeris.transfer-release.v2`, release/skill IDs, positive signed-64-bit sequence;
- issued, not-before and expiry Unix milliseconds with a maximum seven-day interval;
- origin `existing_deterministic_behavior` — other origins need their own implemented contract, not fabricated training lineage;
- an exact target profile and behavior size/SHA-256;
- optional `recovery_of`, referencing a previously received manifest with identical capability bytes. Its new sequence must exceed the persistent floor and its new manifest must be locally approved.

The target binds profile `mujoco-six-axis-goals-v1`, plant dependency identity, declared synthetic calibration identity, six unique ordered joint names, radians, world-base frame, runtime `mujoco-rust-mpc-v1`, runtime version, host OS/architecture and adapter digest. The simulator reports its actual plant closure, joint names and MuJoCo version at startup; those must match. The Python interpreter and adapter bytes are checked locally before execution. The observed host architecture and OS must match at config load.

The behavior is strict `aeris.bounded-joint-goals.v1`: one to four finite six-joint goals within ±0.35 rad of the pinned home. A 64 KiB encoded bundle and 16 KiB manifest limit bound this small behavior profile. This is not a large-model streaming implementation or a generic code/plugin installer.

A signature establishes byte identity under a configured key. Local approval is an allowlist of exact manifest digests. Neither is an independent safety approval or an integrated EVY enterprise review chain.

## Durability and ownership

SQLite uses WAL, synchronous FULL and immediate write transactions. Verified bundle bytes and the monotonically increasing received sequence floor commit together. Activation changes the pointer and event in one transaction. There are no extracted bundle files or cross-filesystem rename windows. Stage and activation acknowledgements happen after commit.

One OS-owned advisory lock covers execution, activation and explicit recovery. SQLite RUNNING rows survive process death, and prevent activation or a new task until explicit recovery. Staging can proceed while execution owns the lock. Each task stores its release digest before spawning the adapter; it never consults the active pointer mid-task. Each sample commits before progress acknowledgement. Terminal state, receipt and completion event commit together before the final acknowledgement.

The database and filesystem are trusted local state, not an adversarial sandbox or externally anchored immutable ledger. OS process-crash consistency is tested; actual power-loss, disk corruption, filesystem durability and malicious local users are not qualified. Admission uses the trusted host clock. Key rotation, revocation delivery, config migration, storage quotas, fleet reconciliation and separately signed device receipts remain integration work.

## Execution and failure boundaries

The Rust executor retains the existing 20 ms MPC dispatch gate and applies local bounds. The Python adapter only advances a 20 ms simulated interval after a fresh parent command. It uses the existing MuJoCo inverse-dynamics plant and sampled collision checker. The fallback braking interval is checked separately for sampled collision clearance. Every retained 2 ms substep is checked for contact, displacement, speed and native/finite-difference acceleration limits.

A blocked or dead adapter times out; a task becomes FAILED and releases ownership after child cleanup. On Rust process death, the pipe closes; the adapter finishes at most the current interval and exits on EOF. Recovery records uncertainty as INTERRUPTED. This is a stepped plant that pauses during IPC, persistence and computation, not a continuously running robot or hard-real-time/watchdog proof. Ten stable control ticks at each goal establish only the declared simulated task outcome.

HTTPS uses certificate validation, only the locally configured CA, no proxies, no redirects, a five-second request timeout and a bounded response read. A bearer file supplies lab endpoint access. The lab publisher is a Python TLS fixture, not a deployed EVY control plane. Local loopback TLS demonstrates real protocol and process boundaries; separate-host/WAN and Intel/Red Hat target qualification are separate gates.

No physical driver, hardware actuation, inspection coverage or learning benefit is claimed. This adapter is not authorized for a real robot.

## Fault injection and proof

Fault hooks compile only with `--features fault-injection`. The lab harness uses `AERIS_TRANSFER_CRASH_AT` to exit without Rust destructors at stage/activation before and after commit, task-start/step commit and completion-before-ack boundaries. Normal builds contain an inert hook. An additional live SIGKILL case tests actual executor death and adapter retirement.

See [the registered proof](../../proof/skill_transfer_v2/README.md) for the full run and independent saved-result audit. Keep this profile distinct from the preserved v1 OpenVINO candidate contract; v1 fixture bytes are not executable capabilities.

## Repeatable action interface

`action REQUEST_FILE` exposes one locally invoked, strict `evy-aeris.transfer-action.v1` request:

```json
{
  "schema": "evy-aeris.transfer-action.v1",
  "action_id": "rework-001",
  "skill_id": "rework-positioning",
  "release_digest": "<exact approved manifest SHA-256>"
}
```

The Rust action binds this immutable request in SQLite before delivery. It verifies the expected capability/digest before staging network bytes, or reuses an already verified staged bundle. It then activates while idle and starts a task pinned to the expected release under the executor lock. Another activation between phases therefore cannot silently change the executed capability. A distinct action lock serializes action orchestration, while the existing executor lock owns motion/activation/recovery. An action retry with different inputs is refused.

The stable task ID is `action-<action_id>`. A terminal retry returns the retained receipt without contacting the publisher or moving again. An interrupted or failed task stays terminal; a new deliberate action ID is required for another simulated attempt. BUSY/recovery-required conditions remain explicit refusals; this CLI is not an asynchronous queue or a scheduler.

Trust configuration, interpreter paths and executor commands are **not** request fields. The action does not install code from a remote package. A caller must inspect terminal business status, not only the CLI exit status. `evy-aeris.transfer-action-result.v1` binds action/capability/release/task, status, idempotency and the runtime receipt, with simulation and physical-authority scope.

The same action is exercised for inspection-positioning and rework-positioning through one six-axis profile. This proves reuse of that process, not arbitrary robot portability. A new profile requires a reviewed compiled adapter, compatibility/resource rules and the shared rejection/crash/execution audit suite. The standalone browser console now invokes the existing EVY action gateway and this Rust executor through the simulator-only edge gateway. See the repository root README and `docs/PRESTON.md` for current entrypoints, controls and qualification limits. The broader production EVY distribution services and physical robot adapters remain separate integration gates.
