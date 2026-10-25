#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3.11 -m venv .setup-venv
.setup-venv/bin/python -m pip install -r requirements-setup.txt
.setup-venv/bin/python -m virtualenv --python "$(command -v python3.11)" .venv
.venv/bin/python --version
.venv/bin/python -m pip check
# No instala dependencias de app ni ejecuta OpenCode o modelos.
