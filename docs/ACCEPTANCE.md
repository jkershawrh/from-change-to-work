# Acceptance gates

Keep the scopes separate: historical Flightpath proof, the current software/browser session, Preston’s compute hardware, and a future physical robot. A green result in one scope cannot upgrade another.

- **TDD:** retained failing contract/frontend tests followed by passing service, existing EVY, Rust, frontend and browser checks. Hosted CI must be reported separately from local verification.
- **CDD:** exact action/control fields and IDs, source/target binding, caller roles, same-origin protection, fixed TLS endpoints, signature/local approval/profile/expiry/sequence checks. Physical profiles must refuse simulator fault controls.
- **BDD:** actual capability transfer and local execution; central cut after measured progress; further observed control and completion before reconnect; terminal retry without another start; running executor interruption; refusal before explicit recovery; new deliberate action completion.
- **CBT:** real browser requests, real EVY dispatcher, authenticated TLS/process boundaries, actual Rust controller and MuJoCo execution. An HTTP 202 or authored animation is insufficient.
- **EDD:** code/binary/target identities, signed received bytes, durable action/job/task bindings, SQLite backup integrity, complete samples/substeps, causal observation journal, exported public evidence and independent audit. Mutated evidence and source changes must reject.

**Green** means the named, finite gate was observed and its evidence retained. **Amber** means a prerequisite, integration or acceptance item is incomplete or provisional. **Red** means the gate was not proved or failed. Refusing an invalid action is a passing rejection test; it is not a completed business task.

Physical motion, cell safeguarding, OEM stop behavior, continuous real-time scheduling, power loss, storage corruption and production identity/revocation remain unproved. The lab code must keep those red until their own hardware acceptance record exists.

## Agent onboarding and readiness

Readiness checks are a separate prerequisite gate. Test rejection of old/missing tools, unpulled LFS assets, mismatched primary packages and contradictory reports. Require authentication for dashboard host inspection, refuse browser command/target parameters, and allow a viewer to inspect without granting control. Packet exports must separate unverified proposed hardware from observed console facts and omit any independent-audit claim. Preserve missing observations in offline packets. A new dashboard capture must prove its actual workflow before assigning current-session green.
