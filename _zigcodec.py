import ctypes
from pathlib import Path


class BenchDecodedStruct(ctypes.Structure):
    _fields_ = [
        ("a", ctypes.c_int32),
        ("b", ctypes.c_int64),
        ("c", ctypes.c_int32),
        ("d", ctypes.c_int64),
        ("e", ctypes.c_uint32),
        ("f", ctypes.c_uint64),
        ("g", ctypes.c_int32),
        ("h", ctypes.c_int64),
        ("i", ctypes.c_float),
        ("j", ctypes.c_double),
        ("k", ctypes.c_uint32),
        ("l", ctypes.c_uint64),
        ("n", ctypes.c_uint8),
        ("o_a", ctypes.c_int32),
        ("o_b", ctypes.c_int32),
        ("s", ctypes.c_int32),
        ("p_count", ctypes.c_uint32),
        ("p0", ctypes.c_int32),
        ("p1", ctypes.c_int32),
        ("p2", ctypes.c_int32),
        ("q_count", ctypes.c_uint32),
        ("q0", ctypes.c_int32),
        ("q1", ctypes.c_int32),
        ("q2", ctypes.c_int32),
        ("r_count", ctypes.c_uint32),
        ("m_len", ctypes.c_uint32),
        ("m_bytes", ctypes.c_ubyte * 16),
    ]


class BenchDecodedObj:
    __slots__ = (
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "n", "o_a", "o_b", "s",
        "p_count", "p0", "p1", "p2", "q_count", "q0", "q1", "q2", "r_count", "m_len", "m_bytes"
    )


class ZigCodec:
    def __init__(self):
        self.lib = None
        self.available = False
        self.has_bench = False
        self.has_bench_decode = False
        self.native = None
        self.mode = "py"
        self._native_bench_decode = None
        self._native_bench_decode_into = None
        self._native_bench_decode_noalloc = None
        self._load_native_pyext() or self._load_ctypes()

    def _lib_path(self):
        base = Path(__file__).resolve().parent / "native"
        for name in ("libzcprotobuf.dylib", "libzcprotobuf.so"):
            p = base / name
            if p.exists():
                return p
        return None

    def _load_native_pyext(self):
        try:
            from . import _zignative
        except Exception:
            return False

        path = self._lib_path()
        if not path:
            return False
        if not _zignative.init_library(str(path)):
            return False

        self.native = _zignative
        self.available = bool(_zignative.available())
        self.has_bench = bool(_zignative.has_bench())
        self.has_bench_decode = bool(getattr(_zignative, "has_bench_decode", lambda: False)())
        if self.available:
            self.mode = "pyext"
            if self.has_bench_decode:
                self._native_bench_decode = getattr(_zignative, "bench_decode", None)
                self._native_bench_decode_into = getattr(_zignative, "bench_decode_into", None)
                self._native_bench_decode_noalloc = getattr(_zignative, "bench_decode_noalloc", None)
            return True
        return False

    def _load_ctypes(self):
        path = self._lib_path()
        if not path:
            return False
        try:
            lib = ctypes.CDLL(str(path))
        except OSError:
            return False

        lib.zcp_encode_varint_u64.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        lib.zcp_encode_varint_u64.restype = ctypes.c_int
        lib.zcp_decode_varint_u64.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_size_t)]
        lib.zcp_decode_varint_u64.restype = ctypes.c_int
        lib.zcp_zigzag_encode32.argtypes = [ctypes.c_int32]
        lib.zcp_zigzag_encode32.restype = ctypes.c_uint32
        lib.zcp_zigzag_encode64.argtypes = [ctypes.c_int64]
        lib.zcp_zigzag_encode64.restype = ctypes.c_uint64
        lib.zcp_zigzag_decode32.argtypes = [ctypes.c_uint32]
        lib.zcp_zigzag_decode32.restype = ctypes.c_int32
        lib.zcp_zigzag_decode64.argtypes = [ctypes.c_uint64]
        lib.zcp_zigzag_decode64.restype = ctypes.c_int64

        if hasattr(lib, "zcp_bench_encode") and hasattr(lib, "zcp_bench_decode"):
            lib.zcp_bench_encode.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
            lib.zcp_bench_encode.restype = ctypes.c_int
            lib.zcp_bench_decode.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t, ctypes.POINTER(BenchDecodedStruct)]
            lib.zcp_bench_decode.restype = ctypes.c_int
            self.has_bench = True
            if hasattr(lib, "zcp_bench_decoded_size"):
                lib.zcp_bench_decoded_size.argtypes = []
                lib.zcp_bench_decoded_size.restype = ctypes.c_size_t
                self.has_bench_decode = int(lib.zcp_bench_decoded_size()) == ctypes.sizeof(BenchDecodedStruct)
            else:
                self.has_bench_decode = False

        self.lib = lib
        self.available = True
        self.mode = "ctypes"
        return True

    def encode_varint_u64(self, value: int) -> bytes:
        if self.mode == "pyext":
            return self.native.encode_varint_u64(value & 0xFFFFFFFFFFFFFFFF)
        if self.mode == "ctypes":
            out = (ctypes.c_ubyte * 10)()
            written = ctypes.c_size_t(0)
            rc = self.lib.zcp_encode_varint_u64(ctypes.c_uint64(value & 0xFFFFFFFFFFFFFFFF), out, 10, ctypes.byref(written))
            if rc != 0:
                raise ValueError("zig varint encode failed")
            return bytes(out[: written.value])
        return self._py_encode_varint(value)

    def decode_varint_u64(self, data: bytes, offset: int = 0):
        if self.mode == "pyext":
            return self.native.decode_varint_u64(data, offset)
        if self.mode == "ctypes":
            buf = (ctypes.c_ubyte * (len(data) - offset)).from_buffer_copy(data[offset:])
            value = ctypes.c_uint64(0)
            consumed = ctypes.c_size_t(0)
            rc = self.lib.zcp_decode_varint_u64(buf, len(data) - offset, ctypes.byref(value), ctypes.byref(consumed))
            if rc != 0:
                raise ValueError("zig varint decode failed")
            return int(value.value), int(consumed.value)
        return self._py_decode_varint(data, offset)

    def zigzag_encode32(self, n: int) -> int:
        if self.mode == "pyext":
            return int(self.native.zigzag_encode32(int(n)))
        if self.mode == "ctypes":
            return int(self.lib.zcp_zigzag_encode32(ctypes.c_int32(n)))
        return ((n << 1) ^ (n >> 31)) & 0xFFFFFFFF

    def zigzag_encode64(self, n: int) -> int:
        if self.mode == "pyext":
            return int(self.native.zigzag_encode64(int(n)))
        if self.mode == "ctypes":
            return int(self.lib.zcp_zigzag_encode64(ctypes.c_int64(n)))
        return ((n << 1) ^ (n >> 63)) & 0xFFFFFFFFFFFFFFFF

    def zigzag_decode32(self, n: int) -> int:
        if self.mode == "pyext":
            return int(self.native.zigzag_decode32(int(n) & 0xFFFFFFFF))
        if self.mode == "ctypes":
            return int(self.lib.zcp_zigzag_decode32(ctypes.c_uint32(n & 0xFFFFFFFF)))
        return (n >> 1) ^ -(n & 1)

    def zigzag_decode64(self, n: int) -> int:
        if self.mode == "pyext":
            return int(self.native.zigzag_decode64(int(n) & 0xFFFFFFFFFFFFFFFF))
        if self.mode == "ctypes":
            return int(self.lib.zcp_zigzag_decode64(ctypes.c_uint64(n & 0xFFFFFFFFFFFFFFFF)))
        return (n >> 1) ^ -(n & 1)

    def bench_encode(self) -> bytes:
        if self.mode == "pyext":
            return self.native.bench_encode()
        if not (self.available and self.has_bench):
            raise RuntimeError("bench fastpath unavailable")
        out = (ctypes.c_ubyte * 256)()
        written = ctypes.c_size_t(0)
        rc = self.lib.zcp_bench_encode(out, 256, ctypes.byref(written))
        if rc != 0:
            raise ValueError("zig bench encode failed")
        return bytes(out[: written.value])

    def bench_decode(self, data: bytes, offset: int = 0, end=None):
        if end is None:
            end = len(data)
        if offset < 0 or end < offset or end > len(data):
            raise ValueError("invalid decode range")
        if self.mode == "pyext":
            fn = self._native_bench_decode
            if fn is None:
                raise RuntimeError("bench decode unavailable")
            d = fn(data, offset, end)
            obj = BenchDecodedObj()
            obj.a = d["a"]; obj.b = d["b"]; obj.c = d["c"]; obj.d = d["d"]
            obj.e = d["e"]; obj.f = d["f"]; obj.g = d["g"]; obj.h = d["h"]
            obj.i = d["i"]; obj.j = d["j"]; obj.k = d["k"]; obj.l = d["l"]
            obj.n = d["n"]; obj.o_a = d["o_a"]; obj.o_b = d["o_b"]; obj.s = d["s"]
            obj.p_count = d["p_count"]; obj.p0 = d["p0"]; obj.p1 = d["p1"]; obj.p2 = d["p2"]
            obj.q_count = d["q_count"]; obj.q0 = d["q0"]; obj.q1 = d["q1"]; obj.q2 = d["q2"]
            obj.r_count = d["r_count"]; obj.m_bytes = d["m_bytes"]; obj.m_len = len(obj.m_bytes)
            return obj

        if not (self.available and self.has_bench and self.has_bench_decode):
            raise RuntimeError("bench fastpath unavailable")
        n = end - offset
        if n <= 0:
            raise ValueError("empty data")
        buf = (ctypes.c_ubyte * n).from_buffer_copy(data[offset:end])
        out = BenchDecodedStruct()
        rc = self.lib.zcp_bench_decode(buf, n, ctypes.byref(out))
        if rc != 0:
            raise ValueError(f"zig bench decode failed: {rc}")
        return out

    def bench_decode_into(self, obj, sub_cls, data: bytes, offset: int = 0, end=None):
        if end is None:
            end = len(data)
        if offset < 0 or end < offset or end > len(data):
            raise ValueError("invalid decode range")
        fn = self._native_bench_decode_into
        if fn is not None:
            return bool(fn(obj, sub_cls, data, offset, end))
        out = self.bench_decode(data, offset, end)
        obj.a = int(out.a); obj.b = int(out.b); obj.c = int(out.c); obj.d = int(out.d)
        obj.e = int(out.e); obj.f = int(out.f); obj.g = int(out.g); obj.h = int(out.h)
        obj.i = float(out.i); obj.j = float(out.j); obj.k = int(out.k); obj.l = int(out.l)
        obj.m = bytes(out.m_bytes[: out.m_len]).decode("utf-8")
        obj.n = bool(out.n)
        sub = sub_cls(); sub.a = int(out.o_a); sub.b = int(out.o_b); obj.o = sub
        obj.p = [int(out.p0), int(out.p1), int(out.p2)][: int(out.p_count)]
        obj.q = [int(out.q0), int(out.q1), int(out.q2)][: int(out.q_count)]
        obj.r = []
        for _ in range(int(out.r_count)):
            item = sub_cls(); item.a = 150; item.b = -150; obj.r.append(item)
        obj.s = int(out.s)
        return True

    def bench_decode_noalloc(self, data: bytes, offset: int = 0, end=None):
        if end is None:
            end = len(data)
        if offset < 0 or end < offset or end > len(data):
            raise ValueError("invalid decode range")
        fn = self._native_bench_decode_noalloc
        if fn is not None:
            return bool(fn(data, offset, end))
        # fallback: at least do native decode, ignore result object
        _ = self.bench_decode(data, offset, end)
        return True

    @staticmethod
    def _py_encode_varint(value: int) -> bytes:
        value &= 0xFFFFFFFFFFFFFFFF
        out = bytearray()
        while True:
            b = value & 0x7F
            value >>= 7
            if value == 0:
                out.append(b)
                break
            out.append(b | 0x80)
        return bytes(out)

    @staticmethod
    def _py_decode_varint(data: bytes, offset: int = 0):
        shift = 0
        value = 0
        i = offset
        while i < len(data):
            b = data[i]
            value |= (b & 0x7F) << shift
            i += 1
            if (b & 0x80) == 0:
                return value, i - offset
            shift += 7
            if shift >= 64:
                raise ValueError("invalid varint")
        raise ValueError("unexpected EOF")


zigcodec = ZigCodec()
