#!/bin/bash
set -euo pipefail
/opt/app-root/bin/python3 -m venv /work/venv
/work/venv/bin/python -m pip install --disable-pip-version-check --no-index --find-links=/work/input/wheels 'mujoco==3.3.7' 'numpy==2.0.2' 'fastapi==0.115.12' 'httpx==0.28.1' 'cryptography==44.0.3' 'pydantic-settings==2.8.1' 'uvicorn==0.34.2' 'redis==5.2.1' 'aiokafka==0.12.0' 'twilio==9.5.2' 'python-multipart==0.0.20' > /work/offline-python-install.log 2>&1
/work/venv/bin/python -m pip freeze > /work/python-freeze.txt
printf 'OFFLINE_PYTHON_READY\n'
