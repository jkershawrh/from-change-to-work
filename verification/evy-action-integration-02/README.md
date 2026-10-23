# EVY action integration checkpoint 02

This is an incremental private patch against EVY commit `ec644a54f6d39df48dc9da93f9593c49be091ebd`. It reuses the existing tracked EVY FastAPI gateway and adds opt-in capability action routes. It does not copy EVY’s separately excluded cinematic demo or alter the existing AERIS Rust executor.

The patch is retained here because the EVY reference repository is public. Apply to a clean checkout at the exact base with `git apply --check evy-capability-action.patch`, then apply the patch and run `python -m pytest tests/actions -q` using EVY’s test dependencies. No credentials or runtime configuration are included.

Twelve action tests pass, including requests through the real EVY gateway. A related regression selection passes 69 tests with six skipped. Retained red logs precede the passing implementation. Two hardening failures covered malformed nested receipts and unclosed SQLite connections.

This checkpoint does not establish remote execution. The network edge gateway, its disconnect/recovery tests, frontend controls, deployment and separate-host Intel/Red Hat execution remain outstanding. A schema-shaped remote result is not independent proof of execution.

Oberon’s API is reachable, but its advertised OAuth endpoint closes the TLS connection before authentication under both TLS 1.2 and TLS 1.3. Login failed with EOF; no password was sent and no workload changed. EVY’s location on Oberon remains unverified. Flightpath login works; a filtered deployment/route metadata search found no matching EVY names. Lab trust remains provisional TOFU.

See `result.json` for the scoped RAG rubric and source identities. Existing local Rust simulator proof results remain unchanged.
