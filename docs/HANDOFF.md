# From Change to Work — testing handoff

This is the standalone repository for the robotics capability-delivery demo. Clone **https://github.com/jkershawrh/from-change-to-work** with Git LFS. All application source, dependency lockfiles, Rust executor/controller source, simulator assets, final film, and retained proof needed by the documented workflow are included. Sibling repositories and saved lab credentials are not prerequisites.

## Deliverables

- `README.md`: business case, film location, clone/start commands, and challenge sequence.
- `presentation/public/film/from-change-to-work-announced.mp4`: current narrated film, including spoken title and music.
- `/`: dashboard, agent prompt, hardware intake, and observed readiness.
- `/show/`: interactive presentation with optional engineering depth.
- `/?actions=1`: actual bounded simulator transfer, disconnect, interruption, and recovery controls.
- `docs/AGENT_START.md` and `onboarding/manifest.json`: agent due diligence and source map.
- `docs/PRESTON.md`: local and separate-host hardware validation procedure.
- `docs/ACCEPTANCE.md`: scoped TDD/EDD/CDD/BDD/CBT gates.

## What Preston needs to supply

No testing bill of materials has been received yet. Record proposed equipment as unverified until measured. Supply central and edge host identities, CPU model/architecture, OS/kernel/platform versions, available resources and limits, network topology, trusted endpoint names, and test owner. If physical work is proposed, also supply the robot/controller model, OEM interface, tooling/payload/calibration, cell owner, watchdog/stop design, and explicit acceptance scope.

Start with compute hardware running the simulator. The smallest next proof is one approved task transferred between named central and edge hosts, a deliberate central data-plane cut after progress, a retained completion receipt, duplicate-request rejection, executor interruption, explicit recovery, and a new deliberate action. Preserve observer-channel topology and evidence from both hosts. Reconcile the independent cross-host capture before declaring that target green.

A physical robot requires a reviewed local adapter and its own cell acceptance. Nothing in this handoff authorizes physical actuation. No kernel work is needed for the current software transfer gate.

## First-session checklist

1. Read `AGENTS.md`, this guide, and the source map. Record the new repository commit and working-tree status.
2. Follow README setup; retain before/after doctor reports in fresh evidence paths.
3. Run `scripts/check.sh` and retain output. A pass verifies the software and retained proof within the checks’ scope.
4. Start a fresh simulator session. Complete the README challenge while observing actual task state.
5. Capture and independently audit. Save failures, identities, source hashes, traces, and receipts.
6. For separate hosts, follow `docs/PRESTON.md`; keep role captures separate until reconciled.
7. Report the rubric and the smallest remaining blocker. Keep proposed hardware, observed hardware, simulator execution, and physical acceptance distinct.

## Acceptance rubric

- **TDD:** rejection paths and ordinary software tests pass on the checked source.
- **EDD:** independent captured evidence demonstrates the claimed sequence; failures remain retained.
- **CDD:** signed release, target/profile, compatibility, expiry, sequence, action identity, and local approval contracts hold.
- **BDD:** the operator can understand acceptance, a cut link, uncertain work, recovery, and retry without accidental repeated execution.
- **CBT:** real central, transfer, edge, executor, simulator, and observer boundaries are exercised. Two configured endpoints alone do not prove two physical hosts.

Use green only for a named passing test on a named source/host; amber for a specific missing condition; red for an unproved or failed required gate. A film, dashboard screenshot, or readiness report cannot make execution green.

## Repository and proof lineage

The new repository starts with a standalone snapshot and a fresh Git history. Frozen execution records, source snapshots, contracts, compatibility identifiers, third-party notices, and original attribution remain intact so historical evidence stays auditable. Repository branding and supported handoff instructions use **From Change to Work**. See `NOTICE.md` and `PROVENANCE.json` for source and asset lineage.

No credentials, generated session state, local dependency symlinks, or development caches belong in Git. Run the normal setup on the recipient’s checkout; do not copy a developer’s environment or private state.

## Handoff verification

All 128 local software tests passed in this standalone source tree, together with builds, blueprint validation, offline assets, and the retained independent audit. A separate package check copied only Git-tracked proof files into a fresh temporary directory and audited them successfully. Git LFS object verification passed. The initial omitted-evidence failure remains recorded; the ignore rule now explicitly includes the public retained exports. New-repository hosted CI was blocked by account billing before any step ran. See `verification/precommit-20261023/result.json`.
