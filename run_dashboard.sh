#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -c "import fastapi, uvicorn, multipart, requests, PIL, keyring" >/dev/null 2>&1 || python3 -m pip install -r requirements.txt
command -v node >/dev/null 2>&1 || { echo "Node.js LTS is required: https://nodejs.org"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required; reinstall Node.js LTS with npm included."; exit 1; }
node -e "require('jsdom')" >/dev/null 2>&1 || npm install --omit=dev
[ -f node_modules/vazir-font/dist/font-face.css ] || npm install --omit=dev
python3 neo_launcher.py
