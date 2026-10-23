#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f verification/handoff-01/session/capture.json ]; then
 export AERIS_SESSION_EVIDENCE_DIR="${AERIS_SESSION_EVIDENCE_DIR:-verification/handoff-01/session}"
fi
.venv/bin/python -B -m unittest discover -s services/tests -v
PYTHONPATH=integrations/evy .venv/bin/python -B -m pytest integrations/evy/tests/actions -q
AERIS_NETWORK_PROOF_DIR=proof/skill_transfer_network_v1/runs/flightpath-002 .venv/bin/python -B -m unittest discover -s proof/skill_transfer_network_v1 -p 'test_*.py' -v
.venv/bin/python -B proof/skill_transfer_network_v1/audit.py proof/skill_transfer_network_v1/runs/flightpath-002
cargo test --locked --manifest-path crates/aeris-skill-transfer/Cargo.toml
npm --prefix frontend run check
npm --prefix presentation run test
npm --prefix presentation run validate:blueprint
npm --prefix presentation run verify:offline
