#!/bin/bash
set -ex
uv run --no-dev fastapi run --port 8080 src/app/main.py