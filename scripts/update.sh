#!/usr/bin/env sh
set -eu

git pull origin main
uv sync
printf '%s\n' "Wind Turbine Design Lab is up to date."
