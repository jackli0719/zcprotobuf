# zcprotobuf 从零开始：安装、使用与测试

本文档面向“本机没有任何依赖”的场景，按步骤完成 `zcprotobuf` 的构建、调用和测试。

## 1. 环境准备

- Python 3.8+
- C 编译器（macOS: `clang`，Linux: `gcc/clang`）
- Zig（可选，但构建原生库时需要）

进入项目根目录：

```bash
cd /Users/liwei/res/proj/study/cprotobuf
```

### 1.1 安装 Zig（含中国源）

方式 A（推荐，npm 中国镜像）：

```bash
mkdir -p /tmp/zig-install && cd /tmp/zig-install
npm init -y
npm install --no-save --registry=https://registry.npmmirror.com @ziglang/cli
```

安装后可执行文件通常在：
- `/tmp/zig-install/node_modules/.bin/zig`

可加入 PATH：

```bash
export PATH="/tmp/zig-install/node_modules/.bin:$PATH"
zig version
```

方式 B（macOS，Homebrew）：

```bash
brew install zig
zig version
```

方式 C（Linux，手动下载官方发行包）：

```bash
# 示例：下载后解压并加入 PATH
tar -xf zig-*.tar.xz
export PATH="$PWD/zig-*/:$PATH"
zig version
```

## 2. 安装 Python 依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip setuptools wheel
python3 -m pip install -e .
```

## 3. 构建 zcprotobuf 原生组件

```bash
./zcprotobuf/native/build.sh
```

构建成功后会生成：
- `zcprotobuf/native/libzcprotobuf.dylib`（macOS）或 `.so`（Linux）
- `zcprotobuf/_zignative.*.so`（Python 扩展）

## 4. 最小使用示例

```python
from zcprotobuf import ProtoEntity, Field

class Person(ProtoEntity):
    id = Field("int32", 1)
    name = Field("string", 2)

p = Person(id=1, name="alice")
raw = p.SerializeToString()
q = Person()
q.ParseFromString(raw)
print(q.id, q.name)
```

运行：

```bash
PYTHONPATH=. python3 demo.py
```

## 5. 功能测试

运行现有测试集：

```bash
PYTHONPATH=. python3 -m pytest -q
```

如果只想快速验证 zcprotobuf 编解码链路：

```bash
PYTHONPATH=. python3 benchmark/bench_zcprotobuf_cli.py encode --iterations 5
PYTHONPATH=. python3 benchmark/bench_zcprotobuf_cli.py decode --iterations 5
```

## 6. 性能对比测试

一键跑全对比（cprotobuf / go / zig / zcprotobuf / zcprotobuf_native）：

```bash
./benchmark/bench_advantage_compare.sh
```

输出核心指标：
- `encode_us_per_op`
- `decode_us_per_op`
- `enc_vs_cprotobuf`
- `dec_vs_cprotobuf`

## 7. 常见问题

1. `build.sh` 失败：先确认 `zig` 可执行，或使用本地 `.tools/zig-ryo/package/zig`。
2. 找不到原生库：确认已执行 `./zcprotobuf/native/build.sh`。
3. 结果波动：压测时固定机器负载，多跑 3-5 次取中位数。

## 8. 生产部署清单（容器 / CI）

### 8.1 构建产物检查

- Python 包可导入：`import zcprotobuf`
- 原生动态库存在：`zcprotobuf/native/libzcprotobuf.*`
- Python 扩展存在：`zcprotobuf/_zignative*.so`

建议在 CI 中加入：

```bash
python3 - <<'PY'
import zcprotobuf
from zcprotobuf._zigcodec import zigcodec
print("mode=", zigcodec.mode, "available=", zigcodec.available)
PY
```

### 8.2 CI 推荐流水线

1. 创建虚拟环境并安装依赖  
2. 执行 `./zcprotobuf/native/build.sh`  
3. 执行单元测试：`PYTHONPATH=. python3 -m pytest -q`  
4. 执行基准冒烟：  
   `PYTHONPATH=. python3 benchmark/bench_zcprotobuf_cli.py encode --iterations 3`  
   `PYTHONPATH=. python3 benchmark/bench_zcprotobuf_cli.py decode --iterations 3`

### 8.3 容器化建议

- 使用多阶段构建：builder 阶段编译 Zig/C 扩展，runtime 阶段仅拷贝运行所需文件。
- 固定 Python/Zig 版本，避免线上行为漂移。
- 运行镜像内保留 `zcprotobuf/native/libzcprotobuf.*` 与 `_zignative*.so`。

### 8.4 发布前门禁

- 功能门禁：核心消息可正确 `SerializeToString/ParseFromString`。
- 性能门禁：至少跑一次 `bench_zcprotobuf_cli.py`，验证未明显回退（例如 >10%）。
- 兼容门禁：旧版本消息样本可被新版本正确解析。

### 8.5 回滚策略

- 保留上一个稳定镜像 tag。
- 配置开关允许降级到纯 Python 路径（或旧服务版本）。
- 回滚后优先核对：错误率、P99 延迟、CPU 使用率。
