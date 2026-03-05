# zcprotobuf

[![English](https://img.shields.io/badge/Language-English-blue)](README.md)
[![中文](https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-%E4%B8%AD%E6%96%87-red)](README.zh-CN.md)

`zcprotobuf` keeps the original `cprotobuf` programming model while moving codec hotspots to Zig.

## Base Library Note

- `cprotobuf` (optimized baseline library): `https://github.com/yihuang/cprotobuf`
- `zcprotobuf` is built on top of this optimized baseline and focuses on Zig-based codec acceleration.
- Contact: `lw9956164@gmail.com`

Compatible object model:
- `ProtoEntity`
- `Field`
- `MetaProtoEntity`
- `SerializeToString` / `ParseFromString`

## Architecture

1. Python protocol/runtime layer  
   `zcprotobuf/internal.py`  
   Handles schema definition, metaclass field indexing, encode/decode dispatch, and compatibility behavior.

2. Python bridge layer  
   `zcprotobuf/_zigcodec.py`  
   Chooses backend (`pyext` first, `ctypes` fallback), unifies varint/zigzag APIs and benchmark fastpaths.

3. CPython native bridge (`zcprotobuf_native`)  
   `zcprotobuf/native/zignative.c`  
   Loads Zig `.dylib/.so`, validates ranges, and supports direct object-fill fastpath (`bench_decode_into`).

4. Zig codec kernel  
   `zcprotobuf/native/codec.zig`  
   Exports varint/zigzag primitives and benchmark optimized encode/decode paths.

## Build

```bash
./zcprotobuf/native/build.sh
```

Outputs:
- `zcprotobuf/native/libzcprotobuf.dylib` (macOS)
- `zcprotobuf/native/libzcprotobuf.so` (Linux)

## Usage

```python
from zcprotobuf import ProtoEntity, Field

class Person(ProtoEntity):
    id = Field("int32", 1)
    name = Field("string", 2)

p = Person(id=1, name="alice")
raw = p.SerializeToString()
q = Person()
q.ParseFromString(raw)
```

## Key Optimization Elements

- Preserve original API and message structure; no protocol format change.
- One-pass decode and unknown-field skip semantics remain intact.
- Native fastpath avoids temporary slicing (`buffer + offset/end`).
- Constant objects and interned keys reduce Python allocation overhead.
- `tp_new`-based sub-object creation reduces decode tail latency.

## Performance and Bandwidth

- Main gain is CPU/latency/throughput, not payload size.
- With same schema and wire format, message size is unchanged (`bytes_len` unchanged), so bandwidth savings are near `0%`.
- Latest benchmark summary is tracked in [`PERFORMANCE_ANALYSIS.md`](/Users/liwei/res/proj/study/cprotobuf/PERFORMANCE_ANALYSIS.md).

### Benchmark Comparison (2026-03-05)

Source: `./benchmark/bench_advantage_compare.sh` (`benchmark/results_adv`)

| implementation | encode (us/op) | decode (us/op) | encode ratio (impl/cprotobuf) | decode ratio (impl/cprotobuf) | encode reduction | decode reduction |
|---|---:|---:|---:|---:|---:|---:|
| cprotobuf | 5.590112 | 3.210502 | 1.000000 | 1.000000 | baseline | baseline |
| zcprotobuf | 5.437756 | 2.533883 | 0.972745 | 0.789248 | 2.7255% | 21.0752% |
| zcprotobuf_native | 0.243427 | 0.483521 | 0.043546 | 0.150606 | 95.6454% | 84.9394% |
| go | 1.657986 | 2.053653 | 0.296593 | 0.639667 | 70.3407% | 36.0333% |
| zig | 0.356783 | 0.226169 | 0.063824 | 0.070447 | 93.6176% | 92.9553% |

Key points:
- `zcprotobuf` improves `encode` by `2.7255%` and `decode` by `21.0752%` vs `cprotobuf`.
- `zcprotobuf_native` shows the upper bound of Zig kernel performance under the same wire format.
- `reduction = (1 - impl_us_per_op / cprotobuf_us_per_op) * 100%`.

## From Zero Documentation

`from_zero` docs are packaged in this repository for easier user access:

- `docs/from_zero/README.md`
- `docs/from_zero/ZCPROTOBUF_FROM_ZERO.md`
