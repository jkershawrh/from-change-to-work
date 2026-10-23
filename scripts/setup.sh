#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
python_bin="${PYTHON_BIN:-python3.12}"
command -v "$python_bin" >/dev/null || { echo 'Python 3.12 required. Set PYTHON_BIN to its executable.'; exit 1; }
command -v cargo >/dev/null || { echo 'Rust/Cargo 1.90+ required.'; exit 1; }
command -v npm >/dev/null || { echo 'Node 22.12+ or 24 and npm required.'; exit 1; }
"$python_bin" -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check -r services/requirements.lock
.venv/bin/python -m pip check
cargo build --release --locked --manifest-path crates/aeris-skill-transfer/Cargo.toml
npm --prefix frontend ci
npm --prefix presentation ci
npm --prefix frontend run build
printf '\nReady. Run ./scripts/run-demo.sh\n'
