# Let an agent take this from clone to a testable cell

Give your coding agent the repository and this prompt: **“Read AGENTS.md and onboarding/manifest.json. Do due diligence, inventory this host, explain the hardware gaps, and guide or perform the authorized simulator acceptance workflow. Preserve evidence and scoped red/amber/green.”** The dashboard also lets you copy the complete prompt and download an agent start packet with proposed hardware and observed readiness.

The packet is context for an agent running in your development environment. The dashboard does not run an autonomous agent or an LLM service, and it does not install robot drivers. No AI-provider credential is needed.

## What to understand first

The business hypothesis is a repeatable way to deploy an approved task capability to an edge cell and retain local control during a central connection failure. Inspection positioning and rework positioning exercise the same process. Inspection accuracy, production quality and financial ROI still require use-case measurements.

The transferred content is a finite signed deterministic joint-goal recipe, not a container, arbitrary plugin, trained model or robot program installer. The existing EVY dispatcher binds an action to its configured edge and release. The local Rust executor verifies identity, signature, approval, compatibility, expiry and sequence; activates only while idle; pins a task; persists samples and receipts; requires explicit process recovery. MuJoCo and the unchanged Rust MPC provide the current plant profile.

The frontend's central disconnection cuts the lab data plane. An independently labeled management observer remains reachable. It does not simulate a total network blackout or an emergency stop. Recovery marks orphaned work interrupted; a new deliberate action is needed to execute again.

## Repository map

Read the paths and boundary descriptions in `onboarding/manifest.json`. Start at `services/action_console/api.py`, follow `services/evy_action_gateway.py` into the existing EVY dispatcher, then `services/edge_gateway.py` and `crates/aeris-skill-transfer/src/`. The independent audit is in `scripts/audit_action_session.py`. `docs/ARCHITECTURE.md` explains the authority boundaries; `docs/ACCEPTANCE.md` defines the rubric.

## Ordered due diligence and testing

1. Review the code and scope above. Record the Git commit and current changes. Run `python3 scripts/doctor.py --out evidence/readiness-001.json` even before installation. It uses the Python standard library, fixed local version/metadata commands, no shell, no network probing and no credentials. Exit 2 means missing prerequisites; use its next-step guidance. The only write is the output path you chose, created exclusively.
2. Observe CPU/OS/kernel/architecture and required tooling. A missing CPU vendor stays unknown. The dashboard preflight describes the **console process host only**; run the CLI independently on edge as well. Intel plus RHEL is a candidate combination, not a support/certification statement. OpenShift node identity is not inferred from a container or UI label.
3. For authorized local testing, install dependencies with `scripts/setup.sh`, then rerun the doctor into a new path. Run `scripts/check.sh` and retain its output. Tool versions, primary Python package versions and artifact presence are prerequisites; the doctor does not prove source/build equivalence, dependency security, execution success or timing headroom. The real tests and capture do that additional work within their stated scopes.
4. Run `scripts/run-demo.sh` for first setup. If `.action-lab` already exists, do not reuse it after implementation changes. Preserve the old evidence and use `action_lab.py prepare --state .action-lab-002`, followed by `action_lab.py start --state .action-lab-002`. Both use the project `.venv/bin/python`. The source freeze is made during prepare.
5. Open the dashboard, authenticate with the local code, inspect observed readiness and the session, then open the workbench. Run transfer, central cut after committed progress, disconnected completion, reconnect and same-ID retry without another start; next action, executor interruption, explicit recovery and deliberately new action completion. Hardware/load refusals are results to retain, not thresholds to relax.
6. Capture and independently audit the idle completed challenge using the exact state path and a fresh evidence output. See README commands. A browser export is not that audit. The current UI's amber evidence gate stays amber until the independent audit exists.
7. For separate compute hosts, use `docs/PRESTON.md`: actual measured edge inventory, fixed reviewed paths, private material via the trusted site process, distinct identities and two role captures. The all-in-one auditor is local-mode-qualified; cross-host reconciliation remains a named acceptance task.

## Hardware intake without guesswork

Ask only for unresolved facts: central and edge model/CPU/architecture; OS/kernel and Red Hat platform version; trusted connection topology; robot/controller/OEM interface if a physical profile is proposed; cell owner, tool/payload/calibration and stop/watchdog acceptance owner. Record unknown values as unknown. Keep planned choices separate from measured values. Do not ask for cluster or robot passwords in the dashboard, a report or chat.

For an existing OEM controller, preserve its supported task interface and local safety authority. For ROS or a custom driver, first define the reviewed adapter, compatibility rules and acceptance envelope. Those are future profile options; neither is implemented by selecting a dashboard field. The reusable module contract is under `modules/capability-transfer/`.

## Report the decision

Produce a short explanation of the actual system and business hypothesis; measured source/host/software; proposed hardware; a scoped TDD/EDD/CDD/BDD/CBT checklist with evidence paths; failures and remaining gaps; and the next smallest test. Include explicit statuses for local simulation, distinct-host transfer, physical motion and real time. Historical Flightpath proof and the prior local handoff remain historical even when all software checks pass today.
