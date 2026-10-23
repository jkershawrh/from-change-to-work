#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
state_path="${AERIS_STATE_DIR:-.action-lab}"
if [ ! -f "$state_path/session.json" ]; then
 .venv/bin/python -B scripts/action_lab.py prepare --state "$state_path"
fi
exec .venv/bin/python -B scripts/action_lab.py start --state "$state_path"
