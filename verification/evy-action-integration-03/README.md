# EVY × AERIS: separate-host simulation proof

**PASS:** actual EVY action dispatch on Flightpath worker `fp2` delivered approved signed recipes over HTTPS to the Rust executor and existing MuJoCo plant on worker `fp3`. Both workers report Intel Xeon 6767P CPUs and RHEL 9.6 containers; Flightpath is OpenShift 4.21.10 on RHCOS. Node UIDs and system UUIDs differ.

Forty scenario checks passed. Independent accounting verified 761 control ticks and 7,610 physics substeps: disconnected inspection COMPLETE, killed rework INTERRUPTED, deliberately new rework action COMPLETE. The central pod was isolated in both network directions after task progress; failed cross-host requests and later edge control/completion were observed before reconnection. Terminal retry and gateway restart did not execute again.

The Rust executor passed eight tests on the Intel/RHEL target. Eighteen adapter/audit tests pass, including six mutations of copies of the actual retained evidence. EVY’s prior local related regression result remains 69 passed, six skipped; this run exercises its real action gateway across nodes, not a mocked network.

TDD, EDD, CDD, BDD, CBT and Intel/Red Hat distinct-node execution are **GREEN for this finite simulator workflow**. Lab control-plane trust and production readiness remain AMBER. Physical robotics and hard real time remain RED. This is not device attestation, vendor certification, model-weight streaming or a production fleet rollout.

The failed first attempt, registered timing repair and successful second attempt are all retained under `proof/skill_transfer_network_v1`. Source snapshots, binary, signed bundles, public CA, operation transcripts, databases and complete traces are included. Credentials and private signing/TLS material are excluded. The public EVY reference checkout was not changed or pushed.

See `result.json` for the precise rubric, and the proof README for the implementation and rerun boundary. Cleanup is recorded separately with namespace UID preconditions.
