# Roadmap and starting metrics

The thesis is a repeatable handoff from an approved central capability to accountable local execution, with explicit recovery and inspectable outcomes. Aerospace manufacturing positioning is the first setting. The current release is a signed bounded joint-goal recipe, not a trained model, defect detector or arbitrary code deployment.

Open the dashboard at `/?roadmap=1`. This page defines the pilot; it is not a live benchmark. The narrated film remains the hangar edition and does not include this new dashboard page.

## Decision and owners

Select one approved task, named central and edge compute hosts, a platform owner, and a task acceptance owner. Preston is the intended hardware test collaborator; assignment and availability still need confirmation. Manufacturing operations owns the business comparison, quality owns the accepted outcome, and a robot integrator and cell safety owner own any physical integration. No timeline or savings commitment is inferred.

## Gated roadmap

1. **Retained simulator evidence — GREEN, historical scope only.** Inspect `proof/skill_transfer_network_v1/runs/flightpath-002` and its independent audit. That named Intel Xeon / RHEL / OpenShift run is a starting reference. It does not qualify new hosts, physical motion or production value.
2. **Qualify named compute hosts — AMBER, next gate.** Follow `docs/PRESTON.md`. Inventory both hosts, establish the trusted certificate path and pin source/release identities. Run a fresh simulator challenge for transfer, central data-plane cut, disconnected completion, same-ID retry, executor interruption, explicit recovery and deliberate new work. Capture central and edge independently and reconcile their evidence. Preserve load-related refusals; do not relax thresholds.
3. **Connect one reviewed robot profile — RED, unqualified.** Select the OEM interface and review the adapter, joint ordering, units, coordinate frames, tool/payload, calibration, limits, watchdog and stop behavior. Review compatibility and acceptance criteria. Physical motion requires separate authorization and cell acceptance. A populated hardware intake does not enable this gate.
4. **Measure a controlled pilot — AMBER, unmeasured.** Measure the site's existing process before introducing the proposed one. Compare equivalent task scope, operators, part conditions and quality criteria. Keep simulated and physical results separate. Continue only if the acceptance owner approves the evidence against criteria agreed before the comparison.
5. **Repeat with a second module — RED, hardware repeatability unproved.** Reuse release identity, delivery, verification, activation, task ownership, recovery and receipts. Qualify device-specific adapters and task acceptance independently. Record integration person-hours, reused components, new adapter work and regressions. Inspection/rework positioning currently share the simulator pipeline; that alone does not establish general physical module portability.

These are gates rather than calendar promises. Schedule estimates require the hardware inventory, adapter choice, site access and owner availability.

## Starting metrics: all current-site baselines are unmeasured

Capture a baseline and proposed-process cohort with the same task definition. Retain every attempt, including invalid deliveries, failures, interruptions and timeouts; classify planned challenge cases separately from ordinary operation. Identify source commit/build, release digest, action/task IDs, host inventory, software versions, operator, load, observation interval and raw evidence paths. Record units and missing values explicitly. Do not replace missing values with zero.

- **Approved release to admitted task:** elapsed seconds from recorded approval to local task admission. Also record completion separately. Across hosts, document clock synchronization and uncertainty; use monotonic clocks for same-host durations. Report attempt count and distributions only when the sample supports them. A missing admission is a rejected or timed-out attempt, not a latency of zero.
- **Operator effort and handoffs:** active person-minutes and handoff count per attempt. Split preparation, deployment and recovery. Track unattended elapsed waiting separately. Document who observed the workflow and use identical boundaries in both cohorts.
- **Recovery to a verified disposition:** elapsed seconds from a named injected fault to independently verified completion or explicit interruption. Central disconnection and executor interruption are different fault classes. A deliberately new action is separate work, not continuation of an interrupted task. Record human intervention.
- **Accepted task outcomes:** accepted tasks divided by all attempted tasks, with completed, rejected, failed, interrupted and timed-out counts retained. Report the counts alongside any rate. Simulator completion does not establish positioning accuracy, inspection quality or part acceptance. The quality owner defines the physical measurement, tolerance and method before testing.
- **Duplicate execution and authority refusals:** unexpected execution starts per same-ID retry, and refused cases per defined invalid challenge. Challenge expiry, signature, target/profile mismatch and changed action identity as well as restart/retry. Acceptance invariants are no new execution for a completed same-ID retry and refusal of every defined invalid case. Broker acknowledgements alone do not prove either invariant.
- **Edge timing and resource headroom:** capture end-to-end and controller latency distributions, deadline misses, CPU and memory on the measured hardware under documented load, including disconnected operation. Record sample count, interval, controller budget and measurement overhead. Agree numerical headroom thresholds with the controller owner before running the acceptance comparison. Simulation ticks are not real-time qualification.

Improvement targets: **agree after the baseline, before the proposed-process comparison**. Do not invent percentage savings, deployment time or throughput gains. Keep media/UI engagement separate from execution evidence and business value. Maintain the immutable execution trace as the source for task identity and outcomes, not as a substitute for observed operator effort or quality measurements.

## Standards adoption workstream

Current delivery uses custom signed recipe/action contracts over HTTPS. Standards interoperability is pending. Evaluate TUF for update metadata/trust lifecycle and CloudEvents for event envelopes first. Add MQTT for fleet notifications only when needed. Select ROS 2/DDS or OPC UA adapters based on the actual robot and factory interfaces; do not implement every protocol as a prerequisite. Transport delivery acknowledgements never substitute for local approval or execution receipts. See the official specifications when defining a conformance profile and pinned test cases.

## TDD / EDD / CDD / BDD / CBT and red–amber–green

- **TDD:** retain the rejection test before implementation, then its passing result. For this dashboard change, retain the failing missing-component test and the passing scope/content tests.
- **EDD:** retain source identities, observations, failures and independent audit outputs. Presentation evidence stays separate from execution evidence.
- **CDD:** enforce exact release/action identities, units, frames, compatibility, approval and state transitions. A roadmap or intake field grants no execution authority.
- **BDD:** demonstrate the operator journey: approved release, local admission, cut, outcome, retry, interruption, recovery and deliberately new action.
- **CBT:** test actual browser, API, network, edge runtime and simulator boundaries for execution claims. Dashboard browser checks prove rendering/navigation only.

GREEN applies to a named gate, source, host, task and retained passing evidence. AMBER means evidence or an owner decision is pending. RED means unproved or failed; preserve the specific reason. Never average the gates into one overall score. A software pass cannot turn physical safety, standards interoperability or financial value green. Hosted CI infrastructure failures must be reported independently from local checks.

## Next smallest test

Run the read-only inventory on Preston's selected central and edge hosts and record the missing facts. Then qualify the unchanged simulator transfer on those hosts using a new session, trusted connections and independent captures. Do not begin physical actuation as part of this compute-only acceptance step.
