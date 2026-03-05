#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT_DIR"
python3 zcprotobuf/native/setup_zignative.py build_ext --inplace
