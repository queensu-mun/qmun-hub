#!/usr/bin/env bash
# Launch QMUN Hub. Forces arm64 because the venv's python is a universal
# binary symlinked to the system Python and macOS may otherwise launch it
# under x86_64 (Rosetta), which mismatches the arm64 wheels in site-packages.
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate
exec arch -arm64 .venv/bin/streamlit run app.py "$@"
