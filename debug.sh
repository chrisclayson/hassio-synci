#!/usr/bin/env bash

set -e

export PYTHONPATH="${PYTHONPATH}:${PWD}/custom_components"

# Start Home Assistant
hass --config "${PWD}/config" --debug
