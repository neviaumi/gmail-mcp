#!/bin/bash
set -ex
PYTHON_VERSION=$(cat .python-version)
apk add gcc musl-dev linux-headers \
python3~=$PYTHON_VERSION \
python3-dev~=$PYTHON_VERSION

uv sync --no-dev --locked