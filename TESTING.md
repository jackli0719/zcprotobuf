# zcprotobuf Testing Guide

This document describes the recommended test flow for `zcprotobuf`.

## 1. Prepare environment

```bash
cd zcprotobuf
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip setuptools wheel
```

Install project dependencies from the repository root:

```bash
cd ..
python3 -m pip install -e .
```

## 2. Build native codec

```bash
./zcprotobuf/native/build.sh
```

Expected artifacts:
- `zcprotobuf/native/libzcprotobuf.so` (Linux) or `libzcprotobuf.dylib` (macOS)
- `zcprotobuf/_zignative*.so`

## 3. Run functional tests

Run existing compatibility tests:

```bash
python3 test/test_pb.py
python3 test/test_skip_optional.py
python3 test/test_decode_subobject.py
```

## 4. Run zcprotobuf smoke benchmarks

```bash
PYTHONPATH=. python3 benchmark/bench_zcprotobuf_cli.py encode --iterations 5
PYTHONPATH=. python3 benchmark/bench_zcprotobuf_cli.py decode --iterations 5
```

## 5. Full performance comparison (optional)

```bash
./benchmark/bench_advantage_compare.sh
```

## 6. CI minimum checks

```bash
./zcprotobuf/native/build.sh
python3 test/test_skip_optional.py
python3 test/test_decode_subobject.py
PYTHONPATH=. python3 benchmark/bench_zcprotobuf_cli.py encode --iterations 3
PYTHONPATH=. python3 benchmark/bench_zcprotobuf_cli.py decode --iterations 3
```
