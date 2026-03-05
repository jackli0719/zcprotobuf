# zcprotobuf

`zcprotobuf` keeps the original `cprotobuf` programming model while moving codec hotspots to Zig.

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

| implementation | encode (us/op) | decode (us/op) | vs cprotobuf encode | vs cprotobuf decode |
|---|---:|---:|---:|---:|
| cprotobuf | 5.590112 | 3.210502 | baseline | baseline |
| zcprotobuf | 5.437756 | 2.533883 | +2.73% | +21.08% |
| zcprotobuf_native | 0.243427 | 0.483521 | +95.65% | +84.94% |
| go | 1.657986 | 2.053653 | +70.34% | +36.03% |
| zig | 0.356783 | 0.226169 | +93.62% | +92.96% |

Key points:
- `zcprotobuf` improves `encode` by about `2.73%` and `decode` by about `21.08%` vs `cprotobuf`.
- `zcprotobuf_native` shows the upper bound of Zig kernel performance under the same wire format.

## From Zero Documentation

`from_zero` docs are packaged in this repository for easier user access:

- `docs/from_zero/README.md`
- `docs/from_zero/ZCPROTOBUF_FROM_ZERO.md`
