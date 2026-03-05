#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
CACHE_GLOBAL="$ROOT_DIR/.zig-cache-global"
CACHE_LOCAL="$ROOT_DIR/.zig-cache-local"
mkdir -p "$CACHE_GLOBAL" "$CACHE_LOCAL"

if [ -x "$ROOT_DIR/.tools/zig-ryo/package/zig" ]; then
  ZIG="$ROOT_DIR/.tools/zig-ryo/package/zig"
else
  ZIG="zig"
fi

OS="$(uname -s)"
case "$OS" in
  Darwin) OUT="$SCRIPT_DIR/libzcprotobuf.dylib" ;;
  Linux) OUT="$SCRIPT_DIR/libzcprotobuf.so" ;;
  *) echo "unsupported OS: $OS"; exit 1 ;;
esac

"$ZIG" build-lib "$SCRIPT_DIR/codec.zig" -O ReleaseFast -dynamic -fPIC \
  --global-cache-dir "$CACHE_GLOBAL" \
  --cache-dir "$CACHE_LOCAL" \
  -femit-bin="$OUT"
echo "built: $OUT"

cd "$ROOT_DIR"
python3 zcprotobuf/native/setup_zignative.py build_ext --inplace >/dev/null
echo "built: zcprotobuf._zignative"
