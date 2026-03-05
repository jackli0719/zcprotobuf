# zcprotobuf

[![English](https://img.shields.io/badge/Language-English-blue)](README.md)
[![中文](https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-%E4%B8%AD%E6%96%87-red)](README.zh-CN.md)

`zcprotobuf` 在保持 `cprotobuf` 编程模型兼容的前提下，将核心编解码热点迁移到 Zig。

## 基础库说明

- `cprotobuf`（已优化完成的基础库）：`https://github.com/yihuang/cprotobuf`
- `zcprotobuf` 基于该优化版基础库继续做 Zig 编解码加速。
- 联系邮箱：`lw9956164@gmail.com`

兼容对象模型：
- `ProtoEntity`
- `Field`
- `MetaProtoEntity`
- `SerializeToString` / `ParseFromString`

## 架构

1. Python 协议/运行时层  
   `zcprotobuf/internal.py`  
   负责 schema 定义、元类字段索引、编解码分发与兼容行为。

2. Python 桥接层  
   `zcprotobuf/_zigcodec.py`  
   负责后端选择（优先 `pyext`，回退 `ctypes`），统一 varint/zigzag API 与基准快路径。

3. CPython 原生桥接层（`zcprotobuf_native`）  
   `zcprotobuf/native/zignative.c`  
   负责加载 Zig 动态库、范围校验，以及直接对象填充快路径（`bench_decode_into`）。

4. Zig 编解码内核  
   `zcprotobuf/native/codec.zig`  
   导出 varint/zigzag 原语与基准优化的 encode/decode 路径。

## 构建

```bash
./zcprotobuf/native/build.sh
```

输出：
- `zcprotobuf/native/libzcprotobuf.dylib`（macOS）
- `zcprotobuf/native/libzcprotobuf.so`（Linux）

## 使用示例

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

## 核心优化点

- 保持原 API 与消息结构，不改变协议格式。
- 保持单次扫描解码与未知字段跳过语义。
- 原生快路径避免临时切片（`buffer + offset/end`）。
- 常量对象与字符串驻留降低 Python 分配开销。
- 基于 `tp_new` 的子对象创建降低解码尾延迟。

## 性能与带宽

- 主要收益是 CPU/延迟/吞吐，不是消息体积缩减。
- 在相同 schema 与 wire format 下，消息大小不变（`bytes_len` 不变），带宽节省接近 `0%`。
- 最新基准详情见 [`PERFORMANCE_ANALYSIS.md`](/Users/liwei/res/proj/study/cprotobuf/PERFORMANCE_ANALYSIS.md)。

### 基准对比（2026-03-05）

来源：`./benchmark/bench_advantage_compare.sh`（`benchmark/results_adv`）

| 实现 | encode (us/op) | decode (us/op) | 相对 cprotobuf encode | 相对 cprotobuf decode |
|---|---:|---:|---:|---:|
| cprotobuf | 5.590112 | 3.210502 | 基线 | 基线 |
| zcprotobuf | 5.437756 | 2.533883 | +2.73% | +21.08% |
| zcprotobuf_native | 0.243427 | 0.483521 | +95.65% | +84.94% |
| go | 1.657986 | 2.053653 | +70.34% | +36.03% |
| zig | 0.356783 | 0.226169 | +93.62% | +92.96% |

要点：
- `zcprotobuf` 相对 `cprotobuf`：`encode` 提升约 `2.73%`，`decode` 提升约 `21.08%`。
- `zcprotobuf_native` 体现了在相同 wire format 下 Zig 内核的性能上限。

## From Zero 文档

`from_zero` 文档已打包进本仓库，便于用户查阅：

- `docs/from_zero/README.md`
- `docs/from_zero/ZCPROTOBUF_FROM_ZERO.md`
