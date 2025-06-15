#!/bin/zsh
set -ex

uv run fastapi dev --port 8080 src/app/main.py